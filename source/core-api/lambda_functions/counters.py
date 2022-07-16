# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module defines the various counters used by the core API.
"""

# counter for requests enqueued
QUEUE_COUNTER = "queue_counter"

# counter for number currently being served
SERVING_COUNTER = "serving_counter"

# counter for tokens generated
# Bandit B105: not a hardcoded password
TOKEN_COUNTER = "token_counter" # nosec

# counter for sessions completed (i.e. token was used to complete transaction)
COMPLETED_SESSION_COUNTER = "completed_counter"

# counter for sessions abandoned (i.e. token was never used to complete transaction)
ABANDONED_SESSION_COUNTER = "abandoned_counter"

# maximum expired queue position
MAX_QUEUE_POSITION_EXPIRED = "max_queue_position_expired"