<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is responsible for retrieving and displaying
the status of the authorization token used for checkout -->

<template>
  <div class="d-flex flex-column border border-2 border-dark rounded p-2">
    <!-- display a header with the last connection status -->
    <div class="text-center lead mb-2">Authorization Token</div>
    <div class="mb-2">
      This compartment shows the status of your authorization token.
    </div>
    <div>
      <!-- show status through different alerts -->
      <div
        v-if="!hasToken && readyForCheckOut"
        class="alert alert-secondary"
        role="alert"
      >
        Retrieving your token to complete the transaction
      </div>
      <div v-if="hasToken" class="alert alert-success" role="alert">
        <!-- format the token expiration as a human string -->
        Your token expires at
        {{ new Date(expires).toLocaleTimeString() }}
      </div>
      <div v-if="tokenRetrievalFailed" class="alert alert-danger" role="alert">
        An error occurred while retrieving your token
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from "vuex";
import axios from "axios";
import axiosRetry from "axios-retry";
const maxApiRetries = 10;
export default {
  name: "AuthorizationToken",
  computed: {
    // mix the getters into computed with object spread operator
    ...mapGetters(["hasRequestId", "hasQueuePosition", "hasToken"]),
    // add computed properties for vuex state
    myPosition() {
      return this.$store.state.myPosition;
    },
    queuePosition() {
      return this.$store.state.queuePosition;
    },
    readyForCheckOut() {
      return (
        this.hasRequestId &&
        this.myPosition &&
        this.queuePosition &&
        this.myPosition <= this.queuePosition
      );
    },
    claims() {
      // this extracts the claims from the token payload
      if (this.hasToken) {
        // split the three components
        let payload = this.$store.state.token.split(".")[1];
        // decode the payload in the dictionary of claims
        if (payload.length % 4) {
          const pad = "=";
          // not a multiple of 4, add padding
          payload += pad.repeat(4 - (payload.length % 4));
        }
        return JSON.parse(window.atob(payload));
      } else {
        return {};
      }
    },
    expires() {
      // return the token expiration in ms timestamp
      if (this.hasToken) {
        return this.claims.exp * 1000;
      } else {
        return 0;
      }
    },
  },
  data() {
    return {
      // component-level flag if we have trouble getting the token
      tokenRetrievalFailed: false,
    };
  },
  mounted() {
    // retrieve the token if the client is ready
    if (this.readyForCheckOut && !this.hasToken) {
      this.retrieveToken();
    }
  },
  methods: {
    retrieveToken() {
      // anything other than 200 is a fail
      const client = axios.create({
        validateStatus: function (status) {
          return status === 200;
        },
      });
      // set the retry interceptor to retry until success
      axiosRetry(client, {
        retries: maxApiRetries,
        retryDelay: axiosRetry.exponentialDelay,
        retryCondition: function (state) {
          return state.response.status !== 200;
        },
      });
      const resource = `${this.$store.state.publicApiUrl}/generate_token`;
      const eventId = this.$store.state.eventId;
      const requestId = this.$store.state.requestId;
      // send the event ID and request ID in the body
      const body = {
        event_id: eventId,
        request_id: requestId,
      };
      const store = this.$store;
      const component = this;
      client
        .post(resource, body)
        .then(function (response) {
          // save the returned token on success
          store.commit("setToken", response.data.access_token);
        })
        .catch(function (error) {
          // print the error and set the state for display
          console.log(error);
          component.tokenRetrievalFailed = true;
        });
    },
  },
};
</script>
