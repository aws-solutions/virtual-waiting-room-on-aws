<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is responsible for providing and 'big yellow button'
for resetting the waiting room to a default state -->

<template>
  <div class="d-flex flex-column mb-2 p-4 border border-2 rounded">
    <!-- add the header with a status of the last connection attempt -->
    <p class="lead">
      Reset Waiting Room
      <span v-if="updateSuccess" class="badge bg-success mx-2"
        >reset in progress</span
      >
      <span v-if="updateError" class="badge bg-danger mx-2"
        >check configuration</span
      >
    </p>
    <div class="d-flex flex-row">
      <!-- add a warning message and a button to initiate the reset -->
      <div class="m-2 mx-5">
        Warning: This will reset the waiting room counters and clear all session
        tokens from the database.
        After resetting the waiting room, some API requests may be return an
        error for up to 30 seconds.
      </div>
      <!-- enable the button if the configuration objects are valid -->
      <button
        type="button"
        class="btn btn-sm btn-warning rounded m-1 p-3"
        v-on:click="resetWaitingRoom"
        v-bind:disabled="
          !(
            configuration.credentials.valid &&
            configuration.endpoints.valid &&
            configuration.eventData.valid
          )
        "
      >
        Reset
      </button>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { aws4Interceptor } from "aws4-axios";
export default {
  name: "IncrementServingCounter",
  props: ["configuration"],
  data() {
    // default data model
    return {
      updateSuccess: false,
      updateError: false,
    };
  },
  methods: {
    resetWaitingRoom() {
      // reset the status values
      this.updateSuccess = false;
      this.updateError = false;
      const client = axios.create();
      // sign the request with the keys from the configuration object
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
      // add the event ID to the body
      let body = {
        event_id: this.configuration.eventData.id,
      };
      // post it to the private API
      client
        .post(
          `${this.configuration.endpoints.privateApiUrl}/reset_initial_state`,
          body
        )
        .then(() => {
          this.updateSuccess = true;
          this.updateError = false;
        })
        .catch(() => {
          this.updateSuccess = false;
          this.updateError = true;
        });
    },
  },
};
</script>
