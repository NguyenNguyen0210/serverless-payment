"""Standalone AWS Lambda handler (Week 3). Deploy ONLY this lambda_function.py.
No shared.py and no imports from project-local modules.
"""
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


def handle(event):
    if event.get('routeKey') != 'GET /transactions/{transactionId}':
        return error(404, 'ROUTE_NOT_FOUND', 'Unsupported route')
    user = verified_user(event)
    if not user:
        return error(401, 'UNAUTHORIZED', 'Missing verified identity')
    tx_id = (event.get('pathParameters') or {}).get('transactionId')
    if not isinstance(tx_id, str) or len(tx_id) > 64 or not tx_id:
        return error(400, 'INVALID_TRANSACTION_ID', 'Invalid transactionId')
    # transactionId UUID v4 is preferred. No hard requirement for historic IDs.
    record = ddb_get(TRANSACTIONS_TABLE, {'transactionId': tx_id})
    if record is None:
        return error(404, 'TRANSACTION_NOT_FOUND', 'Transaction not found')
    from_wallet = ddb_get(WALLETS_TABLE, {'walletId': record['fromWalletId']})
    to_wallet = ddb_get(WALLETS_TABLE, {'walletId': record['toWalletId']})
    participants = {w.get('ownerId') for w in (from_wallet, to_wallet) if w}
    if user not in participants:
        return error(403, 'TRANSACTION_FORBIDDEN', 'You cannot view this transaction')
    return response(200, {field: record.get(field) for field in
                          ('transactionId', 'fromWalletId', 'toWalletId', 'amount',
                           'currency', 'status', 'createdAt') if field in record})


def lambda_handler(event, context):
    try:
        return handle(event)
    except Exception:
        LOG.exception('transaction_query_unexpected_failure')
        return error(500, 'INTERNAL_ERROR', 'Unexpected server error')
