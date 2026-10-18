"""Week 2 TransferLambda — DynamoDB single-table, atomic payments and idempotency.

AWS HTTP API payload v2.0 + Lambda REQUEST authorizer simple-response context.
No JWT processing happens here: the authorizer authenticates the caller first.
"""

import base64
import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
TABLE = os.environ.get('TABLE_NAME', 'serverless-payment')
DDB = boto3.client('dynamodb')


def response(status, payload):
    return {'statusCode': status, 'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(payload, ensure_ascii=False)}


def error(status, code, message):
    return response(status, {'error': {'code': code, 'message': message}})


def attr_s(value):
    return {'S': str(value)}


def attr_n(value):
    return {'N': str(value)}


def ddb_get(pk):
    # Strong reads are necessary to recognize the latest successful request.
    result = DDB.get_item(TableName=TABLE,
                          Key={'PK': attr_s(pk), 'SK': attr_s('META')},
                          ConsistentRead=True)
    return result.get('Item')


def field(item, name, default=None):
    if not item:
        return default
    val = item.get(name)
    if not val:
        return default
    if 'S' in val:
        return val['S']
    if 'N' in val:
        return int(val['N'])
    return default


def canonical_hash(user_id, frm, to, amount):
    payload = {'userId': user_id, 'fromWalletId': frm, 'toWalletId': to,
               'amount': amount, 'currency': 'VND'}
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def uuid4_key(raw):
    if not isinstance(raw, str):
        return False
    try:
        value = uuid.UUID(raw)
        return value.version == 4 and str(value) == raw.lower()
    except (ValueError, AttributeError):
        return False


def prior_result(item, request_hash):
    if field(item, 'requestHash') != request_hash:
        return error(409, 'IDEMPOTENCY_KEY_CONFLICT', 'Key already used for another request.')
    return response(200, {
        'transactionId': field(item, 'transactionId'),
        'fromWalletId': field(item, 'fromWalletId'),
        'toWalletId': field(item, 'toWalletId'),
        'amount': field(item, 'amount'),
        'currency': 'VND', 'status': 'SUCCESS',
        'replayed': True, 'createdAt': field(item, 'createdAt')
    })


def check_wallets(frm, to, user_id, amount):
    """Readable errors for users; transaction conditions still enforce safety atomically."""
    source = ddb_get('WALLET#' + frm)
    target = ddb_get('WALLET#' + to)
    if not source or not target:
        return error(404, 'WALLET_NOT_FOUND', 'Source or destination wallet was not found.')
    if field(source, 'ownerId') != user_id:
        return error(403, 'WALLET_FORBIDDEN', 'Caller does not own source wallet.')
    if field(source, 'status') != 'ACTIVE' or field(target, 'status') != 'ACTIVE':
        return error(409, 'WALLET_INACTIVE', 'Source or destination wallet is not active.')
    if field(source, 'currency') != 'VND' or field(target, 'currency') != 'VND':
        return error(400, 'UNSUPPORTED_CURRENCY', 'Both wallets must use VND.')
    if field(source, 'balance', 0) < amount:
        return error(409, 'INSUFFICIENT_FUNDS', 'Insufficient balance.')
    return None


def build_actions(ident, user_id, frm, to, amount, request_hash, transaction_id, now):
    """All four writes succeed or none do; no two actions target the same item."""
    base = {
        'transactionId': attr_s(transaction_id),
        'userId': attr_s(user_id),
        'idempotencyKey': attr_s(ident),
        'requestHash': attr_s(request_hash),
        'fromWalletId': attr_s(frm),
        'toWalletId': attr_s(to),
        'amount': attr_n(amount),
        'currency': attr_s('VND'),
        'status': attr_s('SUCCESS'),
        'createdAt': attr_s(now)
    }
    return [
        {'Put': {
            'TableName': TABLE,
            'Item': {'PK': attr_s(f'IDEMPOTENCY#{user_id}#{ident}'), 'SK': attr_s('META'), **base},
            'ConditionExpression': 'attribute_not_exists(PK)'
        }},
        {'Update': {
            'TableName': TABLE,
            'Key': {'PK': attr_s(f'WALLET#{frm}'), 'SK': attr_s('META')},
            'UpdateExpression': 'SET balance = balance - :amount, updatedAt = :now',
            'ConditionExpression': 'attribute_exists(PK) AND ownerId = :actor AND #st = :active AND currency = :vnd AND balance >= :amount',
            'ExpressionAttributeNames': {'#st': 'status'},
            'ExpressionAttributeValues': {':amount': attr_n(amount), ':now': attr_s(now),
                                          ':actor': attr_s(user_id), ':active': attr_s('ACTIVE'),
                                          ':vnd': attr_s('VND')}
        }},
        {'Update': {
            'TableName': TABLE,
            'Key': {'PK': attr_s(f'WALLET#{to}'), 'SK': attr_s('META')},
            'UpdateExpression': 'SET balance = balance + :amount, updatedAt = :now',
            'ConditionExpression': 'attribute_exists(PK) AND #st = :active AND currency = :vnd',
            'ExpressionAttributeNames': {'#st': 'status'},
            'ExpressionAttributeValues': {':amount': attr_n(amount), ':now': attr_s(now),
                                          ':active': attr_s('ACTIVE'), ':vnd': attr_s('VND')}
        }},
        {'Put': {
            'TableName': TABLE,
            'Item': {'PK': attr_s(f'TRANSFER#{transaction_id}'), 'SK': attr_s('META'), **base},
            'ConditionExpression': 'attribute_not_exists(PK)'
        }}
    ]


def handle(event):
    # Never trust userId in request body. Only trust authenticated authorizer context.
    authorizer = ((event.get('requestContext') or {}).get('authorizer') or {})
    trusted_context = authorizer.get('lambda') or {}
    user_id = trusted_context.get('userId') or trusted_context.get('sub')
    if not isinstance(user_id, str) or not user_id:
        return error(401, 'UNAUTHORIZED', 'Missing verified authorizer identity.')

    headers = {str(k).lower(): v for k, v in (event.get('headers') or {}).items()}
    ident = headers.get('idempotency-key')
    if not ident:
        return error(400, 'MISSING_IDEMPOTENCY_KEY', 'Idempotency-Key is required.')
    if not uuid4_key(ident):
        return error(400, 'INVALID_IDEMPOTENCY_KEY', 'Idempotency-Key must be UUID v4.')

    try:
        raw_body = event.get('body')
        if event.get('isBase64Encoded'):
            raw_body = base64.b64decode(raw_body).decode('utf-8')
        body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
    except (ValueError, TypeError):
        return error(400, 'INVALID_REQUEST', 'Malformed JSON body.')
    if not isinstance(body, dict):
        return error(400, 'INVALID_REQUEST', 'Body must be a JSON object.')

    frm, to, amount = body.get('fromWalletId'), body.get('toWalletId'), body.get('amount')
    if not isinstance(frm, str) or not isinstance(to, str) or not frm or not to or frm == to:
        return error(400, 'INVALID_WALLET', 'Wallet IDs must be nonempty and different.')
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0 or amount > 10**15:
        return error(400, 'INVALID_AMOUNT', 'Amount must be a positive VND integer (max 10^15).')

    request_hash = canonical_hash(user_id, frm, to, amount)
    idem_pk = f'IDEMPOTENCY#{user_id}#{ident}'
    previous = ddb_get(idem_pk)
    if previous:
        return prior_result(previous, request_hash)

    validation_error = check_wallets(frm, to, user_id, amount)
    if validation_error:
        return validation_error

    transaction_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    actions = build_actions(ident, user_id, frm, to, amount, request_hash, transaction_id, now)

    for attempt in range(3):
        try:
            DDB.transact_write_items(TransactItems=actions)
            LOG.info('payment_committed transaction_id=%s request_id=%s', transaction_id,
                     (event.get('requestContext') or {}).get('requestId', 'direct-test'))
            return response(201, {'transactionId': transaction_id, 'fromWalletId': frm,
                                  'toWalletId': to, 'amount': amount, 'currency': 'VND',
                                  'status': 'SUCCESS', 'replayed': False, 'createdAt': now})
        except ClientError as exc:
            name = exc.response.get('Error', {}).get('Code', '')
            if name not in {'TransactionCanceledException', 'TransactionInProgressException'}:
                raise
            # A concurrent request may have committed while ours was cancelled.
            previous = ddb_get(idem_pk)
            if previous:
                return prior_result(previous, request_hash)
            reasons = exc.response.get('CancellationReasons') or []
            codes = [r.get('Code') for r in reasons]
            if any(code in {'TransactionConflict', 'ProvisionedThroughputExceeded', 'ThrottlingError'}
                   for code in codes) or name == 'TransactionInProgressException':
                if attempt < 2:
                    time.sleep(0.15 * (attempt + 1))
                    continue
                return error(503, 'TRANSACTION_CONFLICT', 'Please retry with the same idempotency key.')
            validation_error = check_wallets(frm, to, user_id, amount)
            if validation_error:
                return validation_error
            if attempt < 2:
                time.sleep(0.15 * (attempt + 1))
                continue
            return error(503, 'TRANSACTION_CONFLICT', 'Please retry with the same idempotency key.')
    return error(503, 'TRANSACTION_CONFLICT', 'Please retry with the same idempotency key.')


def lambda_handler(event, context):
    try:
        return handle(event)
    except Exception:
        # No Authorization header, JWT, secrets or raw request bodies in the logs.
        LOG.exception('transfer_unexpected_failure')
        return error(500, 'INTERNAL_ERROR', 'Unexpected server error. Retry with the same key.')
