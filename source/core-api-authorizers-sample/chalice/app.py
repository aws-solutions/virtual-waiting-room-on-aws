# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
This module represents a client's API that uses the waiting room API Gateway authorizers
to perform store operations after the user has received a token to pass through
the waiting room.
"""

from chalice import Chalice, CustomAuthorizer, CORSConfig, Response

app = Chalice(app_name='core-api-authorizers-sample')

WAITING_ROOM_AUTH = CustomAuthorizer('WaitingRoomAuthorizer',
                                     header='Authorization',
                                     authorizer_uri='PLACEHOLDER')

CORS_CONFIG = CORSConfig(allow_origin='*',
                         allow_headers=['*'],
                         max_age=600,
                         expose_headers=['*'],
                         allow_credentials=True)

RESPONSE_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*'
}


@app.route('/checkout',
           methods=['GET'],
           authorizer=WAITING_ROOM_AUTH,
           cors=CORS_CONFIG)
def checkout():
    """
    This function represents a /checkout API endpoint.
    """
    return Response(status_code=200,
                    body={"result": "Success"},
                    headers=RESPONSE_HEADERS)


@app.route('/search',
           methods=['GET'],
           authorizer=WAITING_ROOM_AUTH,
           cors=CORS_CONFIG)
def search():
    """
    This function represents a /search API endpoint.
    """
    return Response(status_code=200,
                    body={"result": "Success"},
                    headers=RESPONSE_HEADERS)


@app.route('/layaway',
           methods=['GET'],
           authorizer=WAITING_ROOM_AUTH,
           cors=CORS_CONFIG)
def layaway():
    """
    This function represents a /layaway API endpoint.
    """
    return Response(status_code=200,
                    body={"result": "Success"},
                    headers=RESPONSE_HEADERS)
