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
      <span v-if="updateError" class="badge bg-danger mx-2">check configuration</span>
    </p>
    <!-- display the serving counter value from the model -->
    <p class="h2 m-2">
      {{ servingCounter }}
      <span class="h5" v-if="availableCounter === 0">(No servings are currently available)</span>
      <span class="h5" v-if="availableCounter < 0">(There are {{-1 * availableCounter}} waiting with no available serving capacity)</span>
      <span class="h5" v-if="availableCounter > 0">(There are currently {{availableCounter}} servings available)</span>
    </p>
  </div>
</template>

<script>
import { mixin as VueTimers } from "vue-timers";
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
      availableCounter: 0,
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
        const local_this = this;
        const url = `${this.configuration.endpoints.publicApiUrl}/serving_num?event_id=${this.configuration.eventData.id}`;
        fetch(url, {
          method: "GET"
        }).then(function (response) {
          return response.json();
        }).then(function (json) {
          // update the token value on success
          local_this.servingCounter = json.serving_counter;
          local_this.$store.commit("setServingCounter", json.serving_counter);
          local_this.availableCounter = local_this.$store.getters.getAvailableCounter
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
