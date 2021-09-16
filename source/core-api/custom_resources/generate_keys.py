# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the custom resource responsible for generating public and private keys
that will be used by the waiting room for a given event. 
"""

import os
import json
import uuid
import boto3
from jwcrypto import jwk
from crhelper import CfnResource
from botocore import config

helper = CfnResource()
boto_session = boto3.session.Session()
region = boto_session.region_name
SOLUTION_ID = os.environ['SOLUTION_ID']
user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)

secrets_client = boto3.client('secretsmanager', config=user_config)
SECRET_NAME_PREFIX = os.environ["STACK_NAME"]


@helper.create
def create(event, _):
    """
    This function is responsible for generating public and private keys.
    Keys generated are stored in Secrets Manager.
    """
    print(event)

    # key id
    kid = uuid.uuid4().hex

    # create JWK format keys
    keypair = jwk.JWK.generate(kid=kid, alg='RS256', kty='RSA', size=2048)

    # get the private and public JWK from the pair
    private_jwk = keypair.export_private(as_dict=True)
    print("Private key generated.")

    public_jwk = keypair.export_public(as_dict=True)
    print("Public key generated")
    print(f"{json.dumps(public_jwk, indent=4)}")

    # store pub/private keys in secrets manager
    try:
        response = secrets_client.create_secret(
            Name=f"{SECRET_NAME_PREFIX}/jwk-private",
            Description="Private JWK",
            SecretString=json.dumps(private_jwk))
        if response["ResponseMetadata"]["HTTPStatusCode"] ==  200:
            print("Private key saved in secrets manager.")
        response = secrets_client.create_secret(
            Name=f"{SECRET_NAME_PREFIX}/jwk-public",
            Description="Public JWK",
            SecretString=json.dumps(public_jwk))
        if response["ResponseMetadata"]["HTTPStatusCode"] ==  200:
            print("Public key saved in secrets manager.")
            
    except Exception as exception:
        print(exception)
        raise exception


@helper.update
def update(event, _):
    """
    Keys will not be regenerated on resource updates.
    """
    print(event)
    print("Not going to update keys on update.")


@helper.delete
def delete(event, _):
    """
    This function is responsible for deleting the public and private keys from Secrets Manager.
    """
    # remove saved keys
    print(event)
    response = secrets_client.delete_secret(
        SecretId=f"{SECRET_NAME_PREFIX}/jwk-private",
        ForceDeleteWithoutRecovery=True)
    print(response)
    response = secrets_client.delete_secret(
        SecretId=f"{SECRET_NAME_PREFIX}/jwk-public",
        ForceDeleteWithoutRecovery=True)
    print(response)


def handler(event, context):
    """
    This function is the entry point for the Lambda-backed custom resource.
    """
    helper(event, context)
