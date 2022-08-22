
from locust import between, constant

from src.custom_locust import CustomLocust
from src.config.config import MIN_WAIT, MAX_WAIT, WAIT_TYPE

class BaseTest(CustomLocust):
    """
    Define common client (simulated user_ behavior here.

    All test cases should be derived from here.
    """
    abstract = True

    # configure client timing between requests
    if WAIT_TYPE == "constant":
        wait_time = constant(MAX_WAIT)
    else:
        wait_time = between(MAX_WAIT, MAX_WAIT)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # add any properties here


    # on_start is performed at the beginning of the test. good place to do things like signup
    def on_start(self):
        pass

