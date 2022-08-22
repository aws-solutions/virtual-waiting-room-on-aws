#!/usr/bin/env python3
from time import time

from aws_cdk import core
from aws_cdk import aws_lambda
from aws_cdk import aws_iam

from config import loadtest_security_group


class InfrastructureStack(core.Stack):
    """
    Defines the infrastructure required to run load tests
    """
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # grant ec2 access for creating, querying, and destroying instances
        lambda_role = aws_iam.Role(
            self,
            'ControllerLambdaRole',
            assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'),
            role_name='LoadTestControllerLambdaRole-%s' % str(time()).split('.')[0],
        )
        lambda_role.add_managed_policy(
            aws_iam.ManagedPolicy.from_managed_policy_arn(
                self,
                'LambdaBasicExecutionRolePolicy',
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
        )
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                # TODO tighten down actions to bare minimum needed
                actions=["ec2:*"],
                resources=['*']
            )
        )

        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=["iam:PassRole", "iam:ListInstanceProfiles"],
                resources=['*']
            )
        )

        lambda_controller = aws_lambda.Function(
            self,
            'ControllerLambda',
            code=aws_lambda.Code.asset('../lambda'),
            handler='main.lambda_handler',
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            description='creates and destroys load testing environments',
            function_name='loadtest_controller',
            timeout=core.Duration.seconds(60),
            role=lambda_role,
        )

        for k, v in loadtest_security_group.items():
            # skip default entries
            if v == 'sg-xxxxxxxxxx':
                continue
            # add environment variables for non default entries (eg: SG_US_WEST_2)
            lambda_controller.add_environment(
                "SG_" + k.upper().replace("-", "_"), loadtest_security_group[k]
            )

        ec2_loadtest_role = aws_iam.Role(
            self,
            'LoadTestEC2CodecommitRole',
            assumed_by=aws_iam.ServicePrincipal('ec2.amazonaws.com'),
            role_name='LoadTestEC2Role-%s' % str(time()).split('.')[0],
        )

        ec2_loadtest_role.add_to_policy(
            aws_iam.PolicyStatement(
                # TODO codecommit is a temporary solution until this lives in github
                actions=["codecommit:GitPull"],
                resources=['arn:aws:codecommit:us-west-2:727583892702:aws-virtual-waiting-room-loadtest']
            )
        )

        ec2_loadtest_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=["iam:PassRole"],
                resources=["*"]
            )
        )

        ec2_loadtest_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogStreams"
                ],
                resources=["*"]
            )
        )

        ec2_instance_role = aws_iam.CfnInstanceProfile(
            self,
            "LoadTestEC2InstanceProfile",
            instance_profile_name="LoadTestEC2InstanceProfile",
            roles=[ec2_loadtest_role.role_name]
        )

        lambda_controller.add_environment("EC2_INSTANCE_PROFILE_NAME", "LoadTestEC2InstanceProfile")


app = core.App()
InfrastructureStack(app, "loadtest-infrastructure")

app.synth()
