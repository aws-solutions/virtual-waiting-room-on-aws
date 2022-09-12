# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This module is responsible for interacting with the
Lambda Function controller to issues commands
"""

# pylint: disable=line-too-long,consider-using-dict-items


import json
import uuid

import boto3

from config import Regions, REGION_FILTER, BOTO3_CONFIG

REGIONS = Regions()


class LoadTestController:
    """
    This class is responsible for encapsulating the
    commands for Lambda function controller
    """

    def __init__(self, event_id, lamda_arn):
        self.event_id = event_id
        self.lamda_arn = lamda_arn
        self.lambda_client = boto3.client('lambda', config=BOTO3_CONFIG)
        self.test_id = None
        self.coordinator_ip = None
        self.instances = {}

    def start_test(self,
                   test='test_signup_spike_plus_channel',
                   coordinator_instance_type='t3.large',
                   coordinator_region='us-east-1',
                   worker_instance_type='t3.medium',
                   worker_processes_per_instance=2,
                   worker_instances_per_region=10,
                   worker_regions=None):
        """
        This function starts the load testing coordinator and workers
        """
        if not worker_regions:
            worker_regions = REGIONS.list(REGION_FILTER)

        self.test_id = str(uuid.uuid4())

        print("~" * 64)
        print(f"starting load test: {self.test_id}")
        print(f"running test: {test}")
        print("using worker regions:")
        print(*worker_regions)
        print(f"using worker type: {worker_instance_type}")
        print(f"workers instances per region: {worker_instances_per_region}")
        print(
            f"worker processes per instance: {worker_processes_per_instance}")
        print("~" * 64)

        self._create_coordinator(test, coordinator_instance_type,
                                 coordinator_region)
        self._create_workers(test, worker_instance_type,
                             worker_instances_per_region,
                             worker_processes_per_instance, worker_regions)

    def add_workers(self,
                    test,
                    worker_instance_type,
                    worker_instances_per_region,
                    worker_processes_per_instance,
                    worker_regions,
                    coordinator_ip=None):
        """
        This function is responsible for sending the command to
        add more workers to an existing test
        """
        if not self.coordinator_ip and not coordinator_ip:
            raise ValueError("a coordinator ip must be provided")

        if coordinator_ip:
            self.coordinator_ip = coordinator_ip

        self._create_workers(test, worker_instance_type,
                             worker_instances_per_region,
                             worker_processes_per_instance, worker_regions)

    def teardown_test(self):
        """
        This function is responsible for sending the 
        command to terminate EC2 instances
        """
        print(f"destroying resources for test: {self.test_id}")

        for region in self.instances:
            print("-" * 32)
            print(f"region: {region}")
            print("instances:")
            print(*self.instances[region])
            print("-" * 32)

        event = {
            "action": "destroy",
            "params": {
                'instance_ids': self.instances
            }
        }

        result = self.lambda_client.invoke(
            FunctionName=self.lamda_arn,
            InvocationType='RequestResponse',
            Payload=bytes(json.dumps(event).encode('utf-8')))

        result = json.loads(result["Payload"].read())
        # result_body = json.loads(result["body"])

    def _create_coordinator(self, test, coordinator_instance_type,
                            coordinator_region):
        event = {
            "action": "create_coordinator",
            "params": {
                "coordinator_instance_type": coordinator_instance_type,
                "coordinator_region": coordinator_region,
                "event_id": self.event_id,
                "test": f"{test}.py",
                "test_id": self.test_id,
            }
        }

        result = self.lambda_client.invoke(
            FunctionName=self.lamda_arn,
            InvocationType='RequestResponse',
            Payload=bytes(json.dumps(event).encode('utf-8')))

        result = json.loads(result["Payload"].read())
        result_body = json.loads(result["body"])

        self._update_instances(result_body["instance_ids"])
        self.coordinator_ip = result_body["coordinator_ip"]
        print("Locust UI can be reached at: ")
        print(f"http://{self.coordinator_ip}:8089")

    def _create_workers(self, test, worker_instance_type,
                        worker_instances_per_region,
                        worker_processes_per_instance, worker_regions):

        if not self.test_id:
            self.test_id = "added to a running test"

        event = {
            "action": "create_workers",
            "params": {
                "coordinator_ip": self.coordinator_ip,
                "event_id": self.event_id,
                "test": f"{test}.py",
                "test_id": self.test_id,
                "worker_instance_type": worker_instance_type,
                "worker_instances_per_region": worker_instances_per_region,
                "worker_processes_per_instance": worker_processes_per_instance,
                "worker_regions": worker_regions
            }
        }

        result = self.lambda_client.invoke(
            FunctionName=self.lamda_arn,
            InvocationType='RequestResponse',
            Payload=bytes(json.dumps(event).encode('utf-8')))

        result = json.loads(result["Payload"].read())
        result_body = json.loads(result["body"])

        self._update_instances(result_body)

    def _update_instances(self, instance_obj):
        for region in instance_obj:
            if not self.instances.get(region):
                self.instances[region] = []

            for instance_id in instance_obj[region]:
                self.instances[region].append(instance_id)
