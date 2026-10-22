"""Standalone AWS Lambda handler (Week 3). Deploy ONLY this lambda_function.py.
No shared.py and no imports from project-local modules.
"""
import base64
import hashlib
import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
DDB = boto3.client('dynamodb')
WALLETS_TABLE = os.environ.get('WALLETS_TABLE', 'serverless-payment-wallets')
TRANSACTIONS_TABLE = os.environ.get('TRANSACTIONS_TABLE', 'serverless-payment-transactions')
IDEMPOTENCY_TABLE = os.environ.get('IDEMPOTENCY_TABLE', 'serverless-payment-idempotency')
MAX_AMOUNT = int(os.environ.get('MAX_TRANSFER_VND', '1000000000000'))
SQS_URL = os.environ.get('SQS_ERROR_QUEUE_URL')


def response(status, payload):
    return {
        'statusCode': status,
        'headers': {'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store'},
        'body': json.dumps(payload, ensure_ascii=False, separators=(',', ':')),
    }


def error(status, code, message):
    return response(status, {'error': {'code': code, 'message': message}})


def attr_s(value):
    return {'S': str(value)}


def attr_n(value):
    return {'N': str(value)}


def unpack_item(item):
    if not item:
        return None
    output = {}
    for key, value in item.items():
        if 'S' in value:
            output[key] = value['S']
        elif 'N' in value:
            raw = value['N']
            output[key] = int(raw) if re.fullmatch(r'-?\d+', raw) else raw
        elif 'BOOL' in value:
            output[key] = value['BOOL']
        elif 'NULL' in value:
            output[key] = None
    return output


def ddb_get(table, key, strong=True):
    raw = DDB.get_item(TableName=table, Key={k: attr_s(v) for k, v in key.items()}, ConsistentRead=strong)
    return unpack_item(raw.get('Item'))


def verified_user(event):
    """Identity is trusted only when called through the configured Lambda Authorizer."""
    context = (((event.get('requestContext') or {}).get('authorizer') or {}).get('lambda') or {})
    user_id = context.get('userId')
    return user_id if isinstance(user_id, str) and user_id else None


def req_id(event):
    return str((event.get('requestContext') or {}).get('requestId') or 'unknown')


def json_body(event):
    raw = event.get('body')
    if raw is None:
        raise ValueError('Missing JSON request body')
    if event.get('isBase64Encoded'):
        raw = base64.b64decode(raw, validate=True).decode('utf-8')
    if isinstance(raw, str):
        return json.loads(raw)
    return raw


def iso_now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def valid_wallet_id(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,64}', value) is not None


def log_event(event_name, **fields):
    """Machine-parseable application logs without leaking secrets."""
    print(json.dumps({'event': event_name, 'at': iso_now(), **fields}, separators=(',', ':')))


def alert_failure(event, error_type, idempotency_key=None):
    if not SQS_URL:
        return
    try:
        boto3.client('sqs').send_message(
            QueueUrl=SQS_URL,
            MessageBody=json.dumps({
                'requestId': req_id(event),
                'errorType': error_type,
                'idempotencyKey': idempotency_key,
                'at': iso_now(),
            }),
        )
    except Exception:
        LOG.exception('Failed to push failure event to DLQ')


def normalized_uuid(value):
    if not isinstance(value, str) or len(value) > 40:
        return None
    try:
        parsed = uuid.UUID(value)
        if parsed.version != 4 or value.lower() != str(parsed):
            return None
        return str(parsed)
    except (ValueError, TypeError, AttributeError):
        return None


def request_hash(user_id, src, dest, amount):
    content = {'userId': user_id, 'fromWalletId': src, 'toWalletId': dest,
               'amount': amount, 'currency': 'VND'}
    canonical = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def replay(previous, digest):
    if previous.get('requestHash') != digest:
        return error(409, 'IDEMPOTENCY_KEY_CONFLICT', 'Key was used with different transfer details')
    return response(200, {
        'transactionId': previous['transactionId'],
        'fromWalletId': previous['fromWalletId'],
        'toWalletId': previous['toWalletId'],
        'amount': previous['amount'],
        'currency': 'VND',
        'status': 'SUCCESS',
        'replayed': True,
        'createdAt': previous['createdAt'],
    })


def preflight(src, dest, amount, actor):
    wallet_src = ddb_get(WALLETS_TABLE, {'walletId': src})
    wallet_dest = ddb_get(WALLETS_TABLE, {'walletId': dest})
    if wallet_src is None or wallet_dest is None:
        return error(404, 'WALLET_NOT_FOUND', 'Source or destination wallet not found')
    if wallet_src.get('ownerId') != actor:
        return error(403, 'WALLET_FORBIDDEN', 'You do not own source wallet')
    if wallet_src.get('status') != 'ACTIVE' or wallet_dest.get('status') != 'ACTIVE':
        return error(409, 'WALLET_INACTIVE', 'Wallet is not active')
    if wallet_src.get('currency') != 'VND' or wallet_dest.get('currency') != 'VND':
        return error(400, 'UNSUPPORTED_CURRENCY', 'Only VND-to-VND transfers are supported')
    if wallet_src.get('balance', -1) < amount:
        return error(409, 'INSUFFICIENT_FUNDS', 'Insufficient funds')
    return None


