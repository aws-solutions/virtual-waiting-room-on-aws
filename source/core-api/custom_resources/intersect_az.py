# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This custom resource is responsible for determining and returning the list
of AZs that are common to all the service endpoints used in this solution.
"""

import os
import json
import boto3
from crhelper import CfnResource
from botocore import config

helper = CfnResource()
SOLUTION_ID = os.environ['SOLUTION_ID']
user_agent_extra = {"user_agent_extra": SOLUTION_ID}
user_config = config.Config(**user_agent_extra)
client = boto3.client('ec2', config=user_config)

@helper.create
@helper.update
def create_update(event, _):
    """
    This function is responsible for generating a sorted, intersection list of
    AZ names supported by all the specified VPC endpoint services.
    """
    print(event)
    # these are the service names to process
    service_names = event["ResourceProperties"]["ServiceNames"]
    print(f"Service names: {json.dumps(service_names)}")
    # get the endpoint AZs for each service
    response = client.describe_vpc_endpoint_services(
        ServiceNames=service_names)
    print(response)
    # find the AZs common to all services
    intersect_az = set(response['ServiceDetails'][0]['AvailabilityZones'])
    for details in response['ServiceDetails'][1:]:
        intersect_az = intersect_az & set(details['AvailabilityZones'])
    # sort and return the intesecting AZ list
    sorted_az = sorted(intersect_az)
    print(f"Intersecting AZs: {json.dumps(sorted_az)}")
    helper.Data.update({"intersect_az": sorted_az})


def handler(event, context):
    """
    This function is the entry point for the Lambda-backed custom resource.
    """
    helper(event, context)
