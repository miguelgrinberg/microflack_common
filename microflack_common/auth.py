"""Common authentication functions.

This module contains functions to generate and verify JWT tokens.
"""
from datetime import datetime, timedelta

from cachetools.func import ttl_cache
from etcd import EtcdKeyNotFound
from flask import current_app, g, jsonify
from flask_httpauth import HTTPTokenAuth
import jwt

from microflack_common.etcd import etcd_client

token_auth = HTTPTokenAuth('Bearer')
token_optional_auth = HTTPTokenAuth('Bearer')


def generate_token(user_id, expires_in=3600):
    """Generate a JWT token.

    :param user_id the user that will own the token
    :param expires_on expiration time in seconds
    """
    secret_key = current_app.config['JWT_SECRET_KEY']
    return jwt.encode(
        {'user_id': user_id,
         'exp': datetime.utcnow() + timedelta(seconds=expires_in)},
        secret_key, algorithm='HS256').decode('utf-8')


@token_auth.verify_token
def verify_token(token):
    """Token verification callback."""

    # this inner function checks if a token appears in the revoked token list
    # the ttl_cache decorator from the cachetools package saves the revoked
    # status for a token for one minute, to avoid lots of duplicated calls to
    # the etcd service.
    @ttl_cache(ttl=60)
    def is_token_revoked(token):
        try:
            etcd_client().read('/revoked-tokens/' + token)
        except EtcdKeyNotFound:
            return False
        return True

    if not current_app.config['TESTING'] and is_token_revoked(token):
        return False
    secret_key = current_app.config['JWT_SECRET_KEY']
    g.jwt_claims = {}
    try:
        g.jwt_claims = jwt.decode(token, secret_key, algorithms=['HS256'])
    except:
        # we really don't care what is the error here, any tokens that do not
        # pass validation are rejected
        return False
    return True


@token_auth.error_handler
def token_error():
    """Return a 401 error to the client."""
    return (jsonify({'error': 'authentication required'}), 401,
            {'WWW-Authenticate': 'Bearer realm="Authentication Required"'})


@token_optional_auth.verify_token
def verify_optional_token(token):
    """Alternative token authentication that allows anonymous logins."""
    if token == '':
        # no token provided, set an empty claim list and continue
        g.jwt_claims = {}
        return True
    # but if a token was provided, make sure it is valid
    return verify_token(token)


@token_optional_auth.error_handler
def token_optional_error():
    """Return a 401 error to the client."""
    return (jsonify({'error': 'authentication required'}), 401,
            {'WWW-Authenticate': 'Bearer realm="Authentication Required"'})
