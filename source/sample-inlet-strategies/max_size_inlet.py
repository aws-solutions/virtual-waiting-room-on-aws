# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is one of the sample inlet strategies. 
It increments the serving counter based on the maximum size of transactions that the downstream site can handle. 
This module expects to receive a message through an SNS topic that can include:
- exited : number of transactions that have completed
- list of request IDs to be marked completed
- list of request IDs to be marked abandoned
Above data is used to determine how much to increment the serving counter.
"""

import json
import os
from urllib.parse import urlparse

import requests
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

EVENT_ID = os.environ.get("EVENT_ID")
CORE_API_ENDPOINT = os.environ.get("CORE_API_ENDPOINT")
CORE_API_REGION = os.environ.get("CORE_API_REGION")
MAX_SIZE = int(os.environ.get("MAX_SIZE"))
TIMEOUT = 60

increment_by_api = f'{CORE_API_ENDPOINT}/increment_serving_counter'
update_status_api = f'{CORE_API_ENDPOINT}/update_session'
active_tokens_api = f'{CORE_API_ENDPOINT}/num_active_tokens'
num_updated_tokens = 0

def lambda_handler(event, _):
    """
    This function is responsible for processing an SNS message to update serving counter
    """

    print(event)
    msg = json.loads(event["Records"][0]["Sns"]["Message"])
    result = json.dumps({"message": "Nothing to process."})

    if msg:
        exited = None
        increment_by = 0
        parsed = urlparse(CORE_API_ENDPOINT)
        # create an authentication signer for AWS
        auth = BotoAWSRequestsAuth(aws_host=parsed.netloc,
                                    aws_region=CORE_API_REGION,
                                    aws_service='execute-api')
    
        if "exited" in msg:
            exited = int(msg["exited"])

        # Update tokens' status
        if "completed" in msg:
            status = 1
            update_tokens(status, msg["completed"], auth)
                
        if "abandoned" in msg: 
            status = -1
            update_tokens(status, msg["abandoned"], auth)
        
        # Call num_active_tokens and subtract result from max allowed users
        payload = {"event_id": EVENT_ID}
        response = requests.get(active_tokens_api, params=payload, auth=auth, timeout=TIMEOUT)
        active_tokens = response.json()["active_tokens"]
        capacity = MAX_SIZE - int(active_tokens)

        # Always use the value provided with "exited" for increment_serving_counter when provided 
        if exited is not None and exited < capacity:
            increment_by = exited
        # otherwise the sum of items in "completed" and "abandoned" lists
        elif num_updated_tokens < capacity: 
            increment_by = num_updated_tokens
        # but if capacity is less than exited value and num_updated_tokens, 
        # then use that value to increment serving counter
        else: 
            increment_by = capacity
        body = {
                "event_id": EVENT_ID,
                "increment_by": increment_by
        }
        print(f"exited: {exited}, num_updated_tokens: {num_updated_tokens}, capacity: {capacity}, increment_by: {increment_by}")
        # only increment counter if exited information was present or tokens were actually updated
        if exited or num_updated_tokens > 0:
            response = requests.post(increment_by_api, json=body, auth=auth, timeout=TIMEOUT)
            result = response.json()
    print(result)    
    return result

def update_tokens(status, request_ids, auth):
    """
    This function is responsible for updating the status of a token via the API
    """

    global num_updated_tokens
    print(f"number of status {status}: {len(request_ids)}")

    body = {
        "event_id": EVENT_ID,
        "status": status
    }
    for request_id in request_ids:
        body["request_id"] = request_id
        response = requests.post(update_status_api, json=body, auth=auth, timeout=TIMEOUT)
        if response.status_code == 200:
            num_updated_tokens += 1
        print(response.content.decode())
