# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This module is the custom resource used by CloudFormation to install
web pages into a bucket for CloudFront. It also adds a JavaScript file containing
endpoints to access specified APIs.
"""

import os

from crhelper import CfnResource
import boto3
from botocore import config

helper = CfnResource()

# this is where the web contents are packaged
CONTENTS_LOCAL = "www"

SOLUTION_ID = os.environ['SOLUTION_ID']
user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)


@helper.create
@helper.update
def update_web_content(event, _):
    """
    This function is responsible for creating or updating web content
    """
    bucket_name = event["ResourceProperties"]["BucketName"]
    apis = event["ResourceProperties"]["APIs"]
    delete_bucket_contents(bucket_name)
    put_web_contents(bucket_name)
    put_api_endpoints_js(bucket_name, apis)


@helper.delete
def delete_web_content(event, _):
    """
    This function is responsible for deleting web content
    """
    bucket_name = event["ResourceProperties"]["BucketName"]
    delete_bucket_contents(bucket_name)


def handler(event, context):
    """
    Lambda entry point.
    """
    helper(event, context)


def put_web_contents(bucket_name):
    """
    This function is responsible for removing any existing contents
    from the specified bucket, and adding contents to the bucket
    from the packaged contents.
    """
    client = boto3.client("s3", config=user_config)

    # upload each local file to the bucket, preserve folders
    for dirpath, _, filenames in os.walk(CONTENTS_LOCAL):
        for name in filenames:
            local = f"{dirpath}/{name}"
            remote = local.replace(f"{CONTENTS_LOCAL}/", "")
            print(f'put {local}')
            content_type = None
            if remote.endswith(".js"):
                content_type = "application/javascript"
            elif remote.endswith(".html"):
                content_type = "text/html"
            elif remote.endswith(".css"):
                content_type = "text/css"
            else:
                content_type = "binary/octet-stream"
            with open(local, 'rb') as data:
                client.put_object(Bucket=bucket_name,
                                  Key=remote,
                                  Body=data,
                                  ContentType=content_type)


def put_api_endpoints_js(bucket_name, apis):
    """
    This function is responsible for creating a file
    containing the URL of the Core API endpoint.
    """
    client = boto3.client("s3", config=user_config)
    key = "api_endpoints.js"
    content_type = "application/javascript"
    contents = ""
    for name, url in apis.items():
        contents = f'{contents}const {name} = \"{url}\";\n'
    client.put_object(Bucket=bucket_name, 
        Key=key, 
        Body=contents, 
        ContentType=content_type
    )


def delete_bucket_contents(bucket_name):
    """
    This function is responsible for removing all contents from the specified bucket.
    """
    client = boto3.client("s3", config=user_config)
    response = client.list_objects_v2(Bucket=bucket_name)
    for item in response.get("Contents", []):
        print(f'delete {item["Key"]}')
        client.delete_object(Bucket=bucket_name, Key=item["Key"])
    while response.get("NextContinuationToken", False):
        response = client.list_objects_v2(
            Bucket=bucket_name,
            ContinuationToken=response.get("NextContinuationToken"))
        for item in response.get("Contents", []):
            print(f'delete {item["Key"]}')
            client.delete_object(Bucket=bucket_name, Key=item["Key"])
