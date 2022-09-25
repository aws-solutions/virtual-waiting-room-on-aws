# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the unit test for custom resources.
"""

import os
import unittest
import json
from unittest.mock import patch

os.environ['SOLUTION_ID'] = "SO0166"

import generate_client_secret
import generate_redirect_uris_secret


class CustomResourcesTest(unittest.TestCase):
    """
    This class is reponsible for tests against the waiting room core custom resources functions
    """

    def setUp(self):
        """
        This function is responsible for setting up the overall environment before each test
        """
        self.PLACEHOLDER_URIS = [
            "https://DNS/oauth2/idpresponse", "https://CNAME/oauth2/idpresponse"
        ]
        self.mock_event = {
            "ResourceProperties" : {
                "SecretPrefix": "somesecret_prefix"
            }
        }
        self.sercret_prefix = self.mock_event["ResourceProperties"]["SecretPrefix"]


    def tearDown(self):
        """
        This function is responsible for cleaning up the test environment
        """
        print("----------------------------------------------------------------")


    @patch('boto3.client')
    def test_generate_client_secret_create(self, mock_client):
        """
        Test generation of client secret create
        """
      
        generate_client_secret.create(self.mock_event, None)
        mock_client.assert_called_once()
        self.assertEquals(mock_client.call_args[0][0], 'secretsmanager')
        self.assertAlmostEqual(mock_client.mock_calls[3][0], "().create_secret")
        self.assertCountEqual(mock_client.mock_calls[3][2]["Name"], f'{self.sercret_prefix}/client_secret')


    @patch('boto3.client')
    def test_generate_client_secret_delete(self, mock_client):
        """
        Test generation of client secret delete
        """
        generate_client_secret.delete(self.mock_event, None)
        mock_client.assert_called_once()
        self.assertEquals(mock_client.call_args[0][0], 'secretsmanager')
        self.assertAlmostEqual(mock_client.mock_calls[1][0], "().delete_secret")
        self.assertCountEqual(mock_client.mock_calls[1][2]["SecretId"], f'{self.sercret_prefix}/client_secret')
        
    @patch('boto3.client')
    def test_generate_redirecturis_secret_create(self, mock_client):
        """
        Test for generate redirection uris create
        """
      
        generate_redirect_uris_secret.create(self.mock_event, None)
        mock_client.assert_called_once()
        self.assertEquals(mock_client.call_args[0][0], 'secretsmanager')
        self.assertAlmostEqual(mock_client.mock_calls[1][0], "().create_secret")
        self.assertCountEqual(mock_client.mock_calls[1][2]["Name"], f'{self.sercret_prefix}/redirect_uris')
        self.assertCountEqual(mock_client.mock_calls[1][2]["SecretString"], json.dumps(self.PLACEHOLDER_URIS, indent=4))


    @patch('boto3.client')
    def test_generate_redirecturis_delete(self, mock_client):
        """
        Test for generate redirection uris delete
        """
        generate_redirect_uris_secret.delete(self.mock_event, None)
        mock_client.assert_called_once()
        self.assertEquals(mock_client.call_args[0][0], 'secretsmanager')
        self.assertAlmostEqual(mock_client.mock_calls[1][0], "().delete_secret")
        self.assertCountEqual(mock_client.mock_calls[1][2]["SecretId"], f'{self.sercret_prefix}/redirect_uris')


if __name__ == "__main":
    unittest.main()
