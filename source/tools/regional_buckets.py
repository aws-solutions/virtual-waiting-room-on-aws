# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This module creates S3 buckets with a region suffix.
"""

import time
import boto3

ROOT_BUCKET_NAME = "aws-virtual-waiting-room"


regions = ['ap-northeast-1', 'ap-south-1', 'ap-southeast-1', 'ca-central-1', \
    'eu-central-1', 'eu-north-1', 'eu-west-1', 'sa-east-1', \
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']
print(regions)

for region in regions:
    try:
        s3 = boto3.client('s3', region_name=region)
        name = f"{ROOT_BUCKET_NAME}-{region}"
        response = s3.create_bucket(
            Bucket=name,
            CreateBucketConfiguration={'LocationConstraint': region})
        print(response)
    except Exception as exception:
        print(exception)
    time.sleep(2)
