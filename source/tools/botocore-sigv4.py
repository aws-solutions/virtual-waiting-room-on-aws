# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import os
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
import requests


def post_request():
    credentials = Credentials(
        os.environ['AWS_ACCESS_KEY_ID'],
        os.environ['AWS_SECRET_ACCESS_KEY'],
        os.environ['AWS_SESSION_TOKEN']
    )

    sigv4 = SigV4Auth(credentials, 'execute-api', 'us-east-1')
    endpoint = 'https://[API_ID].execute-api.us-east-1.amazonaws.com/prod'
    data = {"My": "body"}
    headers = {'Content-Type': 'application/json'}
    request = AWSRequest(method='POST', url=endpoint, data=data, headers=headers)
    sigv4.add_auth(request)
    prepped = request.prepare()

    response = requests.post(prepped.url, headers=prepped.headers, data=data)
    print("POST Request: {}".format(response.text))


def get_request():
    credentials = Credentials(
        os.environ['AWS_ACCESS_KEY_ID'],
        os.environ['AWS_SECRET_ACCESS_KEY'],
        # os.environ['AWS_SESSION_TOKEN'],
    )

    sigv4 = SigV4Auth(credentials, 'execute-api', 'us-east-1')
    endpoint = 'https://[API_ID].execute-api.us-east-1.amazonaws.com/prod'
    request = AWSRequest(method='GET', url=endpoint)
    sigv4.add_auth(request)
    prepped = request.prepare()

    response = requests.get(prepped.url, headers=prepped.headers)

    print("GET Request: {}".format(response.text))


def lambda_handler(event, context):
    post_request()
    get_request()

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }
