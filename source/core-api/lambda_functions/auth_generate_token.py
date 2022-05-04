# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the auth_generate_token API handler.
It generates a token for a valid request that has been allowed to complete its transaction. 
Authorization is required to invoke this API.
"""

import os
import time
import json
import redis
import boto3
from jwcrypto import jwk, jwt
from http  import HTTPStatus
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from botocore import config
from counters import SERVING_COUNTER, TOKEN_COUNTER
from vwr.common.sanitize import deep_clean
from vwr.common.validate import is_valid_rid

# connection info and other globals
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
DDB_TABLE_NAME = os.environ["TOKEN_TABLE"]
SECRET_NAME_PREFIX = os.environ["STACK_NAME"]
VALIDITY_PERIOD = int(os.environ["VALIDITY_PERIOD"])
EVENT_ID = os.environ["EVENT_ID"]
EVENT_BUS_NAME = os.environ["EVENT_BUS_NAME"]
SOLUTION_ID = os.environ['SOLUTION_ID']

boto_session = boto3.session.Session()
region = boto_session.region_name
user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)
ddb_resource = boto3.resource('dynamodb', endpoint_url=f'https://dynamodb.{region}.amazonaws.com', config=user_config)
ddb_table = ddb_resource.Table(DDB_TABLE_NAME)
events_client = boto3.client('events', endpoint_url=f'https://events.{region}.amazonaws.com', config=user_config)

secrets_client = boto3.client('secretsmanager', endpoint_url=f'https://secretsmanager.{region}.amazonaws.com', config=user_config)
response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/redis-auth")
redis_auth = response.get("SecretString")
rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, ssl=True, decode_responses=True, password=redis_auth)

def lambda_handler(event, context):
    """
    This function is the entry handler for Lambda.
    """

    global VALIDITY_PERIOD
    print(event)
    body = json.loads(event['body'])
    request_id = deep_clean(body['request_id'])
    client_event_id = deep_clean(body['event_id'])
    host = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    issuer = f"https://{host}/{stage}"

    if "issuer" in body:
        issuer = body['issuer']
    if "validity_period" in body:
        VALIDITY_PERIOD = int(body['validity_period'])
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }
    if client_event_id == EVENT_ID and is_valid_rid(request_id):
        if queue_number := rc.hget(request_id, "queue_number"):
            if int(queue_number) <= int(rc.get(SERVING_COUNTER)):
                keypair = create_jwk_keypair()
                # record for the request_id is in the ddb_table
                if record := ddb_table.get_item(Key={"request_id": request_id}):
                    claims = create_claims_from_record(record)
                    (access_token, refresh_token, id_token) = create_tokens(keypair, claims)
                    response = create_return_response(
                        headers, HTTPStatus.OK.value, record['Items'][0]['expires'], access_token, refresh_token, id_token)
                    
                    return response

                # record for the request_id is not in ddb_table, create and save record to ddb_table
                iat = int(time.time())  # issued-at and not-before can be the same time (epoch seconds)
                nbf = iat
                exp = iat + VALIDITY_PERIOD # expiration (exp) is a time after iat and nbf, like 1 hour (epoch seconds)
                claims = create_claims(request_id, issuer, queue_number, iat, nbf, exp)
                record = {
                    "event_id": EVENT_ID,
                    "request_id": request_id,
                    "issued_at": iat,
                    "not_before": nbf,
                    "expires": exp,
                    "queue_number": queue_number,
                    'iss': issuer,
                    "session_status": 0
                }

                response, is_item_put = save_record_to_dynamodb(record, request_id, keypair, claims, headers)
                if is_item_put:
                    write_to_eventbus(request_id)
                    # increment token counter
                    rc.incr(TOKEN_COUNTER, 1)
            else:
                response = {
                    "statusCode": HTTPStatus.ACCEPTED.value,
                    "headers": headers,
                    "body": json.dumps({"error": "Request ID not being served yet"})
                }
        else:
            response = {
                "statusCode": HTTPStatus.NOT_FOUND.value,
                "headers": headers,
                "body": json.dumps({"error": "Invalid request ID"})
            }
    else:
        response = {
            "statusCode": HTTPStatus.BAD_REQUEST.value,
            "headers": headers,
            "body": json.dumps({"error": "Invalid event or request ID"})
        }
    
    return response


def create_jwk_keypair() -> jwk.JWK:
    """
    Create JWK key object
    """
    response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/jwk-private")
    private_key = response.get("SecretString")
    # create JWK format keys
    return jwk.JWK.from_json(private_key)


def make_jwt_token(keypair, claims, token_use) -> jwt.JWT:
    """
    create jwt claims token
    """
    # Bandit B105: not a hardcoded password
    claims["token_use"] = token_use  # nosec
    jwt_token = jwt.JWT(header={"alg": "RS256", "typ": "JWT"}, claims=claims)
    jwt_token.make_signed_token(keypair)
    print(f"{token_use} token header: {jwt_token.serialize().split('.')[0]}")

    return jwt_token


def create_tokens(keypair, claims):
    """
    Create access, refresh and id tokens 
    """
    access_token = make_jwt_token(keypair, claims, "access")
    refresh_token = make_jwt_token(keypair, claims, "refresh")
    id_token = make_jwt_token(keypair, claims, "id")

    return (access_token, refresh_token, id_token)


def create_claims_from_record(record):
    """
    Parse DynamoDB table record and create claims
    """
    return create_claims(
        record['Items'][0]['request_id'], 
        record['Items'][0]['issuer'], 
        record['Items'][0]['queue_number'], 
        record['Items'][0]['issued_at'], 
        record['Items'][0]['not_before'], 
        record['Items'][0]['expires']
    )


def create_claims(request_id, issuer, queue_number, iat, nbf, exp):
    """
    Create claims
    """
    return {
        'aud': EVENT_ID,
        'sub': request_id,
        'queue_position': queue_number,
        'token_use': 'access',
        'iat': iat,
        'nbf': nbf,
        'exp': exp,
        'iss': issuer
    }


def save_record_to_dynamodb(record, request_id, keypair, claims, headers):
    """
    Save record to Dyanamo DB
    """
    is_item_put = False
    try:
        ddb_table.put_item(
            Item=record,
            ConditionExpression="attribute_not_exists(request_id)"
        )
        (access_token, refresh_token, id_token) = create_tokens(keypair, claims)    
        response = create_return_response(headers, HTTPStatus.OK.value, VALIDITY_PERIOD, access_token, refresh_token, id_token)
        is_item_put = True
    except ClientError as e:
        response = handle_client_errors(e, request_id, headers, keypair)
    except Exception as e:
        print(e)
        raise e

    return response, is_item_put


def write_to_eventbus(request_id) -> None:
    """
    write to event bus
    """
    events_client.put_events(
        Entries=[
            {
                'Source': 'custom.waitingroom',
                'DetailType': 'token_generated',
                'Detail': json.dumps(
                    {
                        "event_id": EVENT_ID,
                        "request_id": request_id
                    }
                ),
                'EventBusName': EVENT_BUS_NAME
            }
        ]
    )


def handle_client_errors(e, request_id, headers, keypair):
    """
    Handle client-error when put_item fails
    Exception occurs if the token already exists in the database
    Unlikely situation
    """
    if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
        raise e
    record = ddb_table.query(KeyConditionExpression=Key('request_id').eq(request_id))

    expires = int(record['Items'][0]['expires'])
    cur_time = int(time.time())
    remaining_time = expires - cur_time

    claims = create_claims_from_record(record)
    (access_token, refresh_token, id_token) = create_tokens(keypair, claims)

    return create_return_response(headers, HTTPStatus.OK.value, remaining_time, access_token, refresh_token, id_token)


def create_return_response(headers, status_code, expiry_time, access_token, refresh_token, id_token):
    """
    Create a response message to return
    """
    return {
        "statusCode": status_code, 
        "headers": headers, 
        "body": json.dumps(
            {
                "access_token": access_token.serialize(),
                "refresh_token": refresh_token.serialize(), 
                "id_token": id_token.serialize(), 
                "token_type": "Bearer", 
                "expires_in": expiry_time
            }
        )
    }
    