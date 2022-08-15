from time import sleep

from locust import task

from src.base_test import BaseTest

import resource
#print(resource.getrlimit(resource.RLIMIT_NOFILE))
import logging
import logging.handlers
import sys
import platform

class TestGetJWT(BaseTest):
    """
    Test case that demonstrates the waiting room's ability to serve a JWT when the queue position is served
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # On start is performed by every client when it starts up
    def on_start(self):
        # self.client.get_public_key()
        # self.client.assign_queue_num()
        # while not self.client.queue_num:
        #     self.client.get_queue_num()
        logger = logging.getLogger()
        if "macOS" in platform.platform():
            print("in macOS")
            logger.addHandler(logging.StreamHandler(stream=sys.stdout))
        else:
            logger.addHandler(logging.handlers.SysLogHandler('/dev/log'))
        logger.setLevel(logging.INFO)
        # print(resource.getrlimit(resource.RLIMIT_NOFILE))

    @task(99)
    def waitingroom_flow(self):
        # overall goal is to get a token and we're done
        if self.client.finished == False:
            if self.client.request_id is None:
                # ask for a position in line, get a request id back
                self.client.assign_queue_num()
            elif self.client.queue_num is None:
                # use the request id to get the numeric position in line
                self.client.get_queue_num()
            elif not self.client.queue_num is None and self.client.served == False:
                # get the current serving position of the line (high traffic)
                self.client.get_serving_num()
            elif self.client.served == True:
                # when our position in line <= serving position, ask for a token to move on
                self.client.generate_token()
        # pause between actions
        sleep(0.5)

    @task(1)
    def check_waiting_num(self):
        if not self.client.queue_num is None and self.client.served == False:
            self.client.get_waiting_num()
        sleep(0.5)

    @task(1)
    def regenerate_flow(self):
        if self.client.served == True and self.client.finished == True and self.client.regen_counter > 0:
            self.client.regenerate_token()
            self.client.regen_counter -= 1
        sleep(0.5)