"""Unit tests for Transfer Lambda (3-table ACID transaction & Idempotency).
Run: python -m unittest tests/test_transfer.py -v
"""
import importlib.util
import json
import os
import sys
import unittest
import uuid
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
            def __init__(self, err, op='TransactWriteItems'):
                self.response = err
                self.operation_name = op
                super().__init__(str(err))
        mock_exc.ClientError = ClientError
        mock_bc.exceptions = mock_exc
        sys.modules['botocore'] = mock_bc
        sys.modules['botocore.exceptions'] = mock_exc
else:
    from botocore.exceptions import ClientError

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, rel_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


transfer_mod = load_module('transfer_lambda', 'src/transfer/lambda_function.py')
TEST_IDEM_KEY = '4c7d3e65-1f10-47c7-b6f3-e99c91ba00d1'


def make_event(body=None, key=TEST_IDEM_KEY, user='user-a', req_id='test-request-id-001'):
    headers = {}
    if key is not None:
        headers['idempotency-key'] = key
    request_body = body if body is not None else {
        'fromWalletId': 'W001',
        'toWalletId': 'W002',
        'amount': 30000,
    }
    return {
        'version': '2.0',
        'routeKey': 'POST /transfers',
        'headers': headers,
        'body': json.dumps(request_body) if isinstance(request_body, dict) else str(request_body),
        'requestContext': {
            'authorizer': {'lambda': {'userId': user}} if user else {},
            'requestId': req_id,
        },
    }


def make_wallet(wallet_id='W001', owner='user-a', balance=100000, status='ACTIVE', currency='VND'):
    return {
        'walletId': wallet_id,
        'ownerId': owner,
        'balance': balance,
        'status': status,
        'currency': currency,
    }


