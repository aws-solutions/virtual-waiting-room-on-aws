from locust import User

from custom_client import CustomClient


class CustomLocust(User):
    """
    Override the default locust client with our custom client.

    Inherit the CustomLocust class instead of the Locust User class when writing tests.
    """
    abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = CustomClient(self.environment)