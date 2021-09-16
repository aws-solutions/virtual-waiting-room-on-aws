# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import random
import time
import uuid
import boto3
from jwcrypto import jwk, jwt, jws

secrets_client = boto3.client("secretsmanager")

response = secrets_client.get_secret_value(SecretId='swr/jwk-private')
print(response)
private_key = response.get("SecretString")
response = secrets_client.get_secret_value(SecretId='swr/jwk-public')
print(response)
public_key = response.get("SecretString")

# create JWK format keys
keypair = jwk.JWK.from_json(private_key)

# issuer (iss) can be URL of waiting room instance web endpoint
iss = 'https://ixulut9y89.execute-api.us-east-1.amazonaws.com/api/'

# audience (aud) is the unique event ID for the waiting room
aud = 'DBF95F82-4C93-4E4F-B27B-225529C6AFCD'

# subject (sub) is the unique device/client ID requesting a position
sub = '03C16C5A-8607-4489-B744-1525183A6738'

# issued-at and not-before can be the same time (epoch seconds)
iat = int(time.time())
nbf = iat

# expiration (exp) is a time after iat and nbf, like 1 hour (epoch seconds)
exp = iat + 3600

# waiting room specific claims
# generate a random position
waiting_room = {'position': random.randint(1, 25000)}

# create token claims
claims = {
    'aud': aud,
    'sub': sub,
    'waiting_room': waiting_room,
    'token_use': 'access',
    'iat': iat,
    'nbf': nbf,
    'exp': exp,
    'iss': iss
}

token = jwt.JWT(header={"alg": "RS256", "typ": "JWT"}, claims=claims)
token.make_signed_token(keypair)

# print the token
print(f"{token.serialize()}")
