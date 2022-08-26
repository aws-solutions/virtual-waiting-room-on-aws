# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the custom resource used to intialize the various counters used by the core API.
It also redeploys the public and private APIs whenever there's an update.
"""

import os
import time
from urllib.parse import urlparse
from crhelper import CfnResource
import requests
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
import boto3
from botocore import config

# connection info and other globals
helper = CfnResource()
EVENT_ID = os.environ.get("EVENT_ID")
CORE_API_ENDPOINT = os.environ.get("CORE_API_ENDPOINT")
PUBLIC_API_ID = os.environ.get("PUBLIC_API_ID")
PRIVATE_API_ID = os.environ.get("PRIVATE_API_ID")
API_STAGE = os.environ.get("API_STAGE")
boto_session = boto3.session.Session()
region = boto_session.region_name
SOLUTION_ID = os.environ['SOLUTION_ID']
user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)
api_client = boto3.client("apigateway", config=user_config)

@helper.create
def create(event, _):
    """
    This function makes an authenticated call to the private API endpoint
    to intialize the various counters used by the core API.
    """
    print(event)
    core_api = f'{CORE_API_ENDPOINT}/reset_initial_state'
    body = {
        "event_id": EVENT_ID
    }
    parsed = urlparse(CORE_API_ENDPOINT)
    # create an authentication signer for AWS
    auth = BotoAWSRequestsAuth(aws_host=parsed.netloc,
                                aws_region=region,
                                aws_service='execute-api')
    response = requests.post(core_api, json=body, auth=auth, timeout=600)
    print(response.status_code)

@helper.update
def update(event, _):
    """
    Counters and DynamoDB table are not reset during update.
    Both public and private APIs are redeployed since that doesn't happen automatically.
    """
    print(event)
    print("Not resetting counters on update.")
    print("Redeploying APIs.")
    api_client.create_deployment(
        restApiId=PUBLIC_API_ID, 
        stageName=API_STAGE, 
        description="Automated deployment through waiting room core API update.")
    # avoid throttling
    time.sleep(5)
    api_client.create_deployment(
        restApiId=PRIVATE_API_ID, 
        stageName=API_STAGE, 
        description="Automated deployment through waiting room core API update.")

@helper.delete
def delete(event, _):
    """
    Counters and DynamoDB table are untouched during delete.
    """
    print(event)
    print("Not deleting counters on delete.")

def handler(event, context):
    """
    This function is the entry point for the Lambda-backed custom resource.
    """
    helper(event, context)
