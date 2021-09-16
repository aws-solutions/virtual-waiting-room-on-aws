# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the used to reset the counters and DynamoDB table used by the core API.
"""

import redis
import json
import os
import boto3
from botocore import config
from counters import *
from vwr.common.sanitize import deep_clean

DDB_TABLE_NAME = os.environ["TOKEN_TABLE"]
EVENT_ID = os.environ["EVENT_ID"]
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
SOLUTION_ID = os.environ['SOLUTION_ID']
SECRET_NAME_PREFIX = os.environ["STACK_NAME"]

user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)
boto_session = boto3.session.Session()
region = boto_session.region_name
ddb_resource = boto3.resource('dynamodb', endpoint_url="https://dynamodb."+region+".amazonaws.com", config=user_config)
ddb_table = ddb_resource.Table(DDB_TABLE_NAME)
secrets_client = boto3.client('secretsmanager', config=user_config, endpoint_url="https://secretsmanager."+region+".amazonaws.com")
response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/redis-auth")
redis_auth = response.get("SecretString")
rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, ssl=True, decode_responses=True, password=redis_auth)

def lambda_handler(event, context):
    print(event)
    body = json.loads(event['body'])
    client_event_id = deep_clean(body['event_id'])
    response = {}
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }

    if EVENT_ID == client_event_id:
        # reset counters
        rc.getset(SERVING_COUNTER, 0)
        rc.getset(QUEUE_COUNTER, 0)
        rc.getset(TOKEN_COUNTER, 0)
        rc.getset(COMPLETED_SESSION_COUNTER, 0)
        rc.getset(ABANDONED_SESSION_COUNTER, 0)

        # empty table
        response = ddb_table.scan(ProjectionExpression="request_id")
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = ddb_table.scan(
                ProjectionExpression="request_id",
                ExclusiveStartKey=response["LastEvaluatedKey"])
            items = items + response.get("Items", [])
        for item in items:
            ddb_table.delete_item(Key={"request_id": item["request_id"]})
        response = {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "message": "Counters reset. DynamoDB table cleared."
            })
        }
    else:
        response = {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Invalid event ID"})
        }
    print(response)
    return response
