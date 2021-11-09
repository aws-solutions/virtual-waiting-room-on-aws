<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is responsible for retrieving and displaying
the current serving counter of the waiting room -->

<template>
  <div class="d-flex flex-column mb-2 p-4 border border-2 rounded">
    <!-- display a header with the last connection status -->
    <p class="lead">
      Serving Counter
      <span v-if="updateSuccess" class="badge bg-success mx-2">connected</span>
      <span v-if="updateError" class="badge bg-danger mx-2"
        >check configuration</span
      >
    </p>
    <!-- display the serving counter value from the model -->
    <p class="h2 m-2">{{ servingCounter }}</p>
  </div>
</template>

<script>
import { mixin as VueTimers } from "vue-timers";
import axios from "axios";
// interval for the API call
const UPDATE_INTERVAL_MS = 5000;
export default {
  name: "ServingCounter",
  mixins: [VueTimers],
  // endpoint configuration comes from upstream as a property
  props: ["configuration"],
  // use a vue timer for periodic updates
  timers: {
    updateServingCounter: {
      time: UPDATE_INTERVAL_MS,
      autostart: true,
      repeat: true,
      immediate: true
    },
  },
  data() {
    // default data model before first update attempt
    return {
      servingCounter: 0,
      updateSuccess: false,
      updateError: false,
    };
  },
  methods: {
    updateServingCounter() {
      // only update if the configuration objects are valid
      if (
        this.configuration.credentials.valid &&
        this.configuration.endpoints.valid &&
        this.configuration.eventData.valid
      ) {
        const client = axios.create();
        // add the event ID to the query parameters and GET from the public API
        client
          .get(
            `${this.configuration.endpoints.publicApiUrl}/serving_num?event_id=${this.configuration.eventData.id}`
          )
          .then((res) => {
            // update the model with the latest serving counter
            this.servingCounter = res.data.serving_counter;
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
