# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is a Lambda function custom resource for CloudFormation. It is
responsible for creating and deleting the allowed redirect URIs secret for
the Open ID adapter for the waiting room.
"""

import os
import json
import boto3
from crhelper import CfnResource
from botocore import config

helper = CfnResource()

PLACEHOLDER_URIS = [
    "https://DNS/oauth2/idpresponse", "https://CNAME/oauth2/idpresponse"
]

SOLUTION_ID = os.environ['SOLUTION_ID']
user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)

@helper.create
def create(event, _):
    """
    This function is responsible for creating a new redirect URIs secret
    """
    print(event)
    # create the secret value
    secrets_manager = boto3.client('secretsmanager', config=user_config)
    secret_value = json.dumps(PLACEHOLDER_URIS, indent=4)
    # store the value in a new secret
    secret_id = f'{event["ResourceProperties"]["SecretPrefix"]}/redirect_uris'
    secrets_manager.create_secret(
        Name=secret_id,
        Description="Open ID allowed redirect URIs after authentication",
        SecretString=secret_value)


@helper.delete
def delete(event, _):
    """
    This function is responsible for deleting the redirect URIs secret
    """
    print(event)
    secrets_manager = boto3.client('secretsmanager', config=user_config)
    # delete the secret value
    secret_id = f'{event["ResourceProperties"]["SecretPrefix"]}/redirect_uris'
    secrets_manager.delete_secret(SecretId=secret_id,
                                  ForceDeleteWithoutRecovery=True)


def handler(event, context):
    """
    This is the entry point for the custom resource Lambda function.
    """
    helper(event, context)
