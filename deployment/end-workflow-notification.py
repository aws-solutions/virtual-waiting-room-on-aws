# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module sends notification about the end of a workflow run.
"""

import os
import json
import requests
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
from urllib.parse import urlparse

API_REGION = os.environ.get('AWS_DEFAULT_REGION')
NOTIFICATION_ENDPOINT = os.environ.get("NOTIFICATION_ENDPOINT")
PAYLOAD = os.environ.get("PAYLOAD")

def main():
    print(NOTIFICATION_ENDPOINT)
    parsed = urlparse(NOTIFICATION_ENDPOINT)
    print(parsed)
    auth = BotoAWSRequestsAuth(aws_host=parsed.netloc,
                               aws_region=API_REGION,
                               aws_service='execute-api')
    response = requests.post(NOTIFICATION_ENDPOINT, json=PAYLOAD, auth=auth, timeout=25)
    print(response)
    #print(f"/reset_initial_state {response.status_code}")
    print("some stuff")

if __name__ == "__main__":
    main()
