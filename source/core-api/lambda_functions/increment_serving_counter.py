# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the increment_serving_counter API handler.
As the name implies, it increments the waiting room's serving counter by the given increment_by value.
Authorization is required to invoke this API.
"""

import redis
import os
import json
import boto3
from botocore import config
from counters import SERVING_COUNTER
from vwr.common.sanitize import deep_clean

# connection info and other globals
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
    """
    This function is the entry handler for Lambda.
    """

    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }
    body = json.loads(event['body'])
    increment_by = body['increment_by']
    client_event_id = deep_clean(body['event_id'])

    if client_event_id == EVENT_ID:
        cur_serving = rc.incrby(SERVING_COUNTER, increment_by)
        print(f"cur_serving: {cur_serving}")
        response = {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"serving_num": cur_serving})
        }
    else:
        response = {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Invalid event ID"})
        }
    return response
