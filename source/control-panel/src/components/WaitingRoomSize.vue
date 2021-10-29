<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is responsible for retrieving and displaying
the number of clients in waiting for tokens -->

<template>
  <div class="d-flex flex-column mb-2 p-4 border border-2 rounded">
    <!-- show a header with the last connection statsus -->
    <p class="lead">
      Waiting Room Size
      <span v-if="updateSuccess" class="badge bg-success mx-2">connected</span>
      <span v-if="updateError" class="badge bg-danger mx-2"
        >check configuration</span
      >
    </p>
    <!-- show the last size counter from the model -->
    <p class="h2 m-2">{{ waitingRoomSize }}</p>
  </div>
</template>

<script>
import { mixin as VueTimers } from "vue-timers";
import axios from "axios";
// fixed update interval of 5 seconds
const UPDATE_INTERVAL_MS = 5000;
export default {
  name: "WaitingRoomSize",
  mixins: [VueTimers],
  props: ["configuration"],
  // use a vue timer mixin to periodically update the counter
  timers: {
    updateWaitingRoomSize: {
      time: UPDATE_INTERVAL_MS,
      autostart: true,
      repeat: true,
    },
  },
  data() {
    // default data model before first API update
    return {
      waitingRoomSize: 0,
      updateSuccess: false,
      updateError: false,
    };
  },
  mounted() {
    // update the counter
    this.updateWaitingRoomSize();
  },
  methods: {
    updateWaitingRoomSize() {
      // only try to update if the configuration objects are valid
      if (
        this.configuration.credentials.valid &&
        this.configuration.endpoints.valid &&
        this.configuration.eventData.valid
      ) {
        const client = axios.create();
        // add the event ID and make a GET request to the public API
        client
          .get(
            `${this.configuration.endpoints.publicApiUrl}/waiting_num?event_id=${this.configuration.eventData.id}`
          )
          .then((res) => {
            // update the counter from the API call
            this.waitingRoomSize = res.data.waiting_num;
            this.updateSuccess = true;
            this.updateError = false;
          })
          .catch(() => {
            this.updateSuccess = false;
            this.updateError = true;
          });
      } else {
        this.updateSuccess = false;
        this.updateError = false;
      }
    },
  },
};
</script>
