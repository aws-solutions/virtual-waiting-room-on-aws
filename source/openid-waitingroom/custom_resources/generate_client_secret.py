# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is a Lambda function custom resource for CloudFormation. It is
responsible for creating and deleting the client secret for the Open ID
adapter for the waiting room.
"""

import os
import boto3
from crhelper import CfnResource
from botocore import config

helper = CfnResource()

PASSWORD_LENGTH = 50

SOLUTION_ID = os.environ['SOLUTION_ID']
user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)

@helper.create
def create(event, _):
    """
    This function is responsible for creating a new client secret
    """
    print(event)
    # create the secret value
    secrets_manager = boto3.client('secretsmanager', config=user_config)
    secret_value = secrets_manager.get_random_password( \
        PasswordLength=PASSWORD_LENGTH, ExcludePunctuation=True).get('RandomPassword')
    # store the value in a new secret named <stackname>/client_secret
    secret_id = f'{event["ResourceProperties"]["SecretPrefix"]}/client_secret'
    secrets_manager.create_secret(
        Name=secret_id,
        Description="Open ID client secret used for token requests",
        SecretString=secret_value
    )


@helper.delete
def delete(event, _):
    """
    This function is responsible for deleting the client secret
    """
    print(event)
    # delete the secret value
    secrets_manager = boto3.client('secretsmanager', config=user_config)
    secret_id = f'{event["ResourceProperties"]["SecretPrefix"]}/client_secret'
    secrets_manager.delete_secret(
        SecretId=secret_id,
        ForceDeleteWithoutRecovery=True                                  
    )


def handler(event, context):
    """
    This is the entry point for the custom resource Lambda function.
    """
    helper(event, context)
