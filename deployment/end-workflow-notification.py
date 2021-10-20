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
PAYLOAD = json.loads(os.environ.get('PAYLOAD'))
BRANCH = os.environ.get('BRANCH')
SOLUTION_NAME = 'aws-virtual-waiting-room'

def main():
    print(NOTIFICATION_ENDPOINT)
    print(PAYLOAD)
    PAYLOAD['solution_name'] = SOLUTION_NAME
    PAYLOAD['branch'] = BRANCH
    parsed = urlparse(NOTIFICATION_ENDPOINT)
    print(parsed)
    auth = BotoAWSRequestsAuth(aws_host=parsed.netloc,
                               aws_region=API_REGION,
                               aws_service='execute-api')
    response = requests.post(NOTIFICATION_ENDPOINT, json=PAYLOAD, auth=auth, timeout=25)
    print(response)

if __name__ == "__main__":
    main()
