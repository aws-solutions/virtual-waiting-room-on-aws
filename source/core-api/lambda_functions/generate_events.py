# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module runs only if enabled during core API deployment.
It writes various waiting room metrics to the waiting room's event bus. 
User can subscribe to the event bus to process the published data and act upon it, if desired. 
"""

import redis
import json
import boto3
import os
from botocore import config
from counters import *

# connection info and other globals
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
EVENT_ID = os.environ["EVENT_ID"]
EVENT_BUS_NAME = os.environ["EVENT_BUS_NAME"]
GET_NUM_ACTIVE_TOKENS_FN = os.environ["ACTIVE_TOKENS_FN"]
SOLUTION_ID = os.environ['SOLUTION_ID']
SECRET_NAME_PREFIX = os.environ["STACK_NAME"]

user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)
boto_session = boto3.session.Session()
region = boto_session.region_name
events_client = boto3.client('events', endpoint_url="https://events."+region+".amazonaws.com", config=user_config)
lambda_client = boto3.client('lambda', endpoint_url="https://lambda."+region+".amazonaws.com", config=user_config)
secrets_client = boto3.client('secretsmanager', endpoint_url="https://secretsmanager."+region+".amazonaws.com", config=user_config)
response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/redis-auth")
redis_auth = response.get("SecretString")
rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, ssl=True, decode_responses=True, password=redis_auth)

# put events for number of valid tokens, current queue_counter value, current serving_num value, 
# total items(tokens) in db, and items(tokens) marked session_completed
def lambda_handler(event, context):
    print(event)
    # get number of valid tokens
    # call get_num_active_tokens function
    
    input_params = {"queryStringParameters": {"event_id": EVENT_ID}}
    
    response = lambda_client.invoke(
        FunctionName = GET_NUM_ACTIVE_TOKENS_FN,
        InvocationType = 'RequestResponse',
        Payload = json.dumps(input_params)
    )
    result = response['Payload'].read()
    out = json.loads(result)
    body = json.loads(out["body"])
    num_active_tokens = body["active_tokens"]

    # get current queue_counter value
    queue_counter_value = rc.get(QUEUE_COUNTER)

    # get current serving_num value
    serving_number_value = rc.get(SERVING_COUNTER)

    # get total tokens generated
    total_tokens = rc.get(TOKEN_COUNTER)

    # get tokens marked completed
    completed_sessions = rc.get(COMPLETED_SESSION_COUNTER)

    # get tokens marked abandoned
    abandoned_sessions = rc.get(ABANDONED_SESSION_COUNTER)

    # write to event bus
    try:
        response = events_client.put_events(
            Entries=[
                {
                    'Source': 'custom.waitingroom',
                    'DetailType': 'waiting_room_metrics',
                    'Detail': json.dumps({"event_id": EVENT_ID,
                                "num_active_tokens": num_active_tokens,
                                "total_num_tokens": total_tokens,
                                "queue_counter": queue_counter_value,
                                "serving_number": serving_number_value,
                                "completed_sessions": completed_sessions,
                                "abandoned_sessions": abandoned_sessions}),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
    except Exception as exception:
        print(exception)
        raise exception
    
    return response