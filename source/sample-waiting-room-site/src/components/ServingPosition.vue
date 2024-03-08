<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is responsible for retrieving and displaying
the current serving counter of the waiting room -->

<template>
  <div class="d-flex flex-column border border-2 rounded p-2">
    <!-- display a header with the last connection status -->
    <div class="text-center lead mb-2">Serving Counter Number</div>
    <div class="mb-2">
      This compartment shows the current serving counter number.
    </div>
    <div>
      <!-- show an alert based on the state -->
      <div
        v-if="!apiFailed && queuePosition < myPosition"
        class="alert alert-secondary"
        role="alert"
      >
        Counter {{ queuePosition }} and lower are being served
      </div>
      <div
        v-if="!apiFailed && queuePosition >= myPosition"
        class="alert alert-warning"
        role="alert"
      >
        Counter {{ queuePosition }} and lower are being served
      </div>
      <div v-if="apiFailed" class="alert alert-danger" role="alert">
        An error occurred while updating
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from "vuex";
import axios from "axios";
import axiosRetry from "axios-retry";
import { mixin as VueTimers } from "vue-timers";
const UPDATE_INTERVAL_MS = 3000;
const maxApiRetries = 10;
export default {
  name: "ServingPosition",
  mixins: [VueTimers],
  // use a vue timer for periodic updates
  timers: {
    updateServingPosition: {
      time: UPDATE_INTERVAL_MS,
      autostart: true,
      repeat: true,
      immediate: true,
    },
  },
  data() {
    return {
      apiFailed: false,
    };
  },
  // stop the timer when we leave this component
  unmounted() {
    if (this.timers.updateServingPosition.isRunning) {
      this.$timer.stop("updateServingPosition");
    }
  },
  // start the timer when we re-enter this component
  mounted() {
    if (!this.timers.updateServingPosition.isRunning) {
      this.$timer.start("updateServingPosition");
    }
  },
  computed: {
    // mix the getters into computed with object spread operator
    ...mapGetters(["hasRequestId", "hasQueuePosition", "hasToken"]),
    requestId() {
      return this.$store.state.requestId;
    },
    myPosition() {
      return this.$store.state.myPosition;
    },
    queuePosition() {
      return this.$store.state.queuePosition;
    },
  },
  methods: {
    updateServingPosition() {
      // use retry on this API call
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
      // include the event ID as a parameter on the request
      const eventId = this.$store.state.eventId;
      const resource = `${this.$store.state.publicApiUrl}/serving_num?event_id=${eventId}`;
      const store = this.$store;
      const component = this;
      // send the request
      client
        .get(resource)
        .then(function (response) {
          component.apiFailed = false;
          // store the counter value 
          store.commit(
            "setQueuePosition",
            Number.parseInt(response.data.serving_counter)
          );
        })
        .catch(function (error) {
          // print the error, stop the update timer and
          // update the state locally on this component
          console.log(error);
          component.apiFailed = true;
          component.$timer.stop("updateServingPosition");
        });
    },
  },
};
</script>
