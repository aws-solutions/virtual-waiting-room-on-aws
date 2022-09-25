# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the unit test for the shared functions.
"""

import unittest
import validate
import jwt

class SharedResourcesTests(unittest.TestCase):
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
        print("----------------------------------------------------------------")


    def test_is_valid_rid(self):
        """
        Tests valid rid 
        """
        
        request_id = "26a07142-098a-4bea-b67d-1fe5a098bf29"
        self.assertTrue(validate.is_valid_rid(request_id))

        request_id = "1-26a07142-098a-4bea-b67d1fe5a098bf29"
        self.assertFalse(validate.is_valid_rid(request_id))

        request_id = ""
        self.assertFalse(validate.is_valid_rid(request_id))
        

    def test_jwt_payload(self):
        """
        Function to test JWT payload 
        """

        text = 'A.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.B'

        payload = jwt.claim_dict(text)
        expected = {'sub': '1234567890', 'name': 'John Doe', 'iat': 1516239022 }
        self.assertEqual(payload, expected)

        text = 'A.eyJzdWIiOiIyMTM0NTY3ODk0IiwibmFtZSI6Ik1hcnkgSmFuZSIsImlhdCI6MTUxNjIzOTAyNX0.B'
        payload = jwt.claim_dict(text)
        expected = {'sub': '2134567894', 'name': 'Mary Jane', 'iat': 1516239025 }
        self.assertEqual(payload, expected)

        text = 'A.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkhlbGxvIHdvcmxkIiwiaWF0IjoxNTE2MjM5MDIyfQ.B'
        payload = jwt.claim_dict(text)
        expected = {'sub': '1234567890', 'name': 'Mary Jane', 'iat': 1516239022 }
        self.assertNotEqual(payload, expected)


if __name__ == "__main":
    unittest.main()
