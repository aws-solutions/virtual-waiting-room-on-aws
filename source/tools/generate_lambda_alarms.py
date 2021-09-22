# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This module creates CloudWatch alarms for various functions used by the solution.
"""

import copy
import json

TEMPLATE = {
    "APIHandlerErrorsAlarm": {
        "Type": "AWS::CloudWatch::Alarm",
        "Properties": {
            "AlarmDescription":
            "Errors > 0",
            "ComparisonOperator":
            "GreaterThanThreshold",
            "EvaluationPeriods":
            1,
            "DatapointsToAlarm":
            1,
            "MetricName":
            "Errors",
            "Namespace":
            "AWS/Lambda",
            "Dimensions": [{
                "Name": "FunctionName",
                "Value": {
                    "Ref": "APIHandler"
                }
            }],
            "Period":
            60,
            "Statistic":
            "Maximum",
            "Threshold":
            0,
            "TreatMissingData":
            "notBreaching"
        }
    },
    "APIHandlerThrottlesAlarm": {
        "Type": "AWS::CloudWatch::Alarm",
        "Properties": {
            "AlarmDescription":
            "Throttles > 0",
            "ComparisonOperator":
            "GreaterThanThreshold",
            "EvaluationPeriods":
            1,
            "DatapointsToAlarm":
            1,
            "MetricName":
            "Throttles",
            "Namespace":
            "AWS/Lambda",
            "Dimensions": [{
                "Name": "FunctionName",
                "Value": {
                    "Ref": "APIHandler"
                }
            }],
            "Period":
            60,
            "Statistic":
            "Maximum",
            "Threshold":
            0,
            "TreatMissingData":
            "notBreaching"
        }
    }
}

FUNCTION_NAMES = [
    "AssignQueueNum", "AuthGenerateToken", "GetNumActiveTokens",
    "GetExpiredTokens", "GetServingNum", "GetWaitingNum", "GenerateEvents",
    "GenerateToken", "GetQueueNum", "GetPublicKey", "IncrementServingCounter",
    "UpdateSession", "ResetState"
]

OUTPUT = {}
for name in FUNCTION_NAMES:
    errors_alarm_name = f"{name}ErrorsAlarm"
    throttles_alarm_name = f"{name}ThrottlesAlarm"
    OUTPUT[errors_alarm_name] = copy.deepcopy(
        TEMPLATE["APIHandlerErrorsAlarm"])
    OUTPUT[throttles_alarm_name] = copy.deepcopy(
        TEMPLATE["APIHandlerThrottlesAlarm"])
    OUTPUT[errors_alarm_name]["Properties"]["Dimensions"][0]["Value"][
        "Ref"] = name
    OUTPUT[throttles_alarm_name]["Properties"]["Dimensions"][0]["Value"][
        "Ref"] = name

print(json.dumps(OUTPUT, indent=4))
