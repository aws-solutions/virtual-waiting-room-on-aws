# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the base method implementation for generate_token and auth_generate_token API handler.
It generates a token for a valid request that has been allowed to complete its transaction. 
"""

import time
import json
from http import HTTPStatus
from counters import SERVING_COUNTER, TOKEN_COUNTER
import token_helper

def generate_token_base_method(
        EVENT_ID, request_id, headers, rc, ENABLE_QUEUE_POSITION_TIMEOUT, QUEUE_POSITION_TIMEOUT_PERIOD, 
        secrets_client, SECRET_NAME_PREFIX, VALIDITY_PERIOD, issuer, events_client, EVENT_BUS_NAME, is_header_key_id,
        ddb_table_tokens, ddb_table_queue_position_entry_time, ddb_table_serving_counter_issued_at
    ):
    """
    This function is the base implementation.
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
            "statusCode": HTTPStatus.NOT_FOUND.value,
            "headers": headers,
            "body": json.dumps({"error": "Request ID not being served yet"})
        }

    item = ddb_table_tokens.get_item(Key={"request_id": request_id})
    is_requestid_in_token_table = 'Item' in item

    # check if queue position is valid and not expired only is token not issued
    if ENABLE_QUEUE_POSITION_TIMEOUT == 'true' and not is_requestid_in_token_table:
        queue_position_entry_time = int(queue_position_item['Item']['entry_time'])
        (is_valid, serving_counter) = token_helper.validate_token_expiry(EVENT_ID, queue_number, queue_position_entry_time, 
                                        QUEUE_POSITION_TIMEOUT_PERIOD, rc, ddb_table_serving_counter_issued_at)
        if not is_valid:
            return {
                "statusCode": HTTPStatus.GONE.value,
                "headers": headers,
                "body": json.dumps({"error": "Queue position has expired"})
            }

    keypair = token_helper.create_jwk_keypair(secrets_client, SECRET_NAME_PREFIX)
    if is_requestid_in_token_table: 
        claims = token_helper.create_claims_from_record(EVENT_ID, item)
        (access_token, refresh_token, id_token) = token_helper.create_tokens(claims, keypair, is_header_key_id)
        expires = int(item['Item']['expires'])
        cur_time = int(time.time())

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
    iat = int(time.time())  # issued-at and not-before can be the same time (epoch seconds)
    nbf = iat
    exp = iat + VALIDITY_PERIOD # expiration (exp) is a time after iat and nbf, like 1 hour (epoch seconds)
    item = {
        "event_id": EVENT_ID,
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

    claims = token_helper.create_claims(EVENT_ID, request_id, issuer, queue_number, iat, nbf, exp)
    (access_token, refresh_token, id_token) = token_helper.create_tokens(claims, keypair, True)
    token_helper.write_to_eventbus(events_client, EVENT_ID, EVENT_BUS_NAME, request_id)
    rc.incr(TOKEN_COUNTER, 1)

    if ENABLE_QUEUE_POSITION_TIMEOUT == 'true':
        token_helper.update_queue_positions_served(EVENT_ID, serving_counter, ddb_table_serving_counter_issued_at) 

    return {
        "statusCode": HTTPStatus.OK.value, 
        "headers": headers, 
        "body": json.dumps(
            {
                "access_token": access_token.serialize(), 
                "refresh_token": refresh_token.serialize(), 
                "id_token": id_token.serialize(),
                "token_type": "Bearer",
                "expires_in": VALIDITY_PERIOD
            }
        )
    }
    