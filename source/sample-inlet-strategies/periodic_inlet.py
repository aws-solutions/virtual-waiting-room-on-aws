# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is one of the sample inlet strategies. 
It increments the serving counter every minute based on an increment_by value provided, but only if the current time is greater than the set start time,
and the end time has not been reached or is set to 0 (indefinite).
"""

import json
import os
from urllib.parse import urlparse
import time

import requests
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

EVENT_ID = os.environ.get("EVENT_ID")
CORE_API_ENDPOINT = os.environ.get("CORE_API_ENDPOINT")
INCREMENT_BY = int(os.environ.get("INCREMENT_BY"))
CORE_API_REGION = os.environ.get("CORE_API_REGION")
START_TIME = int(os.environ.get("START_TIME"))
END_TIME = int(os.environ.get("END_TIME"))

def lambda_handler(event, context):
    print(event)
    current_time = int(time.time())
    if (current_time > START_TIME and (END_TIME == 0 or current_time < END_TIME)):
        core_api = f'{CORE_API_ENDPOINT}/increment_serving_counter'
        body = {
            "event_id": EVENT_ID,
            "increment_by": INCREMENT_BY
        }
        parsed = urlparse(CORE_API_ENDPOINT)
        print(parsed)
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