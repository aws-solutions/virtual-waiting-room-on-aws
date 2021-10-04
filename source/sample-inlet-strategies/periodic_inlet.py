# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is one of the sample inlet strategies. 
It increments the serving counter every minute based on an increment_by value provided,
but only if the current time is greater than the set start time,
and the end time has not been reached or is set to 0 (indefinite).
User can optionally attach an alarm to this inlet, and will increment counter
if the alarm is in an OK state.
"""

import json
import os
from urllib.parse import urlparse
import time
import boto3
import requests
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

EVENT_ID = os.environ.get("EVENT_ID")
CORE_API_ENDPOINT = os.environ.get("CORE_API_ENDPOINT")
INCREMENT_BY = int(os.environ.get("INCREMENT_BY"))
CORE_API_REGION = os.environ.get("CORE_API_REGION")
START_TIME = int(os.environ.get("START_TIME"))
END_TIME = int(os.environ.get("END_TIME"))
CLOUDWATCH_ALARM = os.environ.get("CLOUDWATCH_ALARM")
cw_client = boto3.client('cloudwatch')

def lambda_handler(event, context):
    """
    This function is responsible for incrementing the serving counter on a periodic basis
    """

    print(event)
    current_time = int(time.time())
    # alarm could be OK, INSUFFICIENT_DATA or ALARM
    alarm_status = "OK"
    if CLOUDWATCH_ALARM:
        response = cw_client.describe_alarms( AlarmNames=[CLOUDWATCH_ALARM])
        print(response)
        if "MetricAlarms" in response and response["MetricAlarms"]:
            alarm_status = response["MetricAlarms"][0]["StateValue"]
        elif "CompositeAlarms" in response and response["CompositeAlarms"]:
            alarm_status = response["CompositeAlarms"][0]["StateValue"]
        else:
            print("Unable to find alarm.")
    if (current_time > START_TIME and (END_TIME == 0 or current_time < END_TIME) and alarm_status != "ALARM"):
        core_api = f'{CORE_API_ENDPOINT}/increment_serving_counter'
        body = {
            "event_id": EVENT_ID,
            "increment_by": INCREMENT_BY
        }
        parsed = urlparse(CORE_API_ENDPOINT)
        #print(parsed)
        # create an authentication signer for AWS
        auth = BotoAWSRequestsAuth(aws_host=parsed.netloc,
                                    aws_region=CORE_API_REGION,
                                    aws_service='execute-api')
        response = requests.post(core_api, json=body, auth=auth)
        print(response.status_code)
        print(response.content.decode())
        result = {
            "statusCode": response.status_code,
            "headers": {'Content-Type': 'text/plain'},
            "body": json.loads(response.text)
        }
    else:
        result = {
            "statusCode": "400",
            "headers": {'Content-Type': 'text/plain'},
            "body": json.dumps({"error": "Request is outside of valid time period."})
        }
    return result
