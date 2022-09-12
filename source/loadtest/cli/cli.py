#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This module is responsible for handling CLI commands from the user and
interacting with the Lambda Function controller deployed by the stack.
"""

import boto3

from PyInquirer import prompt
from controller import LoadTestController
from config import ACTIONS, InstanceTypes, Regions, INSTANCE_FILTER, REGION_FILTER, BOTO3_CONFIG

REGIONS = Regions()
INSTANCE_TYPES = InstanceTypes()

startup_questions = [
    {
        'type': 'input',
        'name': 'event_id',
        'message': 'Virtual Waiting Room event ID',
        'default': 'Sample'
    },
    {
        'type': 'input',
        'name': 'stack_name',
        'message': 'Load testing CDK stack name',
        'default': 'LoadTestStack'
    },
    {
        'type': 'input',
        'name': 'stack_region',
        'message': 'Load testing CDK stack region',
        'default': boto3.session.Session().region_name
    },
    {
        'type': 'list',
        'name': 'action',
        'message': 'action to perform',
        'choices': ACTIONS,
        'default': ACTIONS[0]
    },
]

worker_region_choices = []
for name in REGIONS.list(REGION_FILTER):
    worker_region_choices.append({"name": name, "checked": True})

start_test_questions = [{
    'type': 'input',
    'name': 'test',
    'message': 'test to run (without .py)',
    'default': 'get_jwt_test'
}, {
    'type': 'list',
    'name': 'coordinator_instance_type',
    'message': 'load test coordinator instance type',
    'choices': INSTANCE_TYPES.list(INSTANCE_FILTER),
}, {
    'type': 'list',
    'name': 'worker_instance_type',
    'message': 'load test worker instance type',
    'choices': INSTANCE_TYPES.list(INSTANCE_FILTER)
}, {
    'type': 'checkbox',
    'name': 'worker_regions',
    'message': 'what regions should load test workers be deployed into?',
    'choices': worker_region_choices
}, {
    'type': 'input',
    'name': 'worker_instances_per_region',
    'message':
    'how many worker instances should be deployed into the selected regions?',
    'default': '5',
}, {
    'type': 'list',
    'name': 'worker_processes_per_instance',
    'message':
    'how many worker processes should be started on each worker instance?',
    'choices': ['4', '8', '16', '32'],
    'default': '16',
}]

confirm_questions = [{
    'type': 'confirm',
    'name': 'confirm',
    'message': 'confirm choices',
    'default': False
}]

test_running_questions = [{
    'type': 'list',
    'name': 'action',
    'message': 'test is running. what action would you like to perform?',
    'choices': ['add workers', 'terminate test']
}]

add_workers_questions = [{
    'type': 'input',
    'name': 'coordinator_ip',
    'message': 'coordinator ip address',
}, {
    'type': 'input',
    'name': 'test',
    'message': 'test to run (without .py)',
    'default': 'get_jwt_test'
}, {
    'type': 'list',
    'name': 'worker_instance_type',
    'message': 'load test worker instance type',
    'choices': INSTANCE_TYPES
}, {
    'type': 'checkbox',
    'name': 'worker_regions',
    'message': 'what regions should load test workers be deployed into?',
    'choices': worker_region_choices
}, {
    'type': 'input',
    'name': 'worker_instances_per_region',
    'message':
    'how many worker instances should be deployed into the selected regions?',
    'default': '10',
}, {
    'type': 'list',
    'name': 'worker_processes_per_instance',
    'message':
    'how many worker processes should be started on each worker instance?',
    'choices': ['4', '8', '16'],
    'default': '16',
}]

if __name__ == '__main__':
    print()
    print("~" * 64)
    print(" " * 16 + "Load Test Controller CLI")
    print("~" * 64)
    print()

    startup = prompt(startup_questions)
    cloudformation = boto3.client("cloudformation",
                                  region_name=startup["stack_region"],
                                  config=BOTO3_CONFIG)
    response = cloudformation.describe_stacks(StackName=startup["stack_name"])
    stack = next((item for item in response["Stacks"]
                  if item['StackName'] == startup["stack_name"]), None)
    lambda_arn = next((item['OutputValue'] for item in stack["Outputs"]
                       if item['OutputKey'] == 'LambdaControllerArn'), None)
    ltc = LoadTestController(startup["event_id"], lambda_arn)

    if startup["action"] == "start new test":
        print("starting new test...\n")
        start = None
        start_confirm = False
        while not start_confirm:
            start = prompt(start_test_questions)
            print("=" * 64)
            print('starting parameters:')
            print(f'test to run: tests/{start["test"]}.py')
            print(
                f'coordinator instance type: {start["coordinator_instance_type"]}'
            )
            print(f'coordinator region: {startup["stack_region"]}')
            print(f'worker instance type: {start["worker_instance_type"]}')
            print(
                f'worker processes per instance: {start["worker_processes_per_instance"]}'
            )
            print(f'worker regions: {start["worker_regions"]}')
            print(
                f'worker instances per region: {start["worker_instances_per_region"]}'
            )
            print("=" * 64)
            start_confirm = prompt(confirm_questions)["confirm"]

        ltc.start_test(start["test"], start["coordinator_instance_type"],
                       startup["stack_region"], start["worker_instance_type"],
                       int(start["worker_processes_per_instance"]),
                       int(start["worker_instances_per_region"]),
                       start["worker_regions"])

        # if os.uname().sysname == "Darwin":
        #     print("I see you're on a mac... let me get that for you.")
        #     print("will need to refresh the page when coordinator is ready")
        #     os.system(f'open http://{ltc.coordinator_ip}:8089')

        test_running = True
        while test_running:
            running = prompt(test_running_questions)

            if running["action"] == "terminate test":
                ltc.teardown_test()
                test_running = False

            elif running["action"] == "add workers":
                workers_to_add = prompt(add_workers_questions[1:])
                ltc.add_workers(
                    workers_to_add["test"],
                    workers_to_add["worker_instance_type"],
                    int(workers_to_add["worker_instances_per_region"]),
                    int(workers_to_add["worker_processes_per_instance"]),
                    workers_to_add["worker_regions"], ltc.coordinator_ip)

    elif startup["action"] == "add workers to existing test":
        workers_to_add = prompt(add_workers_questions)
        ltc.add_workers(workers_to_add["test"],
                        workers_to_add["worker_instance_type"],
                        int(workers_to_add["worker_instances_per_region"]),
                        int(workers_to_add["worker_processes_per_instance"]),
                        workers_to_add["worker_regions"],
                        workers_to_add["coordinator_ip"])

        test_running = True
        while test_running:
            running = prompt(test_running_questions)

            if running["action"] == "terminate test":
                ltc.teardown_test()
                test_running = False

            elif running["action"] == "add workers":
                workers_to_add = prompt(add_workers_questions[1:])
                ltc.add_workers(
                    workers_to_add["test"],
                    workers_to_add["worker_instance_type"],
                    int(workers_to_add["worker_instances_per_region"]),
                    int(workers_to_add["worker_processes_per_instance"]),
                    workers_to_add["worker_regions"], ltc.coordinator_ip)

    print("Exiting")
