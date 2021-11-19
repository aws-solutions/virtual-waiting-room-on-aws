"""
This module is responsible for preparing the waiting room for a load test.
1. Reset the waiting room via API
2. Update the inlet handler Lambda function environment variables
    with desired rate and duration

AWS credentials from the environment are required.
"""

import json
import os
import time
from urllib.parse import urlparse

import boto3
import requests
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

PRIVATE_API_ENDPOINT = os.environ["PRIVATE_API_ENDPOINT"]
PRIVATE_API_REGION = os.environ["PRIVATE_API_REGION"]
INLET_LAMBDA_NAME = os.environ["INLET_LAMBDA_NAME"]
EVENT_ID = os.environ["EVENT_ID"]

INCREMENT = 1000
HOLD_OFF = 30
DURATION = 7200


def reset_waiting_room():
    """
    This function is responsible for calling the reset_initial_state API
    """
    api = f"{PRIVATE_API_ENDPOINT}/reset_initial_state"
    body = {"event_id": EVENT_ID}
    parsed = urlparse(PRIVATE_API_ENDPOINT)
    auth = BotoAWSRequestsAuth(aws_host=parsed.netloc,
                               aws_region=PRIVATE_API_REGION,
                               aws_service='execute-api')
    response = requests.post(api, json=body, auth=auth, timeout=25)
    print(f"/reset_initial_state {response.status_code}")


def update_inlet_run_window():
    """
    This function is responsible for updating the time and increment on
    the periodic inlet Lambda function.
    """
    client = boto3.client("lambda")
    response = client.get_function_configuration(
        FunctionName=INLET_LAMBDA_NAME)
    environment = response["Environment"]["Variables"]
    # start in 1 minute from now
    start_ingest = int(time.time()) + HOLD_OFF
    # stop after 60 minutes
    # stop_ingest = start_ingest + DURATION
    # update the Lambda
    environment["START_TIME"] = f"{start_ingest}"
    # environment["END_TIME"] = f"{stop_ingest}"
    environment["END_TIME"] = "0"
    environment["INCREMENT_BY"] = f"{INCREMENT}"
    response = client.update_function_configuration(
        FunctionName=INLET_LAMBDA_NAME, Environment={"Variables": environment})
    print(json.dumps(response, indent=4))


if __name__ == "__main__":
    reset_waiting_room()
    update_inlet_run_window()
