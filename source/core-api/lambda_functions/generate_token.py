# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the generate_token API handler.
It generates a token for a valid request that has been allowed to complete its transaction. 
"""

import os
import json
import redis
import boto3
from http import HTTPStatus
from botocore import config
from vwr.common.sanitize import deep_clean
from vwr.common.validate import is_valid_rid
from generate_token_base import generate_token_base_method

# connection info and other globals
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
DDB_TOKEN_TABLE = os.environ["TOKEN_TABLE"]
SECRET_NAME_PREFIX = os.environ["STACK_NAME"]
VALIDITY_PERIOD = int(os.environ["VALIDITY_PERIOD"])
EVENT_ID = os.environ["EVENT_ID"]
EVENT_BUS_NAME = os.environ["EVENT_BUS_NAME"]
SOLUTION_ID = os.environ["SOLUTION_ID"]
QUEUE_POSITION_ENTRYTIME_TABLE = os.environ["QUEUE_POSITION_ENTRYTIME_TABLE"]
QUEUE_POSITION_TIMEOUT_PERIOD = os.environ["QUEUE_POSITION_TIMEOUT_PERIOD"]
SERVING_COUNTER_ISSUEDAT_TABLE = os.environ["SERVING_COUNTER_ISSUEDAT_TABLE"]
ENABLE_QUEUE_POSITION_TIMEOUT = os.environ["ENABLE_QUEUE_POSITION_TIMEOUT"]

user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)
boto_session = boto3.session.Session()
region = boto_session.region_name
ddb_resource = boto3.resource('dynamodb', endpoint_url=f'https://dynamodb.{region}.amazonaws.com', config=user_config)
ddb_table_tokens = ddb_resource.Table(DDB_TOKEN_TABLE)
ddb_table_queue_position_entry_time = ddb_resource.Table(QUEUE_POSITION_ENTRYTIME_TABLE)
ddb_table_serving_counter_issued_at = ddb_resource.Table(SERVING_COUNTER_ISSUEDAT_TABLE)
events_client = boto3.client('events', endpoint_url=f'https://events.{region}.amazonaws.com', config=user_config)

secrets_client = boto3.client('secretsmanager', endpoint_url=f'https://secretsmanager.{region}.amazonaws.com', config=user_config)
response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/redis-auth")
redis_auth = response.get("SecretString")
rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, ssl=True, decode_responses=True, password=redis_auth)


def lambda_handler(event, context):
    """
    This function is the entry handler for Lambda.
    """

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

    if client_event_id != EVENT_ID or not is_valid_rid(request_id):
        return {
            "statusCode": HTTPStatus.ACCEPTED.value, 
            "headers": headers,
            "body": json.dumps({"error": "Invalid event or request ID"})
        }

    is_header_key_id = True
    return generate_token_base_method(
        EVENT_ID, request_id, headers, rc, ENABLE_QUEUE_POSITION_TIMEOUT, QUEUE_POSITION_TIMEOUT_PERIOD, 
        secrets_client, SECRET_NAME_PREFIX, VALIDITY_PERIOD, issuer, events_client, EVENT_BUS_NAME, is_header_key_id,
        ddb_table_tokens, ddb_table_queue_position_entry_time, ddb_table_serving_counter_issued_at
    )
