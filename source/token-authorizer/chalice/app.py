# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This module contains the Lambda authorizers that
can be integrated with solutions for the Waiting Room.
"""

import json
import linecache
import os.path
import sys
import time

import requests
from jwcrypto import jwk, jwt
from jwcrypto.common import JWException
from chalice import Chalice, Response
from vwr.common.diag import print_exception

app = Chalice(app_name='token-authorizer')

WAITING_ROOM_EVENT_ID = os.environ.get("WAITING_ROOM_EVENT_ID")
PUBLIC_API_ENDPOINT = os.environ.get("PUBLIC_API_ENDPOINT")
ISSUER = os.environ.get("ISSUER")


def get_public_key():
    """
    This function is responsible for retrieving the
    public JWK from the closest location
    """
    local_key_file = "/tmp/jwks.json"
    key = {}
    if os.path.isfile(local_key_file):
        # retrieve from the local file
        with open(local_key_file, 'rt') as cache_file:
            key = json.loads(cache_file.read())
    else:
        # retrieve from the core API
        api_endpoint = f'{PUBLIC_API_ENDPOINT}/public_key?event_id={WAITING_ROOM_EVENT_ID}'
        try:
            response = requests.get(api_endpoint)
            if response.status_code == 200:
                with open(local_key_file, 'wt') as cache_file:
                    cache_file.write(response.text)
                key = json.loads(response.text)
        except (OSError, RuntimeError):
            print_exception()
    return key


def verify_token_sig(token):
    """
    This function is responsible for verifying a JWT token against public keys and returning
    verified claims within the token or False
    """
    # get the public JWK dictionary
    pubkey_dict = get_public_key()
    # recreate the token with public key verification
    try:
        key = jwk.JWK(**pubkey_dict)
        verified = jwt.JWT(key=key, jwt=token)
        return json.loads(verified.claims)
    except JWException:
        # signature is invalid or token has expired
        print_exception()
        return False


def verify_token(token, use='access'):
    """
    This function is responsible for verifying
    a JWT ID token contents
    """
    # get the verified claims
    verified_claims = verify_token_sig(token)
    if verified_claims:
        # verify the token expiration
        if time.time() > verified_claims.get('exp', 0):
            print('token is expired')
            return False
        # verify the app client id
        if verified_claims.get('aud', '') != WAITING_ROOM_EVENT_ID:
            print('token was not issued for this event')
            return False
        # verify the user pool uri
        if verified_claims.get('iss', '') != ISSUER:
            print('token from the wrong issuer')
            return False
        # verify the token use
        if verified_claims.get("token_use", "") != use:
            print(f'token was not issued for {use} use')
            return False
        return verified_claims
    return False


def check_authorizer_token(token, resource):
    """
    This function is responsible for checking tokens and
    returning a policy for the custom authorizer for the resource
    """
    response = {
        "principalId": "denied",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": []
        }
    }
    statement = {
        "Action": "execute-api:Invoke",
        "Effect": "Deny",
        "Resource": resource
    }
    response["policyDocument"]["Statement"].append(statement)
    claims = verify_token(token)
    if claims:
        principal_id = claims.get("sub", 'approved')
        response["principalId"] = principal_id
        statement["Effect"] = "Allow"
    print(json.dumps(response))
    return response


@app.lambda_function()
def api_gateway_authorizer(event, _):
    """
    This function is a Lambda handler for an API Gateway custom authorizer
    """
    token = event.get('authorizationToken', '')
    arn = event.get('methodArn', '')
    if arn and token:
        # return a wildcard resource in the policy that covers all
        # potential API requests while the response is cached
        base_arn, _, _ = arn.split('/', 2)
        resource = f"{base_arn}/*/*/*"
        return check_authorizer_token(token, resource)
    # no token or method ARN in the request
    return Response(body='Request lacks valid authorization credentials',
                    status_code=401,
                    headers={'Content-Type': 'text/plain'})
