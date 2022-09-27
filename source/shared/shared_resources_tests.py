# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This module is the unit test for the shared functions.
"""

import os
import unittest
from unittest.mock import patch
from unittest.mock import MagicMock

os.environ["SOLUTION_ID"] = "SO12345"

from custom_resources import cfn_bucket_loader


class CustomResourcesSharedTest(unittest.TestCase):
    """
    This class is reponsible for tests against the waiting room core custom resources functions
    """

    def setUp(self):
        """
        This function is responsible for setting up the overall environment before each test
        """

    def tearDown(self):
        """
        This function is responsible for cleaning up the test environment
        """
        print(
            "----------------------------------------------------------------")

    @patch('boto3.client')
    def test_cfn_bucket_loader_update_web_content(self, mock_client):
        """
        Test for update web contents 
        """
        mock_event = {
            "ResourceProperties": {
                "BucketName": "bucket_123",
                "APIs": {
                    "url1": "http://url1/something",
                    "url2": "http://url2/something"
                }
            }
        }

        bkt_loader = cfn_bucket_loader
        bkt_loader.delete_bucket_contents = MagicMock()
        bkt_loader.put_web_contents = MagicMock()
        bkt_loader.put_api_endpoints_js = MagicMock()

        cfn_bucket_loader.update_web_content(mock_event, None)
        bkt_loader.delete_bucket_contents.assert_called_with("bucket_123")
        bkt_loader.put_web_contents.assert_called_with("bucket_123")
        bkt_loader.put_api_endpoints_js.assert_called_with(
            "bucket_123", {
                "url1": "http://url1/something",
                "url2": "http://url2/something"
            })

    @patch('boto3.client')
    def test_cfn_bucket_loader_delete_web_content(self, mock_client):
        """
        Test for delete bucket contents
        """
        mock_event = {
            "ResourceProperties": {
                "BucketName": "bucket_123",
            }
        }

        bkt_loader = cfn_bucket_loader
        bkt_loader.delete_bucket_contents = MagicMock()

        cfn_bucket_loader.delete_web_content(mock_event, None)
        bkt_loader.delete_bucket_contents.assert_called_with("bucket_123")


if __name__ == "__main":
    unittest.main()
