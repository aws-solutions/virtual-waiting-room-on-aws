#!/usr/bin/env python3

import aws_cdk

from loadtest.loadtest_stack import LoadTestStack

app = aws_cdk.App()
LoadTestStack(
    app,
    "LoadTestStack",
)
app.synth()
