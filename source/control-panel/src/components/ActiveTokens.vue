<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!--
This SFC is responsible for retrieving the number of active tokens from the
private API and renders a flexbox with the value. The configuration property
is an object containing the endpoints and credentials for the API.
-->

<template>
  <!--
  Draw the current value in a flexbox with a border,
  including connection status if we've tried to connect.
-->
  <div class="d-flex flex-column mb-2 p-4 border border-2 rounded">
    <p class="lead">
      Active Tokens
      <span v-if="updateSuccess" class="badge bg-success mx-2">connected</span>
      <span v-if="updateError" class="badge bg-danger mx-2"
        >check configuration</span
      >
    </p>
    <p class="h2 m-2">{{ activeTokens }}</p>
  </div>
</template>

<script>
// use the timer mixin for periodic API checks
import { mixin as VueTimers } from "vue-timers";
import axios from "axios";
import { aws4Interceptor } from "aws4-axios";
// update interval for the API call
const UPDATE_INTERVAL_MS = 5000;
export default {
  name: "ActiveTokens",
  mixins: [VueTimers],
  props: ["configuration"],
  // timer starts immediately and repeats
  timers: {
    updateActiveTokenCount: {
      time: UPDATE_INTERVAL_MS,
      autostart: true,
      repeat: true,
      immediate: true
    },
  },
  data() {
    return {
      activeTokens: 0,
      updateSuccess: false,
      updateError: false,
    };
  },
  methods: {
    updateActiveTokenCount() {
      // only try this if the credentials in the properties are marked valid
      if (
        this.configuration.credentials.valid &&
        this.configuration.endpoints.valid &&
        this.configuration.eventData.valid
      ) {
        // update the serving counter
        const client = axios.create();
        // use the interceptor with keys to sign the API request
        const interceptor = aws4Interceptor(
          {
            region: this.configuration.endpoints.regionName,
            service: "execute-api",
          },
          {
            accessKeyId: this.configuration.credentials.accessKey,
            secretAccessKey: this.configuration.credentials.secretAccessKey,
            sessionToken: this.configuration.credentials.sessionToken,
          }
        );
        client.interceptors.request.use(interceptor);
        // add the event ID to the query parameters
        client
          .get(
            `${this.configuration.endpoints.privateApiUrl}/num_active_tokens?event_id=${this.configuration.eventData.id}`
          )
          .then((res) => {
            // update the token value on success
            this.activeTokens = res.data.active_tokens;
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
