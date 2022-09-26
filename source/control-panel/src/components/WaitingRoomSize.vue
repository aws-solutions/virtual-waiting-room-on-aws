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
      <span v-if="updateError" class="badge bg-danger mx-2">check configuration</span>
    </p>
    <!-- show the last size counter from the model -->
    <p class="h2 m-2">{{ waitingRoomSize }}</p>
  </div>
</template>

<script>
import { mixin as VueTimers } from "vue-timers";
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
      immediate: true
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
  methods: {
    updateWaitingRoomSize() {
      // only try to update if the configuration objects are valid
      if (
        this.configuration.credentials.valid &&
        this.configuration.endpoints.valid &&
        this.configuration.eventData.valid
      ) {
        const url = `${this.configuration.endpoints.publicApiUrl}/waiting_num?event_id=${this.configuration.eventData.id}`;
        const local_this = this;
        fetch(url, {
          method: "GET"
        }).then(function (response) {
          return response.json();
        }).then(function (json) {
          // update the token value on success
          local_this.waitingRoomSize = json.waiting_num;
          local_this.updateSuccess = true;
          local_this.updateError = false;
        }).catch((error) => {
          console.error(error);
          local_this.updateSuccess = false;
          local_this.updateError = true;
        });
      } else {
        this.updateSuccess = false;
        this.updateError = false;
      }
    }
  }
};
</script>
