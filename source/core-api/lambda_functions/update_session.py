# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the update_session API handler.
It updates the status of a session (token) stored in DynamoDB.
Session status is denoted by an integer. Sessions set to a status of 1 indicates completed, and -1 indicates abandoned.
Authorization is required to invoke this API.
"""

import redis
import json
import boto3
import os
from botocore.exceptions import ClientError
from botocore import config
from boto3.dynamodb.conditions import Attr
from counters import COMPLETED_SESSION_COUNTER, ABANDONED_SESSION_COUNTER
from vwr.common.sanitize import deep_clean
from vwr.common.validate import is_valid_rid

# connection info and other globals
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
EVENT_ID = os.environ["EVENT_ID"]
EVENT_BUS_NAME = os.environ["EVENT_BUS_NAME"]
DDB_TOKEN_TABLE_NAME = os.environ["TOKEN_TABLE"]
SOLUTION_ID = os.environ['SOLUTION_ID']
SECRET_NAME_PREFIX = os.environ["STACK_NAME"]

user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)
boto_session = boto3.session.Session()
region = boto_session.region_name
ddb_resource = boto3.resource('dynamodb', endpoint_url=f"https://dynamodb.{region}.amazonaws.com", config=user_config)
ddb_table = ddb_resource.Table(DDB_TOKEN_TABLE_NAME)
events_client = boto3.client('events', endpoint_url=f"https://events.{region}.amazonaws.com", config=user_config)
status_codes = {1: "completed", -1: "abandoned"}
secrets_client = boto3.client('secretsmanager', config=user_config, endpoint_url=f"https://secretsmanager.{region}.amazonaws.com")
response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/redis-auth")
redis_auth = response.get("SecretString")
rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, ssl=True, decode_responses=True, password=redis_auth)

def lambda_handler(event, _):
    """
    This function is the entry handler for Lambda.
    """

    print(event)
    body = json.loads(event['body'])
    request_id = deep_clean(body['request_id'])
    client_event_id = deep_clean(body['event_id'])
    status = int(body['status'])
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }

    if client_event_id == EVENT_ID and is_valid_rid(request_id):
        try:
            result = ddb_table.update_item(
                UpdateExpression='SET session_status = :status',
                ConditionExpression=(Attr('request_id').eq(request_id) and Attr('session_status').eq(0)),
                Key={'request_id': request_id},
                ExpressionAttributeValues={':status': status}
            )
            response = {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(result)
            }
            # write to event bus
            events_client.put_events(
                Entries=[
                    {
                        'Source': 'custom.waitingroom',
                        'DetailType': 'session_updated',
                        'Detail': json.dumps({"event_id": EVENT_ID,
                                              "request_id": request_id,
                                              "status": status_codes[status]}),
                        'EventBusName': EVENT_BUS_NAME
                    }
                ]
            )
            # increment counter tracking sessions completed
            if status == -1:
                rc.incr(ABANDONED_SESSION_COUNTER, 1)

            elif status == 1:
                rc.incr(COMPLETED_SESSION_COUNTER, 1)
        except ClientError as e:
            if e.response['Error']['Code'] != 'ConditionalCheckFailedException':
                raise e
            print(e)
            response = {"statusCode": 404, "headers": headers, "body": json.dumps({"error": "Request ID doesn't exist or status already set."})}

        except Exception as e:
            print(e)
            raise e
    else:
        response = {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Invalid event or request ID"})
        }
        
    print(response)
    
    return response
