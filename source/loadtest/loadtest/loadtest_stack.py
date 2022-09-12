# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This module is responsible for the defining the top-level stack contents
"""

import json

from aws_cdk import Stack, Duration, RemovalPolicy, CfnOutput
from aws_cdk import aws_iam, aws_lambda, aws_s3, aws_s3_deployment, aws_ec2
from constructs import Construct

SSH_PORT = 22
LOCUST_COORDINATOR_WEB_PORT = 8089
LOCUST_COORDINATOR_WORKERS_PORT = 5557


class LoadTestStack(Stack):
    """
    This class is defines the infrastructure required to run load tests
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        loadtest_bucket = aws_s3.Bucket(
            self,
            "loadtest",
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        aws_s3_deployment.BucketDeployment(
            self,
            "DeployLoadtest",
            sources=[aws_s3_deployment.Source.asset("locust/")],
            destination_bucket=loadtest_bucket)

        # grant ec2 access for creating, querying, and destroying instances
        lambda_role = aws_iam.Role(
            self,
            'ControllerLambdaRole',
            assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'))
        lambda_role.add_managed_policy(
            aws_iam.ManagedPolicy.from_managed_policy_arn(
                self, 'LambdaBasicExecutionRolePolicy',
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            ))
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(actions=["ec2:*"], resources=['*']))
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(actions=["ssm:*"], resources=['*']))
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=["iam:PassRole", "iam:ListInstanceProfiles"],
                resources=['*']))

        lambda_controller = aws_lambda.Function(
            self,
            'ControllerLambda',
            code=aws_lambda.Code.from_asset('./lambda'),
            handler='main.lambda_handler',
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            description='Creates and destroys load testing environments',
            timeout=Duration.seconds(120),
            role=lambda_role,
        )

        lambda_controller.add_environment("LOADTEST_BUCKET",
                                          loadtest_bucket.bucket_name)

        vpc = aws_ec2.Vpc(self,
                          "CoordinatorVpc",
                          nat_gateways=0,
                          cidr="10.201.0.0/16")

        coordinator_security_group = aws_ec2.SecurityGroup(
            self,
            "CoordinatorSecurityGroup",
            vpc=vpc,
            description="Coordinator security group")

        coordinator_security_group.add_ingress_rule(aws_ec2.Peer.any_ipv4(),
                                                    aws_ec2.Port.tcp(SSH_PORT))

        coordinator_security_group.add_ingress_rule(
            aws_ec2.Peer.any_ipv4(),
            aws_ec2.Port.tcp(LOCUST_COORDINATOR_WEB_PORT))

        coordinator_security_group.add_ingress_rule(
            aws_ec2.Peer.any_ipv4(),
            aws_ec2.Port.tcp(LOCUST_COORDINATOR_WORKERS_PORT))

        lambda_controller.add_environment(
            "SECURITY_GROUP", coordinator_security_group.security_group_id)

        subnet_ids = []
        for subnet in vpc.public_subnets:
            subnet_ids.append(subnet.subnet_id)

        lambda_controller.add_environment("PUBLIC_SUBNETS",
                                          json.dumps(subnet_ids))

        ec2_loadtest_role = aws_iam.Role(
            self,
            'LoadTestEC2Role',
            assumed_by=aws_iam.ServicePrincipal('ec2.amazonaws.com'))

        ec2_loadtest_role.add_to_policy(
            aws_iam.PolicyStatement(actions=["s3:List*", "s3:Get*"],
                                    resources=[
                                        f"{loadtest_bucket.bucket_arn}/*",
                                        f"{loadtest_bucket.bucket_arn}"
                                    ]))

        ec2_loadtest_role.add_to_policy(
            aws_iam.PolicyStatement(actions=["iam:PassRole"], resources=["*"]))

        ec2_loadtest_role.add_to_policy(
            aws_iam.PolicyStatement(actions=[
                "logs:CreateLogGroup", "logs:CreateLogStream",
                "logs:PutLogEvents", "logs:DescribeLogStreams"
            ],
                                    resources=["*"]))

        instance_profile = aws_iam.CfnInstanceProfile(
            self,
            "LoadTestEC2InstanceProfile",
            roles=[ec2_loadtest_role.role_name],
            instance_profile_name=f"{self.stack_name}-loadtesting")

        lambda_controller.add_environment(
            "EC2_INSTANCE_PROFILE_NAME",
            instance_profile.instance_profile_name)

        CfnOutput(
            self,
            "LoadTestBucket",
            value=
            f"https://s3.console.aws.amazon.com/s3/buckets/{loadtest_bucket.bucket_name}",
        )

        CfnOutput(
            self,
            "LambdaControllerArn",
            value=f"{lambda_controller.function_arn}",
        )
