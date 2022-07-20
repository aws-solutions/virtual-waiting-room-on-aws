# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the assign_queue_num API handler.
It processes the requests sent to the SQS queue and
assigns a queue number to each of the request (message).
"""

# pylint: disable=E0401,C0301,W0703

import os
import json

import boto3
import redis
from time import time
from botocore import config
from vwr.common.sanitize import deep_clean
from counters import QUEUE_COUNTER

# connection info and other globals
SOLUTION_ID = os.environ['SOLUTION_ID']
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = os.environ["REDIS_PORT"]
QUEUE_URL = os.environ["QUEUE_URL"]
EVENT_ID = os.environ["EVENT_ID"]
SECRET_NAME_PREFIX = os.environ["STACK_NAME"]
QUEUE_POSITION_ISSUEDAT_TABLE = os.environ["QUEUE_POSITION_ISSUEDAT_TABLE"]
ENABLE_QUEUE_POSITION_EXPIRY = os.environ["ENABLE_QUEUE_POSITION_EXPIRY"]

boto_session = boto3.session.Session()
region = boto_session.region_name
user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)
sqs_client = boto3.client('sqs', config=user_config, endpoint_url=f"https://sqs.{region}.amazonaws.com")
secrets_client = boto3.client('secretsmanager', config=user_config, endpoint_url=f"https://secretsmanager.{region}.amazonaws.com")
secrets_response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/redis-auth")
redis_auth = secrets_response.get("SecretString")
rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, ssl=True, decode_responses=True, password=redis_auth)
ddb_resource = boto3.resource('dynamodb', endpoint_url=f'https://dynamodb.{region}.amazonaws.com', config=user_config)
ddb_table = ddb_resource.Table(QUEUE_POSITION_ISSUEDAT_TABLE)


def lambda_handler(event, _):
    """
    This function is the entry handler for Lambda.
    """
    print(event)
    num_msg = len(event['Records'])

    # this is done atomically
    cur_count = rc.incr(QUEUE_COUNTER, num_msg)
    print(cur_count)

    q_start_num = cur_count - (num_msg-1)
    # iterate over msgs
    return_with_exception = False
    for msg in event['Records']:
        try:
            body = json.loads(msg['body'])
            request_id = msg['messageAttributes']['apig_request_id']['stringValue']
            client_event_id = deep_clean(body['event_id'])

            # if valid, assign number and del msg
            # if the event ID is invalid, don't process it at all
            if client_event_id == EVENT_ID:
                # write item back to redis, use hset and use request_id as the key
                # as item gets written, delete the message from queue right away
                # use HSETNX so no effect on queue_number if already exists
                entry_time = int(time())
                rc.hsetnx(request_id, "entry_time", entry_time)
                rc.hsetnx(request_id, "queue_number", q_start_num)
                rc.hsetnx(request_id, "event_id", EVENT_ID)
                rc.hsetnx(request_id, "status", 1)
                result = rc.hgetall(request_id)
                print(result)

            # sqs has a vpc endpoint
            response = sqs_client.delete_message(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=msg["receiptHandle"]
            )

            if ENABLE_QUEUE_POSITION_EXPIRY == 'true':
                item = {
                    'event_id': EVENT_ID,
                    'queue_position': int(q_start_num),
                    'issue_time': int(time()),
                    'request_id': request_id,
                }
                ddb_table.put_item(Item=item)
                print(f"Item: {item}")

            print(response)
            q_start_num+=1
        except Exception as exception:
            print(exception)
            return_with_exception = True
    if return_with_exception:
        raise Exception("one or more messages failed processing")
    # return the current count based on this batch process
    return cur_count
