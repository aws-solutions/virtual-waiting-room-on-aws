<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is responsible for retrieving and presenting the expired token count -->

<template>
  <!-- wrap everything in the flexbox -->
  <div class="d-flex flex-column mb-2 p-4 border border-2 rounded">
    <p class="lead">
      <!-- show the last connect status -->
      Expired Tokens
      <span v-if="updateSuccess" class="badge bg-success mx-2">connected</span>
      <span v-if="updateError" class="badge bg-danger mx-2">check configuration</span>
    </p>
    <!-- show the last expired tokens count retrieved -->
    <p class="h2 m-2">{{ expiredTokens }}</p>
  </div>
</template>

<script>
import { mixin as VueTimers } from "vue-timers";
import { AwsClient } from 'aws4fetch';
// longer update interval since this call is more expensive
const UPDATE_INTERVAL_MS = 30000;
export default {
  name: "ExpiredTokens",
  mixins: [VueTimers],
  props: ["configuration"],
  // use the vue timers mixin
  timers: {
    updateWaitingRoomSize: {
      time: UPDATE_INTERVAL_MS,
      autostart: true,
      repeat: true,
      immediate: true
    },
  },
  data() {
    // default data model with no value or update status
    return {
      expiredTokens: 0,
      updateSuccess: false,
      updateError: false,
    };
  },
  methods: {
    updateWaitingRoomSize() {
      // continue if the configuration is valid
      if (
        this.configuration.credentials.valid &&
        this.configuration.endpoints.valid &&
        this.configuration.eventData.valid
      ) {
        const aws = new AwsClient({
          accessKeyId: this.configuration.credentials.accessKey,
          secretAccessKey: this.configuration.credentials.secretAccessKey,
          sessionToken: this.configuration.credentials.sessionToken,
          service: "execute-api",
          region: this.configuration.endpoints.regionName
        });
        const url = `${this.configuration.endpoints.privateApiUrl}/expired_tokens?event_id=${this.configuration.eventData.id}`;
        const local_this = this;
        aws.fetch(url, {
          method: "GET"
        }).then(function (response) {
          return response.json();
        }).then(function (json) {
          // update the expired token count in the data model
          const expiredTokens = json.reduce(
            (accumulator, currentValue) => Array.isArray(currentValue) ? accumulator  + currentValue.length : accumulator + 1,
            0
          );
          local_this.expiredTokens = expiredTokens;
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
    },
  },
};
</script>
