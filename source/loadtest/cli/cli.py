#!/usr/bin/env python3

import argparse
import json
import sys

import boto3


def load_configuration(filepath):
    # read the configuration file provided
    with open(filepath, "rt") as configuration_file:
        configuration = json.loads(configuration_file.read())
    # all regions involved
    configuration["regions"] = sorted(
        set(configuration['worker_regions'] +
            [configuration['coordinator_region']]))
    return configuration


def instance_filter(tag_name):
    return [
        {
            'Name': 'tag-key',
            'Values': [tag_name]
        },
        {
            'Name':
            'instance-state-name',
            'Values':
            ['pending', 'running', 'shutting-down', 'stopping', 'stopped']
        },
    ]


def inventory_ec2(region, configuration):
    instances = {}
    ec2_client = boto3.client("ec2", region_name=region)
    for instance_role, tag_name in [[
            "coordinators", configuration["tags"]["coordinator"]
    ], ["workers", configuration["tags"]["worker"]]]:
        instances[instance_role] = []
        # check for instances with our tags
        response = ec2_client.describe_instances(
            Filters=instance_filter(tag_name))
        reservations = response.get("Reservations", [])
        for item in reservations:
            instances[instance_role] = instances[instance_role] + item.get(
                'Instances', [])
        while "NextToken" in response:
            response = ec2_client.describe_instances(
                Filters=instance_filter(tag_name),
                NextToken=response["NextToken"])
            reservations = response.get("Reservations", [])
            for item in reservations:
                instances[instance_role] = instances[instance_role] + item.get(
                    'Instances', [])
    return instances


def security_group_filter(tag_key):
    return [
        {
            'Name': 'tag-key',
            'Values': [tag_key]
        },
    ]


def inventory_security_groups(region, configuration):
    security_groups = []
    ec2_client = boto3.client("ec2", region_name=region)
    # check for security groups with our tags
    response = ec2_client.describe_security_groups(
        Filters=security_group_filter(configuration["tags"]["security_group"]))
    security_groups = security_groups + response.get("SecurityGroups", [])
    while "NextToken" in response:
        response = ec2_client.describe_security_groups(
            Filters=security_group_filter(
                configuration["tags"]["security_group"]),
            NextToken=response["NextToken"])
        security_groups = security_groups + response.get("SecurityGroups", [])
    return security_groups


def inventory_loadtest(configuration):
    inventory = {}
    for region in configuration["regions"]:
        inventory[region] = {}
        inventory[region]["instances"] = inventory_ec2(region, configuration)
        # check for security groups with our tags
        inventory[region]["security_groups"] = inventory_security_groups(
            region, configuration)
    return inventory


def clean_loadtest(configuration):
    pass


def summarize_inventory(inventory):
    summary = {"coordinators": {}, "workers": {}, "security_groups": {}}
    for region_name in inventory:
        summary["coordinators"][region_name] = []
        summary["workers"][region_name] = []
        summary["security_groups"][region_name] = []
        for instance in inventory[region_name]["instances"]["coordinators"]:
            summary["coordinators"][region_name].append({
                'InstanceId':
                instance.get('InstanceId', ""),
                'PublicIpAddress':
                instance.get('PublicIpAddress', "")
            })
        for instance in inventory[region_name]["instances"]["workers"]:
            summary["workers"][region_name].append({
                'InstanceId':
                instance.get('InstanceId', ""),
                'PublicIpAddress':
                instance.get('PublicIpAddress', "")
            })
        for instance in inventory[region_name]["security_groups"]:
            summary["security_groups"][region_name].append({
                "GroupName":
                instance.get("GroupName", ""),
                "GroupId":
                instance.get("GroupId", "")
            })
    return summary


