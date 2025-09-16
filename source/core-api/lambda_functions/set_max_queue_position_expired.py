# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the set_max_queue_position_expired API handler.
It sets the MAX_QUEUE_POSITION_EXPIRED value and optionally increments the serving counter.
"""

import boto3
import os
import redis
import json
from botocore import config
from time import time
from boto3.dynamodb.conditions import Key
from counters import MAX_QUEUE_POSITION_EXPIRED, QUEUE_COUNTER, RESET_IN_PROGRESS, SERVING_COUNTER, EXPIRED_QUEUE_COUNTER

SECRET_NAME_PREFIX = os.environ["STACK_NAME"]
SOLUTION_ID = os.environ['SOLUTION_ID']
EVENT_ID = os.environ["EVENT_ID"]
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
QUEUE_POSITION_ENTRYTIME_TABLE = os.environ["QUEUE_POSITION_ENTRYTIME_TABLE"]
QUEUE_POSITION_EXPIRY_PERIOD = os.environ["QUEUE_POSITION_EXPIRY_PERIOD"]
SERVING_COUNTER_ISSUEDAT_TABLE = os.environ["SERVING_COUNTER_ISSUEDAT_TABLE"]
INCR_SVC_ON_QUEUE_POS_EXPIRY = os.environ["INCR_SVC_ON_QUEUE_POS_EXPIRY"]
EVENT_BUS_NAME = os.environ["EVENT_BUS_NAME"]

user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)
boto_session = boto3.session.Session()
region = boto_session.region_name
ddb_resource = boto3.resource('dynamodb', endpoint_url=f'https://dynamodb.{region}.amazonaws.com', config=user_config)
ddb_table_queue_position_entry_time = ddb_resource.Table(QUEUE_POSITION_ENTRYTIME_TABLE)
ddb_table_serving_counter_issued_at = ddb_resource.Table(SERVING_COUNTER_ISSUEDAT_TABLE)
secrets_client = boto3.client('secretsmanager', config=user_config, endpoint_url=f'https://secretsmanager.{region}.amazonaws.com')
response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/redis-auth")
redis_auth = response.get("SecretString")
rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, ssl=True, decode_responses=True, password=redis_auth)
events_client = boto3.client('events', endpoint_url=f'https://events.{region}.amazonaws.com', config=user_config)

def lambda_handler(event, _):
    """
    This function is the entry handler for Lambda.
    """
    print(event)
    if _is_reset_in_progress():
        return

    counters = _get_current_counters()
    print(f'Queue counter: {counters["queue"]}. Max position expired: {counters["max_expired"]}. Serving counter: {counters["serving"]}')

    serving_items = _get_eligible_serving_items(counters["max_expired"])
    if not serving_items:
        return

    _process_serving_items(serving_items, counters["max_expired"])


def _is_reset_in_progress():
    if int(rc.get(RESET_IN_PROGRESS) or 0) != 0:
        print('Reset in progress. Skipping execution')
        return True
    return False


def _get_current_counters():
    return {
        "max_expired": int(rc.get(MAX_QUEUE_POSITION_EXPIRED) or 0),
        "serving": int(rc.get(SERVING_COUNTER) or 0),
        "queue": int(rc.get(QUEUE_COUNTER) or 0)
    }


def _get_eligible_serving_items(max_expired):
    response = ddb_table_serving_counter_issued_at.query(
        KeyConditionExpression=Key('event_id').eq(EVENT_ID) & Key('serving_counter').gt(max_expired),
    )
    items = response['Items']
    if not items:
        print('No serving counter items eligible')
    return items


def _process_serving_items(serving_items, initial_max_expired):
    previous_position = initial_max_expired
    current_time = int(time())
    
    for item in serving_items:
        if not _should_process_item(item, current_time):
            break
            
        position = int(item['serving_counter'])
        _update_max_expired_position(position)
        
        if INCR_SVC_ON_QUEUE_POS_EXPIRY == 'true':
            queue_positions_served = int(item['queue_positions_served'])
            incr_serving_counter(rc, queue_positions_served, position, previous_position)
            
        previous_position = position


def _should_process_item(serving_item, current_time):
    position = int(serving_item['serving_counter'])
    issue_time = int(serving_item['issue_time'])
    
    response = ddb_table_queue_position_entry_time.query(
        KeyConditionExpression=Key('queue_position').eq(position),
        IndexName='QueuePositionIndex',
    )
    
    if not response['Items']:
        print('No queue postions items eligible')
        return False
        
    entry_time = int(response['Items'][0]['entry_time'])
    queue_time = max(entry_time, issue_time)
    
    return current_time - queue_time >= int(QUEUE_POSITION_EXPIRY_PERIOD)


def _update_max_expired_position(position):
    if rc.set(MAX_QUEUE_POSITION_EXPIRED, position):
        print(f'Max queue expiry position set to: {position}')
    else:
        print(f'Failed to set max queue position served: Current value: {position}')


def incr_serving_counter(rc, queue_positions_served, serving_counter_item_position, previous_serving_counter_position):
    """
    Function to increment the serving counter based on queue postions served (indirectly expired positions)
    """
    # increment the serving counter by taking the difference of counter item entries and subtract positions served in that range
    # [(Current counter - Previous counter) - (Queue positions served in that range)]
    increment_by = (serving_counter_item_position - previous_serving_counter_position) - queue_positions_served
    
    # should never happen, addl guard
    if increment_by <= 0:
        print(f'Increment value calculated as {increment_by}, incrementing serving counter skipped')
        return

    rc.incrby(EXPIRED_QUEUE_COUNTER, int(increment_by))
    
    cur_serving = int(rc.incrby(SERVING_COUNTER, int(increment_by)))
    item = {
        'event_id': EVENT_ID,
        'serving_counter': cur_serving,
        'issue_time': int(time()),
        'queue_positions_served': 0
    }
    ddb_table_serving_counter_issued_at.put_item(Item=item)
    print(f'Item: {item}')
    print(f'Serving counter incremented by {increment_by}. Current value: {cur_serving}')

    events_client.put_events(
        Entries=[
            {
                'Source': 'custom.waitingroom',
                'DetailType': 'automatic_serving_counter_incr',
                'Detail': json.dumps(
                    {
                        'previous_serving_counter_position': cur_serving - increment_by,
                        'increment_by': increment_by,
                        'current_serving_counter_position': cur_serving,
                    }
                ),
                'EventBusName': EVENT_BUS_NAME
            }
        ]
    )
