# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the base method implementation for generate_token and auth_generate_token API handler.
It generates a token for a valid request that has been allowed to complete its transaction. 
"""

import json
from http import HTTPStatus
from typing import Tuple
from jwcrypto import jwk, jwt
from time import time
from boto3.dynamodb.conditions import Key
from counters import MAX_QUEUE_POSITION_EXPIRED, SERVING_COUNTER, TOKEN_COUNTER

def generate_token_base_method(
        event_id, request_id, headers, rc, enable_queue_position_expiry, queue_position_expiry_period, 
        secrets_client, secret_name_prefix, validity_period, issuer, events_client, event_bus_name, is_header_key_id,
        ddb_table_tokens, ddb_table_queue_position_entry_time, ddb_table_serving_counter_issued_at
    ):
    """
    This function is the base implementation of generate token methods.
    """

    queue_position_item = ddb_table_queue_position_entry_time.get_item(Key={"request_id": request_id})
    queue_number = int(queue_position_item['Item']['queue_position']) if 'Item' in queue_position_item else None

    if not queue_number:
        return {
            "statusCode": HTTPStatus.BAD_REQUEST.value,
            "headers": headers,
            "body": json.dumps({"error": "Invalid request ID"})
        }

    if queue_number > int(rc.get(SERVING_COUNTER)):
        return {
            "statusCode": HTTPStatus.ACCEPTED.value,
            "headers": headers,
            "body": json.dumps({"error": "Request ID not being served yet"})
        }

    item = ddb_table_tokens.get_item(Key={"request_id": request_id})
    is_requestid_in_token_table = 'Item' in item

    # check if queue position is valid and not expired only if token not issued
    if enable_queue_position_expiry == 'true' and not is_requestid_in_token_table:
        queue_position_entry_time = int(queue_position_item['Item']['entry_time'])
        (is_valid, serving_counter_item) = validate_queue_position_expiry(event_id, queue_number, queue_position_entry_time, 
                                        queue_position_expiry_period, rc, ddb_table_serving_counter_issued_at)
        if not is_valid:
            return { "statusCode": HTTPStatus.GONE.value, "headers": headers, "body": json.dumps({"error": "Queue position has expired"}) }

    keypair = create_jwk_keypair(secrets_client, secret_name_prefix)
    if is_requestid_in_token_table: 
        claims = create_claims_from_record(event_id, item)
        (access_token, refresh_token, id_token) = create_tokens(claims, keypair, is_header_key_id)
        expires = int(item['Item']['expires'])
        cur_time = int(time())

        # check for session status (non-zero) and reject the request  
        if int(item['Item']['session_status']) != 0:
            return {
                "statusCode": HTTPStatus.GONE.value,
                "headers": headers,
                "body": json.dumps({"error": "Token corresponding to request id has expired"})
            }

        return {
            "statusCode": HTTPStatus.OK.value, 
            "headers": headers, 
            "body": json.dumps(
                {
                    "access_token": access_token.serialize(),
                    "refresh_token": refresh_token.serialize(), 
                    "id_token": id_token.serialize(), 
                    "token_type": "Bearer", 
                    "expires_in": expires - cur_time
                }
            )
        }

    # request_id is not in ddb_table, create and save record to ddb_table
    iat = int(time())  # issued-at and not-before can be the same time (epoch seconds)
    nbf = iat
    exp = iat + validity_period # expiration (exp) is a time after iat and nbf, like 1 hour (epoch seconds)
    item = {
        "event_id": event_id,
        "request_id": request_id,
        "issued_at": iat,
        "not_before": nbf,
        "expires": exp,
        "queue_number": queue_number,
        'issuer': issuer,
        "session_status": 0
    }

    try:
        ddb_table_tokens.put_item(Item=item)
    except Exception as e:
        print(e)
        raise e

    claims = create_claims(event_id, request_id, issuer, queue_number, iat, nbf, exp)
    (access_token, refresh_token, id_token) = create_tokens(claims, keypair, True)
    write_to_eventbus(events_client, event_id, event_bus_name, request_id)
    rc.incr(TOKEN_COUNTER, 1)

    if enable_queue_position_expiry == 'true':
        update_queue_positions_served(event_id, serving_counter_item, ddb_table_serving_counter_issued_at) 

    return {
        "statusCode": HTTPStatus.OK.value, 
        "headers": headers, 
        "body": json.dumps(
            {
                "access_token": access_token.serialize(), 
                "refresh_token": refresh_token.serialize(), 
                "id_token": id_token.serialize(),
                "token_type": "Bearer",
                "expires_in": validity_period
            }
        )
    }
    
    
def create_jwk_keypair(secrets_client, secret_name_prefix) -> jwk.JWK:
    """
    Create JWK key object
    """
    response = secrets_client.get_secret_value(SecretId=f"{secret_name_prefix}/jwk-private")
    private_key = response.get("SecretString")
    # create JWK format keys
    return jwk.JWK.from_json(private_key)


def create_tokens(claims, keypair, is_header_key_id: bool) -> Tuple[jwt.JWT, jwt.JWT, jwt.JWT]:
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


def create_claims_from_record(event_id, item):
    """
    Parse DynamoDB table item and create claims
    """
    return create_claims(
        event_id,
        item['Item']['request_id'], 
        item['Item']['issuer'], 
        item['Item']['queue_number'], 
        int(item['Item']['issued_at']), 
        int(item['Item']['not_before']), 
        int(item['Item']['expires'])
    )


def create_claims(event_id, request_id, issuer, queue_number, iat, nbf, exp):
    """
    Create claims
    """
    return {
        'aud': event_id,
        'sub': request_id,
        'queue_position': queue_number,
        'token_use': 'access',
        'iat': iat,
        'nbf': nbf,
        'exp': exp,
        'iss': issuer
    }


def write_to_eventbus(events_client, event_id, event_bus_name, request_id) -> None:
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
                        "event_id": event_id,
                        "request_id": request_id
                    }
                ),
                'EventBusName': event_bus_name
            }
        ]
    )

def validate_queue_position_expiry(event_id, queue_number, queue_position_entry_time, queue_position_expiry_period, rc, ddb_table_serving_counter_issued_at) -> Tuple[bool, object]:
    """
    Validates the queue position to see if it has expired
    Returns: (is_valid, serving_counter)
    """
    current_time = int(time())
    if int(queue_number) <= int(rc.get(MAX_QUEUE_POSITION_EXPIRED)):
        return (False, None)

    # serving counter gte queue number, should always have atleast 1 result 
    response = ddb_table_serving_counter_issued_at.query(
        KeyConditionExpression=Key('event_id').eq(event_id) & Key('serving_counter').gte(int(queue_number)),
        Limit=1
    )
    serving_counter_item = response['Items'][0]
    serving_counter_issue_time = int(serving_counter_item['issue_time'])

    # time in queue greater than the expiry period 
    queue_time = max(queue_position_entry_time, serving_counter_issue_time)
    if current_time - queue_time > int(queue_position_expiry_period):
        return(False, None)

    return (True, serving_counter_item)


def update_queue_positions_served(event_id, serving_counter_item, ddb_table_serving_counter_issued_at) -> None:
    """
    Update the corresponding serving counter with queue positions served
    """
    ddb_table_serving_counter_issued_at.update_item(
        Key={
            'event_id': event_id,
            'serving_counter': int(serving_counter_item['serving_counter'])
        },
        UpdateExpression='SET queue_positions_served = :val',
        ExpressionAttributeValues={':val': serving_counter_item['queue_positions_served'] + 1}
    )
