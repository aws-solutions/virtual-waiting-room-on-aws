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
from http  import HTTPStatus
from botocore import config
from counters import SERVING_COUNTER, TOKEN_COUNTER
from vwr.common.sanitize import deep_clean
from vwr.common.validate import is_valid_rid
import token_helper

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
                keypair = token_helper.create_jwk_keypair(secrets_client, SECRET_NAME_PREFIX)

                record = ddb_table.get_item(Key={"request_id": request_id})
                if 'Item' in record:
                    claims = token_helper.create_claims_from_record(record)
                    (access_token, refresh_token, id_token) = token_helper.create_tokens(claims, keypair, False)
                    expires = int(record['Item']['expires'])
                    cur_time = int(time.time())

                    return {
                        "statusCode": HTTPStatus.OK.value, 
                        "headers": headers, 
                        "body": json.dumps(
                            {
                                "access_token": access_token.serialize(),
                                "refresh_token": refresh_token.serialize(), 
                                "id_token": id_token.serialize(), 
                                "token_type": "Bearer", 
                                "expires_in": expires - cur_time
                            }
                        )
                    }

                # request_id is not in ddb_table, create and save record to ddb_table
                iat = int(time.time())  # issued-at and not-before can be the same time (epoch seconds)
                nbf = iat
                exp = iat + VALIDITY_PERIOD # expiration (exp) is a time after iat and nbf, like 1 hour (epoch seconds)
                claims = token_helper.create_claims(EVENT_ID, request_id, issuer, queue_number, iat, nbf, exp)
                record = {
                    "event_id": EVENT_ID,
                    "request_id": request_id,
                    "issued_at": iat,
                    "not_before": nbf,
                    "expires": exp,
                    "queue_number": queue_number,
                    'issuer': issuer,
                    "session_status": 0
                }

                try:
                    ddb_table.put_item(Item=record)
                except Exception as e:
                    print(e)
                    raise e
                
                (access_token, refresh_token, id_token) = token_helper.create_tokens(claims, keypair, True)
                token_helper.write_to_eventbus(events_client, EVENT_ID, EVENT_BUS_NAME, request_id)
                rc.incr(TOKEN_COUNTER, 1)

                response = {
                    "statusCode": HTTPStatus.OK.value, 
                    "headers": headers, 
                    "body": json.dumps(
                        {
                            "access_token": access_token.serialize(),
                            "refresh_token": refresh_token.serialize(), 
                            "id_token": id_token.serialize(), 
                            "token_type": "Bearer", 
                            "expires_in": VALIDITY_PERIOD
                        }
                    )
                }
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