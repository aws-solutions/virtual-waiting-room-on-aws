<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is responsible for retrieving and displaying
the current serving counter of the waiting room -->

<template>
  <div class="d-flex flex-column border border-2 rounded p-2">
    <!-- display a header with the last connection status -->
    <div class="text-center lead mb-2">My Position</div>
    <div class="mb-2">
      This compartment shows your position in the line while you wait to reserve
      your widget and check out.
    </div>
    <div>
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
    requestId() {
      return this.$store.state.requestId;
    },
    myPosition() {
      return this.$store.state.myPosition;
    },
  },
  data() {
    return {
      entryFailed: false,
    };
  },
  mounted() {
    if (!this.hasRequestId) {
      this.requestQueuePosition();
    }
    this.$watch("hasRequestId", this.retrieveLinePosition);
  },
  methods: {
    requestQueuePosition() {
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
      const resource = `${this.$store.state.publicApiUrl}/assign_queue_num`;
      const body = {
        event_id: this.$store.state.eventId,
      };
      const store = this.$store;
      const component = this;
      client
        .post(resource, body)
        .then(function (response) {
          store.commit("setRequestId", response.data.api_request_id);
        })
        .catch(function (error) {
          console.log(error);
          component.entryFailed = true;
        });
    },
    retrieveLinePosition() {
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
      // const eventId = this.$store.state.eventId;
      const eventId = this.$store.state.eventId;
      const requestId = this.$store.state.requestId;
      const resource = `${this.$store.state.publicApiUrl}/queue_num?event_id=${eventId}&request_id=${requestId}`;
      const store = this.$store;
      const component = this;
      client
        .get(resource)
        .then(function (response) {
          store.commit(
            "setMyPosition",
            Number.parseInt(response.data.queue_number)
          );
        })
        .catch(function (error) {
          console.log(error);
          component.entryFailed = true;
        });
    },
  },
};
</script>
