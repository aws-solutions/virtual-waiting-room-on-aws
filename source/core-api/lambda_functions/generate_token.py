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
ddb_resource = boto3.resource('dynamodb', endpoint_url="https://dynamodb."+region+".amazonaws.com", config=user_config)
ddb_table = ddb_resource.Table(DDB_TABLE_NAME)
events_client = boto3.client('events', endpoint_url="https://events."+region+".amazonaws.com", config=user_config)

secrets_client = boto3.client('secretsmanager', endpoint_url="https://secretsmanager."+region+".amazonaws.com", config=user_config)
response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/redis-auth")
redis_auth = response.get("SecretString")
rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, ssl=True, decode_responses=True, password=redis_auth)
   
def lambda_handler(event, context):
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
        queue_number = rc.hget(request_id, "queue_number")
        if queue_number:
            if int(queue_number) <= int(rc.get(SERVING_COUNTER)):
                # check to see if there's a valid token for this request in dynamo. if there isn't one or already expired,
                response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/jwk-private")
                private_key = response.get("SecretString")
                response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/jwk-public")
                # create JWK format keys
                keypair = jwk.JWK.from_json(private_key)
                # issued-at and not-before can be the same time (epoch seconds)
                iat = int(time.time())
                nbf = iat
                # expiration (exp) is a time after iat and nbf, like 1 hour (epoch seconds)
                exp = iat + VALIDITY_PERIOD

                # create access token claims
                claims = {
                    'aud': EVENT_ID,
                    'sub': request_id,
                    'queue_position': queue_number,
                    'token_use': 'access',
                    'iat': iat,
                    'nbf': nbf,
                    'exp': exp,
                    'iss': issuer
                }

                access_token = jwt.JWT(header={"alg": "RS256", "typ": "JWT", "kid": keypair.key_id}, claims=claims)
                access_token.make_signed_token(keypair)
                print(f"access token header: {access_token.serialize().split('.')[0]}")
                
                # create ID token claims
                claims["token_use"] = "id"
                id_token = jwt.JWT(header={"alg": "RS256", "typ": "JWT", "kid": keypair.key_id}, claims=claims)
                id_token.make_signed_token(keypair)
                print(f"id token header: {id_token.serialize().split('.')[0]}")

                # create refresh token claims
                claims["token_use"]="refresh"
                refresh_token = jwt.JWT(header={"alg": "RS256", "typ": "JWT", "kid": keypair.key_id}, claims=claims)
                refresh_token.make_signed_token(keypair)
                print(f"refresh token header: {refresh_token.serialize().split('.')[0]}")

                # save claims info and tokens in dynamo
                item = {
                        "event_id": EVENT_ID,
                        "request_id": request_id,
                        "issued_at": iat,
                        "not_before": nbf,
                        "expires": exp,
                        "queue_number": queue_number,
                        "access_token": access_token.serialize(),
                        "id_token": id_token.serialize(),
                        "refresh_token": refresh_token.serialize(),
                        "session_status": 0
                    }
                try:
                    ddb_table.put_item(
                        Item=item,
                        ConditionExpression="attribute_not_exists(request_id)"
                    )
                    response = {
                        "statusCode": 200,
                        "headers": headers,
                        "body": json.dumps({
                            "access_token": access_token.serialize(),
                            "refresh_token": refresh_token.serialize(),
                            "id_token": id_token.serialize(),
                            "token_type": "Bearer",
                            "expires_in": VALIDITY_PERIOD
                        })
                    }
                    # write to event bus
                    events_client.put_events(
                        Entries=[
                            {
                                'Source': 'custom.waitingroom',
                                'DetailType': 'token_generated',
                                'Detail': json.dumps({"event_id": EVENT_ID,
                                                      "request_id": request_id}),
                                'EventBusName': EVENT_BUS_NAME
                            }
                        ]
                    )
                    # increment token counter
                    rc.incr(TOKEN_COUNTER, 1)

                except ClientError as e:
                    if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                        # query the item, and calculate when it expired
                        result = ddb_table.query(
                            KeyConditionExpression=Key('request_id').eq(request_id))
                        expires = int(result['Items'][0]['expires'])
                        cur_time = int(time.time())
                        remaining_time = expires - cur_time
                        response = {
                            "statusCode": 200,
                            "headers": headers,
                            "body": json.dumps({
                                "access_token": result['Items'][0]['access_token'],
                                "refresh_token": result['Items'][0]['refresh_token'],
                                "id_token": result['Items'][0]['id_token'],
                                "token_type": "Bearer",
                                "expires_in": remaining_time
                            })
                        }
                    else:
                        raise e
                except Exception as e:
                    print(e)
                    raise e
            else:
                response = {
                    "statusCode": 202,
                    "headers": headers,
                    "body": json.dumps({"error": "Request ID not being served yet"})
                }
        else:
            response = {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": "Invalid request ID"})
            }
    else:
        response = {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Invalid event or request ID"})
        }
    return response
