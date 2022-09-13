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
        secrets_client, secret_name_prefix, validity_period, issuer, events_client, event_bus_name, is_key_id_in_header,
        ddb_table_tokens, ddb_table_queue_position_entry_time, ddb_table_serving_counter_issued_at
    ): # NOSONAR
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

    token_item = ddb_table_tokens.get_item(Key={"request_id": request_id})
    is_requestid_in_token_table = 'Item' in token_item

    # check if queue position is valid and not expired only if token not issued
    if enable_queue_position_expiry == 'true' and not is_requestid_in_token_table:
        queue_position_entry_time = int(queue_position_item['Item']['entry_time'])
        max_queue_position_expired = int(rc.get(MAX_QUEUE_POSITION_EXPIRED))
        (is_valid, serving_counter) = validate_queue_position_expiry(event_id, queue_number, queue_position_entry_time, 
                                        queue_position_expiry_period, max_queue_position_expired, ddb_table_serving_counter_issued_at)
        if not is_valid:
            return { 
                "statusCode": HTTPStatus.GONE.value, 
                "headers": headers, 
                "body": json.dumps({"error": "Queue position has expired"}) 
            }

    # check for session status (non-zero) and reject the request
    if is_requestid_in_token_table and int(token_item['Item']['session_status']) != 0:
        return {
            "statusCode": HTTPStatus.GONE.value,
            "headers": headers,
            "body": json.dumps({"error": "Token corresponding to request id has expired"})
        }

    keypair = create_jwk_keypair(secrets_client, secret_name_prefix)

    # retrive (create) existing token information form in tokens_table 
    if is_requestid_in_token_table: 
        claims = create_claims_from_record(event_id, token_item)
        (access_token, refresh_token, id_token) = create_tokens(claims, keypair, is_key_id_in_header)
        expires = int(token_item['Item']['expires'])
        cur_time = int(time())

        return {
            "statusCode": HTTPStatus.OK.value, 
            "headers": headers, 
            "body": json.dumps(
                {
                    "access_token": access_token.serialize(),
                    "refresh_token": refresh_token.serialize(), 
                    "id_token": id_token.serialize(), 
                    "token_type": "Bearer", 
                    "expires_in": max(expires - cur_time, 0)
                }
            )
        }

    # if request_id is not in tokens_table, create and save record to tokens_table
    iat = int(time())  # issued-at and not-before can be the same time (epoch seconds)
    nbf = iat
    exp = iat + validity_period # expiration (exp) is a time after iat and nbf
    token_item = {
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
        ddb_table_tokens.put_item(Item=token_item)
    except Exception as e:
        print(e)
        raise e

    claims = create_claims(event_id, request_id, issuer, queue_number, iat, nbf, exp)
    (access_token, refresh_token, id_token) = create_tokens(claims, keypair, True)
    write_to_eventbus(events_client, event_id, event_bus_name, request_id)
    rc.incr(TOKEN_COUNTER, 1)

    if enable_queue_position_expiry == 'true':
        update_queue_positions_served(event_id, serving_counter, ddb_table_serving_counter_issued_at) 

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


def create_tokens(claims, keypair, is_key_id_in_header: bool) -> Tuple[jwt.JWT, jwt.JWT, jwt.JWT]:
    """
    Create access, refresh and id tokens 
    """
    access_token = make_jwt_token(claims, keypair, "access", is_key_id_in_header)
    refresh_token = make_jwt_token(claims, keypair, "refresh", is_key_id_in_header)
    id_token = make_jwt_token(claims, keypair, "id", is_key_id_in_header)

    return (access_token, refresh_token, id_token)


def make_jwt_token(claims, keypair, token_use, is_key_id_in_header) -> jwt.JWT:
    """
    create signed jwt claims token
    """
    # Bandit B105: not a hardcoded password
    claims["token_use"] = token_use  # nosec
    if is_key_id_in_header:
        jwt_token = jwt.JWT(header={"alg": "RS256", "typ": "JWT", "kid": keypair.key_id}, claims=claims)
    else:
        jwt_token = jwt.JWT(header={"alg": "RS256", "typ": "JWT"}, claims=claims)

    jwt_token.make_signed_token(keypair)
    print(f"{token_use} token header: {jwt_token.serialize().split('.')[0]}")

    return jwt_token


def create_claims_from_record(event_id, token_item):
    """
    Parse DynamoDB table item and create claims
    """
    return create_claims(
        event_id,
        token_item['Item']['request_id'], 
        token_item['Item']['issuer'], 
        int(token_item['Item']['queue_number']), 
        int(token_item['Item']['issued_at']), 
        int(token_item['Item']['not_before']), 
        int(token_item['Item']['expires'])
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


def validate_queue_position_expiry(event_id, queue_number, queue_position_entry_time, 
    queue_position_expiry_period, max_queue_position_expired, ddb_table_serving_counter_issued_at) -> Tuple[bool, int]:
    """
    Validates the queue position to see if it has expired. Serving counter corresponding to queue position.
    Returns: (is_valid, serving_counter).
    """
    current_time = int(time())
    if queue_number <= max_queue_position_expired:
        return (False, None)

    # serving counter gte queue number, should always have atleast 1 result 
    response = ddb_table_serving_counter_issued_at.query(
        KeyConditionExpression=Key('event_id').eq(event_id) & Key('serving_counter').gte(queue_number),
        Limit=1
    )
    serving_counter_item = response['Items'][0]
    serving_counter_issue_time = int(serving_counter_item['issue_time'])

    # queue time should not be greater than the expiry period 
    queue_time = max(queue_position_entry_time, serving_counter_issue_time)
    if current_time - queue_time > int(queue_position_expiry_period):
        return(False, None)

    return (True, int(serving_counter_item['serving_counter']))


def update_queue_positions_served(event_id, serving_counter, ddb_table_serving_counter_issued_at) -> None:
    """
    Update the corresponding serving counter with queue positions served
    """
    ddb_table_serving_counter_issued_at.update_item(
        Key={
            'event_id': event_id,
            'serving_counter': serving_counter
        },
        UpdateExpression='SET queue_positions_served = queue_positions_served + :val',
        ExpressionAttributeValues={':val': 1}
    )
