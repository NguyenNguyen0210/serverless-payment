"""Unit tests for Wallet Query and Transaction Query Lambdas.
Run: python -m unittest tests/test_query.py -v
"""
import base64
import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure boto3/botocore mocks exist if not installed locally
if 'boto3' not in sys.modules:
    try:
        import boto3
    except ImportError:
        mock_b = MagicMock()
        sys.modules['boto3'] = mock_b

if 'botocore' not in sys.modules:
    try:
        import botocore
    except ImportError:
        mock_bc = MagicMock()
        mock_exc = MagicMock()
        class ClientError(Exception):
            def __init__(self, err, op=''):
                self.response = err
                self.operation_name = op
                super().__init__(str(err))
        mock_exc.ClientError = ClientError
        mock_bc.exceptions = mock_exc
        sys.modules['botocore'] = mock_bc
        sys.modules['botocore.exceptions'] = mock_exc

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, rel_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


wallet_mod = load_module('wallet_query_lambda', 'src/wallet_query/lambda_function.py')
tx_mod = load_module('transaction_query_lambda', 'src/transaction_query/lambda_function.py')


def make_wallet_event(route='GET /wallets/{walletId}', wallet_id='W001', user='user-a', query=None):
    return {
        'version': '2.0',
        'routeKey': route,
        'pathParameters': {'walletId': wallet_id} if wallet_id is not None else {},
        'queryStringParameters': query or {},
        'requestContext': {
            'authorizer': {'lambda': {'userId': user}} if user else {},
            'requestId': 'query-request-001',
        },
    }


def make_tx_event(tx_id='tx-uuid-1234', user='user-a', route='GET /transactions/{transactionId}'):
    return {
        'version': '2.0',
        'routeKey': route,
        'pathParameters': {'transactionId': tx_id} if tx_id is not None else {},
        'requestContext': {
            'authorizer': {'lambda': {'userId': user}} if user else {},
            'requestId': 'query-tx-request-001',
        },
    }


