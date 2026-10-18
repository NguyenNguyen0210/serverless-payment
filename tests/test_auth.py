"""Run from repository root: python -m unittest discover -s tests -v"""

import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import jwt

ROOT = Path(__file__).resolve().parents[1]
TEST_SECRETS = {"jwtSigningKey": "local-unit-test-signing-key-32bytes-abcdef", "demoAccessCode": "local-only-test-code"}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.token = load_module("token_lambda", "src/token/lambda_function.py")
        cls.authorizer = load_module("authorizer_lambda", "src/authorizer/lambda_function.py")

    def _issue(self, user="user-a", code=TEST_SECRETS["demoAccessCode"]):
        event = {"body": json.dumps({"userId": user, "demoCode": code})}
        with patch.object(self.token, "_load_secrets", return_value=TEST_SECRETS):
            return self.token.lambda_handler(event, None)

    def test_token_success_and_authorizer_context(self):
        result = self._issue()
        self.assertEqual(result["statusCode"], 200)
        access_token = json.loads(result["body"])["accessToken"]
        event = {"headers": {"authorization": "Bearer " + access_token}}
        with patch.object(self.authorizer, "_load_secrets", return_value=TEST_SECRETS):
            auth_result = self.authorizer.lambda_handler(event, None)
        self.assertEqual(auth_result, {"isAuthorized": True, "context": {"userId": "user-a"}})

    def test_bad_demo_code(self):
        self.assertEqual(self._issue(code="wrong")["statusCode"], 401)

    def test_unapproved_user(self):
        self.assertEqual(self._issue(user="admin")["statusCode"], 401)

    def test_invalid_body(self):
        result = self.token.lambda_handler({"body": "{bad-json"}, None)
        self.assertEqual(result["statusCode"], 400)

    def test_missing_authorization(self):
        self.assertEqual(self.authorizer.lambda_handler({"headers": {}}, None), {"isAuthorized": False})

    def test_invalid_signature(self):
        token = jwt.encode({"sub": "user-a", "iss": "serverless-payment-demo", "aud": "payment-api", "exp": 9999999999, "iat": 1600000000, "jti": "unit-test"}, "different-local-signing-key-32bytes-abcdef", algorithm="HS256")
        with patch.object(self.authorizer, "_load_secrets", return_value=TEST_SECRETS):
            result = self.authorizer.lambda_handler({"headers": {"authorization": "Bearer " + token}}, None)
        self.assertEqual(result, {"isAuthorized": False})

    def test_expired_token(self):
        token = jwt.encode({"sub": "user-a", "iss": "serverless-payment-demo", "aud": "payment-api", "exp": 1600000010, "iat": 1600000000, "jti": "unit-test"}, TEST_SECRETS["jwtSigningKey"], algorithm="HS256")
        with patch.object(self.authorizer, "_load_secrets", return_value=TEST_SECRETS):
            result = self.authorizer.lambda_handler({"headers": {"authorization": "Bearer " + token}}, None)
        self.assertEqual(result, {"isAuthorized": False})


if __name__ == "__main__":
    unittest.main()
