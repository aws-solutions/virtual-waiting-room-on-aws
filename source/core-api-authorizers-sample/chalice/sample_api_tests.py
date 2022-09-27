"""
This module is provides unit tests for the inlet strategies module.
"""

# pylint: disable=C0415,W0201,E1101

import unittest
from unittest.mock import patch, MagicMock


class SampleAPITestException(Exception):
    """
    This class is an exception subclass for unit testing errors
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


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


@patch('boto3.resource')
@patch('boto3.client')
@patch('requests.post')
@patch('requests.get')
@patch('chalice.Chalice', new=chalice_mock)
class TestSampleAPI(unittest.TestCase):
    """
    This class extends TestCase with testing functions
    """

    def test_checkout(self, patched_resource, patched_client, patched_post,
                      patched_get):
        """
        Test the checkout function
        """
        import app
        app.checkout()

    def test_search(self, patched_resource, patched_client, patched_post,
                    patched_get):
        """
        Test the search function
        """
        import app
        app.search()

    def test_layaway(self, patched_resource, patched_client, patched_post,
                     patched_get):
        """
        Test the layaway function
        """
        import app
        app.layaway()


if __name__ == '__main__':
    unittest.main()
