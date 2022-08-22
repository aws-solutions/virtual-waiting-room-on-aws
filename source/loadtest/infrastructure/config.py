# the load testing coordinator requires a security group with the following ingress rules:
#
# Type          Protocol        Port Range      Source                          Description
#
# Custom TCP    TCP             8089             <trusted IP address>/32         Allows access to Locust Web UI
# Custom TCP    TCP             5557            0.0.0.0/0                       Allows worker instance(s) to send results
#
loadtest_security_group = {
    'us-east-1': 'sg-xxxxxxxxxx',
    'us-east-2': 'sg-xxxxxxxxxx',
    'us-west-1': 'sg-xxxxxxxxxx',
    'us-west-2': 'sg-0fe88c6b4d1c99342',
}
