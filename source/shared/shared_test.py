# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the unit test for the shared functions.
"""

import os
import unittest
from unittest.mock import patch
from requests.models import Response
from custom_resources import cfn_bucket_loader

class SharedResourcesTests(unittest.TestCase):
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

    def cfn_bucket_loader_delete_test(self):
        pass


if __name__ == "__main":
    unittest.main()
