import json
import uuid

import boto3


ALL_REGIONS = [
    'us-east-1',
    'us-east-2',
    'us-west-1',
    'us-west-2'
]

LAMBDA_FUNCTION_NAME = "loadtest_controller"


class LoadTestController:
    def __init__(self, git_user, git_pass):
        self.git_user = git_user
        self.git_pass = git_pass
        self.lambda_client = boto3.client('lambda')
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

        if not worker_regions:
            worker_regions = ALL_REGIONS

        self.test_id = str(uuid.uuid4())

        print("~"*64)
        print("starting load test: %s" % self.test_id)
        print("running test: %s" % test)
        print("using worker regions:")
        print(*worker_regions)
        print("using worker type: %s" % worker_instance_type)
        print("workers instances per region: %s" % worker_instances_per_region)
        print("worker processes per instance: %s" % worker_processes_per_instance)
        print("~"*64)

        self._create_coordinator(test, coordinator_instance_type, coordinator_region)
        self._create_workers(test, worker_instance_type, worker_instances_per_region, worker_processes_per_instance, worker_regions)

    def add_workers(self,
                    test,
                    worker_instance_type,
                    worker_instances_per_region,
                    worker_processes_per_instance,
                    worker_regions,
                    coordinator_ip=None):
        if not self.coordinator_ip and not coordinator_ip:
            raise ValueError("a coordinator ip must be provided")

        if coordinator_ip:
            self.coordinator_ip = coordinator_ip

        self._create_workers(
            test,
            worker_instance_type,
            worker_instances_per_region,
            worker_processes_per_instance,
            worker_regions
        )

    def teardown_test(self):
        print("destroying resources for test: %s" % self.test_id)

        for region in self.instances:
            print("-"*32)
            print("region: %s" % region)
            print("instances:")
            print(*self.instances[region])
            print("-"*32)

        event = {
            "action": "destroy",
            "params": {
                'instance_ids': self.instances
            }
        }

        result = self.lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType='RequestResponse',
            Payload=bytes(json.dumps(event).encode('utf-8'))
        )

        result = json.loads(result["Payload"].read())
        result_body = json.loads(result["body"])

    def _create_coordinator(self, test, coordinator_instance_type, coordinator_region):
        event = {
            "action": "create_coordinator",
            "params": {
                "coordinator_instance_type": coordinator_instance_type,
                "coordinator_region": coordinator_region,
                "gituser": self.git_user,
                "gituserpass": self.git_pass,
                "test": "test/%s.py" % test,
                "test_id": self.test_id,
            }
        }

        result = self.lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType='RequestResponse',
            Payload=bytes(json.dumps(event).encode('utf-8'))
        )

        result = json.loads(result["Payload"].read())
        result_body = json.loads(result["body"])

        self._update_instances(result_body["instance_ids"])
        self.coordinator_ip = result_body["coordinator_ip"]
        print("Locust UI can be reached at: ")
        print("http://%s:8089" % self.coordinator_ip)

    def _create_workers(self,
                        test,
                        worker_instance_type,
                        worker_instances_per_region,
                        worker_processes_per_instance,
                        worker_regions):

        if not self.test_id:
            self.test_id = "added to a running test"

        event = {
            "action": "create_workers",
            "params": {
                "coordinator_ip": self.coordinator_ip,
                "gituser": self.git_user,
                "gituserpass": self.git_pass,
                "test": "test/%s.py" % test,
                "test_id": self.test_id,
                "worker_instance_type": worker_instance_type,
                "worker_instances_per_region": worker_instances_per_region,
                "worker_processes_per_instance": worker_processes_per_instance,
                "worker_regions": worker_regions
            }
        }

        result = self.lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType='RequestResponse',
            Payload=bytes(json.dumps(event).encode('utf-8'))
        )

        result = json.loads(result["Payload"].read())
        result_body = json.loads(result["body"])

        self._update_instances(result_body)

    def _update_instances(self, instance_obj):
        for region in instance_obj:
            if not self.instances.get(region):
                self.instances[region] = []

            for instance_id in instance_obj[region]:
                self.instances[region].append(instance_id)