def assess_inventory(summary):
    assessment = {
        "workers_present": True,
        "security_groups_ready": True,
        "security_groups_need_clean": True,
        "coordinators_present": True
    }
    # check each region involved that it has the needed resources
    for region_name in summary["security_groups"]:
        if not region_name in assessment:
            assessment[region_name] = {}
        assessment[region_name]["security_groups"] = len(
            summary["security_groups"][region_name])
        assessment["security_groups_ready"] = assessment[
            "security_groups_ready"] and (
                assessment[region_name]["security_groups"] == 1)
        assessment["security_groups_need_clean"] = assessment[
            "security_groups_need_clean"] or (
                assessment[region_name]["security_groups"] > 1)
    for region_name in summary["workers"]:
        if not region_name in assessment:
            assessment[region_name] = {}
        assessment[region_name]["workers"] = len(
            summary["workers"][region_name])
        assessment["workers_present"] = assessment["workers_present"] or (
            assessment[region_name]["workers"] > 0)
    for region_name in summary["coordinators"]:
        if not region_name in assessment:
            assessment[region_name] = {}
        assessment[region_name]["coordinators"] = len(
            summary["coordinators"][region_name])
        assessment[
            "coordinators_present"] = assessment["coordinators_present"] or (
                assessment[region_name]["coordinators"] > 0)
    return assessment


def create_security_group(region_name, configuration):
    ec2_client = boto3.client("ec2", region_name=region_name)
    response = ec2_client.create_security_group(Description='string',
                                                GroupName='string',
                                                VpcId='string',
                                                TagSpecifications=[
                                                    {
                                                        'ResourceType':
                                                        'security-group',
                                                        'Tags': [
                                                            {
                                                                'Key':
                                                                configuration["tags"]["security_group"],
                                                                'Value':
                                                                'true'
                                                            },
                                                        ]
                                                    },
                                                ],
                                                DryRun=True | False)
    response = ec2_client.modify_security_group_rules(
    GroupId='string',
    SecurityGroupRules=[
        {
            'SecurityGroupRuleId': 'string',
            'SecurityGroupRule': {
                'IpProtocol': 'string',
                'FromPort': 123,
                'ToPort': 123,
                'CidrIpv4': 'string',
                'CidrIpv6': 'string',
                'PrefixListId': 'string',
                'ReferencedGroupId': 'string',
                'Description': 'string'
            }
        },
    ],
    DryRun=True|False
)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=
        """Control the Virtual Waiting Room on AWS Load Testing Tools""")
    parser.add_argument('--file',
                        required=True,
                        help='JSON configuration file')
    parser.add_argument('--action',
                        choices=["start", "stop", "clean", "show"],
                        help='Configure and launch instances')
    parser.add_argument('--print',
                        action='store_true',
                        help='Pretty-print JSON configuration')

    args = parser.parse_args()
    configuration = load_configuration(args.file)

    # print the configuration
    if args.print:
        print(json.dumps(configuration, indent=4))

    if args.action == "show":
        inventory = inventory_loadtest(configuration)
        summary = summarize_inventory(inventory)
        print(json.dumps(summary, indent=4, default=str))

    if args.action == "clean":
        print("clean")
        pass

    if args.action == "start":
        inventory = inventory_loadtest(configuration)
        summary = summarize_inventory(inventory)
        assessment = assess_inventory(summary)
        exit_error = False
        if assessment["workers_present"] or assessment["coordinators_present"]:
            print(
                "coordinator or worker instances are found, run '--action stop' or '--action clean' to terminate these"
            )
            exit_error = True
        if assessment["security_groups_need_clean"]:
            print(
                "more than one tagged security group found in specified regions, run '--action clean' to remove these"
            )
            exit_error = True
        if exit_error:
            sys.exit(1)

        # create missing security groups
        for region_name in configuration["regions"]:
            if len(inventory[region_name]["security_groups"]) == 0:
                # create a security group for this region
                pass

        # update inventory/summary/assessment

        # deploy the coordinator
        # wait/get the coordinator public IP address

        # launch the workers
        # print counts of launched instances (coordinator + workers)
        pass

    if args.action == "stop":
        print("stop")
        # enumerate ec2s for each region involved
        # check tags if this is a coordinator or worker
        # terminate it if so
        # print counts of terminated instances
        pass
