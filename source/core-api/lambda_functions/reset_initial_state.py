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
ddb_client = boto3.client('dynamodb', endpoint_url="https://dynamodb."+region+".amazonaws.com", config=user_config)
secrets_client = boto3.client('secretsmanager', config=user_config, endpoint_url="https://secretsmanager."+region+".amazonaws.com")
response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/redis-auth")
redis_auth = response.get("SecretString")
rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, ssl=True, decode_responses=True, password=redis_auth)

def lambda_handler(event, context):
    """
    This function is the entry handler for Lambda.
    """

    print(event)
    client_event_id = deep_clean(event['event_id'])
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

        try:                       
            response = ddb_client.delete_table( TableName=DDB_TABLE_NAME )
            waiter = ddb_client.get_waiter('table_not_exists')
            # wait for table to get deleted
            waiter.wait(TableName=DDB_TABLE_NAME)
            print("Token table deleted")
            # recreate table
            response = ddb_client.create_table(
                TableName= DDB_TABLE_NAME,
                BillingMode = "PAY_PER_REQUEST",
                AttributeDefinitions = [
                    {
                        "AttributeName": "request_id",
                        "AttributeType": "S"
                    },
                    {
                        "AttributeName": "expires",
                        "AttributeType": "N"
                    },
                    {
                        "AttributeName": "event_id",
                        "AttributeType": "S"
                    }
                ],
                KeySchema = [
                    {
                        "AttributeName": "request_id",
                        "KeyType": "HASH"
                    }
                ],
                GlobalSecondaryIndexes = [
                    {
                        "IndexName": "EventExpiresIndex",
                        "KeySchema": [
                            {
                                "AttributeName": "event_id",
                                "KeyType": "HASH"
                            },
                            {
                                "AttributeName": "expires",
                                "KeyType": "RANGE"
                            }
                        ],
                        "Projection": {
                            "ProjectionType": "ALL"
                        }
                    }
                ],
                SSESpecification = {
                    "Enabled": True
                }
            )
            waiter = ddb_client.get_waiter('table_exists')
            # wait for table to get created
            waiter.wait(TableName=DDB_TABLE_NAME)
            print("Token table recreated")
            # enable PITR
            ddb_client.update_continuous_backups(
                TableName=DDB_TABLE_NAME,
                PointInTimeRecoverySpecification={
                    'PointInTimeRecoveryEnabled': True
                }
            )
            response = {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps({
                            "message": "Counters reset. DynamoDB table recreated."
                    })
            }
        except Exception as other_exception:
            print(other_exception)
            raise other_exception
    else:
        response = {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Invalid event ID"})
        }
    print(response)
    return response
