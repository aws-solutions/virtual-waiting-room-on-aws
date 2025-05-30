# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is provides unit tests for the inlet strategies module.
"""

# pylint: disable=C0415,W0201,E1101

import json
import unittest
from unittest.mock import patch, MagicMock

TESTING_PUBLIC_KEY = """
{"kty": "RSA", 
"alg": "RS256", 
"kid": "303694c8a3394c59aec8260e34787f9a", 
"n": "q_00x09ISc2elL-QKBCBOHSP0ZenaRwomIkuln0oWrQ6aHCzjKrkuW4v7isz_ifX6DT5ECzTSsTokb2BEkRDLKYmXfhLxFYgXusO2kPv17tbIMyoQPejFlJOIn5K4sPgP-AoE9GGR2boqtqMBEGPJdDYNvFNBgUBhdGwwus3DrcTtb9lsuFKcx5OdX99k8vEDwwHy2bZGBPyS6EXW1Xu1_-nrrMSn7LhbhyZWwGFWuvwG4D9iegZm51UdoT1xZqH8vVUAkt3ZvHztB4LMEK2U3DRvGE7I-6OWs1ohm6sYxnVeI4podcQ2YuD6YgNTbJqdrpCZVgOSnRvZNHhXFRgrw", 
"e": "AQAB"}
"""

TESTING_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjMwMzY5NGM4YTMzOTRjNTlhZWM4MjYwZTM0Nzg3ZjlhIiwidHlwIjoiSldUIn0.eyJhdWQiOiJTYW1wbGUiLCJleHAiOjE2NjM5Nzc5NjIsImlhdCI6MTY2Mzk3NzY2MiwiaXNzIjoiaHR0cHM6Ly9tYTgwY2VvZmFrLmV4ZWN1dGUtYXBpLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tL2FwaSIsIm5iZiI6MTY2Mzk3NzY2MiwicXVldWVfcG9zaXRpb24iOjI1ODIsInN1YiI6ImUzN2EyZTk2LWZlOTgtNGQ1Zi04NWM5LWIwNDczMzFmOWVmYiIsInRva2VuX3VzZSI6ImFjY2VzcyJ9.UkYE9edglO6kPN5_r3wy9OeP15w7iB3M7tDCDzPr3wxGehfBJaZv1J-K4-VnJ4q04BLXtExnOlFG2TVHak1zdOClt47ioUmBJ-eyva2YtWWTOhIgBR_pC2dDXR3MCJ1sHyD5_EpfzgBDjD_BwbyOesi_h72CSTTcusGv-wiIiJR85C3rLn3eVjoziFoWl0X2O0SSDkxkxWCNRX6tWf9z983OUX7OL02rh0q2M6iKtokIvzDcL4imgvrho9M9eIKV66kF3VN7GqE2sIifv5ClrOVvQA4x0OY1K6Z5TOVQ0936-81BYBABASrRqUlMPfSYcZDbj2uW5HI1TgcEfBwJug"  #nosec B105


class OpenIDWaitingRoomTestException(Exception):
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
    elif key in ["PUBLIC_API_ENDPOINT", "ISSUER"]:
        result = "https://www.example.com"
    elif default_value is not None:
        result = default_value
    return result


def get_public_key():
    """
    This function for returning a mock public key used with JWT
    """
    return json.loads(TESTING_PUBLIC_KEY)


def chalice_mock(app_name=None):
    """
    This function handles the mock for the Chalice object
    """
    mock = MagicMock()
    mock.current_request = MagicMock()
    mock.current_request.query_params = MagicMock()
    mock.current_request.query_params.get = MagicMock()
    mock.current_request.query_params.get.return_value = ""
    return mock


@patch('os.environ.get', new=environ_get_mock)
@patch('boto3.resource')
@patch('boto3.client')
@patch('requests.post')
@patch('requests.get')
@patch('chalice.Chalice', new=chalice_mock)
class TestOpenIDWaitingRoom(unittest.TestCase):
    """
    This class extends TestCase with testing functions
    """

    def test_bad_request(self, patched_resource, patched_client, patched_post,
                         patched_get):
        """
        Test the bad_request function
        """
        import app
        app.bad_request()

    def test_extract_oidc_request(self, patched_resource, patched_client,
                                  patched_post, patched_get):
        """
        Test the extract_oidc_request function
        """
        import app
        app.extract_oidc_request()

    def test_authorize(self, patched_resource, patched_client, patched_post,
                       patched_get):
        """
        Test the authorize function
        """
        import app
        app.authorize()

    def test_token(self, patched_resource, patched_client, patched_post,
                   patched_get):
        """
        Test the token function
        """
        import app
        app.token()

    def test_userinfo(self, patched_resource, patched_client, patched_post,
                      patched_get):
        """
        Test the userinfo function
        """
        import app
        app.userinfo()

    def test_openid_configuration(self, patched_resource, patched_client,
                                  patched_post, patched_get):
        """
        Test the openid_configuration function
        """
        import app
        app.openid_configuration()

    def test_jwks_json(self, patched_resource, patched_client, patched_post,
                       patched_get):
        """
        Test the jwks_json function
        """
        import app
        app.jwks_json()


if __name__ == '__main__':
    unittest.main()
