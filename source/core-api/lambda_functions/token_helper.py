# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module contains helper methods for generating tokens.
"""

import json
from typing import Tuple
from jwcrypto import jwk, jwt
from time import time 
from boto3.dynamodb.conditions import Key
from counters import MAX_QUEUE_POSITION_EXPIRED

def create_jwk_keypair(secrets_client, SECRET_NAME_PREFIX) -> jwk.JWK:
    """
    Create JWK key object
    """
    response = secrets_client.get_secret_value(SecretId=f"{SECRET_NAME_PREFIX}/jwk-private")
    private_key = response.get("SecretString")
    # create JWK format keys
    return jwk.JWK.from_json(private_key)


def create_tokens(claims, keypair, is_header_key_id):
    """
    Create access, refresh and id tokens 
    """
    access_token = make_jwt_token(claims, keypair, "access", is_header_key_id)
    refresh_token = make_jwt_token(claims, keypair, "refresh", is_header_key_id)
    id_token = make_jwt_token(claims, keypair, "id", is_header_key_id)

    return (access_token, refresh_token, id_token)


def make_jwt_token(claims, keypair, token_use, is_header_key_id) -> jwt.JWT:
    """
    create signed jwt claims token
    """
    # Bandit B105: not a hardcoded password
    claims["token_use"] = token_use  # nosec
    if is_header_key_id:
        jwt_token = jwt.JWT(header={"alg": "RS256", "typ": "JWT", "kid": keypair.key_id}, claims=claims)
    else:
        jwt_token = jwt.JWT(header={"alg": "RS256", "typ": "JWT"}, claims=claims)

    jwt_token.make_signed_token(keypair)
    print(f"{token_use} token header: {jwt_token.serialize().split('.')[0]}")

    return jwt_token


def create_claims_from_record(EVENT_ID, item):
    """
    Parse DynamoDB table item and create claims
    """
    return create_claims(
        EVENT_ID,
        item['Item']['request_id'], 
        item['Item']['issuer'], 
        item['Item']['queue_number'], 
        int(item['Item']['issued_at']), 
        int(item['Item']['not_before']), 
        int(item['Item']['expires'])
    )


def create_claims(EVENT_ID, request_id, issuer, queue_number, iat, nbf, exp):
    """
    Create claims
    """
    return {
        'aud': EVENT_ID,
        'sub': request_id,
        'queue_position': queue_number,
        'token_use': 'access',
        'iat': iat,
        'nbf': nbf,
        'exp': exp,
        'iss': issuer
    }


def write_to_eventbus(events_client, EVENT_ID, EVENT_BUS_NAME, request_id) -> None:
    """
    write to event bus
    """
    events_client.put_events(
        Entries=[
            {
                'Source': 'custom.waitingroom',
                'DetailType': 'token_generated',
                'Detail': json.dumps(
                    {
                        "event_id": EVENT_ID,
                        "request_id": request_id
                    }
                ),
                'EventBusName': EVENT_BUS_NAME
            }
        ]
    )

def validate_token_expiry(event_id, queue_number, queue_position_expiry_period,rc, 
        ddb_table_queue_position_issued_at, ddb_table_serving_counter_issued_at) -> Tuple[bool, int]:
    """
    Validates the queue position to see if it has expired
    Returns: (is_valid, serving_counter)
    """
    current_time = int(time())
    if int(queue_number) <= int(rc.get(MAX_QUEUE_POSITION_EXPIRED)):
        return (False, None)

    response = ddb_table_queue_position_issued_at.query(
        KeyConditionExpression=Key('event_id').eq(event_id) & Key('queue_position').eq(int(queue_number)),
    )
    queue_position_item = response['Items'][0]
    queue_position_issue_time = int(queue_position_item['issue_time'])

    # serving counter gte queue number, should always have atleast 1 result 
    response = ddb_table_serving_counter_issued_at.query(
        KeyConditionExpression=Key('event_id').eq(event_id) & Key('serving_counter').gte(int(queue_number)),
        Limit=1
    )
    serving_counter_item = response['Items'][0]
    serving_counter_issue_time = int(serving_counter_item['issue_time'])

    # time in queue greater than the expiry period 
    queue_time = max(queue_position_issue_time, serving_counter_issue_time)
    if current_time - queue_time > int(queue_position_expiry_period):
        return(False, None)

    return (True, int(serving_counter_item['serving_counter']))


def update_queue_positions_served(event_id, serving_counter, ddb_table_serving_counter_issued_at) -> None:
    """
    Update the corresponding serving counter with queue positions served
    """
    response = ddb_table_serving_counter_issued_at.query(
        KeyConditionExpression=Key('event_id').eq(event_id) & Key('serving_counter').eq(serving_counter)
    )
    serving_counter_item = response['Items'][0]

    ddb_table_serving_counter_issued_at.update_item(
        Key={
            'event_id': serving_counter_item['event_id'],
            'serving_counter': serving_counter_item['serving_counter']
        },
        UpdateExpression='SET queue_positions_served = :val',
        ExpressionAttributeValues={':val': serving_counter_item['queue_positions_served'] + 1}
    )
