# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This class defines the most common qualities of a test
"""

# pylint: disable=no-name-in-module,useless-parent-delegation

from locust import between, constant

from custom_locust import CustomLocust
from config.config import MAX_WAIT, WAIT_TYPE


class BaseTest(CustomLocust):
    """
    Define common client (simulated user behavior here)
    All test cases should be derived from here
    """
    abstract = True

    # configure client timing between requests
    if WAIT_TYPE == "constant":
        wait_time = constant(MAX_WAIT)
    else:
        wait_time = between(MAX_WAIT, MAX_WAIT)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_start(self):
        """
        on_start is performed at the beginning of the test
        """
