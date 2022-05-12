# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module contains helper methods for generating tokens.
"""

import json
from jwcrypto import jwk, jwt

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


def create_claims_from_record(EVENT_ID, record):
    """
    Parse DynamoDB table item and create claims
    """
    return create_claims(
        EVENT_ID,
        record['Item']['request_id'], 
        record['Item']['issuer'], 
        record['Item']['queue_number'], 
        int(record['Item']['issued_at']), 
        int(record['Item']['not_before']), 
        int(record['Item']['expires'])
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
