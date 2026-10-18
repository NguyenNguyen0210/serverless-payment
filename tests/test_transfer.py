"""Lightweight unit tests; no network or AWS account required."""
import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
os.environ.setdefault('AWS_EC2_METADATA_DISABLED', 'true')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src' / 'transfer'))
import lambda_function as transfer

KEY = '4c7d3e65-1f10-47c7-b6f3-e99c91ba00d1'


def event(body=None, key=KEY, user='user-a'):
    return {
        'version': '2.0',
        'headers': {'idempotency-key': key} if key is not None else {},
        'body': json.dumps(body or {'fromWalletId': 'W001', 'toWalletId': 'W002', 'amount': 30000}),
        'requestContext': {'authorizer': {'lambda': {'userId': user}}, 'requestId': 'demo-request'}
    }


def wallet(owner, balance, status='ACTIVE', currency='VND'):
    return {'ownerId': {'S': owner}, 'balance': {'N': str(balance)},
            'status': {'S': status}, 'currency': {'S': currency}}


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.patch = patch.object(transfer, 'DDB', self.db)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def set_wallets(self):
        self.db.get_item.side_effect = [
            {}, {'Item': wallet('user-a', 100000)}, {'Item': wallet('user-b', 50000)}]

    def test_success_has_four_atomic_actions(self):
        self.set_wallets()
        result = transfer.lambda_handler(event(), None)
        self.assertEqual(result['statusCode'], 201)
        self.assertFalse(json.loads(result['body'])['replayed'])
        actions = self.db.transact_write_items.call_args.kwargs['TransactItems']
        self.assertEqual(len(actions), 4)
        self.assertEqual([next(iter(a)) for a in actions], ['Put', 'Update', 'Update', 'Put'])
        self.assertEqual(actions[1]['Update']['ExpressionAttributeValues'][':amount'], {'N': '30000'})

    def test_replay(self):
        recorded = {
            'requestHash': {'S': transfer.canonical_hash('user-a', 'W001', 'W002', 30000)},
            'transactionId': {'S': 'tx-123'}, 'fromWalletId': {'S': 'W001'},
            'toWalletId': {'S': 'W002'}, 'amount': {'N': '30000'},
            'createdAt': {'S': '2026-10-18T00:00:00Z'}}
        self.db.get_item.return_value = {'Item': recorded}
        result = transfer.lambda_handler(event(), None)
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(json.loads(result['body'])['transactionId'], 'tx-123')
        self.db.transact_write_items.assert_not_called()

    def test_same_key_different_payload(self):
        self.db.get_item.return_value = {'Item': {'requestHash': {'S': 'bad-hash'}}}
        result = transfer.lambda_handler(event(), None)
        self.assertEqual(result['statusCode'], 409)
        self.db.transact_write_items.assert_not_called()

    def test_insufficient_funds(self):
        self.db.get_item.side_effect = [{}, {'Item': wallet('user-a', 1000)},
                                        {'Item': wallet('user-b', 50000)}]
        self.assertEqual(transfer.lambda_handler(event(), None)['statusCode'], 409)
        self.db.transact_write_items.assert_not_called()

    def test_wrong_owner(self):
        self.db.get_item.side_effect = [{}, {'Item': wallet('user-b', 100000)},
                                        {'Item': wallet('user-a', 50000)}]
        self.assertEqual(transfer.lambda_handler(event(), None)['statusCode'], 403)

    def test_missing_verified_identity(self):
        e = event(); e['requestContext'] = {}
        self.assertEqual(transfer.lambda_handler(e, None)['statusCode'], 401)

    def test_amount_bool_rejected(self):
        e = event(body={'fromWalletId': 'W001', 'toWalletId': 'W002', 'amount': True})
        self.assertEqual(transfer.lambda_handler(e, None)['statusCode'], 400)

    def test_missing_key(self):
        self.assertEqual(transfer.lambda_handler(event(key=None), None)['statusCode'], 400)


if __name__ == '__main__':
    unittest.main()
