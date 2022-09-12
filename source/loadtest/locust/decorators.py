# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
Decorators:
    @require_authentication:
        - this means that the endpoint requires authentication to access.

    @stopwatch
        - measures the decorated function/method for load test results.
        - decorated function/method should return a (requests) response object
"""


# pylint: disable=inconsistent-return-statements

import functools
import time

from locust import events


def require_authentication(func):
    """ Simple decorator to check for the authentication """

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        if not (self.HEADERS.get("TODO") and self.HEADERS.get("MAYBETODO")
                and self.HEADERS.get("Authorization")):
            raise Exception("Not Authenticated")
        return func(self, *args, **kwargs)

    return wrap


def capture_stats(func):
    """
    Use this decorator on CustomClient methods.
    When decorated, the method's request statistics will be captured during load testing.
    """

    def wrapper(*args, **kwargs):
        start = time.time()
        result = None
        try:
            result = func(*args, **kwargs)
            # print(result)
            if result is None:
                raise Exception("No response")
            if result.status_code not in [200, 201, 202]:
                raise Exception(str(result.status_code), str(result.text))

            total = int((time.time() - start) * 1000)
            if func.__name__ != "wrapper":
                events.request_success.fire(
                    request_type="TYPE",
                    name=func.__name__,
                    response_time=total,
                    response_length=len(result.content),
                )

                return result

        except Exception as e:
            # print("failed: %s" % e)
            total = int((time.time() - start) * 1000)
            response_length = 0
            if result:
                response_length = len(result.content)
            events.request_failure.fire(
                request_type="TYPE",
                name=func.__name__,
                response_time=total,
                exception=e,
                response_length=response_length,
            )

    return wrapper
