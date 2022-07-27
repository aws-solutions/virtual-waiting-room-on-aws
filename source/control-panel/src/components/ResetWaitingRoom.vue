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
      <span v-if="updateSuccess" class="badge bg-success mx-2">reset in progress</span>
      <span v-if="updateError" class="badge bg-danger mx-2">check configuration</span>
    </p>
    <div class="d-flex flex-row">
      <!-- add a warning message and a button to initiate the reset -->
      <div class="m-2 mx-5">
        Warning: This will reset the waiting room counters and clear all session
        tokens from the database.
        After resetting the waiting room, some API requests may return an
        error for several seconds and in some cases a few minutes.
      </div>
      <!-- enable the button if the configuration objects are valid -->
      <button type="button" class="btn btn-sm btn-warning rounded m-1 p-3" v-on:click="resetWaitingRoom"
        v-bind:disabled="
          !(
            configuration.credentials.valid &&
            configuration.endpoints.valid &&
            configuration.eventData.valid
          )
        ">
        Reset
      </button>
    </div>
  </div>
</template>

<script>
import { AwsClient } from 'aws4fetch';
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
      // configure the request signer
      const aws = new AwsClient({
        accessKeyId: this.configuration.credentials.accessKey,
        secretAccessKey: this.configuration.credentials.secretAccessKey,
        sessionToken: this.configuration.credentials.sessionToken,
        service: "execute-api",
        region: this.configuration.endpoints.regionName
      });
      const url = `${this.configuration.endpoints.privateApiUrl}/reset_initial_state`;
      // add the event ID to the body
      let body = {
        event_id: this.configuration.eventData.id,
      };
      // post it to the private API
      const local_this = this;
      aws.fetch(url, {
        method: "POST",
        headers: {},
        body: body
      }).then(function (response) {
        return response.json();
      }).then(function () {
        local_this.updateSuccess = true;
        local_this.updateError = false;
      }).catch((error) => {
        console.error(error);
        local_this.updateSuccess = false;
        local_this.updateError = true;
      });
    },
  },
};
</script>
