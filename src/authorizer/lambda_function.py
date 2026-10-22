"""Standalone AWS Lambda handler (Week 3). Deploy ONLY this lambda_function.py.
No shared.py and no imports from project-local modules.
"""
import json
import os
import time
from datetime import datetime, timezone

import boto3
import jwt

SECRET_NAME = os.environ.get('JWT_SECRET_NAME', 'serverless-payment/jwt-secret')
ISSUER = os.environ.get('JWT_ISSUER', 'serverless-payment-demo')
AUDIENCE = os.environ.get('JWT_AUDIENCE', 'payment-api')
ALLOWED_USERS = set(os.environ.get('ALLOWED_USERS', 'user-a,user-b').split(','))
_cache = {'value': None, 'expires': 0}


def iso_now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def log_event(event_name, **fields):
    """Safe, machine-parseable application logs. Callers must not pass secrets."""
    print(json.dumps({'event': event_name, 'at': iso_now(), **fields}, separators=(',', ':')))


def signing_secret():
    now = time.monotonic()
    if _cache['value'] and now < _cache['expires']:
        return _cache['value']
    raw = boto3.client('secretsmanager').get_secret_value(SecretId=SECRET_NAME)['SecretString']
    key = json.loads(raw)['jwtSigningKey']
    if not isinstance(key, str) or len(key.encode('utf-8')) < 32:
        raise ValueError('Invalid JWT secret')
    _cache.update(value=key, expires=now + 60)
    return key


def deny(reason):
    log_event('jwt_denied', reason=reason)
    return {'isAuthorized': False}


def lambda_handler(event, context):
    headers = {str(k).lower(): v for k, v in (event.get('headers') or {}).items()}
    auth = headers.get('authorization')
    if not isinstance(auth, str):
        return deny('missing_header')
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return deny('invalid_bearer_format')
    key = signing_secret()  # AWS errors must surface as integration errors.
    try:
        claims = jwt.decode(parts[1], key, algorithms=['HS256'], issuer=ISSUER, audience=AUDIENCE,
                            options={'require': ['sub', 'iss', 'aud', 'iat', 'exp', 'jti']})
    except jwt.ExpiredSignatureError:
        return deny('expired')
    except jwt.PyJWTError:
        return deny('invalid_signature_or_claims')
    sub = claims.get('sub')
    if sub not in ALLOWED_USERS:
        return deny('invalid_subject')
    return {'isAuthorized': True, 'context': {'userId': sub}}
