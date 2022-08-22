# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
This module is the unit test for the core API Lambda functions.
"""
# pylint: disable=R0902 

import os
import unittest
import time
from unittest.mock import Mock, patch, MagicMock

import json
from botocore.response import StreamingBody
from botocore.exceptions import ClientError
from io import StringIO

os.environ["REDIS_HOST"] = "local"
os.environ["REDIS_PORT"] = "1234"
os.environ["EVENT_ID"] = "abc123"
# Bandit B105: not a hardcoded password
os.environ["TOKEN_TABLE"] = "token_table" # nosec
os.environ["SOLUTION_ID"] = "SO0166"
os.environ["STACK_NAME"] = "vwr"
os.environ["EVENT_BUS_NAME"] = "vwr_event_bus"
os.environ["VALIDITY_PERIOD"] = "3600"
os.environ["ACTIVE_TOKENS_FN"] = "get_num_active_tokens"
os.environ["QUEUE_URL"] = "queue_url"
os.environ["QUEUE_POSITION_ENTRYTIME_TABLE"] = "queue_position_entry_time_table"
os.environ["SERVING_COUNTER_ISSUEDAT_TABLE"] = "serving_counter_issuedat_table"
os.environ["QUEUE_POSITION_EXPIRY_PERIOD"] = "100"
os.environ["ENABLE_QUEUE_POSITION_EXPIRY"] = "true"
os.environ["INCR_SVC_ON_QUEUE_POS_EXPIRY"] = "true"

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
import get_queue_position_expiry_time
import set_max_queue_position_expired
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
        self.expired_queue_position_msg = "Queue position has expired"
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
    @patch.object(assign_queue_num.sqs_client, 'delete_message', return_value={})
    def test_assign_queue_num(self, mock_incr, mock_delete_message):
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
        with patch.object(assign_queue_num.ddb_table, 'put_item', return_value=None) as mock_method:
            mock_event["Records"][0]["body"] = json.dumps({"event_id": self.event_id})
            response = assign_queue_num.lambda_handler(mock_event, None)
            self.assertEqual(response, 10)
            mock_method.assert_called_once()

        # invalid event_id
        with patch.object(assign_queue_num.ddb_table, 'put_item', return_value=None) as mock_method:
            mock_event["Records"][0]["body"] = json.dumps({"event_id": self.invalid_id})
            response = assign_queue_num.lambda_handler(mock_event, None)
            self.assertEqual(response, 10)
            self.assertRaises(Exception)
            mock_method.assert_not_called()


    @patch.object(auth_generate_token.ddb_table_tokens, 'query',
                  return_value={"Items": [{"request_id": "fe7a5f04-6ff0-4bd6-9c31-52088cc4e73a", "expires": 1000,
                                           "access_token": "accesstoken", "refresh_token": "refreshtoken", "id_token": "idtoken"}]})
    @patch.object(auth_generate_token.ddb_table_tokens, 'put_item',
                  return_value={"Items": [{"request_id": "fe7a5f04-6ff0-4bd6-9c31-52088cc4e73a"}]})
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
    def test_auth_generate_token(self, mock_query, mock_put_item, mock_incr, mock_get_secret, mock_put_events):
        """
        This function tests the auth_generate_function lambda function
        """

        redis_cache = {'max_queue_position_expired': '2', 'serving_counter': '5' }
        def get(key):
            return redis_cache[key]

        auth_generate_token.rc = MagicMock()
        auth_generate_token.rc.get = Mock(side_effect=get)

         # invalid event_id
        mock_event_400 = {
            "requestContext": {
                "domainName": "example1.com",
                "stage": "dev"
            },
            "body": json.dumps({"event_id": self.invalid_id, "request_id": self.invalid_id})
        }
        response = generate_token.lambda_handler(mock_event_400, None)
        self.assertEqual(response["statusCode"], 400)
        response_body = json.loads(response["body"])
        self.assertEqual(response_body["error"], self.invalid_event_req_id_msg)

        # valid event_id
        mock_event = {
            "requestContext": {
                "domainName": "example1.com",
                "stage": "dev"
            },
            "body": json.dumps({"event_id": self.event_id, "request_id": self.request_id})
        }

        # invalid request_id
        with patch.object(auth_generate_token.ddb_table_queue_position_entry_time, 'get_item', return_value={}):
            response = auth_generate_token.lambda_handler(mock_event, None)
            self.assertEqual(response["statusCode"], 400)
            response_body = json.loads(response["body"])
            self.assertEqual(response_body["error"], self.invalid_request_id_msg)

        # queue number is not being served yet
        # queue number = 3, serving number = 2
        redis_cache['serving_counter'] = '2'
        with patch.object(auth_generate_token.ddb_table_queue_position_entry_time, 'get_item', 
                return_value={'Item': {"queue_position": 3, "event_id": "abc123", "entry_time": 1002, "status": 1}}):
            # with patch.object(generate_token.rc, 'get', return_value=2):
            response = auth_generate_token.lambda_handler(mock_event, None)
            self.assertEqual(response["statusCode"], 202)
            response_body = json.loads(response["body"])
            self.assertEqual(response_body["error"], "Request ID not being served yet")

        # request id in token table
        redis_cache['serving_counter'] = '5'
        with patch.object(auth_generate_token.ddb_table_queue_position_entry_time, 'get_item', 
                return_value={'Item': {"queue_position": 3, "event_id": "abc123", "entry_time": 1002, "status": 1}}):
            with patch.object(auth_generate_token.ddb_table_tokens, 'get_item', 
                return_value={"Item": {"request_id": "fe7a5f04-6ff0-4bd6-9c31-52088cc4e73a", "session_status" : "0", "expires": 2000, "issued_at": 1000, 
                                "not_before": 1000, "queue_number": 2, "issuer": "someone"}}):
                response = auth_generate_token.lambda_handler(mock_event, None)
                self.assertEqual(response["statusCode"], 200)

        # generate new token
        with patch.object(auth_generate_token.ddb_table_queue_position_entry_time, 'get_item', 
                return_value={'Item': {"queue_position": 3, "event_id": "abc123", "entry_time": 1002, "status": 1}}):
            with patch.object(auth_generate_token.ddb_table_tokens, 'get_item', return_value={}):
                with patch.object(auth_generate_token.ddb_table_tokens, 'put_item', return_value={}) as mock_method:
                    with patch.object(auth_generate_token.ddb_table_serving_counter_issued_at, 'query', 
                        return_value={ 'Items': [{'issue_time': int(time.time()) - 50, 'serving_counter': '5', 'queue_positions_served': 1 } ]}):
                        with patch.dict(os.environ, { "QUEUE_POSITION_EXPIRY_PERIOD": "100"} ):
                            response = auth_generate_token.lambda_handler(mock_event, None)
                            self.assertEqual(response["statusCode"], 200)
                            mock_method.assert_called_once()

        # add test for regenerate token


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
                generate_events.lambda_handler(None, None)

    @patch.object(generate_token.ddb_table_tokens, 'query',
                  return_value={"Items": [{"request_id": "fe7a5f04-6ff0-4bd6-9c31-52088cc4e73a", "expires": 1000,
                                           "access_token": "accesstoken", "refresh_token": "refreshtoken", "id_token": "idtoken"}]})
    @patch.object(generate_token.ddb_table_tokens, 'put_item',
                  return_value={"Items": [{"request_id": "fe7a5f04-6ff0-4bd6-9c31-52088cc4e73a"}]})
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
    def test_generate_token(self, mock_query, mock_put_item, mock_incr, mock_get_secret, mock_put_events):
        """
        This function tests the generate_token lambda function
        """
        redis_cache = {'max_queue_position_expired': '2', 'serving_counter': '5' }
        def get(key):
            return redis_cache[key]

        generate_token.rc = MagicMock()
        generate_token.rc.get = Mock(side_effect=get)

        # invalid event_id
        mock_event_400 = {
            "requestContext": {
                "domainName": "example.com",
                "stage": "dev"
            },
            "body": json.dumps({"event_id": self.invalid_id, "request_id": self.invalid_id})
        }
        response = generate_token.lambda_handler(mock_event_400, None)
        self.assertEqual(response["statusCode"], 400)
        response_body = json.loads(response["body"])
        self.assertEqual(response_body["error"], self.invalid_event_req_id_msg)

        # valid event_id
        mock_event = {
            "requestContext": {
                "domainName": "example.com",
                "stage": "dev"
            },
            "body": json.dumps({"event_id": self.event_id, "request_id": self.request_id})
        }

        # invalid request_id
        with patch.object(generate_token.ddb_table_queue_position_entry_time, 'get_item', return_value={}):
            response = generate_token.lambda_handler(mock_event, None)
            self.assertEqual(response["statusCode"], 400)
            response_body = json.loads(response["body"])
            self.assertEqual(response_body["error"], self.invalid_request_id_msg)

        # queue number is not being served yet
        # queue number = 3, serving number = 2
        redis_cache['serving_counter'] = '2'
        with patch.object(generate_token.ddb_table_queue_position_entry_time, 'get_item', 
                return_value={'Item': {"queue_position": 3, "event_id": "abc123", "entry_time": 1002, "status": 1}}):
            # with patch.object(generate_token.rc, 'get', return_value=2):
            response = generate_token.lambda_handler(mock_event, None)
            self.assertEqual(response["statusCode"], 202)
            response_body = json.loads(response["body"])
            self.assertEqual(response_body["error"], "Request ID not being served yet")

        # request id in token table
        redis_cache['serving_counter'] = '5'
        with patch.object(generate_token.ddb_table_queue_position_entry_time, 'get_item', 
                return_value={'Item': {"queue_position": 3, "event_id": "abc123", "entry_time": 1002, "status": 1}}):
            with patch.object(generate_token.ddb_table_tokens, 'get_item', 
                return_value={"Item": {"request_id": "fe7a5f04-6ff0-4bd6-9c31-52088cc4e73a", "session_status" : "0", "expires": 2000, "issued_at": 1000, 
                                "not_before": 1000, "queue_number": 2, "issuer": "someone"}}):
                response = generate_token.lambda_handler(mock_event, None)
                self.assertEqual(response["statusCode"], 200)

        # generate new token
        with patch.object(generate_token.ddb_table_queue_position_entry_time, 'get_item', 
                return_value={'Item': {"queue_position": 3, "event_id": "abc123", "entry_time": 1002, "status": 1}}):
            with patch.object(generate_token.ddb_table_tokens, 'get_item', return_value={}):
                with patch.object(generate_token.ddb_table_tokens, 'put_item', return_value={}) as mock_method:
                    with patch.object(generate_token.ddb_table_serving_counter_issued_at, 'query', 
                        return_value={ 'Items': [{'issue_time': int(time.time()) - 50, 'serving_counter': '5', 'queue_positions_served': 1 } ]}):
                        with patch.dict(os.environ, { "QUEUE_POSITION_EXPIRY_PERIOD": "100"} ):
                            response = generate_token.lambda_handler(mock_event, None)
                            self.assertEqual(response["statusCode"], 200)
                            mock_method.assert_called_once()

    @patch.object(get_list_expired_tokens.ddb_table, 'query',return_value={"Items": [{"request_id": "fe7a5f04-6ff0-4bd6-9c31-52088cc4e73a"}]})
    def test_get_list_expired_tokens(self, mock_query):
        """
        This function tests the get_list_expired_tokens lambda function
        """
        # valid event_id
        mock_event_200 = {'queryStringParameters': {'event_id': self.event_id}}
        response = get_list_expired_tokens.lambda_handler(mock_event_200, None)
        self.assertEqual(response["statusCode"], 200)

        # invalid event_id
        mock_event_400 = {'queryStringParameters': {'event_id': self.invalid_id}}
        response = get_list_expired_tokens.lambda_handler(mock_event_400, None)
        self.assertEqual(response["statusCode"], 400)
        response_body = json.loads(response["body"])
        self.assertEqual(response_body["error"], self.invalid_event_id_msg)

        # query failed with an exception
        # repatch the output of query call to return an exception
        response = {}
        with patch.object(get_list_expired_tokens.ddb_table, 'query', side_effect=Exception):
            with self.assertRaises(Exception):
                get_list_expired_tokens.lambda_handler(mock_event_200, None)

    @patch.object(get_num_active_tokens.ddb_table, 'query',return_value={"Items": [{"request_id": "fe7a5f04-6ff0-4bd6-9c31-52088cc4e73a"}]})
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
        mock_event_400 = {'queryStringParameters': {'event_id': self.invalid_id}}
        response = get_num_active_tokens.lambda_handler(mock_event_400, None)
        self.assertEqual(response["statusCode"], 400)
        response_body = json.loads(response["body"])
        self.assertEqual(response_body["error"], self.invalid_event_id_msg)

        # query failed with an exception
        # repatch the output of query call to return an exception
        response = {}
        with patch.object(get_num_active_tokens.ddb_table, 'query', side_effect=Exception):
            with self.assertRaises(Exception):
                get_num_active_tokens.lambda_handler(mock_event_200, None)

    def test_get_public_key(self):
        """
        This function tests the get_public_key lambda function
        """
        stack_name = os.environ.get('STACK_NAME')
        mock_event_200 = {'queryStringParameters': {'event_id': self.event_id }}
        with patch('get_public_key.client') as mock_client:
            mock_client.get_secret_value.return_value = {"SecretString": "somesecretstring", "Name": f"{stack_name}/jwk-public"}
            response = get_public_key.lambda_handler(mock_event_200, None)
            self.assertEqual(response["statusCode"], 200)

    @patch.object(get_queue_num.rc, 'hget', return_value=1)
    @patch.object(get_queue_num.ddb_table_queue_position_entry_time, 'get_item', 
        return_value={'Item': {"queue_position": 1, "event_id": "abc123", "entry_time": 1002, "status": 1}})
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
        with patch.object(get_queue_num.ddb_table_queue_position_entry_time, 'get_item', return_value={}):
            mock_event_202 = {'queryStringParameters': {'event_id': self.event_id, 'request_id': self.invalid_id}}
            response = get_queue_num.lambda_handler(mock_event_202, None)
            self.assertEqual(response["statusCode"], 202)
            self.assertEqual(json.loads(response['body'])["error"], "Request ID not found")
            

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
        self.assertEqual(json.loads(response['body'])["error"], self.invalid_event_id_msg)

        # request_id exists
        mock_event_200 = {'queryStringParameters': {
            'event_id': self.event_id, 'request_id': self.request_id}}
        response = get_serving_num.lambda_handler(mock_event_200, None)
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['serving_counter'], 1)

    @patch.object(get_waiting_num.rc, 'get', return_value=1)
    @patch.object(get_waiting_num.rc, 'exists', return_value=1)
    def test_get_waiting_num(self, mock_get, mock_exists):
        """
        This function tests the get_waiting_num lambda function
        """
        # event_id is invalid
        mock_event_400 = {'queryStringParameters': {
            'event_id': self.invalid_id, 'request_id': self.request_id}}
        response = get_waiting_num.lambda_handler(mock_event_400, None)
        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(json.loads(response['body'])["error"], self.invalid_event_id_msg)

        # request_id exists
        mock_event_200 = {'queryStringParameters': {
            'event_id': self.event_id, 'request_id': self.request_id}}
        response = get_waiting_num.lambda_handler(mock_event_200, None)
        self.assertEqual(response["statusCode"], 200)
        # waiting num = queue_count - token_count
        body = json.loads(response['body'])
        self.assertEqual(int(body['waiting_num']), 0)

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
    @patch.object(reset_initial_state.ddb_client, 'describe_table', return_value={})
    @patch.object(reset_initial_state.ddb_client, 'delete_table', return_value={})
    @patch.object(reset_initial_state.ddb_client, 'get_waiter', return_value=MagicMock().wait)
    @patch.object(reset_initial_state.ddb_client, 'create_table', return_value={})
    @patch.object(reset_initial_state.rc, 'set', return_value=0)
    def test_reset_initial_state(self, mock_rc_getset, mock_describe, mock_delete, mock_waiter, mock_create, mock_rc_set):
        """
        This function tests the reset_initial_state lambda function
        """
        # event_id is valid
        mock_event_200 = {"event_id": self.event_id}
        response = reset_initial_state.lambda_handler(mock_event_200, None)
        self.assertEqual(response["statusCode"], 200)

        # invalid event_id
        mock_event_400 = {"event_id": self.invalid_id}
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
        mock_event_200 = {"body": json.dumps({"event_id": self.event_id, "request_id": self.request_id, "status": 1})}
        response = update_session.lambda_handler(mock_event_200, None)
        self.assertEqual(response["statusCode"], 200)

        # invalid event_id
        mock_event_400 = {"body": json.dumps({"event_id": self.invalid_id, "request_id": self.request_id, "status": 1})}
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
                    update_session.lambda_handler(mock_event_200, None)


    @patch.object(get_queue_position_expiry_time.ddb_table_queue_position_entry_time, 'get_item', 
        return_value={'Item': {"queue_position": 2, "event_id": "abc123", "entry_time": 1002, "status": 1}})
    def test_get_queue_position_expiry_time(self, mock_table):
        """
        This function tests the get_queue_position_expiry_time lambda function
        """
        redis_cache = {'max_queue_position_expired': '3', 'serving_counter': '5', 'queue_position_expiry_time': '200' }
        def get(key):
            return redis_cache[key]

        get_queue_position_expiry_time.rc = MagicMock()
        get_queue_position_expiry_time.rc.get = Mock(side_effect=get)

        # event_id is invalid
        mock_event_400 = {'queryStringParameters': {'event_id': self.invalid_id, 'request_id': self.request_id}}
        response = get_queue_position_expiry_time.lambda_handler(mock_event_400, None)
        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(json.loads(response['body'])["error"], self.invalid_event_req_id_msg)

        # invalid request id 
        with patch.object(get_queue_position_expiry_time.ddb_table_queue_position_entry_time, 'get_item', return_value={}):
            mock_event = {'queryStringParameters': {'event_id': self.event_id, 'request_id': self.invalid_id}}
            response = get_queue_position_expiry_time.lambda_handler(mock_event, None)
            self.assertEqual(response["statusCode"], 404)
            self.assertEqual(json.loads(response['body'])["error"], self.invalid_request_id_msg)

        # # Enable queue position expiry is False (needs reset of environment variable)
        # with patch.dict(os.environ, {"ENABLE_QUEUE_POSITION_EXPIRY": "false"}):
        #     print(os.environ["ENABLE_QUEUE_POSITION_EXPIRY"])
        #     mock_event_202 = {'queryStringParameters': {'event_id': self.event_id, 'request_id': self.request_id}}
        #     response = get_queue_position_expiry_time.lambda_handler(mock_event_202, None)
        #     self.assertEqual(response["statusCode"], 202)
        #     self.assertEqual(json.loads(response['body'])["error"], "Queue position expiration not enabled")

        # Queue position expired due to max queue position
        mock_event = {'queryStringParameters': {'event_id': self.event_id, 'request_id': self.request_id}}
        response = get_queue_position_expiry_time.lambda_handler(mock_event, None)
        self.assertEqual(response["statusCode"], 410)
        self.assertEqual(json.loads(response['body'])["error"], self.expired_queue_position_msg)

        # Queue position expired due to time out
        redis_cache['max_queue_position_expired'] = '1'
        with patch.object(get_queue_position_expiry_time.ddb_table_queue_position_entry_time, 'query', 
            return_value={'Items': [{"queue_position": 2, "event_id": "abc123", "entry_time": 1002, "status": 1}]}):
            with patch.object(get_queue_position_expiry_time.ddb_table_serving_counter_issued_at, 'query', return_value= { 'Items': [{'issue_time': 1000}] }):
                mock_event = {'queryStringParameters': {'event_id': self.event_id, 'request_id': self.request_id}}
                response = get_queue_position_expiry_time.lambda_handler(mock_event, None)
                self.assertEqual(response["statusCode"], 410)
                self.assertEqual(json.loads(response['body'])["error"], self.expired_queue_position_msg)
        
        # Queue position has valid expiry time
        redis_cache['max_queue_position_expired'] = '1'
        with patch.object(get_queue_position_expiry_time.ddb_table_queue_position_entry_time, 'query', 
            return_value={'Items': [{"queue_position": 2, "event_id": "abc123", "entry_time": 1002, "status": 1}]}):
            with patch.object(get_queue_position_expiry_time.ddb_table_serving_counter_issued_at, 'query', return_value= { 'Items': [{'issue_time': int(time.time()) - 10}] }):
                mock_event = {'queryStringParameters': {'event_id': self.event_id, 'request_id': self.request_id}}
                response = get_queue_position_expiry_time.lambda_handler(mock_event, None)
                self.assertEqual(response["statusCode"], 200)
                self.assertTrue(isinstance(json.loads(response['body'])["expires_in"], int))


    @patch.object(set_max_queue_position_expired.ddb_table_serving_counter_issued_at, 'query', 
        return_value= { 'Items': [
                {'serving_counter' : 10, 'queue_positions_served': 8, 'issue_time': int(time.time()) - 1000},
                {'serving_counter' : 25, 'queue_positions_served': 11, 'issue_time': int(time.time()) - 500 }
            ] }
        )
    def test_set_max_queue_position_expired(self, mock_table):
        """
        This function tests the get_queue_position_expiry_time lambda function
        """
        mock_redis_cache = {'max_queue_position_expired': '0', 'serving_counter': '0' }
        def mock_get(key):
            return mock_redis_cache[key]

        def mock_set(key, value):
            if mock_redis_cache:
                mock_redis_cache[key] = value
        
        def mock_incr(key, value):
            if mock_redis_cache:
                _value =  int(mock_redis_cache[key]) + int(value)
                mock_redis_cache[key] = _value
                return _value

        set_max_queue_position_expired.rc = MagicMock()
        set_max_queue_position_expired.rc.get = Mock(side_effect=mock_get)
        set_max_queue_position_expired.rc.set = Mock(side_effect=mock_set)
        set_max_queue_position_expired.rc.incrby = Mock(side_effect=mock_incr)

        mock_event = {'id': '3475893474', 'detail-type': 'Scheduled Event', 'source': 'aws.events', 'account': 'dummy123' }

        # reset in progress test
        with patch('builtins.print') as mocked_print:
            mock_redis_cache['reset_in_progress'] = 1
            set_max_queue_position_expired.lambda_handler(mock_event, None)
            mocked_print.assert_called_with('Reset in progress. Skipping execution')
        mock_redis_cache['reset_in_progress'] = 0

        # no queue positions eligible
        with patch.object(set_max_queue_position_expired.ddb_table_queue_position_entry_time, 'query', return_value={'Items': [] }):
            with patch('builtins.print') as mocked_print:
                mock_redis_cache['queue_counter'] = 6
                set_max_queue_position_expired.lambda_handler(mock_event, None)
                mocked_print.assert_called_with('No queue postions items eligible')

        # # set max queue position expired (no svc increment, set os.environ INCR_SVC_ON_QUEUE_POS_EXPIRY to false)
        # with patch.object(set_max_queue_position_expired.ddb_table_queue_position_entry_time, 'query', 
        #     return_value={'Items': [{"queue_position": 12, "event_id": "abc123", "entry_time": int(time.time()) - 150, "status": 1}] }):
        #     with patch.object(set_max_queue_position_expired, 'incr_serving_counter') as mock_method:
        #         set_max_queue_position_expired.lambda_handler(mock_event, None)
        #         self.assertEqual(mock_redis_cache['max_queue_position_expired'], 25)
        #         mock_method.assert_not_called()

        # set max queue position expired (with svc increment)
        with patch.object(set_max_queue_position_expired.ddb_table_queue_position_entry_time, 'query', 
            return_value={'Items': [{"queue_position": 12, "event_id": "abc123", "entry_time": int(time.time()) - 150, "status": 1}] }):
            with patch.object(set_max_queue_position_expired.ddb_table_serving_counter_issued_at, 'put_item', return_value=None) as mock_svc_table:
                with patch.object(set_max_queue_position_expired.events_client, 'put_events', return_value=None) as mock_events_client:
                    set_max_queue_position_expired.lambda_handler(mock_event, None)
                    self.assertEqual(mock_redis_cache['max_queue_position_expired'], 25)
                    self.assertEqual(mock_redis_cache['serving_counter'], 2 + 4)      
                    mock_events_client.assert_called()
                    mock_svc_table.assert_called()  
        
if __name__ == '__main__':
    unittest.main()
