"""Standalone AWS Lambda handler (Week 3). Deploy ONLY this lambda_function.py.
No shared.py and no imports from project-local modules.
"""
import base64
import json
import logging
import os
import re

import boto3

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
DDB = boto3.client('dynamodb')
WALLETS_TABLE = os.environ.get('WALLETS_TABLE', 'serverless-payment-wallets')
TRANSACTIONS_TABLE = os.environ.get('TRANSACTIONS_TABLE', 'serverless-payment-transactions')
FROM_WALLET_INDEX = os.environ.get('FROM_WALLET_INDEX', 'FromWalletIndex')
TO_WALLET_INDEX = os.environ.get('TO_WALLET_INDEX', 'ToWalletIndex')


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


def valid_wallet_id(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,64}', value) is not None


def wallet_access(event):
    user = verified_user(event)
    if not user:
        return None, error(401, 'UNAUTHORIZED', 'Missing verified identity')
    wallet_id = (event.get('pathParameters') or {}).get('walletId')
    if not valid_wallet_id(wallet_id):
        return None, error(400, 'INVALID_WALLET', 'Invalid wallet ID')
    wallet = ddb_get(WALLETS_TABLE, {'walletId': wallet_id})
    if wallet is None:
        return None, error(404, 'WALLET_NOT_FOUND', 'Wallet not found')
    if wallet.get('ownerId') != user:
        return None, error(403, 'WALLET_FORBIDDEN', 'Not permitted to view this wallet')
    return wallet, None


def cursor_encode(wallet_id, user_id, time_key):
    payload = json.dumps({'v': 1, 'w': wallet_id, 'u': user_id, 'before': time_key},
                         ensure_ascii=False, separators=(',', ':')).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip('=')


def cursor_decode(raw, wallet_id, user_id):
    if not isinstance(raw, str) or not 1 <= len(raw) <= 1500 or not re.fullmatch(r'[A-Za-z0-9_-]+', raw):
        raise ValueError('Invalid nextToken')
    try:
        obj = json.loads(base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4)))
    except (ValueError, UnicodeDecodeError, TypeError) as exc:
        raise ValueError('Invalid nextToken') from exc
    if (not isinstance(obj, dict) or obj.get('v') != 1 or obj.get('w') != wallet_id
            or obj.get('u') != user_id or not isinstance(obj.get('before'), str)
            or len(obj['before']) > 200 or not obj['before']):
        raise ValueError('Invalid nextToken')
    return obj['before']


def history_query(index, key_name, wallet_id, cutoff, page_size):
    keys = '#wallet = :wallet'
    values = {':wallet': attr_s(wallet_id)}
    names = {'#wallet': key_name}
    if cutoff:
        keys += ' AND #time < :before'
        names['#time'] = 'timeKey'
        values[':before'] = attr_s(cutoff)
    result = DDB.query(
        TableName=TRANSACTIONS_TABLE, IndexName=index,
        KeyConditionExpression=keys, ExpressionAttributeNames=names,
        ExpressionAttributeValues=values, ScanIndexForward=False,
        Limit=page_size,
    )
    return [unpack_item(item) for item in result.get('Items', [])]


def history(event, wallet):
    user = verified_user(event)
    wallet_id = wallet['walletId']
    query = event.get('queryStringParameters') or {}
    try:
        raw_limit = str(query.get('limit', '10'))
        if not re.fullmatch(r'\d{1,2}', raw_limit):
            raise ValueError('Invalid limit')
        limit = int(raw_limit)
        if not 1 <= limit <= 50:
            raise ValueError('Invalid limit')
        before = cursor_decode(query['nextToken'], wallet_id, user) if query.get('nextToken') else None
    except (ValueError, TypeError) as exc:
        return error(400, 'INVALID_PAGINATION', str(exc))

    # Fetch limit+1 from BOTH indexes, then merge by timeKey to keep pagination
    # precise for immutable, stable data. Each index query may read up to 1 MB.
    outbound = history_query(FROM_WALLET_INDEX, 'fromWalletId', wallet_id, before, limit + 1)
    inbound = history_query(TO_WALLET_INDEX, 'toWalletId', wallet_id, before, limit + 1)
    by_id = {}
    for record in outbound + inbound:
        if record and record.get('transactionId') and record.get('timeKey'):
            by_id[record['transactionId']] = record
    ordered = sorted(by_id.values(), key=lambda item: item['timeKey'], reverse=True)
    selected = ordered[:limit]
    items = []
    for item in selected:
        out = item['fromWalletId'] == wallet_id
        items.append({
            'transactionId': item['transactionId'],
            'type': 'OUTGOING' if out else 'INCOMING',
            'counterpartyWalletId': item['toWalletId'] if out else item['fromWalletId'],
            'amount': item['amount'], 'currency': item['currency'],
            'status': item['status'], 'createdAt': item['createdAt'],
        })
    next_token = (cursor_encode(wallet_id, user, selected[-1]['timeKey'])
                  if len(ordered) > limit else None)
    return response(200, {'walletId': wallet_id, 'items': items, 'nextToken': next_token})


def handle(event):
    route = event.get('routeKey')
    if route not in {'GET /wallets/{walletId}', 'GET /wallets/{walletId}/transactions'}:
        return error(404, 'ROUTE_NOT_FOUND', 'Unsupported route')
    wallet, failure = wallet_access(event)
    if failure:
        return failure
    if route == 'GET /wallets/{walletId}':
        return response(200, {field: wallet.get(field) for field in
                              ('walletId', 'ownerId', 'balance', 'currency', 'status', 'createdAt', 'updatedAt')
                              if field in wallet})
    return history(event, wallet)


def lambda_handler(event, context):
    try:
        return handle(event)
    except Exception:
        LOG.exception('wallet_query_unexpected_failure')
        return error(500, 'INTERNAL_ERROR', 'Unexpected server error')
