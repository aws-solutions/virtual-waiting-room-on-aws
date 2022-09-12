# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This module is responsible for containing several
constants common to other modules
"""

import re
import boto3
from botocore.config import Config

ACTIONS = ['start new test', 'add workers to existing test']

DEFAULT_INSTANCE_FILTER = """^t3\."""

DEFAULT_REGION_FILTER = """^(us\-|eu\-west|ca\-)"""

BOTO3_CONFIG = Config(retries={'max_attempts': 25})


class InstanceTypes():
    """
    This class is responsible for retrieving and
    filtering instance types for testing choices
    """

    def __init__(self) -> None:
        self.ec2_client = boto3.client("ec2", config=BOTO3_CONFIG)
        self.instance_types = []
        response = self.ec2_client.describe_instance_type_offerings(
            LocationType='region',
            Filters=[
                {
                    'Name': 'location',
                    'Values': [boto3.session.Session().region_name]
                },
            ],
        )
        for item in response['InstanceTypeOfferings']:
            self.instance_types.append(item['InstanceType'])
        while 'NextToken' in response:
            response = self.ec2_client.describe_instance_type_offerings(
                LocationType='region',
                Filters=[
                    {
                        'Name': 'location',
                        'Values': [boto3.session.Session().region_name]
                    },
                ],
                NextToken=response["NextToken"])
            for item in response['InstanceTypeOfferings']:
                self.instance_types.append(item['InstanceType'])
        self.instance_types = sorted(self.instance_types)

    def list(self, regexp_string=None):
        """
        API entry point to retrieve all regions based on EC2.
        """
        if regexp_string:
            results = []
            for name in self.instance_types:
                if re.search(regexp_string, name):
                    results.append(name)
            return results
        return self.instance_types


class Regions():
    """
    This class is responsible for retrieving and
    filtering region names for test choices
    """

    def __init__(self) -> None:
        self.names = sorted(
            boto3.session.Session().get_available_regions(service_name="ec2"))

    def list(self, regexp_string=None):
        """
        API entry point to retrieve all regions based on EC2.
        """
        if regexp_string:
            results = []
            for name in self.names:
                if re.search(regexp_string, name):
                    results.append(name)
            return results
        return self.names
