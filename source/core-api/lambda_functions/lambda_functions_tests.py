# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the unit test for the core API Lambda functions.
"""

import os
import unittest
from unittest.mock import patch
from unittest.mock import Mock

from botocore import response
from counters import *
import json
from botocore.response import StreamingBody
from botocore.exceptions import ClientError
from io import StringIO

os.environ["REDIS_HOST"] = "local"
os.environ["REDIS_PORT"] = "1234"
os.environ["EVENT_ID"] = "abc123"
os.environ["TOKEN_TABLE"] = "token_table"
os.environ["SOLUTION_ID"] = "SO0166"
os.environ["STACK_NAME"] = "vwr"
os.environ["EVENT_BUS_NAME"] = "vwr_event_bus"
os.environ["VALIDITY_PERIOD"] = "3600"
os.environ["ACTIVE_TOKENS_FN"] = "get_num_active_tokens"
os.environ["QUEUE_URL"] = "queue_url"

# patch the boto3 client calls before importing all the functions we need to test
patcher = patch('botocore.client.BaseClient._make_api_call')
patcher.start()
# these functions have to be imported after the environment variables have been set
import assign_queue_num
import generate_events
import auth_generate_token
import generate_token
import get_list_expired_tokens
import get_num_active_tokens
import update_session
import reset_initial_state
import get_public_key
import get_queue_num
import get_serving_num
import get_waiting_num
import increment_serving_counter
#patcher.stop()

class CoreApiTestCase(unittest.TestCase):
    """
    This class is reponsible for tests against the waiting room core API functions
    """

    def setUp(self):
        """
        This function is responsible for setting up the overall environment before each test
        """
        self.request_id = "5a571026-3bdd-4c36-aaed-323cb4c37262"
        self.invalid_id = "6b571026-4c36-3bdd-3bdd-323cb4c37263"
        self.event_id = os.environ["EVENT_ID"]
        self.invalid_event_id_msg = "Invalid event ID"
        self.invalid_event_req_id_msg = "Invalid event or request ID"
        self.invalid_request_id_msg = "Invalid request ID"
        self.validity_period = int(os.environ["VALIDITY_PERIOD"])

    def tearDown(self):
        """
        This function is responsible for cleaning up the test environment
        """
        print("----------------------------------------------------------------")

    
    """
    Start of test methods
    """
    @patch.object(assign_queue_num.rc, 'incr', return_value=10)
    @patch.object(assign_queue_num.rc, 'hsetnx', return_value=1)
    @patch.object(assign_queue_num.rc, 'hgetall', return_value={"queue_number": 1, "event_id": "abc123"})
    @patch.object(assign_queue_num.sqs_client, 'delete_message', return_value={})
    def test_assign_queue_num(self, mock_incr, mock_hsetnx, mock_hgetall, mock_delete_message):
        """
        This function tests the assign_queue_num lambda function
        """
        mock_event = {
            "Records": [{
                "messageId": "ef44b0dc-5184-4cd8-a140-fb9d8a11b8e5",
                "receiptHandle": "AQEBzHTDpcozyKFctjEWiT",
                "body": json.dumps({"event_id": self.event_id}),
                "messageAttributes": {
                    "apig_request_id": {
                        "stringValue": "5a571026-3bdd-4c36-aaed-323cb4c37262"
                    }
                }
            }]
        }
        
        # valid event_id
        mock_event["Records"][0]["body"] = json.dumps({"event_id": self.event_id})
        response = assign_queue_num.lambda_handler(mock_event, None)
        self.assertEqual(response, 10)

        # invalid event_id
        mock_event["Records"][0]["body"] = json.dumps({"event_id": self.invalid_id})
        response = assign_queue_num.lambda_handler(mock_event, None)
        self.assertEqual(response, 10)


    @patch.object(auth_generate_token.ddb_table, 'query',
                  return_value={"Items": [{"request_id": "fe7a5f04-6ff0-4bd6-9c31-52088cc4e73a", "expires": 1000,
                                           "access_token": "accesstoken", "refresh_token": "refreshtoken", "id_token": "idtoken"}]})
    @patch.object(auth_generate_token.ddb_table, 'put_item',
                  return_value={"Items": [{"request_id": "fe7a5f04-6ff0-4bd6-9c31-52088cc4e73a"}]})
    @patch.object(auth_generate_token.rc, 'hget', return_value=1)
    @patch.object(auth_generate_token.rc, 'get', return_value=2)
    @patch.object(auth_generate_token.rc, 'incr', return_value=1)
    @patch.object(auth_generate_token.secrets_client, 'get_secret_value',
                  return_value={"SecretString": json.dumps({
                      "kty": "RSA",
                      "alg": "RS256",
                      "kid": "3baff5c775df470bb97265d45f9020d0",
                      "n": "o6joiAn5iXShgsMDZa8U_6JSzT1pwMWRP3fT6LW5nswUSSUySGTM7f3iNp48D7lxE0AxLnUbPhs_lDrx59cMU5w5mhO6sLTD0gHiyUsxYjP6MIKx_sDAkh_PqQGRdNJ041yoSrATk5Lrqzv_rzHYBOw7juBbLyvZWhQry33FrAXjA73yUVJakks1hSzoCNzu3l7f9xbWJ0GLWj6S51B4i3R7ZylSQ8pY8rRC5ASo740-BD1C2v_psezf1_EDJ8pEYiZU2kc7X9uVbz5X-xEImS14TAmYDBUrrm5R9dmp5iz8KJ16sJ9GFFq5kq8NHnQwi2YeifGk2xi_E70woHtGzQ",
                      "e": "AQAB",
                      "d": "CwZy-88oN2FbDBMVJIGB-aK2z0rG2Ay3Nz5cUT4EzjTTXQYbeBMKVzIWTjWkuC529qQJbCbJegqd4t-BsmujUfKhUsbnecYDtx8XZxYgsovr297CHPZhQrbP54PKh8MxyqtQTw_DkdqA890r4WKLOfGsJXjpy6i5kL7xIFlNusPjLFlz9R3sUxBJT8Ps24Z6j9LMMsaGRzyhz8ewKEGauR1RjgnKjjp90Q0Ij5ptzQ_wngeCsMZ_wHl2zTlmSqpM8LpugNcmlaUDhbNjRQ49-VaJUEoVLf60Hg7dcicpm8IdhLm-g7RbGxXqiJDHOSF60QUrnZ2wXaLfBWXK6SR-5Q",
                      "p": "0VCZCPtImDsA2Ww9-Br7xWk1S-1HPJVFMoABeQka3AeVgvPgtt9kpw1PYSblan8yVIcBE1OGBVF4ulyelwZAO3YcXXRoNcy4Gn-AdO-P9Mx_YjMcNJR_wPSirVpaVNdQv7HjMepjjW2tvM0K1mFHUwtdFBeUCCERpDOIFvF1LdM",
                      "q": "yCmC8acbXFj-nFdAqKP8_UGX-pQ8M3lZAMAswM690T0vlm-5_VOFaNzSNFRJjIPaUmJhiy-A0dLJMXHNB2imwocRJJwbPh8FB2QBUvySljrvr8P1IZe2sXrxEk_3fT7jHsj98BcvyZ1loYj40y96rtoV4FzV_QT8zb3GkI4QtN8",
                      "dp": "ZxdBKFFLAd8dnfhX1RjFJAebPlgRG9-RAzxUfV5kojYCB0tCRA9mrXg6vmi_2WHoUgVkHDao7Xmg8nini06C2EZl1gl9QfIgQrzFcdKDnlgR7TWrEKKLAWf7r1Gu59ZcaO2eLnl4qrF4PmLmkYu760TPhRPPzukqnSrcPiCSTA0",
                      "dq": "M6Y6ir6zGbZBJPiCz8FZE8SsQdWkXyft5nqwUaRHaMmgEPKNjKfTogZxG12wiNixKlcGkpLUa9A3aFHUNRg1B7cwnkDF6ta4RnrwuIhCDw_wL2uiQmPSmaN-t1n5I9Fpa9UzaZOiGiVKR09_3Ya_4oSV5oouEZcK4NAaf8yY1QM",
                      "qi": "zjmvKSb74G0tzCdfKLkDSNBIT9dDhhrEnmSGblC2-0i5oCpp9rjjFKEv-vTsiARS0Qh9geD0u9fbw2HaBwUqsN-r2L_nDpc3U-3NoLTh20dIxYTbESdbxtqcWS9Sooi6Sjq2lT1lIOhBvh310lOvDMnwXWojUL1rNNApiSzKBV4"
                  })})
    @patch.object(auth_generate_token.events_client, 'put_events',
                  return_value={'ResponseMetadata': {'FailedEntryCount': 0, "Entries": [{"EventId": "11710aed-b79e-4468-a20b-bb3c0c3b4860"}]}})
    def test_auth_generate_token(self, mock_query, mock_put_item, mock_hget,
                                 mock_get, mock_incr, mock_get_secret, mock_put_events):
        """
        This function tests the auth_generate_function lambda function
        """
        # valid event_id
        mock_event = {
            "requestContext": {
                "domainName": "example.com",
                "stage": "dev"
            },
            "body": json.dumps({"event_id": self.event_id, "request_id": self.request_id})
        }
        response = auth_generate_token.lambda_handler(mock_event, None)
        self.assertEqual(response["statusCode"], 200)
        response_body = json.loads(response["body"])
        self.assertEqual(response_body["expires_in"], self.validity_period)

        # valid event_id with overriding issuer and validity_period
        new_validity_period = "2400"
        mock_event["body"]= json.dumps({"event_id": self.event_id, "request_id": self.request_id, 
                "validity_period": new_validity_period, "issuer": "example2.com"})
        
        response = auth_generate_token.lambda_handler(mock_event, None)
        self.assertEqual(response["statusCode"], 200)
        response_body = json.loads(response["body"])
        self.assertEqual(response_body["expires_in"], int(new_validity_period))

        # queue number is not being served yet
        # queue number = 3, serving number = 2
        with patch.object(auth_generate_token.rc, 'hget', return_value=3):
            response = auth_generate_token.lambda_handler(mock_event, None)
            self.assertEqual(response["statusCode"], 202)
            response_body = json.loads(response["body"])
            self.assertEqual(
                response_body["error"], "Request ID not being served yet")

        # request_id already exists in the database
        with patch.object(auth_generate_token.rc, 'hget', return_value=1):
            with patch.object(auth_generate_token.ddb_table, 'put_item',
                              side_effect=ClientError({"Error": {"Code": "400", "Message": "ConditionalCheckFailedException"}}, "UpdateItem")):
                with self.assertRaises(ClientError):
                    response = auth_generate_token.lambda_handler(
                        mock_event, None)
                    self.assertEqual(response["statusCode"], 200)

        # put_event raised an exception
        with patch.object(auth_generate_token.events_client, 'put_events', side_effect=Exception):
            with self.assertRaises(Exception):
                response = auth_generate_token.lambda_handler(
                    mock_event, None)

        # invalid request_id
        with patch.object(auth_generate_token.rc, 'hget', return_value=None):
            response = auth_generate_token.lambda_handler(mock_event, None)
            self.assertEqual(response["statusCode"], 404)
            response_body = json.loads(response["body"])
            self.assertEqual(
                response_body["error"], self.invalid_request_id_msg)

        # invalid event_id
        mock_event["body"]=json.dumps({"event_id": self.invalid_id, "request_id": self.request_id})
        response = auth_generate_token.lambda_handler(mock_event, None)
        self.assertEqual(response["statusCode"], 400)
        response_body = json.loads(response["body"])
        self.assertEqual(response_body["error"], self.invalid_event_req_id_msg)


    @patch.object(generate_events.rc, 'get', return_value=1)
    @patch.object(generate_events.events_client, 'put_events',
                  return_value={'ResponseMetadata': {'FailedEntryCount': 0, "Entries": [{"EventId": "11710aed-b79e-4468-a20b-bb3c0c3b4860"}]}})
    def test_generate_events(self, mock_get, mock_put_events):
        """
        This function tests the generate_events lambda function
        """
        response_body = json.dumps({"body": json.dumps({"active_tokens": 0})})
        invoke_response = {"Payload": StreamingBody(StringIO(str(response_body)),
                                                    len(str(response_body)))}

        # both lambda invoke and put_events are succesful
        with patch.object(generate_events.lambda_client, 'invoke', return_value=invoke_response):
            # valid event_id
            response = generate_events.lambda_handler(None, None)
            self.assertEqual(
                response['ResponseMetadata']['FailedEntryCount'], 0)

        # put_events throws an exception
        with patch.object(generate_events.events_client, 'put_events', side_effect=Exception):
            with self.assertRaises(Exception):
                response = generate_events.lambda_handler(None, None)

    @patch.object(generate_token.ddb_table, 'query',
                  return_value={"Items": [{"request_id": "fe7a5f04-6ff0-4bd6-9c31-52088cc4e73a", "expires": 1000,
                                           "access_token": "accesstoken", "refresh_token": "refreshtoken", "id_token": "idtoken"}]})
    @patch.object(generate_token.ddb_table, 'put_item',
                  return_value={"Items": [{"request_id": "fe7a5f04-6ff0-4bd6-9c31-52088cc4e73a"}]})
    @patch.object(generate_token.rc, 'hget', return_value=1)
    @patch.object(generate_token.rc, 'get', return_value=2)
    @patch.object(generate_token.rc, 'incr', return_value=1)
    @patch.object(generate_token.secrets_client, 'get_secret_value',
                  return_value={"SecretString": json.dumps({
                      "kty": "RSA",
                      "alg": "RS256",
                      "kid": "3baff5c775df470bb97265d45f9020d0",
                      "n": "o6joiAn5iXShgsMDZa8U_6JSzT1pwMWRP3fT6LW5nswUSSUySGTM7f3iNp48D7lxE0AxLnUbPhs_lDrx59cMU5w5mhO6sLTD0gHiyUsxYjP6MIKx_sDAkh_PqQGRdNJ041yoSrATk5Lrqzv_rzHYBOw7juBbLyvZWhQry33FrAXjA73yUVJakks1hSzoCNzu3l7f9xbWJ0GLWj6S51B4i3R7ZylSQ8pY8rRC5ASo740-BD1C2v_psezf1_EDJ8pEYiZU2kc7X9uVbz5X-xEImS14TAmYDBUrrm5R9dmp5iz8KJ16sJ9GFFq5kq8NHnQwi2YeifGk2xi_E70woHtGzQ",
                      "e": "AQAB",
                      "d": "CwZy-88oN2FbDBMVJIGB-aK2z0rG2Ay3Nz5cUT4EzjTTXQYbeBMKVzIWTjWkuC529qQJbCbJegqd4t-BsmujUfKhUsbnecYDtx8XZxYgsovr297CHPZhQrbP54PKh8MxyqtQTw_DkdqA890r4WKLOfGsJXjpy6i5kL7xIFlNusPjLFlz9R3sUxBJT8Ps24Z6j9LMMsaGRzyhz8ewKEGauR1RjgnKjjp90Q0Ij5ptzQ_wngeCsMZ_wHl2zTlmSqpM8LpugNcmlaUDhbNjRQ49-VaJUEoVLf60Hg7dcicpm8IdhLm-g7RbGxXqiJDHOSF60QUrnZ2wXaLfBWXK6SR-5Q",
                      "p": "0VCZCPtImDsA2Ww9-Br7xWk1S-1HPJVFMoABeQka3AeVgvPgtt9kpw1PYSblan8yVIcBE1OGBVF4ulyelwZAO3YcXXRoNcy4Gn-AdO-P9Mx_YjMcNJR_wPSirVpaVNdQv7HjMepjjW2tvM0K1mFHUwtdFBeUCCERpDOIFvF1LdM",
                      "q": "yCmC8acbXFj-nFdAqKP8_UGX-pQ8M3lZAMAswM690T0vlm-5_VOFaNzSNFRJjIPaUmJhiy-A0dLJMXHNB2imwocRJJwbPh8FB2QBUvySljrvr8P1IZe2sXrxEk_3fT7jHsj98BcvyZ1loYj40y96rtoV4FzV_QT8zb3GkI4QtN8",
                      "dp": "ZxdBKFFLAd8dnfhX1RjFJAebPlgRG9-RAzxUfV5kojYCB0tCRA9mrXg6vmi_2WHoUgVkHDao7Xmg8nini06C2EZl1gl9QfIgQrzFcdKDnlgR7TWrEKKLAWf7r1Gu59ZcaO2eLnl4qrF4PmLmkYu760TPhRPPzukqnSrcPiCSTA0",
                      "dq": "M6Y6ir6zGbZBJPiCz8FZE8SsQdWkXyft5nqwUaRHaMmgEPKNjKfTogZxG12wiNixKlcGkpLUa9A3aFHUNRg1B7cwnkDF6ta4RnrwuIhCDw_wL2uiQmPSmaN-t1n5I9Fpa9UzaZOiGiVKR09_3Ya_4oSV5oouEZcK4NAaf8yY1QM",
                      "qi": "zjmvKSb74G0tzCdfKLkDSNBIT9dDhhrEnmSGblC2-0i5oCpp9rjjFKEv-vTsiARS0Qh9geD0u9fbw2HaBwUqsN-r2L_nDpc3U-3NoLTh20dIxYTbESdbxtqcWS9Sooi6Sjq2lT1lIOhBvh310lOvDMnwXWojUL1rNNApiSzKBV4"
                  })})
    @patch.object(generate_token.events_client, 'put_events',
                  return_value={'ResponseMetadata': {'FailedEntryCount': 0, "Entries": [{"EventId": "11710aed-b79e-4468-a20b-bb3c0c3b4860"}]}})
    def test_generate_token(self, mock_query, mock_put_item, mock_hget,
                            mock_get, mock_incr, mock_get_secret, mock_put_events):
        """
        This function tests the generate_token lambda function
        """
        # valid event_id
        mock_event = {
            "requestContext": {
                "domainName": "example.com",
                "stage": "dev"
            },
            "body": json.dumps({"event_id": self.event_id, "request_id": self.request_id})
        }
        response = generate_token.lambda_handler(mock_event, None)
        self.assertEqual(response["statusCode"], 200)
        response_body = json.loads(response["body"])
        self.assertEqual(response_body["expires_in"], self.validity_period)

        # invalid request_id
        with patch.object(generate_token.rc, 'hget', return_value=None):
            response = generate_token.lambda_handler(mock_event, None)
            self.assertEqual(response["statusCode"], 404)
            response_body = json.loads(response["body"])
            self.assertEqual(
                response_body["error"], self.invalid_request_id_msg)

        # queue number is not being served yet
        # queue number = 3, serving number = 2
        with patch.object(generate_token.rc, 'hget', return_value=3):
            response = generate_token.lambda_handler(mock_event, None)
            self.assertEqual(response["statusCode"], 202)
            response_body = json.loads(response["body"])
            self.assertEqual(
                response_body["error"], "Request ID not being served yet")

        # request_id already exists in the database
        with patch.object(generate_token.rc, 'hget', return_value=1):
            with patch.object(generate_token.ddb_table, 'put_item',
                              side_effect=ClientError({"Error": {"Code": "400", "Message": "ConditionalCheckFailedException"}}, "UpdateItem")):
                with self.assertRaises(ClientError):
                    response = generate_token.lambda_handler(
                        mock_event, None)
                    self.assertEqual(response["statusCode"], 200)

        # put_event raised an exception
        with patch.object(generate_token.events_client, 'put_events', side_effect=Exception):
            with self.assertRaises(Exception):
                response = generate_token.lambda_handler(mock_event, None)

        # invalid event_id
        mock_event["body"] = json.dumps({"event_id": self.invalid_id, "request_id": self.request_id})
        response = generate_token.lambda_handler(mock_event, None)
        self.assertEqual(response["statusCode"], 400)
        response_body = json.loads(response["body"])
        self.assertEqual(response_body["error"], self.invalid_event_req_id_msg)


    @patch.object(get_list_expired_tokens.ddb_table, 'query',
                  return_value={"Items": [{"request_id": "fe7a5f04-6ff0-4bd6-9c31-52088cc4e73a"}]})
    def test_get_list_expired_tokens(self, mock_query):
        """
        This function tests the get_list_expired_tokens lambda function
        """
        # valid event_id
        mock_event_200 = {'queryStringParameters': {'event_id': self.event_id}}
        response = get_list_expired_tokens.lambda_handler(mock_event_200, None)
        self.assertEqual(response["statusCode"], 200)

        # invalid event_id
        mock_event_400 = {'queryStringParameters': {
            'event_id': self.invalid_id}}
        response = get_list_expired_tokens.lambda_handler(mock_event_400, None)
        self.assertEqual(response["statusCode"], 400)
        response_body = json.loads(response["body"])
        self.assertEqual(response_body["error"], self.invalid_event_id_msg)

        # query failed with an exception
        # repatch the output of query call to return an exception
        response = {}
        with patch.object(get_list_expired_tokens.ddb_table, 'query',
                          side_effect=Exception):
            with self.assertRaises(Exception):
                response = get_list_expired_tokens.lambda_handler(
                    mock_event_200, None)

    @patch.object(get_num_active_tokens.ddb_table, 'query',
                  return_value={"Items": [{"request_id": "fe7a5f04-6ff0-4bd6-9c31-52088cc4e73a"}]})
    def test_get_num_active_tokens(self, mock_query):
        """
        This function tests the get_num_active_tokens lambda function
        """
        # valid event_id
        mock_event_200 = {'queryStringParameters': {'event_id': self.event_id}}
        response = get_num_active_tokens.lambda_handler(mock_event_200, None)
        self.assertEqual(response["statusCode"], 200)
        response_body = json.loads(response["body"])
        self.assertEqual(response_body["active_tokens"], 1)

        # invalid event_id
        mock_event_400 = {'queryStringParameters': {
            'event_id': self.invalid_id}}
        response = get_num_active_tokens.lambda_handler(mock_event_400, None)
        self.assertEqual(response["statusCode"], 400)
        response_body = json.loads(response["body"])
        self.assertEqual(response_body["error"], self.invalid_event_id_msg)

        # query failed with an exception
        # repatch the output of query call to return an exception
        response = {}
        with patch.object(get_num_active_tokens.ddb_table, 'query',
                          side_effect=Exception):
            with self.assertRaises(Exception):
                response = get_num_active_tokens.lambda_handler(
                    mock_event_200, None)

    def test_get_public_key(self):
        """
        This function tests the get_public_key lambda function
        """
        stack_name = os.environ.get('STACK_NAME')
        with patch('get_public_key.client') as mock_client:
            mock_client.get_secret_value.return_value = {
                "SecretString": "somesecretstring", "Name": f"{stack_name}/jwk-public"}
            response = get_public_key.lambda_handler(None, None)
            self.assertEqual(response["statusCode"], 200)

    @patch.object(get_queue_num.rc, 'hget', return_value=1)
    @patch.object(get_queue_num.rc, 'hgetall', return_value={"queue_number": 1, "event_id": "abc123"})
    def test_get_queue_num(self, mock_hget, mock_hgetall):
        """
        This function tests the get_queue_num lambda function
        """
        # event_id is invalid
        mock_event_400 = {'queryStringParameters': {
            'event_id': self.invalid_id, 'request_id': self.request_id}}
        response = get_queue_num.lambda_handler(mock_event_400, None)
        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(json.loads(response['body'])["error"], self.invalid_event_req_id_msg)

        # request_id exists
        mock_event_200 = {'queryStringParameters': {
            'event_id': self.event_id, 'request_id': self.request_id}}
        response = get_queue_num.lambda_handler(mock_event_200, None)
        self.assertEqual(response["statusCode"], 200)

        # request_id does not exist
        with patch.object(get_queue_num.rc, 'hget', return_value=None):
            mock_event_202 = {'queryStringParameters': {
                'event_id': self.event_id, 'request_id': self.invalid_id}}
            response = get_queue_num.lambda_handler(mock_event_202, None)
            self.assertEqual(response["statusCode"], 202)

    @patch.object(get_serving_num.rc, 'get', return_value=1)
    @patch.object(get_serving_num.rc, 'exists', return_value=1)
    def test_get_serving_num(self, mock_get, mock_exists):
        """
        This function tests the get_serving_num lambda function
        """
        # invalid event_id
        mock_event_400 = {'queryStringParameters': {
            'event_id': self.invalid_id, 'request_id': self.request_id}}
        response = get_serving_num.lambda_handler(mock_event_400, None)
        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(json.loads(response['body'])["error"], self.invalid_event_req_id_msg)

        # request_id exists
        mock_event_200 = {'queryStringParameters': {
            'event_id': self.event_id, 'request_id': self.request_id}}
        response = get_serving_num.lambda_handler(mock_event_200, None)
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['serving_counter'], 1)

        # request_id does not exist
        with patch.object(get_serving_num.rc, 'exists', return_value=0):
            mock_event_404 = {'queryStringParameters': {
                'event_id': self.event_id, 'request_id': self.invalid_id}}
            response = get_serving_num.lambda_handler(mock_event_404, None)
            self.assertEqual(response["statusCode"], 404)
        self.assertEqual(json.loads(response['body'])["error"], self.invalid_request_id_msg)

    @patch.object(get_waiting_num.rc, 'get', return_value=1)
    @patch.object(get_waiting_num.rc, 'exists', return_value=1)
    def test_get_waiting_num(self, mock_get, mock_exists):
        """
        This function tests the get_waiting_num lambda function
        """
        event_id = os.environ["EVENT_ID"]

        # event_id is invalid
        mock_event_400 = {'queryStringParameters': {
            'event_id': self.invalid_id, 'request_id': self.request_id}}
        response = get_waiting_num.lambda_handler(mock_event_400, None)
        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(json.loads(response['body'])["error"], self.invalid_event_req_id_msg)

        # request_id exists
        mock_event_200 = {'queryStringParameters': {
            'event_id': self.event_id, 'request_id': self.request_id}}
        response = get_waiting_num.lambda_handler(mock_event_200, None)
        self.assertEqual(response["statusCode"], 200)
        # waiting num = queue_count - token_count
        body = json.loads(response['body'])
        self.assertEqual(int(body['waiting_num']), 0)

        # request_id does not exist
        with patch.object(get_waiting_num.rc, 'exists', return_value=0):
            mock_event_404 = {'queryStringParameters': {
                'event_id': self.event_id, 'request_id': self.invalid_id}}
            response = get_waiting_num.lambda_handler(mock_event_404, None)
            self.assertEqual(response["statusCode"], 404)
        self.assertEqual(json.loads(response['body'])["error"], self.invalid_request_id_msg)

    @patch.object(increment_serving_counter.rc, 'incrby', return_value=1)
    def test_increment_serving_counter(self, mock_incrby):
        """
        This function tests the increment_serving_counter lambda function
        """
        # event_id is valid
        mock_event_200 = {"body": json.dumps(
            {"event_id": self.event_id, "increment_by": 1})}
        response = increment_serving_counter.lambda_handler(
            mock_event_200, None)
        self.assertEqual(response["statusCode"], 200)

        # event_id is invalid
        mock_event_400 = {"body": json.dumps(
            {"event_id": self.invalid_id, "increment_by": 1})}
        response = increment_serving_counter.lambda_handler(
            mock_event_400, None)
        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response['body'])
        self.assertEqual(body["error"], self.invalid_event_id_msg)

    @patch.object(reset_initial_state.rc, 'getset', return_value=0)
    @patch.object(reset_initial_state.ddb_table, 'scan',
                  return_value={"Items": [{"request_id": "fe7a5f04-6ff0-4bd6-9c31-52088cc4e73a"}]})
    @patch.object(reset_initial_state.ddb_table, 'delete_item',
                  return_value={'ResponseMetadata': {'RequestId': '9KOGMPHCTEBNFOKONNM94K2QTRVV4KQNSO5AEMVJF66Q9ASUAAJG', 'HTTPStatusCode': 200}})
    def test_reset_initial_state(self, mock_get, mock_scan, mock_delete):
        """
        This function tests the reset_initial_state lambda function
        """
        # event_id is valid
        mock_event_200 = {"body": json.dumps({"event_id": self.event_id})}
        response = reset_initial_state.lambda_handler(mock_event_200, None)
        self.assertEqual(response["statusCode"], 200)

        # invalid event_id
        mock_event_400 = {"body": json.dumps({"event_id": self.invalid_id})}
        response = reset_initial_state.lambda_handler(mock_event_400, None)
        self.assertEqual(response["statusCode"], 400)

    @patch.object(update_session.rc, 'incr', return_value=1)
    @patch.object(update_session.ddb_table, 'update_item',
                  return_value={"Items": [{"request_id": "fe7a5f04-6ff0-4bd6-9c31-52088cc4e73a"}]})
    @patch.object(update_session.events_client, 'put_events',
                  return_value={'ResponseMetadata': {'FailedEntryCount': 0, "Entries": [{"EventId": "11710aed-b79e-4468-a20b-bb3c0c3b4860"}]}})
    def test_update_session(self, mock_rcincr, mock_update, mock_put_events):
        """
        This function tests the update_session lambda function
        """
        # valid event_id
        mock_event_200 = {"body": json.dumps(
            {"event_id": self.event_id, "request_id": self.request_id, "status": 1})}
        response = update_session.lambda_handler(mock_event_200, None)
        self.assertEqual(response["statusCode"], 200)

        # invalid event_id
        mock_event_400 = {"body": json.dumps(
            {"event_id": self.invalid_id, "request_id": self.request_id, "status": 1})}
        response = update_session.lambda_handler(mock_event_400, None)
        self.assertEqual(response["statusCode"], 400)

        # request_id doesn't exist
        # repatch the output of update_item call to return an exception
        response = {}
        with patch.object(update_session.ddb_table, 'update_item',
                          side_effect=ClientError({"Error": {"Code": "400", "Message": "ConditionalCheckFailedException"}}, "UpdateItem")):
            with self.assertRaises(ClientError):
                response = update_session.lambda_handler(mock_event_200, None)
                self.assertEqual(response["statusCode"], 404)
                response_body = json.loads(response["body"])
                self.assertEqual(
                    response_body["error"], "Request ID doesn't exist.")

        # error with putting an object
        # repatch the output of update_item call to return an exception
        response = {}
        with patch.object(update_session.events_client, 'put_events',
                          side_effect=Exception):
            with patch.object(update_session.ddb_table, 'update_item', return_value={"Items": [{"request_id": self.request_id}]}):
                with self.assertRaises(Exception):
                    response = update_session.lambda_handler(
                        mock_event_200, None)


if __name__ == '__main__':
    unittest.main()