class WalletQueryLambdaTests(unittest.TestCase):
    def setUp(self):
        self.mock_ddb = MagicMock()
        self.ddb_patcher = patch.object(wallet_mod, 'DDB', self.mock_ddb)
        self.ddb_patcher.start()
        self.addCleanup(self.ddb_patcher.stop)

    def test_wallet_get_success(self):
        wallet_record = {
            'walletId': 'W001',
            'ownerId': 'user-a',
            'balance': 100000,
            'currency': 'VND',
            'status': 'ACTIVE',
            'createdAt': '2026-10-22T00:00:00Z',
            'updatedAt': '2026-10-22T06:00:00Z',
        }
        with patch.object(wallet_mod, 'ddb_get', return_value=wallet_record):
            res = wallet_mod.lambda_handler(make_wallet_event(wallet_id='W001', user='user-a'), None)

        self.assertEqual(res['statusCode'], 200)
        body = json.loads(res['body'])
        self.assertEqual(body['walletId'], 'W001')
        self.assertEqual(body['ownerId'], 'user-a')
        self.assertEqual(body['balance'], 100000)
        self.assertEqual(body['currency'], 'VND')
        self.assertEqual(body['status'], 'ACTIVE')

    def test_wallet_get_unauthorized_missing_user(self):
        res = wallet_mod.lambda_handler(make_wallet_event(user=None), None)
        self.assertEqual(res['statusCode'], 401)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'UNAUTHORIZED')

    def test_wallet_get_not_found(self):
        with patch.object(wallet_mod, 'ddb_get', return_value=None):
            res = wallet_mod.lambda_handler(make_wallet_event(wallet_id='W999', user='user-a'), None)
        self.assertEqual(res['statusCode'], 404)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'WALLET_NOT_FOUND')

    def test_wallet_get_forbidden_different_owner(self):
        wallet_record = {
            'walletId': 'W002',
            'ownerId': 'user-b',
            'balance': 50000,
            'currency': 'VND',
            'status': 'ACTIVE',
        }
        with patch.object(wallet_mod, 'ddb_get', return_value=wallet_record):
            res = wallet_mod.lambda_handler(make_wallet_event(wallet_id='W002', user='user-a'), None)
        self.assertEqual(res['statusCode'], 403)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'WALLET_FORBIDDEN')

    def test_wallet_get_invalid_wallet_id(self):
        res = wallet_mod.lambda_handler(make_wallet_event(wallet_id='!@#bad-wallet!'), None)
        self.assertEqual(res['statusCode'], 400)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'INVALID_WALLET')

    def test_wallet_unsupported_route(self):
        res = wallet_mod.lambda_handler(make_wallet_event(route='DELETE /wallets/{walletId}'), None)
        self.assertEqual(res['statusCode'], 404)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'ROUTE_NOT_FOUND')

    def test_wallet_history_success_merged_and_sorted(self):
        wallet_record = {'walletId': 'W001', 'ownerId': 'user-a', 'balance': 100000}
        outbound_tx = [{
            'transactionId': 'tx-out-1',
            'fromWalletId': 'W001',
            'toWalletId': 'W002',
            'amount': 20000,
            'currency': 'VND',
            'status': 'SUCCESS',
            'timeKey': '2026-10-22T07:00:00Z#tx-out-1',
            'createdAt': '2026-10-22T07:00:00Z',
        }]
        inbound_tx = [{
            'transactionId': 'tx-in-1',
            'fromWalletId': 'W003',
            'toWalletId': 'W001',
            'amount': 50000,
            'currency': 'VND',
            'status': 'SUCCESS',
            'timeKey': '2026-10-22T08:00:00Z#tx-in-1',
            'createdAt': '2026-10-22T08:00:00Z',
        }]

        with patch.object(wallet_mod, 'ddb_get', return_value=wallet_record), \
             patch.object(wallet_mod, 'history_query', side_effect=[outbound_tx, inbound_tx]):
            event = make_wallet_event(route='GET /wallets/{walletId}/transactions', wallet_id='W001', user='user-a')
            res = wallet_mod.lambda_handler(event, None)

        self.assertEqual(res['statusCode'], 200)
        body = json.loads(res['body'])
        self.assertEqual(body['walletId'], 'W001')
        self.assertEqual(len(body['items']), 2)

        # Sorted by timeKey desc: tx-in-1 (08:00) before tx-out-1 (07:00)
        self.assertEqual(body['items'][0]['transactionId'], 'tx-in-1')
        self.assertEqual(body['items'][0]['type'], 'INCOMING')
        self.assertEqual(body['items'][0]['counterpartyWalletId'], 'W003')

        self.assertEqual(body['items'][1]['transactionId'], 'tx-out-1')
        self.assertEqual(body['items'][1]['type'], 'OUTGOING')
        self.assertEqual(body['items'][1]['counterpartyWalletId'], 'W002')

    def test_wallet_history_invalid_limit(self):
        wallet_record = {'walletId': 'W001', 'ownerId': 'user-a'}
        with patch.object(wallet_mod, 'ddb_get', return_value=wallet_record):
            event = make_wallet_event(route='GET /wallets/{walletId}/transactions',
                                      wallet_id='W001', user='user-a', query={'limit': '100'})
            res = wallet_mod.lambda_handler(event, None)
        self.assertEqual(res['statusCode'], 400)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'INVALID_PAGINATION')

    def test_wallet_history_invalid_next_token(self):
        wallet_record = {'walletId': 'W001', 'ownerId': 'user-a'}
        with patch.object(wallet_mod, 'ddb_get', return_value=wallet_record):
            event = make_wallet_event(route='GET /wallets/{walletId}/transactions',
                                      wallet_id='W001', user='user-a', query={'nextToken': '!invalid-base64!'})
            res = wallet_mod.lambda_handler(event, None)
        self.assertEqual(res['statusCode'], 400)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'INVALID_PAGINATION')

    def test_wallet_cursor_encode_decode(self):
        encoded = wallet_mod.cursor_encode('W001', 'user-a', '2026-10-22T06:00:00Z#tx-1')
        self.assertIsInstance(encoded, str)
        decoded = wallet_mod.cursor_decode(encoded, 'W001', 'user-a')
        self.assertEqual(decoded, '2026-10-22T06:00:00Z#tx-1')

        # Decoding for different wallet or user raises ValueError
        with self.assertRaises(ValueError):
            wallet_mod.cursor_decode(encoded, 'W002', 'user-a')
        with self.assertRaises(ValueError):
            wallet_mod.cursor_decode(encoded, 'W001', 'user-b')


