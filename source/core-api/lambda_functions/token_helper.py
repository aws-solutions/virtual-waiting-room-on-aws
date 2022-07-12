# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module contains helper methods for generating tokens.
"""

import json
from jwcrypto import jwk, jwt
from time import time
from boto3.dynamodb.conditions import Key, Attr

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

def is_queue_position_valid(EVENT_ID, queue_number, ddb_table, expiry_period) -> bool:
    '''
    Check if the queue_number's serving counter is still valid 
    '''
    counter_expiry_time = int(time()) + int(expiry_period)
    kce = Key('event_id').eq(EVENT_ID) & Key('serving_position').gte(queue_number) & Key('issue_time').lte(counter_expiry_time)
    response = ddb_table.query(
        KeyConditionExpression=kce,
        ScanIndexForward=False, # check 
        FilterExpression=Attr('marked_obsolete').ne(0),
        Limit=1
    )

    return bool(response['Items'])

def update_served_positions_count(EVENT_ID, queue_number, ddb_table) -> None:
    '''
    Update the served positions count when a token is successfully generated
    '''
    kce = Key('event_id').eq(EVENT_ID) & Key('serving_position').gte(queue_number)
    response = ddb_table.query(
        KeyConditionExpression=kce,
        ScanIndexForward=True,
        Limit=1 # check
    )

    item = response['Items'][0]
    ddb_table.update_item(
        Key={
            'event_id': item['event_id'],
            'serving_position': item['serving_position']
        },
        UpdateExpression='SET served_positions_count = :val',
        ExpressionAttributeValues={':val': item['served_positions_count'] + 1 }
    )