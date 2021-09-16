# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the custom resource used to update the CloudFront distribution used by the public API.
Initial creation of the distribution uses API ID for the API key header.
This update sets the header to use to actual API key of the API.
"""

import os
from crhelper import CfnResource
import boto3
from botocore import config

DISTRIBUTION_ID = os.environ.get("DISTRIBUTION_ID")
API_KEY_ID = os.environ.get("API_KEY_ID")
SOLUTION_ID = os.environ['SOLUTION_ID']
user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)

# connection info and other globals
helper = CfnResource()
cf_client = boto3.client('cloudfront', config=user_config)
api_client = boto3.client('apigateway', config=user_config)

@helper.create
@helper.update
def create_update(event, _):
    """
    This function is responsible for updating the CloudFront distribution's x-api-key header
    with actual API key value. The API key is regenerated during stack updates so this needs
    to run not only during create, but update as well.
    """
    print(event)
    response = cf_client.get_distribution_config(Id=DISTRIBUTION_ID)
    # get config and ETag
    distribution_config = response['DistributionConfig']
    etag = response["ETag"]
    api_key = api_client.get_api_key(
        apiKey=API_KEY_ID,
        includeValue=True
    )
    # update header with actual API key value
    distribution_config["Origins"]["Items"][0]["CustomHeaders"]["Items"][0]["HeaderValue"] = api_key["value"]
    # update distribution with new header value
    response = cf_client.update_distribution(
        Id=DISTRIBUTION_ID,
        DistributionConfig=distribution_config,
        IfMatch=etag
    )
    print(response)


@helper.delete
def delete(event, _):
    """
    Distribution is not deleted as it is created natively in the API core template.
    CloudFormation will handle its deletion.
    """
    print(event)
    print("Not deleting distribution. CloudFormation will handle this.")


def handler(event, context):
    """
    This function is the entry point for the Lambda-backed custom resource.
    """
    helper(event, context)
