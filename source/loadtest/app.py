#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This module is responsible for synthesizing a new stack
"""

# pylint: disable=no-name-in-module

import aws_cdk

from loadtest.loadtest_stack import LoadTestStack

app = aws_cdk.App()
LoadTestStack(
    app,
    "LoadTestStack",
)
app.synth()
