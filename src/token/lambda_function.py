"""Standalone AWS Lambda handler (Week 3). Deploy ONLY this lambda_function.py.
No shared.py and no imports from project-local modules.
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

SECRET_NAME = os.environ.get('JWT_SECRET_NAME', 'serverless-payment/jwt-secret')
ISSUER = os.environ.get('JWT_ISSUER', 'serverless-payment-demo')
AUDIENCE = os.environ.get('JWT_AUDIENCE', 'payment-api')
TOKEN_TTL_SECONDS = 900
ALLOWED_USERS = set(os.environ.get('ALLOWED_USERS', 'user-a,user-b').split(','))
_secret_cache = {'value': None, 'expires': 0}


def response(status, payload):
    return {
        'statusCode': status,
        'headers': {'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store'},
        'body': json.dumps(payload, ensure_ascii=False, separators=(',', ':')),
    }


def error(status, code, message):
    return response(status, {'error': {'code': code, 'message': message}})


def json_body(event):
    raw = event.get('body')
    if raw is None:
        raise ValueError('Missing JSON request body')
    if event.get('isBase64Encoded'):
        raw = base64.b64decode(raw, validate=True).decode('utf-8')
    if isinstance(raw, str):
        return json.loads(raw)
    return raw


def secrets():
    now = time.monotonic()
    if _secret_cache['value'] is not None and now < _secret_cache['expires']:
        return _secret_cache['value']
    result = boto3.client('secretsmanager').get_secret_value(SecretId=SECRET_NAME)
    value = json.loads(result['SecretString'])
    if (not isinstance(value.get('jwtSigningKey'), str)
            or len(value['jwtSigningKey'].encode('utf-8')) < 32
            or not isinstance(value.get('demoAccessCode'), str)):
        raise ValueError('Invalid JWT secret configuration')
    _secret_cache.update(value=value, expires=now + 60)
    return value


def lambda_handler(event, context):
    try:
        body = json_body(event)
    except (ValueError, UnicodeDecodeError, TypeError, json.JSONDecodeError):
        return error(400, 'INVALID_REQUEST', 'Malformed JSON')
    if not isinstance(body, dict):
        return error(400, 'INVALID_REQUEST', 'JSON object required')
    user_id, code = body.get('userId'), body.get('demoCode')
    if not isinstance(user_id, str) or not isinstance(code, str) or len(code) > 256:
        return error(400, 'INVALID_REQUEST', 'userId and demoCode required')
    config = secrets()
    matched = hmac.compare_digest(code.encode('utf-8'), config['demoAccessCode'].encode('utf-8'))
    if user_id not in ALLOWED_USERS or not matched:
        return error(401, 'INVALID_CREDENTIALS', 'Invalid demo credentials')
    now = datetime.now(timezone.utc)
    jwt_token = jwt.encode({
        'sub': user_id, 'iss': ISSUER, 'aud': AUDIENCE,
        'iat': now, 'exp': now + timedelta(seconds=TOKEN_TTL_SECONDS),
        'jti': str(uuid.uuid4()),
    }, config['jwtSigningKey'], algorithm='HS256')
    return response(200, {'accessToken': jwt_token, 'tokenType': 'Bearer', 'expiresIn': TOKEN_TTL_SECONDS})
