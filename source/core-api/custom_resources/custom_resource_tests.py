# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the unit test for the core API Lambda functions.
"""

import os
import unittest
from unittest.mock import patch
from requests.models import Response

os.environ["SOLUTION_ID"] = "SO0166"
os.environ["STACK_NAME"] = "vwr"
os.environ["EVENT_ID"] = "abc123"
os.environ["API_STAGE"] = "dev"
os.environ["CORE_API_ENDPOINT"] = "http://localhost"
os.environ["PUBLIC_API_ID"] = "public_api"
os.environ["PRIVATE_API_ID"] = "private_api"
os.environ["DISTRIBUTION_ID"] = "distribution_id"
os.environ["API_KEY_ID"] = "api_key_id"

# these functions have to be imported after the environment variables have been set
import update_distribution
import intersect_az
import initialize_state
import generate_keys

class CoreCustomResourcesTestCase(unittest.TestCase):
    """
    This class is reponsible for tests against the waiting room core custom resources functions
    """

    def setUp(self):
        """
        This function is responsible for setting up the overall environment before each test
        """
        self.request_id = "5a571026-3bdd-4c36-aaed-323cb4c37262"
        self.invalid_id = "6b571026-4c36-3bdd-3bdd-323cb4c37263"
        self.event_id = os.environ["EVENT_ID"]
        self.invalid_event_id_msg = "Invalid event ID"
        self.invalid_request_id_msg = "Invalid request ID"

    def tearDown(self):
        """
        This function is responsible for cleaning up the test environment
        """
        print("----------------------------------------------------------------")

    
    """
    Start of test methods
    """
    @patch.object(generate_keys.secrets_client, 'create_secret',
                  return_value={
                    "Name": "vwr/jwk-secret",
                    "VersionId": "8834bb97-2e66-4b28-b239-a747318a133f",
                    "ResponseMetadata": {
                        "RequestId": "b8cb4a8b-b59e-4e5f-b28d-6c086b414438",
                        "HTTPStatusCode": 200}})
    @patch.object(generate_keys.secrets_client, 'delete_secret',
                  return_value={
                    "Name": "vwr/jwk-secret",
                    "VersionId": "8834bb97-2e66-4b28-b239-a747318a133f",
                    "ResponseMetadata": {
                        "RequestId": "b8cb4a8b-b59e-4e5f-b28d-6c086b414438",
                        "HTTPStatusCode": 200}})
    def test_generate_keys(self, mock_create_secret, mock_delete_secret):
        """
        This function tests the generate_keys custom resource function
        """ 
        # test create
        generate_keys.create(None, None)

        # test create with exception
        with patch.object(generate_keys.secrets_client, 'create_secret', side_effect=Exception):
            with self.assertRaises(Exception):
                generate_keys.create(None, None)

        # test delete
        generate_keys.delete(None, None)


    def test_initialize_state(self):
        """
        This function tests the initialize_state custom resource function
        """ 
        # test create        
        post_response = Response()
        post_response.status_code = 200
        with patch.object(initialize_state.requests, 'post', return_value=post_response):
            initialize_state.create(None, None)

        # test update
        with patch.object(initialize_state.api_client, 'create_deployment',
            return_value = {}):
            initialize_state.update(None, None)

    @patch.object(intersect_az.client, 'describe_vpc_endpoint_services', 
                  return_value={
                      "ServiceNames": [
                          "com.amazonaws.us-west-2.dynamodb",
                          "com.amazonaws.us-west-2.events"],
                      "ServiceDetails": [
                          {
                              "ServiceName": "com.amazonaws.us-west-2.dynamodb",
                              "AvailabilityZones": [
                                  "us-west-2a",
                                  "us-west-2b",
                                  "us-west-2c",
                                  "us-west-2d"
                              ]},
                          {
                              "ServiceName": "com.amazonaws.us-west-2.events",
                              "AvailabilityZones": [
                                  "us-west-2a",
                                  "us-west-2b",
                                  "us-west-2c"
                              ]}]
        })
    def test_intersect_az(self, mock_client):
        """
        This function tests the intersect_az custom resource function
        """ 
        mock_event = {
            "ResourceProperties":
            {
                "ServiceNames": ["com.amazonaws.us-west-2.dynamodb", 
                "com.amazonaws.us-west-2.events"]
            }}
        # test create
        intersect_az.create_update(mock_event, None)


    @patch.object(update_distribution.cf_client, 'get_distribution_config',
                  return_value={
                      "ETag": "ETKNX57U97DXK",
                      "DistributionConfig":
                      {"Origins":
                       {"Items": [
                           {"CustomHeaders": {
                               "Quantity": 1,
                               "Items": [
                                   {
                                       "HeaderName": "x-api-key",
                                       "HeaderValue": "zbZCFuCRh31oBZERgjsyB4mxEit0SdZz6q4TkqTP"
                                   }
                               ]
                           }}]}}})
    @patch.object(update_distribution.cf_client, 'update_distribution',
                  return_value={ "ETag": "ETKNX57U97DXK",
                            "Distribution": { "Id": "distribution_id"}
                  })
    @patch.object(update_distribution.api_client, 'get_api_key',
                  return_value={"value": "someapikeystring"
                    })
    def test_update_distribution(self, mock_get, mock_update, mock_get_api_key):
        """
        This function tests the update_distribution custom resource function
        """ 
        # test create/update
        update_distribution.create_update(None, None)     


if __name__ == '__main__':
    unittest.main()
