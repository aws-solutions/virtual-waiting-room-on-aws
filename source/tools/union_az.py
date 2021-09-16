import json
import boto3

# REGION = 'us-west-2'
# REGION = 'us-east-1'
REGION = 'eu-west-1'

SERVICE_NAMES = [
    f'com.amazonaws.{REGION}.sqs', f'com.amazonaws.{REGION}.dynamodb',
    f'com.amazonaws.{REGION}.secretsmanager', f'com.amazonaws.{REGION}.events',
    f'com.amazonaws.{REGION}.lambda'
]

client = boto3.client('ec2', region_name=REGION)
response = client.describe_vpc_endpoint_services(ServiceNames=SERVICE_NAMES)
common_az = None
for details in response['ServiceDetails']:
    if common_az is None:
        common_az = set(details['AvailabilityZones'])
    else:
        common_az = common_az & set(details['AvailabilityZones'])
print(sorted(common_az))
