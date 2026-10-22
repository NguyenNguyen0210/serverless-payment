"""Unit tests for Token and Lambda Authorizer functions.
Run: python -m unittest tests/test_auth.py -v
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
            def __init__(self, err, op):
                self.response = err
                self.operation_name = op
                super().__init__(str(err))
        mock_exc.ClientError = ClientError
        mock_bc.exceptions = mock_exc
        sys.modules['botocore'] = mock_bc
        sys.modules['botocore.exceptions'] = mock_exc

import jwt

ROOT = Path(__file__).resolve().parents[1]
TEST_SECRET_CONFIG = {
    'jwtSigningKey': 'super-secret-key-for-local-unit-tests-32bytes!',
    'demoAccessCode': 'spg-demo-code-2026',
}


def load_module(name, rel_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


token_mod = load_module('token_lambda', 'src/token/lambda_function.py')
auth_mod = load_module('authorizer_lambda', 'src/authorizer/lambda_function.py')


class TokenLambdaTests(unittest.TestCase):
    def setUp(self):
        # Reset cached secret in token lambda
        token_mod._secret_cache = {'value': None, 'expires': 0}

    def _call_token(self, body=None, is_base64=False):
        if body is None:
            body = {'userId': 'user-a', 'demoCode': 'spg-demo-code-2026'}
        raw = json.dumps(body)
        if is_base64:
            raw = base64.b64encode(raw.encode('utf-8')).decode('utf-8')
        event = {'body': raw, 'isBase64Encoded': is_base64}
        with patch.object(token_mod, 'secrets', return_value=TEST_SECRET_CONFIG):
            return token_mod.lambda_handler(event, None)

    def test_token_success(self):
        res = self._call_token({'userId': 'user-a', 'demoCode': 'spg-demo-code-2026'})
        self.assertEqual(res['statusCode'], 200)
        body = json.loads(res['body'])
        self.assertIn('accessToken', body)
        self.assertEqual(body['tokenType'], 'Bearer')
        self.assertEqual(body['expiresIn'], 900)

        # Decode token and verify claims
        claims = jwt.decode(body['accessToken'], TEST_SECRET_CONFIG['jwtSigningKey'],
                            algorithms=['HS256'], audience='payment-api', issuer='serverless-payment-demo')
        self.assertEqual(claims['sub'], 'user-a')
        self.assertIn('jti', claims)

    def test_token_base64_encoded_body(self):
        res = self._call_token({'userId': 'user-b', 'demoCode': 'spg-demo-code-2026'}, is_base64=True)
        self.assertEqual(res['statusCode'], 200)
        body = json.loads(res['body'])
        claims = jwt.decode(body['accessToken'], TEST_SECRET_CONFIG['jwtSigningKey'],
                            algorithms=['HS256'], audience='payment-api', issuer='serverless-payment-demo')
        self.assertEqual(claims['sub'], 'user-b')

    def test_token_invalid_demo_code(self):
        res = self._call_token({'userId': 'user-a', 'demoCode': 'wrong-code'})
        self.assertEqual(res['statusCode'], 401)
        body = json.loads(res['body'])
        self.assertEqual(body['error']['code'], 'INVALID_CREDENTIALS')

    def test_token_unallowed_user(self):
        res = self._call_token({'userId': 'user-hacker', 'demoCode': 'spg-demo-code-2026'})
        self.assertEqual(res['statusCode'], 401)
        body = json.loads(res['body'])
        self.assertEqual(body['error']['code'], 'INVALID_CREDENTIALS')

    def test_token_missing_demo_code(self):
        res = self._call_token({'userId': 'user-a'})
        self.assertEqual(res['statusCode'], 400)
        body = json.loads(res['body'])
        self.assertEqual(body['error']['code'], 'INVALID_REQUEST')

    def test_token_malformed_json(self):
        with patch.object(token_mod, 'secrets', return_value=TEST_SECRET_CONFIG):
            res = token_mod.lambda_handler({'body': '{broken-json'}, None)
        self.assertEqual(res['statusCode'], 400)
        body = json.loads(res['body'])
        self.assertEqual(body['error']['code'], 'INVALID_REQUEST')

    def test_token_non_dict_body(self):
        with patch.object(token_mod, 'secrets', return_value=TEST_SECRET_CONFIG):
            res = token_mod.lambda_handler({'body': '"just a string"'}, None)
        self.assertEqual(res['statusCode'], 400)


class AuthorizerLambdaTests(unittest.TestCase):
    def setUp(self):
        # Reset cached secret in authorizer
        auth_mod._cache = {'value': None, 'expires': 0}

    def _generate_token(self, sub='user-a', iss='serverless-payment-demo', aud='payment-api', exp_offset=900, key=None):
        import time
        now = int(time.time())
        payload = {
            'sub': sub,
            'iss': iss,
            'aud': aud,
            'iat': now,
            'exp': now + exp_offset,
            'jti': 'test-token-uuid-1234',
        }
        signing_key = key or TEST_SECRET_CONFIG['jwtSigningKey']
        return jwt.encode(payload, signing_key, algorithm='HS256')

    def _call_auth(self, auth_header=None):
        headers = {}
        if auth_header is not None:
            headers['authorization'] = auth_header
        event = {'headers': headers}
        with patch.object(auth_mod, 'signing_secret', return_value=TEST_SECRET_CONFIG['jwtSigningKey']):
            return auth_mod.lambda_handler(event, None)

    def test_auth_success(self):
        t = self._generate_token(sub='user-a')
        res = self._call_auth(f'Bearer {t}')
        self.assertEqual(res, {'isAuthorized': True, 'context': {'userId': 'user-a'}})

    def test_auth_success_user_b(self):
        t = self._generate_token(sub='user-b')
        res = self._call_auth(f'Bearer {t}')
        self.assertEqual(res, {'isAuthorized': True, 'context': {'userId': 'user-b'}})

    def test_auth_missing_header(self):
        res = self._call_auth(None)
        self.assertEqual(res, {'isAuthorized': False})

    def test_auth_invalid_bearer_format(self):
        res = self._call_auth('Basic abcdef')
        self.assertEqual(res, {'isAuthorized': False})
        res2 = self._call_auth('Bearer')
        self.assertEqual(res2, {'isAuthorized': False})
        res3 = self._call_auth('Bearer too many parts here')
        self.assertEqual(res3, {'isAuthorized': False})

    def test_auth_expired_token(self):
        t = self._generate_token(exp_offset=-60)  # expired 60 seconds ago
        res = self._call_auth(f'Bearer {t}')
        self.assertEqual(res, {'isAuthorized': False})

    def test_auth_invalid_signature(self):
        t = self._generate_token(key='different-key-that-does-not-match-32b!')
        res = self._call_auth(f'Bearer {t}')
        self.assertEqual(res, {'isAuthorized': False})

    def test_auth_invalid_audience(self):
        t = self._generate_token(aud='wrong-api')
        res = self._call_auth(f'Bearer {t}')
        self.assertEqual(res, {'isAuthorized': False})

    def test_auth_invalid_issuer(self):
        t = self._generate_token(iss='untrusted-issuer')
        res = self._call_auth(f'Bearer {t}')
        self.assertEqual(res, {'isAuthorized': False})

    def test_auth_unapproved_subject(self):
        t = self._generate_token(sub='user-c-not-in-allowed')
        res = self._call_auth(f'Bearer {t}')
        self.assertEqual(res, {'isAuthorized': False})


if __name__ == '__main__':
    unittest.main()
