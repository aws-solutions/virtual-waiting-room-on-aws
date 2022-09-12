# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This module defines a custom client for testing
"""

# pylint: disable=no-name-in-module,useless-parent-delegation

import logging
import logging.handlers
import sys
import platform
from time import sleep

from locust import task
from base_test import BaseTest


class TestGetJWT(BaseTest):
    """
    Test case that demonstrates the waiting room's ability to serve a JWT when the queue position is served
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_start(self):
        """
        On start is performed by every client when it starts up        
        """
        logger = logging.getLogger()
        if "macOS" in platform.platform():
            print("in macOS")
            logger.addHandler(logging.StreamHandler(stream=sys.stdout))
        else:
            logger.addHandler(logging.handlers.SysLogHandler('/dev/log'))
        logger.setLevel(logging.INFO)

    @task(98)
    def waitingroom_flow(self):
        """
        overall goal is to get a token and we're done      
        finished is set when there is nothing left to do  
        """
        if not self.client.finished:
            if self.client.request_id is None:
                # ask for a position in line, get a request id back
                self.client.assign_queue_num()
            elif self.client.queue_num is None:
                # use the request id to get the numeric position in line
                self.client.get_queue_num()
            elif not self.client.queue_num is None and not self.client.served:
                # get the current serving position of the line (high traffic)
                self.client.get_serving_num()
            elif self.client.served:
                # when our position in line <= serving position, ask for a token to move on
                self.client.generate_token()
        # pause between actions
        sleep(1)

    @task(1)
    def check_waiting_num(self):
        """
        Get the number of users in the waiting room
        """
        if not self.client.queue_num is None and not self.client.served:
            self.client.get_waiting_num()
        sleep(1)

    @task(1)
    def regenerate_flow(self):
        """
        Request a token that was already requested
        """
        if self.client.served and self.client.finished and self.client.regen_counter > 0:
            self.client.regenerate_token()
            self.client.regen_counter -= 1
        sleep(1)
