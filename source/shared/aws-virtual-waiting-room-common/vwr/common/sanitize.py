# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This module provides functions for sanitizing input from various sources.
"""

import bleach


def deep_clean(text):
    """
    Escape and clean all undesirable characters and tags in the input
    """
    return bleach.clean(text,
                        tags=[],
                        attributes={},
                        styles=[],
                        strip=True,
                        strip_comments=True)