def build_actions(user_id, idem_key, src, dest, amount, digest, tx_id, now):
    time_key = f'{now}#{tx_id}'
    base = {
        'transactionId': attr_s(tx_id), 'userId': attr_s(user_id),
        'idempotencyKey': attr_s(idem_key), 'requestHash': attr_s(digest),
        'fromWalletId': attr_s(src), 'toWalletId': attr_s(dest),
        'amount': attr_n(amount), 'currency': attr_s('VND'),
        'status': attr_s('SUCCESS'), 'createdAt': attr_s(now),
    }
    tx_record = {
        'transactionId': attr_s(tx_id), 'userId': attr_s(user_id),
        'fromWalletId': attr_s(src), 'toWalletId': attr_s(dest),
        'amount': attr_n(amount), 'currency': attr_s('VND'),
        'status': attr_s('SUCCESS'), 'createdAt': attr_s(now),
        'timeKey': attr_s(time_key),
    }
    return [
        {'Put': {'TableName': IDEMPOTENCY_TABLE,
                 'Item': {'userId': attr_s(user_id), 'idempotencyKey': attr_s(idem_key), **base},
                 'ConditionExpression': 'attribute_not_exists(userId)'}},
        {'Update': {'TableName': WALLETS_TABLE,
                    'Key': {'walletId': attr_s(src)},
                    'UpdateExpression': 'SET balance = balance - :amt, updatedAt = :now',
                    'ConditionExpression': ('attribute_exists(walletId) AND ownerId = :actor '
                                            'AND #st = :active AND currency = :vnd AND balance >= :amt'),
                    'ExpressionAttributeNames': {'#st': 'status'},
                    'ExpressionAttributeValues': {':amt': attr_n(amount), ':now': attr_s(now),
                                                 ':actor': attr_s(user_id), ':active': attr_s('ACTIVE'),
                                                 ':vnd': attr_s('VND')}}},
        {'Update': {'TableName': WALLETS_TABLE,
                    'Key': {'walletId': attr_s(dest)},
                    'UpdateExpression': 'SET balance = balance + :amt, updatedAt = :now',
                    'ConditionExpression': ('attribute_exists(walletId) AND #st = :active '
                                            'AND currency = :vnd'),
                    'ExpressionAttributeNames': {'#st': 'status'},
                    'ExpressionAttributeValues': {':amt': attr_n(amount), ':now': attr_s(now),
                                                 ':active': attr_s('ACTIVE'), ':vnd': attr_s('VND')}}},
        {'Put': {'TableName': TRANSACTIONS_TABLE, 'Item': tx_record,
                 'ConditionExpression': 'attribute_not_exists(transactionId)'}},
    ]


def handle(event):
    actor = verified_user(event)
    if not actor:
        return error(401, 'UNAUTHORIZED', 'Missing verified identity')
    headers = {str(k).lower(): v for k, v in (event.get('headers') or {}).items()}
    idem_key = normalized_uuid(headers.get('idempotency-key'))
    if not idem_key:
        return error(400, 'INVALID_IDEMPOTENCY_KEY', 'Idempotency-Key must be a UUID v4')
    try:
        body = json_body(event)
    except (ValueError, TypeError, UnicodeDecodeError):
        return error(400, 'INVALID_REQUEST', 'Invalid JSON body')
    if not isinstance(body, dict) or set(body) != {'fromWalletId', 'toWalletId', 'amount'}:
        return error(400, 'INVALID_REQUEST', 'Required: fromWalletId, toWalletId, amount')
    src, dest, amount = body['fromWalletId'], body['toWalletId'], body['amount']
    if not valid_wallet_id(src) or not valid_wallet_id(dest) or src == dest:
        return error(400, 'INVALID_WALLET', 'Wallet IDs must be valid and different')
    if isinstance(amount, bool) or not isinstance(amount, int) or not 0 < amount <= MAX_AMOUNT:
        return error(400, 'INVALID_AMOUNT', 'Amount must be positive integer VND')

    digest = request_hash(actor, src, dest, amount)
    key = {'userId': actor, 'idempotencyKey': idem_key}
    previous = ddb_get(IDEMPOTENCY_TABLE, key)
    if previous:
        return replay(previous, digest)

    failure = preflight(src, dest, amount, actor)
    if failure:
        return failure

    tx_id = str(uuid.uuid4())
    now = iso_now()
    actions = build_actions(actor, idem_key, src, dest, amount, digest, tx_id, now)

    for attempt in range(4):
        try:
            DDB.transact_write_items(TransactItems=actions)
            log_event('payment_committed', requestId=req_id(event), transactionId=tx_id)
            return response(201, {'transactionId': tx_id, 'fromWalletId': src,
                                  'toWalletId': dest, 'amount': amount, 'currency': 'VND',
                                  'status': 'SUCCESS', 'replayed': False, 'createdAt': now})
        except ClientError as exc:
            code = exc.response.get('Error', {}).get('Code', '')
            if code not in {'TransactionCanceledException', 'TransactionInProgressException',
                            'IdempotentParameterMismatchException'}:
                raise
            previous = ddb_get(IDEMPOTENCY_TABLE, key)
            if previous:
                return replay(previous, digest)
            if code == 'IdempotentParameterMismatchException':
                return error(409, 'TRANSACTION_CONFLICT', 'Conflicting transaction parameters')
            failure = preflight(src, dest, amount, actor)
            if failure:
                return failure
            if attempt < 3:
                time.sleep(0.1 * (2 ** attempt))
                continue
            return error(503, 'TRANSACTION_CONFLICT', 'Retry with the same Idempotency-Key')
    return error(503, 'TRANSACTION_CONFLICT', 'Retry with the same Idempotency-Key')


def lambda_handler(event, context):
    try:
        return handle(event)
    except Exception as exc:
        LOG.exception('transfer_unexpected_failure')
        headers = {str(k).lower(): v for k, v in (event.get('headers') or {}).items()}
        log_event('transfer_failed', requestId=req_id(event), errorType=type(exc).__name__)
        alert_failure(event, type(exc).__name__, normalized_uuid(headers.get('idempotency-key')))
        return error(500, 'INTERNAL_ERROR', 'Unknown result. Retry with same Idempotency-Key')

