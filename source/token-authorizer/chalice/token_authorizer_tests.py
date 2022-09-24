"""
This module is provides unit tests for the inlet strategies module.
"""

# pylint: disable=C0415,W0201

import json
import unittest
from unittest.mock import patch

PUBLIC_KEY = """
{"kty": "RSA", 
"alg": "RS256", 
"kid": "303694c8a3394c59aec8260e34787f9a", 
"n": "q_00x09ISc2elL-QKBCBOHSP0ZenaRwomIkuln0oWrQ6aHCzjKrkuW4v7isz_ifX6DT5ECzTSsTokb2BEkRDLKYmXfhLxFYgXusO2kPv17tbIMyoQPejFlJOIn5K4sPgP-AoE9GGR2boqtqMBEGPJdDYNvFNBgUBhdGwwus3DrcTtb9lsuFKcx5OdX99k8vEDwwHy2bZGBPyS6EXW1Xu1_-nrrMSn7LhbhyZWwGFWuvwG4D9iegZm51UdoT1xZqH8vVUAkt3ZvHztB4LMEK2U3DRvGE7I-6OWs1ohm6sYxnVeI4podcQ2YuD6YgNTbJqdrpCZVgOSnRvZNHhXFRgrw", 
"e": "AQAB"}
"""

TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjMwMzY5NGM4YTMzOTRjNTlhZWM4MjYwZTM0Nzg3ZjlhIiwidHlwIjoiSldUIn0.eyJhdWQiOiJTYW1wbGUiLCJleHAiOjE2NjM5Nzc5NjIsImlhdCI6MTY2Mzk3NzY2MiwiaXNzIjoiaHR0cHM6Ly9tYTgwY2VvZmFrLmV4ZWN1dGUtYXBpLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tL2FwaSIsIm5iZiI6MTY2Mzk3NzY2MiwicXVldWVfcG9zaXRpb24iOjI1ODIsInN1YiI6ImUzN2EyZTk2LWZlOTgtNGQ1Zi04NWM5LWIwNDczMzFmOWVmYiIsInRva2VuX3VzZSI6ImFjY2VzcyJ9.UkYE9edglO6kPN5_r3wy9OeP15w7iB3M7tDCDzPr3wxGehfBJaZv1J-K4-VnJ4q04BLXtExnOlFG2TVHak1zdOClt47ioUmBJ-eyva2YtWWTOhIgBR_pC2dDXR3MCJ1sHyD5_EpfzgBDjD_BwbyOesi_h72CSTTcusGv-wiIiJR85C3rLn3eVjoziFoWl0X2O0SSDkxkxWCNRX6tWf9z983OUX7OL02rh0q2M6iKtokIvzDcL4imgvrho9M9eIKV66kF3VN7GqE2sIifv5ClrOVvQA4x0OY1K6Z5TOVQ0936-81BYBABASrRqUlMPfSYcZDbj2uW5HI1TgcEfBwJug"


class TokenAuthorizerUnitTestException(Exception):
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
    if key == "WAITING_ROOM_EVENT_ID":
        result = "641EE9DD-57BE-437E-B157-BAD15F3D6408"
    elif key == "PUBLIC_API_ENDPOINT" or key == "ISSUER":
        result = "https://www.example.com"
    elif default_value is not None:
        result = default_value
    return result


def get_public_key():
    return json.loads(PUBLIC_KEY)


@patch('os.environ.get', new=environ_get_mock)
@patch('boto3.resource')
@patch('boto3.client')
@patch('requests.post')
@patch('requests.get')
class TestInletStrategies(unittest.TestCase):
    """
    This class extends TestCase with testing functions
    """

    def test_get_public_key(self, patched_resource, patched_client,
                            patched_post, patched_get):
        """
        Test the get_public_key function
        """
        import app
        app.get_public_key()

    @patch('app.get_public_key', new=get_public_key)
    def test_verify_token_sig(self, patched_resource, patched_client,
                              patched_post, patched_get):
        """
        Test the verify_token_sig function
        """
        import app
        app.verify_token_sig(TOKEN)

    @patch('app.get_public_key', new=get_public_key)
    def test_verify_token(self, patched_resource, patched_client, patched_post,
                          patched_get):
        """
        Test the verify_token function
        """
        import app
        app.verify_token(TOKEN)

    @patch('app.get_public_key', new=get_public_key)
    def test_check_authorizer_token(self, patched_resource, patched_client,
                                    patched_post, patched_get):
        """
        Test the check_authorizer_token function
        """
        import app
        app.check_authorizer_token(TOKEN, "/")

    @patch('app.get_public_key', new=get_public_key)
    def test_api_gateway_authorizer(self, patched_resource, patched_client,
                                    patched_post, patched_get):
        """
        Test the api_gateway_authorizer function
        """
        import app
        app.api_gateway_authorizer(
            {
                'authorizationToken':
                TOKEN,
                'methodArn':
                "arn:aws:execute-api:us-east-1:0123456789012:pvb6r6th3e/*/GET/expired_tokens"
            }, {})


if __name__ == '__main__':
    unittest.main()
