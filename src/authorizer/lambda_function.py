"""HTTP API REQUEST Lambda Authorizer (payload 2.0, simple responses).

Pass only the verified subject through context.userId; never trust userId from
client request bodies when authorizing source-wallet transfers.
"""

import json
import os
import time

import boto3
import jwt

SECRET_NAME = os.environ.get("JWT_SECRET_NAME", "serverless-payment/jwt-secret")
ISSUER = os.environ.get("JWT_ISSUER", "serverless-payment-demo")
AUDIENCE = os.environ.get("JWT_AUDIENCE", "payment-api")
ALLOWED_USERS = {"user-a", "user-b"}
_secret_cache = {"value": None, "until": 0.0}


def _load_secrets():
    """Read the signing key from Secrets Manager, with short-lived cache."""
    now = time.monotonic()
    if _secret_cache["value"] is not None and now < _secret_cache["until"]:
        return _secret_cache["value"]
    response = boto3.client("secretsmanager").get_secret_value(SecretId=SECRET_NAME)
    value = json.loads(response["SecretString"])
    if not isinstance(value.get("jwtSigningKey"), str) or len(value["jwtSigningKey"].encode("utf-8")) < 32:
        raise ValueError("Missing or weak signing key")
    _secret_cache["value"] = value
    _secret_cache["until"] = now + 60
    return value


def _deny(reason):
    # A log reason without JWT/signature content is safe for CloudWatch diagnosis.
    print(json.dumps({"event": "jwt_denied", "reason": reason}))
    return {"isAuthorized": False}


def lambda_handler(event, context):
    """Validate JWT signature and required claims before authorizing."""
    headers = event.get("headers") or {}
    authorization = next(
        (value for name, value in headers.items() if name.lower() == "authorization"),
        None,
    )
    if not isinstance(authorization, str):
        return _deny("missing_header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        return _deny("invalid_bearer_format")

    # Secrets Manager errors should surface as integration errors, not as a
    # misleading "invalid user" decision. Check LabRole when this fails.
    signing_key = _load_secrets()["jwtSigningKey"]
    try:
        claims = jwt.decode(
            parts[1],
            signing_key,
            algorithms=["HS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={"require": ["sub", "iss", "aud", "iat", "exp", "jti"]},
        )
    except jwt.ExpiredSignatureError:
        return _deny("expired")
    except jwt.PyJWTError:
        return _deny("invalid_signature_or_claims")

    if claims.get("sub") not in ALLOWED_USERS:
        return _deny("invalid_subject")
    return {"isAuthorized": True, "context": {"userId": claims["sub"]}}
