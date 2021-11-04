# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module sends notification about the end of a workflow run
and its associated artifacts.
"""

import os
import json
import requests
import json
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
from urllib.parse import urlparse

API_REGION = os.environ.get('AWS_DEFAULT_REGION')
NOTIFICATION_ENDPOINT = os.environ.get('NOTIFICATION_ENDPOINT')

SOLUTION_NAME = 'aws-virtual-waiting-room'
PAYLOAD = {}
PAYLOAD['solution_name'] = SOLUTION_NAME
PAYLOAD['branch'] = os.environ.get('BRANCH')
PAYLOAD['workflow_name'] = os.environ.get('WORKFLOW_NAME')
PAYLOAD['commit_id'] = os.environ.get('COMMIT_ID')
PAYLOAD['workflow_run_id'] = os.environ.get('WORKFLOW_RUN_ID')

def main():
    parsed = urlparse(NOTIFICATION_ENDPOINT)
    auth = BotoAWSRequestsAuth(aws_host=parsed.netloc,
                               aws_region=API_REGION,
                               aws_service='execute-api')
    print(PAYLOAD)
    response = requests.post(NOTIFICATION_ENDPOINT, json=PAYLOAD, auth=auth, timeout=25)
    print(response.text)
    if response.status_code != 200:
        return 1
    else:
        return 0

if __name__ == "__main__":
    main()
