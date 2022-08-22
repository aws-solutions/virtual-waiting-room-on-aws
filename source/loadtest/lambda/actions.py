from os import environ
from time import sleep

import boto3


# TODO: see if there is a way to programatically retrieve the AMIs
amazon2linux_ami = {
    'us-east-1': 'ami-0742b4e673072066f',
    'us-east-2': 'ami-05d72852800cbf29e',
    'us-west-1': 'ami-0577b787189839998',
    'us-west-2': 'ami-0518bb0e75d3619ca'
}

# To help identify resources belonging to the load test
tag_name_coordinator = "aws-waiting-room-load-coordinator"
tag_name_worker = "aws-waiting-room-load-worker"

# mapping the region to the environment variable name
sg_env_var = {
    'us-east-1': 'SG_US_EAST_1',
    'us-east-2': 'SG_US_EAST_2',
    'us-west-1': 'SG_US_WEST_1',
    'us-west-2': 'SG_US_WEST_2'
}


# TODO: need to update the script to work with the final location of where this will live (both coordiantor and worker)
# note: if the repository address changes these commands will need to be updated accordingly
cmd_coordinator = """
#!/bin/bash
yum update -y
yum install python3-devel git gcc awslogs -y
systemctl start awslogsd
su ec2-user -c 'pip3 install --user awscli'
cd /home/ec2-user/
su ec2-user -c 'git clone https://%s:%s@git-codecommit.us-west-2.amazonaws.com/v1/repos/aws-virtual-waiting-room-loadtest'
cd aws-virtual-waiting-room-loadtest
su ec2-user -c 'pip3 install -r requirements.txt --user'
su ec2-user -c '/home/ec2-user/.local/bin/locust -f %s --master &> ~/loadtest.log &'
"""

cmd_workers = """
#!/bin/bash
export MASTER_IP=%s
yum update -y
yum install python3-devel git gcc awslogs -y
sudo systemctl start awslogsd
su ec2-user -c 'pip3 install --user awscli'
cd /home/ec2-user/
sleep $(($RANDOM %% 10))
sleep $(($RANDOM %% 10))
sleep $(($RANDOM %% 10))
sleep $(($RANDOM %% 10))
su ec2-user -c 'git clone https://%s:%s@git-codecommit.us-west-2.amazonaws.com/v1/repos/aws-virtual-waiting-room-loadtest'
cd aws-virtual-waiting-room-loadtest
su ec2-user -c 'pip3 install -r requirements.txt --user'
su ec2-user -c '/home/ec2-user/.local/bin/locust -f %s --worker --master-host=$MASTER_IP &> ~/loadtest.log &'
"""

extra_worker = """
su ec2-user -c '/home/ec2-user/.local/bin/locust -f %s --worker --master-host=$MASTER_IP &> ~/loadtest.log &'
"""


def create_coordinator(params):
    region = params["coordinator_region"]
    ec2_client = boto3.client('ec2', region_name=region)
    
    create_response = ec2_client.run_instances(
        ImageId=amazon2linux_ami[region],
        InstanceType=params["coordinator_instance_type"],
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[
            {
                "ResourceType": "network-interface",
                "Tags": [
                    {
                        "Key": "Name",
                        "Value": tag_name_coordinator
                    },
                    {
                        "Key": "test_id",
                        "Value": params["test_id"]
                    }
                ]
            
            },
            {
                "ResourceType": "instance",
                "Tags": [
                    {
                        "Key": "Name",
                        "Value": tag_name_coordinator
                    },
                    {
                        "Key": "test_id",
                        "Value": params["test_id"]
                    }
                ]
            },
            {
                "ResourceType": "volume",
                "Tags": [
                    {
                        "Key": "Name",
                        "Value": tag_name_coordinator
                    },
                    {
                        "Key": "test_id",
                        "Value": params["test_id"]
                    }
                ]
            }
        ],
        NetworkInterfaces=[
            {
                "AssociatePublicIpAddress": True,
                "DeleteOnTermination": True,
                "DeviceIndex": 0,
                "Groups": [environ[sg_env_var[region]]]
            }
        ],
        IamInstanceProfile={
            "Name": environ.get("EC2_INSTANCE_PROFILE_NAME")
        },
        UserData=cmd_coordinator % (params["gituser"], params["gituserpass"], params["test"])
    )
    
    instance_ids = {
        params["coordinator_region"]: []
    }
    ips = []
    
    for instance in create_response["Instances"]:
        instance_ids[params["coordinator_region"]].append(instance["InstanceId"])
        
    while len(instance_ids[params["coordinator_region"]]) > 0 and len(instance_ids[params["coordinator_region"]]) != len(ips):
        sleep(1)
        describe_response = ec2_client.describe_instances(
            InstanceIds=instance_ids[params["coordinator_region"]],
        )
        
        if describe_response["Reservations"][0].get("Instances"):
            for instance in describe_response["Reservations"][0]["Instances"]:
                if instance.get("PublicIpAddress"):
                    ips.append(instance["PublicIpAddress"])
                    
    return {
        "coordinator_ip": ips[0],
        "instance_ids": instance_ids
    }


def create_workers(params):
    cmd = cmd_workers % (params["coordinator_ip"], params["gituser"], params["gituserpass"], params["test"])
    
    for i in range(1, params["worker_processes_per_instance"]):
        cmd += extra_worker % params["test"]

    instance_ids = {}

    for region in params["worker_regions"]:
        ec2_client = boto3.client("ec2", region_name=region)
        
        create_response = ec2_client.run_instances(
            ImageId=amazon2linux_ami[region],
            InstanceType=params["worker_instance_type"],
            MinCount=params["worker_instances_per_region"],
            MaxCount=params["worker_instances_per_region"],
            TagSpecifications=[
                {
                    "ResourceType": "network-interface",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": tag_name_worker
                        },
                        {
                            "Key": "test_id",
                            "Value": params["test_id"]
                        }
                    ]

                },
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": tag_name_worker
                        },
                        {
                            "Key": "test_id",
                            "Value": params["test_id"]
                        }
                    ]
                },
                {
                    "ResourceType": "volume",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": tag_name_worker
                        },
                        {
                            "Key": "test_id",
                            "Value": params["test_id"]
                        }
                    ]
                }
            ],
        IamInstanceProfile={
            "Name": environ.get("EC2_INSTANCE_PROFILE_NAME")
        },
            UserData=cmd
        )

        if not instance_ids.get(region):
            instance_ids[region] = []

        for instance in create_response["Instances"]:
            instance_ids[region].append(instance["InstanceId"])

        # sleep 30 seconds between region to address code commit 429 ratelimiting
        sleep(30)

    return instance_ids


def destroy(params):

    for region in params["instance_ids"]:
        ec2_client = boto3.client("ec2", region_name=region)

        destroy_response = ec2_client.terminate_instances(
            InstanceIds=params["instance_ids"][region]
        )
    
        print(destroy_response)
    
    return params["instance_ids"]


