<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is responsible for retrieving and displaying
the number of users currently in the waiting room -->

<template>
  <div class="d-flex flex-column border border-2 rounded p-2">
    <div class="text-center lead mb-2">Waiting Room Size</div>
    <div class="mb-2">
      This compartment shows the number of people including you waiting
      to check out.
    </div>
    <div>
      <!-- display an alert with the count or an error message -->
      <div v-if="!apiFailed" class="alert alert-secondary" role="alert">
        {{ waitingRoomSize }} people are in the waiting room
      </div>
      <div v-if="apiFailed" class="alert alert-danger" role="alert">
        An error occurred while updating
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import axiosRetry from "axios-retry";
import { mixin as VueTimers } from "vue-timers";
const UPDATE_INTERVAL_MS = 3000;
const maxApiRetries = 10;
export default {
  name: "WaitingRoomSize",
  mixins: [VueTimers],
  // use a vue timer for periodic updates
  timers: {
    updateWaitingRoomSite: {
      time: UPDATE_INTERVAL_MS,
      autostart: true,
      repeat: true,
      immediate: true,
    },
  },
  // stop and restart the timers if we leave and re-enter this view
  unmounted() {
    if (this.timers.updateWaitingRoomSite.isRunning) {
      this.$timer.stop("updateWaitingRoomSite");
    }
  },
  mounted() {
    if (!this.timers.updateWaitingRoomSite.isRunning) {
      this.$timer.start("updateWaitingRoomSite");
    }
  },
  data() {
    // track local state on the component
    return {
      apiFailed: false,
      waitingRoomSize: 0,
    };
  },
  methods: {
    updateWaitingRoomSite() {
      // retry until we get a 200 status back, or we've tried enough times
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
      // include the event ID on the request
      const eventId = this.$store.state.eventId;
      const resource = `${this.$store.state.publicApiUrl}/waiting_num?event_id=${eventId}`;
      const component = this;
      client
        .get(resource)
        .then(function (response) {
          // keep the waiting room size locally
          component.apiFailed = false;
          component.waitingRoomSize = Number.parseInt(
            response.data.waiting_num
          );
        })
        .catch(function (error) {
          // print the error and stop the timer
          console.log(error);
          component.apiFailed = true;
          component.$timer.stop("updateWaitingRoomSite");
        });
    },
  },
};
</script>
