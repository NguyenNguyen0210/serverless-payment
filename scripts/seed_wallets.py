#!/usr/bin/env python3
"""Seeds four wallets without ever overwriting existing balances."""
import argparse
import os
from datetime import datetime, timezone

import boto3

REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
WALLETS = os.environ.get('WALLETS_TABLE', 'serverless-payment-wallets')
SEED = [
    {'walletId': 'W001', 'ownerId': 'user-a', 'balance': 100000, 'currency': 'VND', 'status': 'ACTIVE'},
    {'walletId': 'W002', 'ownerId': 'user-b', 'balance': 50000, 'currency': 'VND', 'status': 'ACTIVE'},
    {'walletId': 'W003', 'ownerId': 'user-b', 'balance': 20000, 'currency': 'VND', 'status': 'SUSPENDED'},
    {'walletId': 'W004', 'ownerId': 'user-a', 'balance': 10000, 'currency': 'USD', 'status': 'ACTIVE'},
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--apply', action='store_true')
    p.add_argument('--region', default=REGION)
    args = p.parse_args()
    print('TARGET TABLE:', WALLETS, 'REGION:', args.region)
    for wallet in SEED:
        print(wallet)
    if not args.apply:
        print('DRY RUN: no data written')
        return
    session = boto3.Session(region_name=args.region)
    print('ACCOUNT', session.client('sts').get_caller_identity()['Account'])
    table = session.resource('dynamodb').Table(WALLETS)
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    for wallet in SEED:
        item = dict(wallet, createdAt=now, updatedAt=now)
        try:
            table.put_item(Item=item, ConditionExpression='attribute_not_exists(walletId)')
            print('SEEDED', wallet['walletId'])
        except table.meta.client.exceptions.ConditionalCheckFailedException:
            print('SKIP EXISTING WALLET', wallet['walletId'])
    print('Seed completed without overwriting existing balances.')


if __name__ == '__main__':
    main()
