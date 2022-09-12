# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This lambda function is responsible for initiating load test
operations sent from the command line.
"""

import json

from actions import create_coordinator, create_workers, destroy

allowed_actions = ["create_coordinator", "create_workers", "destroy"]


def lambda_handler(event, _):
    """
    This function extracts the action name from the
    event and routes to a specific function handler
    """
    print(event)
    action = event.get("action", "")
    params = event.get("params", {})

    if action not in allowed_actions:
        raise ValueError(f"Invalid action: {action}")

    if action == "create_coordinator":
        response = create_coordinator(params)

    elif action == "create_workers":
        response = create_workers(params)

    elif action == "destroy":
        response = destroy(params)

    return {'statusCode': 200, 'body': json.dumps(response)}
