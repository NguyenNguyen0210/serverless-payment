"""POST /token - issue short-lived JWTs to allowlisted demo accounts.

Runtime: Python 3.12; AWS Lambda proxy integration payload version 2.0.
Never log incoming bodies, demo codes, access tokens or Secrets Manager values.
"""

import base64
import hmac
import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone

import boto3
import jwt

SECRET_NAME = os.environ.get("JWT_SECRET_NAME", "serverless-payment/jwt-secret")
ISSUER = os.environ.get("JWT_ISSUER", "serverless-payment-demo")
AUDIENCE = os.environ.get("JWT_AUDIENCE", "payment-api")
ALLOWED_USERS = {"user-a", "user-b"}
TOKEN_TTL_SECONDS = 900
_secret_cache = {"value": None, "until": 0.0}


def _load_secrets():
    """Cache secrets for 60 s to reduce calls while allowing key rotation."""
    now = time.monotonic()
    if _secret_cache["value"] is not None and now < _secret_cache["until"]:
        return _secret_cache["value"]

    response = boto3.client("secretsmanager").get_secret_value(SecretId=SECRET_NAME)
    value = json.loads(response["SecretString"])
    if not isinstance(value.get("jwtSigningKey"), str) or not isinstance(value.get("demoAccessCode"), str):
        raise ValueError("Secret JSON has missing or invalid fields")
    if len(value["jwtSigningKey"].encode("utf-8")) < 32:
        raise ValueError("JWT signing key must be at least 32 bytes")
    _secret_cache["value"] = value
    _secret_cache["until"] = now + 60
    return value


def _reply(status, payload):
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json", "cache-control": "no-store"},
        "body": json.dumps(payload, separators=(",", ":")),
    }


def lambda_handler(event, context):
    """Validate fixed demo identities and return signed JWT after code check."""
    try:
        body = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")
        body = json.loads(body)
    except (ValueError, UnicodeDecodeError, TypeError):
        return _reply(400, {"error": {"code": "INVALID_REQUEST", "message": "Malformed JSON"}})
    if not isinstance(body, dict):
        return _reply(400, {"error": {"code": "INVALID_REQUEST", "message": "JSON object required"}})

    user_id = body.get("userId")
    demo_code = body.get("demoCode")
    if not isinstance(user_id, str) or not isinstance(demo_code, str) or len(demo_code) > 256:
        return _reply(400, {"error": {"code": "INVALID_REQUEST", "message": "userId and demoCode required"}})

    secrets = _load_secrets()
    code_matches = hmac.compare_digest(
        demo_code.encode("utf-8"), secrets["demoAccessCode"].encode("utf-8")
    )
    if user_id not in ALLOWED_USERS or not code_matches:
        return _reply(401, {"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid demo credentials"}})

    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(seconds=TOKEN_TTL_SECONDS),
        "jti": str(uuid.uuid4()),
    }
    access_token = jwt.encode(payload, secrets["jwtSigningKey"], algorithm="HS256")
    return _reply(200, {
        "accessToken": access_token,
        "tokenType": "Bearer",
        "expiresIn": TOKEN_TTL_SECONDS,
    })
