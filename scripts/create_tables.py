#!/usr/bin/env python3
"""Idempotent infrastructure initializer. Dry-run unless --apply is supplied.

Creates Wallets, Transactions (with two GSIs), IdempotencyKeys. For an existing
Transactions table, creates only missing indexes, one at a time.
"""
import argparse
import os
import time
import boto3
from botocore.exceptions import ClientError

PREFIX = os.environ.get('TABLE_PREFIX', 'serverless-payment')
REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
TAGS = [{'Key': 'Project', 'Value': 'serverless-payment'},
        {'Key': 'Owner', 'Value': os.environ.get('RESOURCE_OWNER', 'Serverless-Team')},
        {'Key': 'Environment', 'Value': 'Lab'}]


def wait_ready(ddb, table, wait_for_indexes=True):
    while True:
        desc = ddb.describe_table(TableName=table)['Table']
        indexes = desc.get('GlobalSecondaryIndexes', [])
        if desc['TableStatus'] == 'ACTIVE' and (
            not wait_for_indexes or all(x['IndexStatus'] == 'ACTIVE' for x in indexes)):
            return desc
        time.sleep(4)


def create_new(ddb, table, keys, attributes, gsis=None):
    args = dict(TableName=table,
                KeySchema=[{'AttributeName': k, 'KeyType': t} for k, t in keys],
                AttributeDefinitions=[{'AttributeName': a, 'AttributeType': 'S'} for a in attributes],
                BillingMode='PAY_PER_REQUEST', Tags=TAGS)
    if gsis:
        args['GlobalSecondaryIndexes'] = [
            {'IndexName': index, 'KeySchema': [
                {'AttributeName': key, 'KeyType': 'HASH'},
                {'AttributeName': 'timeKey', 'KeyType': 'RANGE'}],
             'Projection': {'ProjectionType': 'ALL'}} for index, key in gsis]
    print('CREATING', table)
    ddb.create_table(**args)
    return wait_ready(ddb, table)


def ensure_gsis(ddb, table):
    expected = {'FromWalletIndex': 'fromWalletId', 'ToWalletIndex': 'toWalletId'}
    for index, key in expected.items():
        desc = wait_ready(ddb, table)
        existing = {x['IndexName']: x for x in desc.get('GlobalSecondaryIndexes', [])}
        if index in existing:
            keys = existing[index]['KeySchema']
            if keys != [{'AttributeName': key, 'KeyType': 'HASH'},
                        {'AttributeName': 'timeKey', 'KeyType': 'RANGE'}]:
                raise RuntimeError(f'{table}/{index} has wrong key schema')
            print('EXISTS GSI', index)
            continue
        print('CREATING GSI', index)
        ddb.update_table(TableName=table,
                         AttributeDefinitions=[
                             {'AttributeName': key, 'AttributeType': 'S'},
                             {'AttributeName': 'timeKey', 'AttributeType': 'S'}],
                         GlobalSecondaryIndexUpdates=[{'Create': {
                             'IndexName': index,
                             'KeySchema': [{'AttributeName': key, 'KeyType': 'HASH'},
                                           {'AttributeName': 'timeKey', 'KeyType': 'RANGE'}],
                             'Projection': {'ProjectionType': 'ALL'}}}])
        wait_ready(ddb, table)


def ensure_table(ddb, table, keys, attributes, gsis=None):
    try:
        desc = ddb.describe_table(TableName=table)['Table']
        print('EXISTS', table)
    except ddb.exceptions.ResourceNotFoundException:
        desc = create_new(ddb, table, keys, attributes, gsis)
    want = [{'AttributeName': k, 'KeyType': t} for k, t in keys]
    if desc['KeySchema'] != want:
        raise RuntimeError(f'{table} has wrong primary key schema; not modifying existing data')
    if gsis:
        ensure_gsis(ddb, table)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--apply', action='store_true', help='Actually create missing resources')
    p.add_argument('--region', default=REGION)
    args = p.parse_args()
    wallet, tx, idem = (PREFIX + '-wallets', PREFIX + '-transactions', PREFIX + '-idempotency')
    print('REGION', args.region, 'TABLES', wallet, tx, idem)
    if not args.apply:
        print('DRY RUN. Re-run with --apply to create missing tables/indexes.')
        return
    session = boto3.Session(region_name=args.region)
    print('ACCOUNT', session.client('sts').get_caller_identity()['Account'])
    ddb = session.client('dynamodb')
    ensure_table(ddb, wallet, [('walletId', 'HASH')], ['walletId'])
    ensure_table(ddb, tx, [('transactionId', 'HASH')],
                 ['transactionId', 'fromWalletId', 'toWalletId', 'timeKey'],
                 [('FromWalletIndex', 'fromWalletId'), ('ToWalletIndex', 'toWalletId')])
    ensure_table(ddb, idem, [('userId', 'HASH'), ('idempotencyKey', 'RANGE')],
                 ['userId', 'idempotencyKey'])
    print('ALL READY')


if __name__ == '__main__':
    main()
