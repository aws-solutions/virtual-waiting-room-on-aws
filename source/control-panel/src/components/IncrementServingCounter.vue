<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is responsible for providing controls to
increment the serving counter of the waiting room -->

<template>
<!-- wrap everything in a flexbox -->
  <div class="d-flex flex-column mb-2 p-4 border border-2 rounded">
    <p class="lead">
      Increment Serving Counter
      <!-- show the last connect status if available -->
      <span v-if="updateSuccess" class="badge bg-success mx-2">updated</span>
      <span v-if="updateError" class="badge bg-danger mx-2"
        >check configuration</span
      >
    </p>
    <p>
      <!-- add a label and slider for the increment value -->
      <label class="form-label"></label>
      <!-- connect the slider to the data model and input handler -->
      <input
        type="range"
        class="form-range"
        min="1"
        max="1000"
        step="1"
        v-model="increment"
        @input="newValue = true"
      />
    </p>
    <div class="d-flex flex-row-reverse">
      <!-- enable change the button if the configuration is valid -->
      <button
        type="button"
        class="btn btn-sm btn-primary rounded m-1 p-3"
        v-on:click="changeCounter"
        v-bind:disabled="
          !(
            configuration.credentials.valid &&
            configuration.endpoints.valid &&
            configuration.eventData.valid
          )
        "
      >
        Change
      </button>
      <!-- display the slider value -->
      <div class="m-2 mx-5">
        Increment by: <span class="mx-2 h3">{{ increment }}</span>
      </div>
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
      increment: 100,
      newValue: true,
      updateSuccess: false,
      updateError: false,
    };
  },
  methods: {
    changeCounter() {
      // change the data model state
      this.newValue = false;
      this.updateSuccess = false;
      this.updateError = false;
      // update the serving counter
      const client = axios.create();
      // sign the API call with the configuration's keys
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
      // event ID goes into the body data
      let body = {
        event_id: this.configuration.eventData.id,
        increment_by: Number.parseInt(this.increment),
      };
      // make the request via POST
      client
        .post(
          `${this.configuration.endpoints.privateApiUrl}/increment_serving_counter`,
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
