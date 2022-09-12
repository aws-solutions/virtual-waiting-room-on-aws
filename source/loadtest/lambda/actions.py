# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This module is responsible for the action to deploy,
start and stop the load testing operations.
"""


# pylint: disable=line-too-long

from distutils.command.config import config
import json
import random
from os import environ
from time import sleep

import boto3
from botocore.config import Config

BOTO3_CONFIG = Config(retries={'max_attempts': 25})

# To help identify resources belonging to the load test
TAG_NAME_COORDINATOR = "loadtest-coordinator"
TAG_NAME_WORKER = "loadtest-worker"

SSM_INSTANCE_PARAMETER = "/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2"

CMD_COORDINATOR = """
#!/bin/bash
cd /home/ec2-user/
mkdir loadtest
cd loadtest
aws s3 sync s3://%s .
pip3 install locust
locust -f %s --master &> ~/loadtest.log &
"""

CMD_WORKERS_INIT = """
#!/bin/bash
cd /home/ec2-user/
mkdir loadtest
cd loadtest
aws s3 sync s3://%s .
pip3 install locust
%s
"""

CMD_START_WORKER = """
locust -f %s --worker --master-host=%s &> ~/loadtest.log &
"""

COORDINATOR_SUBNETS = json.loads(environ["PUBLIC_SUBNETS"])


def create_coordinator(params):
    """
    This function is responsible for launching the coordinator
    EC2 that tracks the workers and provides the web UI
    """
    region = params["coordinator_region"]
    ec2_client = boto3.client('ec2', region_name=region, config=BOTO3_CONFIG)
    ssm_client = boto3.client('ssm', region_name=region, config=BOTO3_CONFIG)
    ssm_response = ssm_client.get_parameter(Name=SSM_INSTANCE_PARAMETER)
    ami_id = ssm_response["Parameter"]["Value"]
    create_response = ec2_client.run_instances(
        ImageId=ami_id,
        InstanceType=params["coordinator_instance_type"],
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[{
            "ResourceType":
            "network-interface",
            "Tags": [{
                "Key": "Name",
                "Value": TAG_NAME_COORDINATOR
            }, {
                "Key": "test_id",
                "Value": params["test_id"]
            }]
        }, {
            "ResourceType":
            "instance",
            "Tags": [{
                "Key": "Name",
                "Value": TAG_NAME_COORDINATOR
            }, {
                "Key": "test_id",
                "Value": params["test_id"]
            }]
        }, {
            "ResourceType":
            "volume",
            "Tags": [{
                "Key": "Name",
                "Value": TAG_NAME_COORDINATOR
            }, {
                "Key": "test_id",
                "Value": params["test_id"]
            }]
        }],
        NetworkInterfaces=[{
            "AssociatePublicIpAddress": True,
            "DeleteOnTermination": True,
            "DeviceIndex": 0,
            "Groups": [environ["SECURITY_GROUP"]],
            "SubnetId": random.choice(COORDINATOR_SUBNETS)
        }],
        IamInstanceProfile={"Name": environ.get("EC2_INSTANCE_PROFILE_NAME")},
        UserData=CMD_COORDINATOR %
        (environ["LOADTEST_BUCKET"], params["test"]))

    instance_ids = {params["coordinator_region"]: []}
    ips = []

    for instance in create_response["Instances"]:
        instance_ids[params["coordinator_region"]].append(
            instance["InstanceId"])

    while len(instance_ids[params["coordinator_region"]]) > 0 and len(
            instance_ids[params["coordinator_region"]]) != len(ips):
        sleep(1)
        describe_response = ec2_client.describe_instances(
            InstanceIds=instance_ids[params["coordinator_region"]], )

        if describe_response["Reservations"][0].get("Instances"):
            for instance in describe_response["Reservations"][0]["Instances"]:
                if instance.get("PublicIpAddress"):
                    ips.append(instance["PublicIpAddress"])

    return {"coordinator_ip": ips[0], "instance_ids": instance_ids}


def create_workers(params):
    """
    This function is responsible for creating the
    worker EC2s in each of the selected regions
    """
    cmd = CMD_WORKERS_INIT % (environ["LOADTEST_BUCKET"],
                              ((CMD_START_WORKER %
                                (params["test"], params["coordinator_ip"])) *
                               params["worker_processes_per_instance"]))

    instance_ids = {}

    for region in params["worker_regions"]:
        ec2_client = boto3.client("ec2",
                                  region_name=region,
                                  config=BOTO3_CONFIG)
        ssm_client = boto3.client('ssm',
                                  region_name=region,
                                  config=BOTO3_CONFIG)
        ssm_response = ssm_client.get_parameter(Name=SSM_INSTANCE_PARAMETER)
        ami_id = ssm_response["Parameter"]["Value"]
        create_response = ec2_client.run_instances(
            ImageId=ami_id,
            InstanceType=params["worker_instance_type"],
            MinCount=params["worker_instances_per_region"],
            MaxCount=params["worker_instances_per_region"],
            TagSpecifications=[{
                "ResourceType":
                "network-interface",
                "Tags": [{
                    "Key": "Name",
                    "Value": TAG_NAME_WORKER
                }, {
                    "Key": "test_id",
                    "Value": params["test_id"]
                }]
            }, {
                "ResourceType":
                "instance",
                "Tags": [{
                    "Key": "Name",
                    "Value": TAG_NAME_WORKER
                }, {
                    "Key": "test_id",
                    "Value": params["test_id"]
                }]
            }, {
                "ResourceType":
                "volume",
                "Tags": [{
                    "Key": "Name",
                    "Value": TAG_NAME_WORKER
                }, {
                    "Key": "test_id",
                    "Value": params["test_id"]
                }]
            }],
            IamInstanceProfile={
                "Name": environ.get("EC2_INSTANCE_PROFILE_NAME")
            },
            UserData=cmd)

        if not instance_ids.get(region):
            instance_ids[region] = []

        for instance in create_response["Instances"]:
            instance_ids[region].append(instance["InstanceId"])

    return instance_ids


def destroy(params):
    """
    This function is responsible for terminating all EC2 instances
    """
    for region in params["instance_ids"]:
        ec2_client = boto3.client("ec2",
                                  region_name=region,
                                  config=BOTO3_CONFIG)

        destroy_response = ec2_client.terminate_instances(
            InstanceIds=params["instance_ids"][region])

        print(destroy_response)

    return params["instance_ids"]
