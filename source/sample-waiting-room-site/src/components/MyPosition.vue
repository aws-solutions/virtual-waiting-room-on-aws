<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is responsible for adding the user into the waiting
room queue and displaying their position from the request -->

<template>
  <div class="d-flex flex-column border border-2 rounded p-2">
    <!-- display a header with the last connection status -->
    <div class="text-center lead mb-2">My Position</div>
    <div class="mb-2">
      This compartment shows your position in the line while you wait to reserve
      your widget and check out.
    </div>
    <div>
      <!-- display an alert based on the state -->
      <div
        v-if="!hasQueuePosition && !entryFailed"
        class="alert alert-primary"
        role="alert"
      >
        Retrieving your place in line
      </div>
      <div
        v-if="hasQueuePosition && !entryFailed"
        class="alert alert-success"
        role="alert"
      >
        You are number {{ myPosition }} in line
      </div>
      <div v-if="entryFailed" class="alert alert-danger" role="alert">
        An error occurred while entering the line
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
  name: "MyPosition",
  computed: {
    // mix the getters into computed with object spread operator
    ...mapGetters(["hasRequestId", "hasQueuePosition", "hasToken"]),
    // properties for vuex state
    requestId() {
      return this.$store.state.requestId;
    },
    myPosition() {
      return this.$store.state.myPosition;
    },
  },
  data() {
    return {
      // state tracking for entering the queue
      entryFailed: false,
    };
  },
  mounted() {
    // retrieve the request ID if we need it
    if (!this.hasRequestId) {
      this.requestQueuePosition();
    } else {
      // already have the request ID, get the position
      this.retrieveLinePosition();
    }
    // retrieve the queue position after we get the ID
    this.$watch("hasRequestId", this.retrieveLinePosition);
  },
  methods: {
    requestQueuePosition() {
      // use axios and axios-retry to get a request ID
      const client = axios.create({
        validateStatus: function (status) {
          return status === 200;
        },
      });
      // keep retrying until we get a 200 status
      axiosRetry(client, {
        retries: maxApiRetries,
        retryDelay: axiosRetry.exponentialDelay,
        retryCondition: function (state) {
          return state.response.status !== 200;
        },
      });
      const resource = `${this.$store.state.publicApiUrl}/assign_queue_num`;
      // event ID goes into the body of the request
      const body = {
        event_id: this.$store.state.eventId,
      };
      const store = this.$store;
      const component = this;
      // post the request
      client
        .post(resource, body)
        .then(function (response) {
          console.log(response.data);
          // store the request ID returned from API Gateway
          store.commit("setRequestId", response.data.api_request_id);
        })
        .catch(function (error) {
          console.log(error);
          component.entryFailed = true;
        });
    },
    retrieveLinePosition() {
      // retrieve the position in line from the request ID
      const client = axios.create({
        validateStatus: function (status) {
          return status === 200;
        },
      });
      axiosRetry(client, {
        retries: maxApiRetries,
        retryDelay: axiosRetry.exponentialDelay,
        retryCondition: function (state) {
          return state.response.status !== 200;
        },
      });
      const eventId = this.$store.state.eventId;
      const requestId = this.$store.state.requestId;
      // send the event ID and request ID as parameters
      const resource = `${this.$store.state.publicApiUrl}/queue_num?event_id=${eventId}&request_id=${requestId}`;
      const store = this.$store;
      const component = this;
      // we might need to make this request more than once depending
      // on the queue depth and rate of incoming users to the waiting room
      client
        .get(resource)
        .then(function (response) {
          // save the numeric position in the vuex state
          store.commit(
            "setMyPosition",
            Number.parseInt(response.data.queue_number)
          );
        })
        .catch(function (error) {
          // record the failure on the component's state
          console.log(error);
          component.entryFailed = true;
        });
    },
  },
};
</script>