class TransactionQueryLambdaTests(unittest.TestCase):
    def setUp(self):
        self.mock_ddb = MagicMock()
        self.ddb_patcher = patch.object(tx_mod, 'DDB', self.mock_ddb)
        self.ddb_patcher.start()
        self.addCleanup(self.ddb_patcher.stop)

    def test_tx_get_success_sender_owner(self):
        tx_record = {
            'transactionId': 'tx-uuid-1234',
            'fromWalletId': 'W001',
            'toWalletId': 'W002',
            'amount': 30000,
            'currency': 'VND',
            'status': 'SUCCESS',
            'createdAt': '2026-10-22T06:00:00Z',
        }
        wallets = {
            'W001': {'walletId': 'W001', 'ownerId': 'user-a'},
            'W002': {'walletId': 'W002', 'ownerId': 'user-b'},
        }
        def mock_get(table, key, strong=True):
            if table == tx_mod.TRANSACTIONS_TABLE:
                return tx_record
            return wallets.get(key.get('walletId'))

        with patch.object(tx_mod, 'ddb_get', side_effect=mock_get):
            res = tx_mod.lambda_handler(make_tx_event(tx_id='tx-uuid-1234', user='user-a'), None)

        self.assertEqual(res['statusCode'], 200)
        body = json.loads(res['body'])
        self.assertEqual(body['transactionId'], 'tx-uuid-1234')
        self.assertEqual(body['fromWalletId'], 'W001')
        self.assertEqual(body['toWalletId'], 'W002')
        self.assertEqual(body['amount'], 30000)

    def test_tx_get_success_recipient_owner(self):
        tx_record = {
            'transactionId': 'tx-uuid-1234',
            'fromWalletId': 'W001',
            'toWalletId': 'W002',
            'amount': 30000,
            'currency': 'VND',
            'status': 'SUCCESS',
            'createdAt': '2026-10-22T06:00:00Z',
        }
        wallets = {
            'W001': {'walletId': 'W001', 'ownerId': 'user-a'},
            'W002': {'walletId': 'W002', 'ownerId': 'user-b'},
        }
        def mock_get(table, key, strong=True):
            if table == tx_mod.TRANSACTIONS_TABLE:
                return tx_record
            return wallets.get(key.get('walletId'))

        with patch.object(tx_mod, 'ddb_get', side_effect=mock_get):
            res = tx_mod.lambda_handler(make_tx_event(tx_id='tx-uuid-1234', user='user-b'), None)

        self.assertEqual(res['statusCode'], 200)
        body = json.loads(res['body'])
        self.assertEqual(body['transactionId'], 'tx-uuid-1234')

    def test_tx_get_forbidden_third_party(self):
        tx_record = {
            'transactionId': 'tx-uuid-1234',
            'fromWalletId': 'W001',
            'toWalletId': 'W002',
            'amount': 30000,
        }
        wallets = {
            'W001': {'walletId': 'W001', 'ownerId': 'user-a'},
            'W002': {'walletId': 'W002', 'ownerId': 'user-b'},
        }
        def mock_get(table, key, strong=True):
            if table == tx_mod.TRANSACTIONS_TABLE:
                return tx_record
            return wallets.get(key.get('walletId'))

        with patch.object(tx_mod, 'ddb_get', side_effect=mock_get):
            res = tx_mod.lambda_handler(make_tx_event(tx_id='tx-uuid-1234', user='user-c-intruder'), None)

        self.assertEqual(res['statusCode'], 403)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'TRANSACTION_FORBIDDEN')

    def test_tx_get_not_found(self):
        with patch.object(tx_mod, 'ddb_get', return_value=None):
            res = tx_mod.lambda_handler(make_tx_event(tx_id='non-existent-tx', user='user-a'), None)
        self.assertEqual(res['statusCode'], 404)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'TRANSACTION_NOT_FOUND')

    def test_tx_get_unauthorized_missing_user(self):
        res = tx_mod.lambda_handler(make_tx_event(tx_id='tx-1', user=None), None)
        self.assertEqual(res['statusCode'], 401)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'UNAUTHORIZED')

    def test_tx_get_invalid_id(self):
        res = tx_mod.lambda_handler(make_tx_event(tx_id='', user='user-a'), None)
        self.assertEqual(res['statusCode'], 400)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'INVALID_TRANSACTION_ID')

    def test_tx_unsupported_route(self):
        res = tx_mod.lambda_handler(make_tx_event(route='DELETE /transactions/{transactionId}'), None)
        self.assertEqual(res['statusCode'], 404)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'ROUTE_NOT_FOUND')


if __name__ == '__main__':
    unittest.main()