class TransferLambdaTests(unittest.TestCase):
    def setUp(self):
        self.mock_ddb = MagicMock()
        self.ddb_patcher = patch.object(transfer_mod, 'DDB', self.mock_ddb)
        self.ddb_patcher.start()
        self.addCleanup(self.ddb_patcher.stop)

    def test_successful_transfer_commits_4_actions(self):
        # 1. ddb_get(IDEMPOTENCY_TABLE) -> None (no prior key)
        # 2. preflight: ddb_get(WALLETS_TABLE, W001) -> source wallet
        # 3. preflight: ddb_get(WALLETS_TABLE, W002) -> dest wallet
        with patch.object(transfer_mod, 'ddb_get', side_effect=[
            None,
            make_wallet('W001', 'user-a', 100000),
            make_wallet('W002', 'user-b', 50000),
        ]):
            res = transfer_mod.lambda_handler(make_event(), None)

        self.assertEqual(res['statusCode'], 201)
        body = json.loads(res['body'])
        self.assertEqual(body['status'], 'SUCCESS')
        self.assertFalse(body['replayed'])
        self.assertEqual(body['fromWalletId'], 'W001')
        self.assertEqual(body['toWalletId'], 'W002')
        self.assertEqual(body['amount'], 30000)
        self.assertEqual(body['currency'], 'VND')
        self.assertIn('transactionId', body)
        self.assertIn('createdAt', body)

        # Check transact_write_items call
        self.mock_ddb.transact_write_items.assert_called_once()
        actions = self.mock_ddb.transact_write_items.call_args.kwargs['TransactItems']
        self.assertEqual(len(actions), 4)

        # 1. Put Idempotency
        self.assertIn('Put', actions[0])
        self.assertEqual(actions[0]['Put']['TableName'], transfer_mod.IDEMPOTENCY_TABLE)
        self.assertIn('attribute_not_exists', actions[0]['Put']['ConditionExpression'])

        # 2. Update Source Wallet
        self.assertIn('Update', actions[1])
        self.assertEqual(actions[1]['Update']['TableName'], transfer_mod.WALLETS_TABLE)
        self.assertIn('balance >= :amt', actions[1]['Update']['ConditionExpression'])
        self.assertEqual(actions[1]['Update']['ExpressionAttributeValues'][':amt'], {'N': '30000'})

        # 3. Update Dest Wallet
        self.assertIn('Update', actions[2])
        self.assertEqual(actions[2]['Update']['TableName'], transfer_mod.WALLETS_TABLE)
        self.assertIn('currency = :vnd', actions[2]['Update']['ConditionExpression'])

        # 4. Put Transaction
        self.assertIn('Put', actions[3])
        self.assertEqual(actions[3]['Put']['TableName'], transfer_mod.TRANSACTIONS_TABLE)
        self.assertIn('timeKey', actions[3]['Put']['Item'])
        self.assertIn('#', actions[3]['Put']['Item']['timeKey']['S'])

    def test_idempotency_replay_success(self):
        digest = transfer_mod.request_hash('user-a', 'W001', 'W002', 30000)
        prior_record = {
            'userId': 'user-a',
            'idempotencyKey': TEST_IDEM_KEY,
            'requestHash': digest,
            'transactionId': 'prior-tx-uuid-1234',
            'fromWalletId': 'W001',
            'toWalletId': 'W002',
            'amount': 30000,
            'createdAt': '2026-10-22T06:00:00Z',
        }
        with patch.object(transfer_mod, 'ddb_get', return_value=prior_record):
            res = transfer_mod.lambda_handler(make_event(), None)

        self.assertEqual(res['statusCode'], 200)
        body = json.loads(res['body'])
        self.assertTrue(body['replayed'])
        self.assertEqual(body['transactionId'], 'prior-tx-uuid-1234')
        self.assertEqual(body['amount'], 30000)
        # TransactWriteItems must not be called
        self.mock_ddb.transact_write_items.assert_not_called()

    def test_idempotency_conflict_different_amount(self):
        # Prior was 30000, new request is 50000 with same key
        prior_digest = transfer_mod.request_hash('user-a', 'W001', 'W002', 30000)
        prior_record = {
            'userId': 'user-a',
            'idempotencyKey': TEST_IDEM_KEY,
            'requestHash': prior_digest,
            'transactionId': 'prior-tx-uuid-1234',
        }
        with patch.object(transfer_mod, 'ddb_get', return_value=prior_record):
            event = make_event(body={'fromWalletId': 'W001', 'toWalletId': 'W002', 'amount': 50000})
            res = transfer_mod.lambda_handler(event, None)

        self.assertEqual(res['statusCode'], 409)
        body = json.loads(res['body'])
        self.assertEqual(body['error']['code'], 'IDEMPOTENCY_KEY_CONFLICT')
        self.mock_ddb.transact_write_items.assert_not_called()

    def test_missing_verified_identity(self):
        event = make_event(user=None)
        res = transfer_mod.lambda_handler(event, None)
        self.assertEqual(res['statusCode'], 401)
        body = json.loads(res['body'])
        self.assertEqual(body['error']['code'], 'UNAUTHORIZED')

    def test_missing_idempotency_key(self):
        event = make_event(key=None)
        res = transfer_mod.lambda_handler(event, None)
        self.assertEqual(res['statusCode'], 400)
        body = json.loads(res['body'])
        self.assertEqual(body['error']['code'], 'INVALID_IDEMPOTENCY_KEY')

    def test_invalid_uuid_idempotency_key(self):
        event = make_event(key='not-a-valid-uuid')
        res = transfer_mod.lambda_handler(event, None)
        self.assertEqual(res['statusCode'], 400)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'INVALID_IDEMPOTENCY_KEY')

    def test_uppercase_uuid_normalized(self):
        upper_key = TEST_IDEM_KEY.upper()
        self.assertEqual(transfer_mod.normalized_uuid(upper_key), TEST_IDEM_KEY.lower())

    def test_same_wallet_transfer_rejected(self):
        event = make_event(body={'fromWalletId': 'W001', 'toWalletId': 'W001', 'amount': 10000})
        res = transfer_mod.lambda_handler(event, None)
        self.assertEqual(res['statusCode'], 400)
        body = json.loads(res['body'])
        self.assertEqual(body['error']['code'], 'INVALID_WALLET')

    def test_invalid_wallet_format(self):
        event = make_event(body={'fromWalletId': 'W001!@#$', 'toWalletId': 'W002', 'amount': 10000})
        res = transfer_mod.lambda_handler(event, None)
        self.assertEqual(res['statusCode'], 400)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'INVALID_WALLET')

    def test_amount_negative_rejected(self):
        event = make_event(body={'fromWalletId': 'W001', 'toWalletId': 'W002', 'amount': -500})
        res = transfer_mod.lambda_handler(event, None)
        self.assertEqual(res['statusCode'], 400)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'INVALID_AMOUNT')

    def test_amount_zero_rejected(self):
        event = make_event(body={'fromWalletId': 'W001', 'toWalletId': 'W002', 'amount': 0})
        res = transfer_mod.lambda_handler(event, None)
        self.assertEqual(res['statusCode'], 400)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'INVALID_AMOUNT')

    def test_amount_boolean_rejected(self):
        event = make_event(body={'fromWalletId': 'W001', 'toWalletId': 'W002', 'amount': True})
        res = transfer_mod.lambda_handler(event, None)
        self.assertEqual(res['statusCode'], 400)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'INVALID_AMOUNT')

    def test_amount_float_rejected(self):
        event = make_event(body={'fromWalletId': 'W001', 'toWalletId': 'W002', 'amount': 15.5})
        res = transfer_mod.lambda_handler(event, None)
        self.assertEqual(res['statusCode'], 400)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'INVALID_AMOUNT')

    def test_source_wallet_not_found(self):
        with patch.object(transfer_mod, 'ddb_get', side_effect=[
            None,  # idempotency check
            None,  # source wallet lookup fails
            make_wallet('W002', 'user-b'),
        ]):
            res = transfer_mod.lambda_handler(make_event(), None)
        self.assertEqual(res['statusCode'], 404)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'WALLET_NOT_FOUND')

    def test_dest_wallet_not_found(self):
        with patch.object(transfer_mod, 'ddb_get', side_effect=[
            None,
            make_wallet('W001', 'user-a'),
            None,  # dest wallet lookup fails
        ]):
            res = transfer_mod.lambda_handler(make_event(), None)
        self.assertEqual(res['statusCode'], 404)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'WALLET_NOT_FOUND')

    def test_source_wallet_forbidden_not_owner(self):
        with patch.object(transfer_mod, 'ddb_get', side_effect=[
            None,
            make_wallet('W001', 'user-other-person', 100000),
            make_wallet('W002', 'user-b', 50000),
        ]):
            res = transfer_mod.lambda_handler(make_event(user='user-a'), None)
        self.assertEqual(res['statusCode'], 403)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'WALLET_FORBIDDEN')

    def test_source_wallet_inactive(self):
        with patch.object(transfer_mod, 'ddb_get', side_effect=[
            None,
            make_wallet('W001', 'user-a', 100000, status='SUSPENDED'),
            make_wallet('W002', 'user-b', 50000, status='ACTIVE'),
        ]):
            res = transfer_mod.lambda_handler(make_event(), None)
        self.assertEqual(res['statusCode'], 409)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'WALLET_INACTIVE')

    def test_dest_wallet_inactive(self):
        with patch.object(transfer_mod, 'ddb_get', side_effect=[
            None,
            make_wallet('W001', 'user-a', 100000, status='ACTIVE'),
            make_wallet('W002', 'user-b', 50000, status='SUSPENDED'),
        ]):
            res = transfer_mod.lambda_handler(make_event(), None)
        self.assertEqual(res['statusCode'], 409)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'WALLET_INACTIVE')

    def test_unsupported_currency(self):
        with patch.object(transfer_mod, 'ddb_get', side_effect=[
            None,
            make_wallet('W001', 'user-a', 100000, currency='USD'),
            make_wallet('W002', 'user-b', 50000, currency='VND'),
        ]):
            res = transfer_mod.lambda_handler(make_event(), None)
        self.assertEqual(res['statusCode'], 400)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'UNSUPPORTED_CURRENCY')

    def test_insufficient_funds(self):
        with patch.object(transfer_mod, 'ddb_get', side_effect=[
            None,
            make_wallet('W001', 'user-a', 5000),  # balance 5k < transfer 30k
            make_wallet('W002', 'user-b', 50000),
        ]):
            res = transfer_mod.lambda_handler(make_event(), None)
        self.assertEqual(res['statusCode'], 409)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'INSUFFICIENT_FUNDS')

    def test_concurrency_retry_exhausted_returns_503(self):
        wallets = {
            'W001': make_wallet('W001', 'user-a', 100000),
            'W002': make_wallet('W002', 'user-b', 50000),
        }
        def mock_get(table, key, strong=True):
            if table == transfer_mod.IDEMPOTENCY_TABLE:
                return None
            return wallets.get(key.get('walletId'))

        client_err = ClientError({'Error': {'Code': 'TransactionCanceledException'}}, 'TransactWriteItems')
        self.mock_ddb.transact_write_items.side_effect = client_err

        with patch.object(transfer_mod, 'ddb_get', side_effect=mock_get), \
             patch.object(transfer_mod.time, 'sleep'):
            res = transfer_mod.lambda_handler(make_event(), None)

        self.assertEqual(res['statusCode'], 503)
        self.assertEqual(self.mock_ddb.transact_write_items.call_count, 4)

    def test_concurrency_peer_commit_detected_returns_replay(self):
        digest = transfer_mod.request_hash('user-a', 'W001', 'W002', 30000)
        recorded = {
            'userId': 'user-a', 'idempotencyKey': TEST_IDEM_KEY,
            'requestHash': digest, 'transactionId': 'peer-tx-uuid-5678',
            'fromWalletId': 'W001', 'toWalletId': 'W002',
            'amount': 30000, 'createdAt': '2026-10-22T06:01:00Z',
        }
        calls = 0
        def mock_get(table, key, strong=True):
            nonlocal calls
            calls += 1
            if table == transfer_mod.IDEMPOTENCY_TABLE:
                if calls == 1:
                    return None  # First pre-check
                return recorded  # Concurrent peer completed
            return make_wallet(key['walletId'], 'user-a' if key['walletId'] == 'W001' else 'user-b')

        client_err = ClientError({'Error': {'Code': 'TransactionCanceledException'}}, 'TransactWriteItems')
        self.mock_ddb.transact_write_items.side_effect = client_err

        with patch.object(transfer_mod, 'ddb_get', side_effect=mock_get):
            res = transfer_mod.lambda_handler(make_event(), None)

        self.assertEqual(res['statusCode'], 200)
        body = json.loads(res['body'])
        self.assertTrue(body['replayed'])
        self.assertEqual(body['transactionId'], 'peer-tx-uuid-5678')

    def test_unhandled_exception_returns_500_and_alerts_dlq(self):
        with patch.object(transfer_mod, 'ddb_get', side_effect=RuntimeError('Database crashed')), \
             patch.object(transfer_mod, 'alert_failure') as mock_alert:
            res = transfer_mod.lambda_handler(make_event(), None)

        self.assertEqual(res['statusCode'], 500)
        self.assertEqual(json.loads(res['body'])['error']['code'], 'INTERNAL_ERROR')
        mock_alert.assert_called_once()


if __name__ == '__main__':
    unittest.main()
