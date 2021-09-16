# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the get_queue_num API handler.
It retrieves the queue number assigned to a request from redis.
"""

import redis
import json
import os
import boto3
from botocore import config
from vwr.common.sanitize import deep_clean
from vwr.common.validate import is_valid_rid

# connection info
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
EVENT_ID = os.environ["EVENT_ID"]
SECRET_NAME_PREFIX = os.environ["STACK_NAME"]
SOLUTION_ID = os.environ['SOLUTION_ID']

boto_session = boto3.session.Session()
region = boto_session.region_name
user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)
secrets_client = boto3.client('secretsmanager', config=user_config, endpoint_url="https://secretsmanager."+region+".amazonaws.com")
response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/redis-auth")
redis_auth = response.get("SecretString")
rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, ssl=True, decode_responses=True, password=redis_auth)


def lambda_handler(event, context):
    print(event)
    request_id = deep_clean(event['queryStringParameters']['request_id'])
    client_event_id = deep_clean(event['queryStringParameters']['event_id'])
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }

    if client_event_id == EVENT_ID and is_valid_rid(request_id):
        queue_number = rc.hget(request_id, "queue_number")
        client_record = rc.hgetall(request_id)
        if queue_number:
            print(queue_number)
            response = {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(client_record)
            }
        else:
            # request wasn't found in redis but event_id is valid
            response = {
                "statusCode": 202,
                "headers": headers,
                "body": json.dumps({"error": "Request ID not found"})
            }
    else:
        response = {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Invalid event or request ID"})
        }
    return response
