#!/usr/bin/env python3
import os

from PyInquirer import prompt

from controller import LoadTestController


ACTIONS = [
    'start new test',
    'add workers to existing test'
]

INSTANCE_TYPES = [
    'c5.xlarge',
    'c5.2xlarge',
    'c5.4xlarge'
]

REGIONS = [
    'us-east-1',
    'us-east-2',
    'us-west-1',
    'us-west-2'
]

startup_questions = [
    {
        'type': 'input',
        'name': 'gituser',
        'message': 'code commit git user:',
        'default': "gituser-at-727583892702"
    },
    {
        'type': 'password',
        'name': 'gituserpass',
        'message': 'code commit git user password: ',
        'default': "J3BcwnLlReGJt0CApVSFQ16SR6ZOp3rlKaCxrvwWjAs="
    },
    {
        'type': 'list',
        'name': 'action',
        'message': 'action to perform',
        'choices': ACTIONS,
        'default': ACTIONS[0]
    },
]

start_test_questions = [
    {
        'type': 'input',
        'name': 'test',
        'message': 'test to run (without .py)',
        'default': 'get_jwt_test'
    },
    {
        'type': 'list',
        'name': 'coordinator_instance_type',
        'message': 'load test coordinator instance type',
        'choices': INSTANCE_TYPES,
        'default': INSTANCE_TYPES[2]
    },
    {
        'type': 'list',
        'name': 'coordinator_region',
        'message': 'what region should the load test coordinator be deployed into?',
        'choices': REGIONS,
        'default': REGIONS[3]
    },
    {
        'type': 'list',
        'name': 'worker_instance_type',
        'message': 'load test worker instance type',
        'choices': INSTANCE_TYPES,
        'default': INSTANCE_TYPES[2]
    },
    {
        'type': 'checkbox',
        'name': 'worker_regions',
        'message': 'what regions should load test workers be deployed into?',
        'choices': [
            {
                "name": "us-east-1",
                "checked": True
            },
            {
                "name": "us-east-2",
                "checked": True
            },
            {
                "name": "us-west-1",
                "checked": True
            },
            {
                "name": "us-west-2",
                "checked": True
            },
        ]
    },
    {
        'type': 'input',
        'name': 'worker_instances_per_region',
        'message': 'how many worker instances should be deployed into the selected regions?',
        'default': '10',
    },
    {
        'type': 'list',
        'name': 'worker_processes_per_instance',
        'message': 'how many worker processes should be started on each worker instance?',
        'choices': [
            '4',
            '8',
            '16',
            '32'
        ],
        'default': '16',
    }

]

confirm_questions = [
    {
        'type': 'confirm',
        'name': 'confirm',
        'message': 'confirm choices',
        'default': False
    }
]


test_running_questions = [
    {
        'type': 'list',
        'name': 'action',
        'message': 'test is running. what action would you like to perform?',
        'choices': [
            'add workers',
            'terminate test'
        ]
    }
]

add_workers_questions = [
    {
        'type': 'input',
        'name': 'coordinator_ip',
        'message': 'coordinator ip address',
    },
    {
        'type': 'input',
        'name': 'test',
        'message': 'test to run (without .py)',
        'default': 'get_jwt_test'
    },
    {
        'type': 'list',
        'name': 'worker_instance_type',
        'message': 'load test worker instance type',
        'choices': INSTANCE_TYPES,
        'default': INSTANCE_TYPES[2]
    },
    {
        'type': 'checkbox',
        'name': 'worker_regions',
        'message': 'what regions should load test workers be deployed into?',
        'choices': [
            {
                "name": "us-east-1",
                "checked": True
            },
            {
                "name": "us-east-2"
            },
            {
                "name": "us-west-1"
            },
            {
                "name": "us-west-2"
            },
        ]
    },
    {
        'type': 'input',
        'name': 'worker_instances_per_region',
        'message': 'how many worker instances should be deployed into the selected regions?',
        'default': '10',
    },
    {
        'type': 'list',
        'name': 'worker_processes_per_instance',
        'message': 'how many worker processes should be started on each worker instance?',
        'choices': [
            '4',
            '8',
            '16'
        ],
        'default': '16',
    }
]

if __name__ == '__main__':
    print()
    print("~" * 64)
    print(" " * 16 + "Load Test Controller CLI")
    print("~" * 64)
    print()

    startup = prompt(startup_questions)
    ltc = LoadTestController(startup["gituser"], startup["gituserpass"])

    if startup["action"] == "start new test":
        print("starting new test...\n")
        start = None
        start_confirm = False
        while not start_confirm:
            start = prompt(start_test_questions)
            print("="*64)
            print('starting parameters:')
            print('test to run: tests/%s.py' % start["test"])
            print('coordinator instance type: %s' % start["coordinator_instance_type"])
            print('coordinator region: %s' % start["coordinator_region"])
            print('worker instance type: %s' % start["worker_instance_type"])
            print('worker processes per instance: %s' % start["worker_processes_per_instance"])
            print('worker regions: %s' % start["worker_regions"])
            print('worker instances per region: %s' % start["worker_instances_per_region"])
            print("="*64)
            start_confirm = prompt(confirm_questions)["confirm"]

        ltc.start_test(
            start["test"],
            start["coordinator_instance_type"],
            start["coordinator_region"],
            start["worker_instance_type"],
            int(start["worker_processes_per_instance"]),
            int(start["worker_instances_per_region"]),
            start["worker_regions"]
        )

        if os.uname().sysname == "Darwin":
            print("I see you're on a mac... let me get that for you.")
            print("will need to refresh the page when coordinator is ready")
            os.system('open http://%s:8089' % ltc.coordinator_ip)

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
                    workers_to_add["worker_regions"],
                    ltc.coordinator_ip
                )

    elif startup["action"] == "add workers to existing test":
        workers_to_add = prompt(add_workers_questions)
        ltc.add_workers(
            workers_to_add["test"],
            workers_to_add["worker_instance_type"],
            int(workers_to_add["worker_instances_per_region"]),
            int(workers_to_add["worker_processes_per_instance"]),
            workers_to_add["worker_regions"],
            workers_to_add["coordinator_ip"]
        )

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
                    workers_to_add["worker_regions"],
                    ltc.coordinator_ip
                )

    print("have an AWSome day.")
