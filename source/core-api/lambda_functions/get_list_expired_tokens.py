# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the get_list_expired_tokens API handler.
It queries DynamoDB for requests that were issued tokens which have since expired.
"""

import json
import boto3
import os
import time
from botocore import config
from boto3.dynamodb.conditions import Key
from vwr.common.sanitize import deep_clean

DDB_TABLE_NAME = os.environ["TOKEN_TABLE"]
EVENT_ID = os.environ["EVENT_ID"]
SOLUTION_ID = os.environ['SOLUTION_ID']

user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)
boto_session = boto3.session.Session()
region = boto_session.region_name
ddb_resource = boto3.resource('dynamodb', config=user_config)
ddb_table = ddb_resource.Table(DDB_TABLE_NAME)
    
def lambda_handler(event, context):
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
                KeyConditionExpression=Key('event_id').eq(EVENT_ID) & Key('expires').lt(current_time))
            items = [item['request_id'] for item in response['Items']]
            while "LastEvaluatedKey" in response:
                response = ddb_table.query(
                    IndexName="EventExpiresIndex",
                    ProjectionExpression="request_id",
                    KeyConditionExpression=Key('event_id').eq(EVENT_ID) & Key('expires').lt(current_time),
                    ExclusiveStartKey=response["LastEvaluatedKey"])
                items.append([item['request_id'] for item in response['Items']])
            response = {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(items)
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
