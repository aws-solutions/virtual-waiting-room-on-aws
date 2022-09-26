"""
This module is provides unit tests for the inlet strategies module.
"""

# pylint: disable=C0415,W0201

import json
import time
import unittest
from unittest.mock import patch

SNS_EVENT = {
    "Records": [{
        "Sns": {
            "Message":
            json.dumps({
                "completed": ["FC4FBD08-D930-42CD-8F0E-D7333B5979A5"],
                "abandoned": ["5188734F-7FFC-4AA0-B485-24660723F8AC"],
                "exited": "10"
            }),
            "Subject":
            "TestInvoke"
        }
    }]
}


class InletStrategyUnitTestException(Exception):
    """
    This class is an exception subclass for unit testing errors
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


def environ_get_mock(key, default_value=None):
    """
    This function is the mocked (replaced) function for returning environment variables
    """
    result = ""
    if key == "EVENT_ID":
        result = "641EE9DD-57BE-437E-B157-BAD15F3D6408"
    elif key == "CORE_API_ENDPOINT":
        result = "https://www.example.com"
    elif key == "CORE_API_REGION":
        result = "us-east-1"
    elif key == "MAX_SIZE":
        result = "100"
    elif key == "INCREMENT_BY":
        result = "100"
    elif key == "START_TIME":
        result = str(int(time.time()))
    elif key == "END_TIME":
        result = str(int(time.time()))
    elif key == "CLOUDWATCH_ALARM":
        result = "NonExistantAlarmName"
    elif default_value is not None:
        result = default_value
    return result


@patch('os.environ.get', new=environ_get_mock)
@patch('boto3.resource')
@patch('boto3.client')
@patch('requests.post')
@patch('requests.get')
class TestInletStrategies(unittest.TestCase):
    """
    This class extends TestCase with testing functions
    """

    def test_max_size_inlet(self, patched_resource, patched_client,
                            patched_post, patched_get):
        """
        Test the max size inlet strategy
        """
        import max_size_inlet
        max_size_inlet.lambda_handler(SNS_EVENT, {})

    def test_periodic_inlet(self, patched_resource, patched_client,
                            patched_post, patched_get):
        """
        Test the periodic inlet strategy
        """
        import periodic_inlet
        periodic_inlet.lambda_handler({}, {})


if __name__ == '__main__':
    unittest.main()
