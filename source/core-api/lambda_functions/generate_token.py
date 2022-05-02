# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the generate_token API handler.
It generates a token for a valid request that has been allowed to complete its transaction. 
"""

import os
import time
import json
import redis
import boto3
from jwcrypto import jwk, jwt
from http import HTTPStatus
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

user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)
boto_session = boto3.session.Session()
region = boto_session.region_name
ddb_resource = boto3.resource('dynamodb', endpoint_url=f'https://dynamodb.{region}.amazonaws.com', config=user_config)
ddb_table = ddb_resource.Table(DDB_TABLE_NAME)
events_client = boto3.client('events', endpoint_url='https://events.{region}.amazonaws.com', config=user_config)

secrets_client = boto3.client('secretsmanager', endpoint_url=f'https://secretsmanager.{region}.amazonaws.com', config=user_config)
response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/redis-auth")
redis_auth = response.get("SecretString")
rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, ssl=True, decode_responses=True, password=redis_auth)

def lambda_handler(event, context):
    """
    This function is the entry handler for Lambda.
    """

    print(event)
    body = json.loads(event['body'])
    request_id = deep_clean(body['request_id'])
    client_event_id = deep_clean(body['event_id'])
    host = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    issuer = f"https://{host}/{stage}"
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }

    if client_event_id == EVENT_ID and is_valid_rid(request_id):
        if queue_number := rc.hget(request_id, "queue_number"):
            if int(queue_number) <= int(rc.get(SERVING_COUNTER)):
                response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/jwk-public")
                if ddb_table.get_item(Key={"request_id": request_id}):
                    print('hi')
                    return response
                
                iat = int(time.time())  # issued-at and not-before can be the same time (epoch seconds)
                nbf = iat
                exp = iat + VALIDITY_PERIOD # expiration (exp) is a time after iat and nbf, like 1 hour (epoch seconds)
                claims = create_claims(request_id, issuer, queue_number, iat, nbf, exp)

                keypair = create_jwk_keypair()
                access_token = make_jwt_token(keypair, claims, "access")
                id_token = make_jwt_token(keypair, claims, "id")
                refresh_token = make_jwt_token(keypair, claims, "refresh")

                response = save_token_dynamodb(request_id, queue_number, headers, iat, nbf, exp, access_token, id_token, refresh_token)
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

def create_claims(request_id, issuer, queue_number, iat, nbf, exp) -> dict:
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

def make_jwt_token(keypair, claims, token_use) -> jwt.JWT:
    # create jwt claims token 
    # Bandit B105: not a hardcoded password
    claims["token_use"] = token_use  # nosec
    jwt_token = jwt.JWT(
        header={"alg": "RS256", "typ": "JWT", "kid": keypair.key_id},
        claims=claims,
    )

    jwt_token.make_signed_token(keypair)
    print(f"{token_use} token header: {jwt_token.serialize().split('.')[0]}")
    
    return jwt_token

def create_jwk_keypair() -> jwk.JWK:
    response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/jwk-private")
    private_key = response.get("SecretString")
    # create JWK format keys
    return jwk.JWK.from_json(private_key)

def save_token_dynamodb(request_id, queue_number, headers, iat, nbf, exp, access_token, id_token, refresh_token):
    # save claims info and tokens in dynamo
    item = {
        "event_id": EVENT_ID,
        "request_id": request_id,
        "issued_at": iat,
        "not_before": nbf,
        "expires": exp,
        "queue_number": queue_number,
        "access_token": access_token.serialize(), #scrub
        "id_token": id_token.serialize(),#scrub
        "refresh_token": refresh_token.serialize(),#scrub
        "session_status": 0
    }

    try:
        ddb_table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(request_id)"
        )
        response = {
            "statusCode": HTTPStatus.OK.value,
            "headers": headers,
            "body": json.dumps({
                "access_token": access_token.serialize(),
                "refresh_token": refresh_token.serialize(),
                "id_token": id_token.serialize(),
                "token_type": "Bearer",
                "expires_in": VALIDITY_PERIOD
            })
        }

        write_to_eventbus(request_id)
    except ClientError as e:
        response = handle_client_errors(e, request_id, headers)
    except Exception as e:
        print(e)
        raise e

    return response

def write_to_eventbus(request_id) -> None:
    # write to event bus
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
    # increment token counter
    rc.incr(TOKEN_COUNTER, 1)

def handle_client_errors(e, request_id, headers):
    if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
        raise e
    result = ddb_table.query(
        KeyConditionExpression=Key('request_id').eq(request_id))

    expires = int(result['Items'][0]['expires'])
    cur_time = int(time.time())
    remaining_time = expires - cur_time
    result = {
        "statusCode": HTTPStatus.OK.value, 
        "headers": headers, 
        "body": json.dumps(
            {
                "access_token": result['Items'][0]['access_token'], \
                "refresh_token": result['Items'][0]['refresh_token'], \
                "id_token": result['Items'][0]['id_token'], \
                "token_type": "Bearer", "expires_in": remaining_time
            }
        )
    }

    return result
