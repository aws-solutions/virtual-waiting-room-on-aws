# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the get_queue_position_expiry_time API handler.
It retrieves the expiry time for a queue number
"""

# pylint: disable=R0911

from http import HTTPStatus
import redis
import json
import os
import boto3
from time import time
from botocore import config
from boto3.dynamodb.conditions import Key
from vwr.common.sanitize import deep_clean
from vwr.common.validate import is_valid_rid
from counters import MAX_QUEUE_POSITION_EXPIRED, SERVING_COUNTER

REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
EVENT_ID = os.environ["EVENT_ID"]
SECRET_NAME_PREFIX = os.environ["STACK_NAME"]
SOLUTION_ID = os.environ["SOLUTION_ID"]
QUEUE_POSITION_ENTRYTIME_TABLE = os.environ["QUEUE_POSITION_ENTRYTIME_TABLE"]
QUEUE_POSITION_TIMEOUT_PERIOD = os.environ["QUEUE_POSITION_TIMEOUT_PERIOD"]
SERVING_COUNTER_ISSUEDAT_TABLE = os.environ["SERVING_COUNTER_ISSUEDAT_TABLE"]
ENABLE_QUEUE_POSITION_TIMEOUT = os.environ["ENABLE_QUEUE_POSITION_TIMEOUT"]

boto_session = boto3.session.Session()
region = boto_session.region_name
user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)
secrets_client = boto3.client('secretsmanager', config=user_config, endpoint_url=f"https://secretsmanager.{region}.amazonaws.com")
response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/redis-auth")
redis_auth = response.get("SecretString")
rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, ssl=True, decode_responses=True, password=redis_auth)
ddb_resource = boto3.resource('dynamodb', endpoint_url=f'https://dynamodb.{region}.amazonaws.com', config=user_config)
ddb_table_queue_position_entry_time = ddb_resource.Table(QUEUE_POSITION_ENTRYTIME_TABLE)
ddb_table_serving_counter_issued_at = ddb_resource.Table(SERVING_COUNTER_ISSUEDAT_TABLE)


def lambda_handler(event, context):
    """
    This function is the entry handler for Lambda.
    """
    print(event)
    current_time = int(time())
    request_id = deep_clean(event['queryStringParameters']['request_id'])
    client_event_id = deep_clean(event['queryStringParameters']['event_id'])
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }

    if not (client_event_id == EVENT_ID and is_valid_rid(request_id)):
        return {
            "statusCode": HTTPStatus.BAD_REQUEST.value,
            "headers": headers,
            "body": json.dumps({"error": "Invalid event or request ID"})
        }

    if not ENABLE_QUEUE_POSITION_TIMEOUT:
        return {
            "statusCode": HTTPStatus.ACCEPTED.value,
            "headers": headers,
            "body": json.dumps({"error": "Queue position expiration not enabled"})
        }

    queue_number = rc.hget(request_id, "queue_number")
    if not queue_number:
        return {
            "statusCode": HTTPStatus.NOT_FOUND.value,
            "headers": headers,
            "body": json.dumps({"error": "Request ID not found"})
        }

    print(f'Queue number: {queue_number}')

    if int(queue_number) > int(rc.get(SERVING_COUNTER)):
        return {
            "statusCode": HTTPStatus.ACCEPTED.value,
            "headers": headers,
            "body": json.dumps({"error": "Request ID not being served yet"})
        }
  
    if int(queue_number) <= int(rc.get(MAX_QUEUE_POSITION_EXPIRED)):
        return {
            "statusCode": HTTPStatus.GONE.value,
            "headers": headers,
            "body": json.dumps({"error": "Queue position has expired"})
        }

    response = ddb_table_queue_position_entry_time.query(
        KeyConditionExpression=Key('queue_position').eq(int(queue_number)),
        IndexName='QueuePositionIndex'
    )
    queue_position_item = response['Items'][0]
    queue_position_entry_time = int(queue_position_item['entry_time'])

    # serving counter gte queue number, should always have atleast 1 result 
    response = ddb_table_serving_counter_issued_at.query(
        KeyConditionExpression=Key('serving_counter').gte(int(queue_number)),
        Limit=1
    )
    serving_counter_item = response['Items'][0]
    serving_counter_issue_time = int(serving_counter_item['issue_time'])

    queue_time = max(queue_position_entry_time, serving_counter_issue_time)
    if current_time - queue_time > int(QUEUE_POSITION_TIMEOUT_PERIOD):
        return {
            "statusCode": HTTPStatus.GONE.value,
            "headers": headers,
            "body": json.dumps({"error": "Queue position has expired"})
        }
    
    return {
        "statusCode": HTTPStatus.OK.value,
        "headers": headers,
        "body": json.dumps({"Expires_in": int(QUEUE_POSITION_TIMEOUT_PERIOD) - (current_time - queue_time)})
    }
