# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the get_waiting_num API handler.
It retrieves the number currently queued in the waiting room and have not been issued a token yet.
"""


import redis
import json
import os
import boto3
from botocore import config
from counters import QUEUE_COUNTER, TOKEN_COUNTER, EXPIRED_QUEUE_COUNTER
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
secrets_client = boto3.client('secretsmanager', config=user_config, endpoint_url=f"https://secretsmanager.{region}.amazonaws.com")

response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/redis-auth")
redis_auth = response.get("SecretString")
rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, ssl=True, decode_responses=True, password=redis_auth)

def lambda_handler(event, _):
    """
    This function is the entry handler for Lambda.
    """
 
    print(event)
    client_event_id = deep_clean(event['queryStringParameters']['event_id'])
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }

    if client_event_id != EVENT_ID:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Invalid event ID"})
        }

    queue_count = int(rc.get(QUEUE_COUNTER))
    token_count = int(rc.get(TOKEN_COUNTER))
    expired_queue_count = int(rc.get(EXPIRED_QUEUE_COUNTER)) if rc.get(EXPIRED_QUEUE_COUNTER) else 0
    waiting_num = queue_count - token_count - expired_queue_count

    return {
        "statusCode": 200,
        "headers": headers,
        "body": json.dumps({"waiting_num": waiting_num})
    }
