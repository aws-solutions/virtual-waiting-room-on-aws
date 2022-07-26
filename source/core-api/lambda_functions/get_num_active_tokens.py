# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the get_num_active_tokens API handler.
It queries DynamoDB for number of requests that have yet to expire, have not been completed, 
and have not been deemed abandoned. 
"""

import json
import os
import time
import boto3
from botocore import config
from boto3.dynamodb.conditions import Key, Attr
from vwr.common.sanitize import deep_clean

DDB_TOKEN_TABLE_NAME = os.environ["TOKEN_TABLE"]
EVENT_ID = os.environ["EVENT_ID"]
SOLUTION_ID = os.environ['SOLUTION_ID']

user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)
boto_session = boto3.session.Session()
region = boto_session.region_name
ddb_resource = boto3.resource('dynamodb', config=user_config)
ddb_table = ddb_resource.Table(DDB_TOKEN_TABLE_NAME)
    
def lambda_handler(event, context):
    """
    This function is the entry handler for Lambda.
    """

    print(event)
    client_event_id = deep_clean(event['queryStringParameters']['event_id'])
    headers = { 
                  'Content-Type': 'application/json',
                  'Access-Control-Allow-Origin': '*'
            }
    if client_event_id == EVENT_ID:
        try:
            current_time = int(time.time())
            response = ddb_table.query(
                IndexName="EventExpiresIndex",
                ProjectionExpression="request_id",
                KeyConditionExpression=Key('event_id').eq(EVENT_ID) & Key('expires').gte(current_time),
                FilterExpression=Attr('session_status').eq(0))
            items = response.get("Items", [])
            while "LastEvaluatedKey" in response:
                response = ddb_table.query(
                    IndexName="EventExpiresIndex",
                    ProjectionExpression="request_id",
                    KeyConditionExpression=Key('event_id').eq(EVENT_ID) & Key('expires').gte(current_time),
                    FilterExpression=Attr('session_status').eq(0),
                    ExclusiveStartKey=response["LastEvaluatedKey"])
                items = items + response.get("Items", [])
            response = { 
                        "statusCode": 200,
                        "headers": headers,
                        "body": json.dumps({"active_tokens": len(items)})
                }
        except Exception as e:
            print(e)
            raise e                      
    else:
        response = { 
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "Invalid event ID"})
        }
    print(response)
    return response
