# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This module provides functions for working with JSON Web Tokens.
"""

import base64
import json


def claim_dict(encoded_token):
    """
    This function returns a dictionary of claims from a string JWT.
    Check the token's signature elsewhere.
    """
    # split the three components
    _, payload, _ = encoded_token.split('.')
    # decode the payload in the dictionary of claims
    if len(payload) % 4:
        # not a multiple of 4, add padding:
        payload += '=' * (4 - len(payload) % 4)
    claims = json.loads(base64.b64decode(payload).decode('utf-8'))
    return claims
