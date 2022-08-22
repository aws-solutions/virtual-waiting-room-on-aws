# need to monkey-patch before requests is imported
# https://github.com/gevent/gevent/issues/1016
import gevent.monkey

gevent.monkey.patch_all()

import json
import threading

import requests

from src.decorators import capture_stats, require_authentication
from src.config.config import EVENT_ID

REQUEST_TIMEOUT_SECONDS = 20

class CustomClient:
    """
    A custom requests based rest client.
    """
    def __init__(self, environment):
        # we derive the base_url for the rest api from the URL passed to the load test UI
        self.environment = environment
        self.public_api_base_url, self.private_api_base_url = environment.host.split(
            ";")
        # self.private_api_base_url = environment.host.split(";")[1]

        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8"
        }

        self.event_id = EVENT_ID
        self.request_id = None
        self.queue_num = None
        self.served = False
        self.finished = False
        self.access_token = None
        self.refresh_token = None
        self.id_token = None
        self.session = requests.Session()
        self.regen_counter = 3

    def __str__(self):
        pass

    @capture_stats
    def assign_queue_num(self):
        """
        Request to enter the waiting room queue. This is usually the first request issued by client when
        they are ready to get in line. This is an asynchronous request that returns a request ID
        immediately that can be used later to retrieve the result this request using /queue_num.
        :return:  {
                    "api_request_id": REQUEST_ID
                  }
        """
        request_body = {"event_id": self.event_id}
        response = self.session.post(url=self.public_api_base_url +
                                 "/assign_queue_num",
                                 headers=self.headers,
                                 data=json.dumps(request_body), stream=False, timeout=REQUEST_TIMEOUT_SECONDS)
        if response.status_code == 200:
            self.request_id = response.json()["api_request_id"]
            # print("request id: %s" % self.request_id)
        #response.close()
        return response

    @capture_stats
    def get_queue_num(self):
        """
        Returns the queue position for the provided event and request ID. This API may need to be called more than
        once depending on load of the waiting room. This API will return a 404 status code until it has processed
        the request from API Gateway.
        :return: {
                    "entry_time": TIMESTAMP,
                    "queue_number": INTEGER,
                    "event_id": EVENT_ID,
                    "status": STATUS (1 = successfully entered, -1 = invalid request sent)
                }
        """
        query_str = "event_id=%s&request_id=%s" % (self.event_id,
                                                   self.request_id)
        response = self.session.get(url=self.public_api_base_url + "/queue_num?" +
                                query_str,
                                headers=self.headers, stream=False, timeout=REQUEST_TIMEOUT_SECONDS)
        if response.status_code == 200:
            self.queue_num = int(response.json()["queue_number"])
            # print("assigned queue num: %s" % self.queue_num)
        #response.close()
        return response

    @capture_stats
    def get_serving_num(self):
        """
        Returns the current serving position in the queue. Requests with an equal or lower position in the waiting
        room can request tokens from the API
        :return: {
                    "serving_counter": INTEGER
                }
        """
        query_str = "event_id=%s" % (self.event_id)
        response = self.session.get(url=self.public_api_base_url +
                                "/serving_num?" + query_str,
                                headers=self.headers, stream=False, timeout=REQUEST_TIMEOUT_SECONDS)
        # print(response.status_code)
        if response.status_code == 200:
            serving_counter = int(response.json()["serving_counter"])
            # print("serving: %s" % serving_counter)
            # print(self.queue_num <= serving_counter)
            if self.queue_num <= serving_counter:
                self.served = True
        #response.close()
        return response

    @capture_stats
    def get_waiting_num(self):
        """
        Returns the number users currently queued in the waiting room and have not been issued a token yet.
        :return: {
                    "waiting_num": INTEGER
                }
        """
        query_str = "event_id=%s" % (self.event_id)
        response = self.session.get(url=self.public_api_base_url + "/waiting_num?" +
                            query_str,
                            headers=self.headers, stream=False, timeout=REQUEST_TIMEOUT_SECONDS)
        #response.close()
        return response

    @capture_stats
    def get_public_key(self):
        """
        Returns the public JWT that can be used to verify signed tokens issued by this stack
        :return: {
                    "kty": "RSA",
                    "alg": "RS256",
                    "kid": KID,
                    "n": KEY,
                    "e": "AQAB"
                }
        """
        response = self.session.get(url=self.public_api_base_url +
                            "/public_key?event_id=%s" % self.event_id,
                            headers=self.headers, stream=False, timeout=REQUEST_TIMEOUT_SECONDS)
        #response.close()
        return response

    @capture_stats
    def generate_token(self):
        """
        Description: Generates a JWT set with options to override the token claims. The current serving
        position must be equal or greater to this request ID’s queue position to obtain a token.
        This API is idempotent, meaning, the exact tokens generated for the event and request ID are
        returned on all future requests.
        :return: {
                    "access_token": JWT,
                    "refresh_token": JWT,
                    "id_token": JWT,
                    "token_type": "Bearer",
                    "expires_in": SECONDS
                }
        """
        request_body = {
            "event_id": self.event_id,
            "request_id": self.request_id
        }
        response = self.session.post(url=self.public_api_base_url +
                                 "/generate_token",
                                 headers=self.headers,
                                 data=json.dumps(request_body), stream=False, timeout=REQUEST_TIMEOUT_SECONDS)
        # print(response)
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            # self.refresh_token = response.json()["refresh_token"]
            # self.id_token = response.json()["id_token"]
            self.finished = True
        #response.close()
        return response
    
    @capture_stats
    def regenerate_token(self):
        """
        Description: Generates a JWT set with options to override the token claims. The current serving
        position must be equal or greater to this request ID’s queue position to obtain a token.
        This API is idempotent, meaning, the exact tokens generated for the event and request ID are
        returned on all future requests.
        :return: {
                    "access_token": JWT,
                    "refresh_token": JWT,
                    "id_token": JWT,
                    "token_type": "Bearer",
                    "expires_in": SECONDS
                }
        """
        request_body = {
            "event_id": self.event_id,
            "request_id": self.request_id
        }
        response = self.session.post(url=self.public_api_base_url +
                                 "/generate_token",
                                 headers=self.headers,
                                 data=json.dumps(request_body), stream=False, timeout=REQUEST_TIMEOUT_SECONDS)
        # print(response)
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            # self.refresh_token = response.json()["refresh_token"]
            # self.id_token = response.json()["id_token"]
            self.finished = True
        #response.close()
        return response