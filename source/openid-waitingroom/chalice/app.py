# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This Lambda function provides the endpoint functions
for the OpenID interface of the AWS Virtual Meeting Room
"""

import json
import os
from urllib.parse import unquote, parse_qs, urlparse

import boto3
import requests
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
from botocore import config
from chalice import Chalice, Response
from vwr.common.sanitize import deep_clean
from vwr.common.diag import print_exception
from vwr.common.jwt import claim_dict

app = Chalice(app_name='openid-waitingroom')
app.debug = True

# user agent info
SOLUTION_ID = os.environ.get("SOLUTION_ID")
user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)

SECRETS_CLIENT = boto3.client("secretsmanager", config=user_config)

# secret IDs and values provided via environment variables
REDIRECT_URIS_SECRET_ID = os.environ.get("REDIRECT_URIS_SECRET_ID")
WWW_RESOURCES_URL = os.environ.get("WWW_RESOURCES_URL")
WAITING_ROOM_EVENT_ID = os.environ.get("WAITING_ROOM_EVENT_ID")
PUBLIC_API_ENDPOINT = os.environ.get("PUBLIC_API_ENDPOINT")
PRIVATE_API_ENDPOINT = os.environ.get("PRIVATE_API_ENDPOINT")
API_REGION = os.environ.get("API_REGION")
CLIENT_SECRET_ID = os.environ.get("CLIENT_SECRET_ID")
ISSUER = os.environ.get("ISSUER")
TIMEOUT = 60

# these are open ID parameter values this module supports
RESPONSE_TYPES = ['code']
REQUEST_SCOPES = ['openid']
GRANT_TYPES = ['authorization_code']


def bad_request():
    """
    This is a helper function that returns a standard client error response for several cases below.
    """
    return Response(status_code=400,
                    body='Bad Request',
                    headers={'Content-Type': 'text/plain'})


def extract_oidc_request():
    """
    This function retrieves the parameters for the OIDC request
    """
    request = app.current_request
    # extract the query parameters sent from the site
    query_params = request.query_params if request.query_params is not None else {}
    client_id = deep_clean(unquote(query_params.get('client_id', '')))
    redirect_uri = deep_clean(unquote(query_params.get('redirect_uri', '')))
    response_type = deep_clean(unquote(query_params.get('response_type', '')))
    scope = deep_clean(unquote(query_params.get('scope', '')))
    code = deep_clean(unquote(query_params.get('code', '')))
    # the state parameter is passed along as-is and not processed
    state = query_params.get('state', '')
    return (client_id, redirect_uri, response_type, state, scope, code)


def validate_oidc_request(client_id, redirect_uri, response_type, scope):
    """
    The function validates the three OIDC request parameters from the web site
    """
    valid_redirect_uris = json.loads(
        SECRETS_CLIENT.get_secret_value(
            SecretId=REDIRECT_URIS_SECRET_ID).get("SecretString"))
    return (client_id == WAITING_ROOM_EVENT_ID) and (
        redirect_uri in valid_redirect_uris) and (
            response_type in RESPONSE_TYPES) and (scope in REQUEST_SCOPES)


@app.route('/authorize', methods=['GET'])
def authorize():
    """
    This is the authorize endpoint
    """
    app.log.info('/authorize')
    app.log.info(app.current_request.to_dict())
    try:
        client_id, redirect_uri, response_type, state, scope, _ = extract_oidc_request(
        )
        # validate query parameters
        if validate_oidc_request(client_id, redirect_uri, response_type,
                                 scope):
            app.log.info('valid /authorize request')
            # redirect to the bucket login page with parameters
            return Response(status_code=302,
                            body=None,
                            headers={
                                'Location':
                                (f'{WWW_RESOURCES_URL}/login.html?' +
                                 f'client_id={client_id}&' +
                                 f'redirect_uri={redirect_uri}&' +
                                 f'response_type={response_type}&' +
                                 f'state={state}&' + f'scope={scope}'),
                                'Content-Type':
                                'text/html'
                            })
        app.log.info('invalid /authorize request')
    except (KeyError, IndexError, TypeError):
        app.log.error('validation failed')
    return bad_request()


@app.route('/token',
           methods=['POST'],
           content_types=['application/x-www-form-urlencoded'])
def token():
    """
    This is the token endpoint
    """
    app.log.info('/token')
    app.log.info(app.current_request.to_dict())
    app.log.info(app.current_request.raw_body)
    query_parameters = parse_qs(app.current_request.raw_body.decode("utf-8"))
    try:
        event_id = deep_clean(query_parameters.get("client_id")[0])
        provided_secret = deep_clean(query_parameters.get("client_secret")[0])
        request_id = deep_clean(query_parameters.get("code")[0])
        grant_type = deep_clean(query_parameters.get("grant_type")[0])
        # get the client secret from secrets manager
        valid_client_secret = SECRETS_CLIENT.get_secret_value(
            SecretId=CLIENT_SECRET_ID).get("SecretString")
        if (provided_secret == valid_client_secret) and (
                grant_type in GRANT_TYPES) and (WAITING_ROOM_EVENT_ID
                                                == event_id):
            app.log.info('valid /token request')
            generate_token_api = f'{PRIVATE_API_ENDPOINT}/generate_token'
            # context comes from API Gateway and not the supplied headers
            issuer = (f'https://{app.current_request.context["domainName"]}' +
                      f'/{app.current_request.context["stage"]}')
            body = {
                "event_id": event_id,
                "request_id": request_id,
                "issuer": issuer
            }
            parsed = urlparse(PRIVATE_API_ENDPOINT)
            # create an authentication signer for AWS
            auth = BotoAWSRequestsAuth(aws_host=parsed.netloc,
                                       aws_region=API_REGION,
                                       aws_service='execute-api')
            response = requests.post(generate_token_api, json=body, auth=auth, timeout=TIMEOUT)
            # app.log.info(response.text)
            if response.status_code == 200:
                return Response(status_code=200,
                                body=response.text,
                                headers={'Content-Type': 'application/json'})
            message = f'{response.status_code} status from private API'
            app.log.info(message)
        else:
            app.log.info('invalid /token request')
    except (KeyError, IndexError, TypeError):
        print_exception()
    return bad_request()


@app.route('/userInfo', methods=['GET'])
def userinfo():
    """
    This is the userInfo endpoint
    """
    app.log.info('/userInfo')
    request = app.current_request.to_dict()
    app.log.info(request)
    try:
        _, dirty_access_token = request.get('headers',
                                            {}).get('authorization',
                                                    '').split(" ")
        dirty_claims = claim_dict(dirty_access_token)
        app.log.info(dirty_claims)
        event_id = deep_clean(dirty_claims.get("aud"))
        request_id = deep_clean(dirty_claims.get("sub"))
        private_api = f'{PRIVATE_API_ENDPOINT}/generate_token'
        # context comes from API Gateway and not the supplied headers
        issuer = (f'https://{app.current_request.context["domainName"]}' +
                  f'/{app.current_request.context["stage"]}')
        body = {
            "event_id": event_id,
            "request_id": request_id,
            "issuer": issuer
        }
        parsed = urlparse(PRIVATE_API_ENDPOINT)
        # create an authentication signer for AWS
        auth = BotoAWSRequestsAuth(aws_host=parsed.netloc,
                                   aws_region=API_REGION,
                                   aws_service='execute-api')
        response = requests.post(private_api, json=body, auth=auth, timeout=TIMEOUT)
        if response.status_code == 200:
            clean_tokens = json.loads(response.text)
            clean_claims = claim_dict(clean_access_token)
            clean_access_token = clean_tokens.get("access_token")
            if clean_claims == dirty_claims:
                app.log.info('token claims match')
                app.log.info(clean_claims)
                return clean_claims
            app.log.info("tokens claims don't match")
    except (KeyError, IndexError, TypeError):
        app.log.error('validation failed')
    return bad_request()


@app.route('/.well-known/openid-configuration', methods=['GET'])
def openid_configuration():
    """
    This endpoint is used for auto-configuration of sites
    """
    app.log.info('/.well-known/openid-configuration')
    app.log.info(app.current_request.to_dict())
    issuer = (f'https://{app.current_request.context["domainName"]}' +
              f'/{app.current_request.context["stage"]}')
    return {
        "authorization_endpoint":
        f"{issuer}/authorize",
        "id_token_signing_alg_values_supported": ["RS256"],
        "issuer":
        f"{issuer}",
        "jwks_uri":
        f"{issuer}/.well-known/jwks.json",
        "response_types_supported":
        RESPONSE_TYPES,
        "scopes_supported": ["openid"],
        "subject_types_supported": ["public"],
        "token_endpoint":
        f"{issuer}/token",
        "token_endpoint_auth_methods_supported":
        ["client_secret_basic", "client_secret_post"],
        "userinfo_endpoint":
        f"{issuer}/userInfo"
    }


@app.route('/.well-known/jwks.json', methods=['GET'])
def jwks_json():
    """
    This endpoint is used for retrieval of public keys to verify tokens
    """
    app.log.info('/.well-known/jwks.json')
    app.log.info(app.current_request.to_dict())
    public_jwk = {}
    public_api = f'{PUBLIC_API_ENDPOINT}/public_key?event_id={WAITING_ROOM_EVENT_ID}'
    try:
        response = requests.get(public_api, timeout=TIMEOUT)
        if response.status_code == 200:
            public_jwk = json.loads(response.text)
    except (OSError, RuntimeError):
        print_exception()
    return {"keys": [public_jwk]}
