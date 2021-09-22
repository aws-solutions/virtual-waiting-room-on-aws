# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json
import random
import time
import uuid
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt, jwk, jws

# generate a 2048-bit key pair
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# serialize the private key to a PEM string
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption())

# get the public key from the private key
public_key = private_key.public_key()

# serialize the public key to a PEM string
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo)

# print both PEM strings
print(f"{private_pem.decode('utf-8')}")
print()
print(f"{public_pem.decode('utf-8')}")

# create JWK format keys from PEM strings
jwk_private_key = jwk.construct(private_pem, "RS256").to_dict()
jwk_public_key = jwk.construct(public_pem, "RS256").to_dict()

# add a unique key-id (kid) to the JWKs
kid = 'C0A72061-1175-48BE-BC1B-E31AC1116641'
jwk_private_key['kid'] = kid
jwk_public_key['kid'] = kid

# print the JWKs
print(f"{json.dumps(jwk_private_key, indent=4)}")
print()
print(f"{json.dumps(jwk_public_key, indent=4)}")

# issuer (iss) can be URL of waiting room instance web endpoint
iss = 'https://dbp8x633tkgup.cloudfront.net'

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
# Bandit B311: not used for cryptographic purposes
waiting_room = {'position': random.randint(1, 25000)} # nosec

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

# sign them with the JWK private key
token = jws.sign(claims, jwk_private_key, algorithm="RS256")

# print the token
print(f"{token}")
