"""Safe seed: writes demo wallets only when they do not already exist.
Run in AWS CloudShell with us-east-1 selected. Never overwrites tested balances.
"""
import os
import boto3
from botocore.exceptions import ClientError

TABLE_NAME = os.environ.get('TABLE_NAME', 'serverless-payment')
TABLE = boto3.resource('dynamodb', region_name='us-east-1').Table(TABLE_NAME)
SEED = [
    ('W001', 'user-a', 100000, 'VND', 'ACTIVE'),
    ('W002', 'user-b', 50000, 'VND', 'ACTIVE'),
    ('W003', 'user-b', 20000, 'VND', 'SUSPENDED'),
    ('W004', 'user-a', 10000, 'USD', 'ACTIVE'),
]

for wallet_id, owner, balance, currency, status in SEED:
    item = {'PK': f'WALLET#{wallet_id}', 'SK': 'META', 'walletId': wallet_id,
            'ownerId': owner, 'balance': balance, 'currency': currency, 'status': status}
    try:
        TABLE.put_item(Item=item, ConditionExpression='attribute_not_exists(PK)')
        print('CREATED', wallet_id, balance, currency, status)
    except ClientError as exc:
        if exc.response.get('Error', {}).get('Code') == 'ConditionalCheckFailedException':
            print('SKIPPED (already exists)', wallet_id)
        else:
            raise
