<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!--
This SFC is responsible for containing each of the configuration
components, combining their output and emitting an event to the parent
and storing the configuration on the seesion when the use button is clicked.
-->

<template>
  <!-- contain everything in a flexbox -->
  <div class="d-flex flex-column w-50 mx-auto p-4 border border-2 rounded">
    <p class="lead">Configuration</p>
    <Credentials
      @inputChanged="credentialsChangeHandler"
      :credentials="credentials"
    />
    <div class="my-3">&nbsp;</div>
    <Endpoints @inputChanged="endpointsChangeHandler" :endpoints="endpoints" />
    <div class="my-3">&nbsp;</div>
    <Event @inputChanged="eventDataChangeHandler" :event-data="eventData" />
    <div class="d-flex flex-row-reverse">
      <!-- show revert changes button if something has changed -->
      <button
        type="button"
        class="btn btn-sm btn-primary btn-warning rounded m-1"
        v-on:click="revert"
        v-bind:disabled="!changed"
      >
        Revert
      </button>
      <!-- show the save button if the inputs are valid and have changed -->
      <button
        type="button"
        class="btn btn-sm btn-primary btn-success rounded m-1"
        v-on:click="use"
        v-bind:disabled="
          !(credentials.valid && endpoints.valid && eventData.valid && changed)
        "
      >
        Use
      </button>
    </div>
  </div>
</template>

<script>
import Credentials from "./Credentials.vue";
import Endpoints from "./Endpoints.vue";
import Event from "./Event.vue";
import _ from "lodash";
const sessionKey = "configuration";
export default {
  name: "Configuration",
  emits: ["use"],
  components: { Credentials, Endpoints, Event },
  data() {
    // try to restore the configuration data from the session
    let configuration = this.restore();
    return configuration;
  },
  mounted() {
    // emit the event after mount if the restored credentials are valid
    if (
      this.credentials.valid &&
      this.endpoints.valid &&
      this.eventData.valid
    ) {
      this.$emit("use", {
        // cloning strips the reactive proxy if it exists
        credentials: _.cloneDeep(this.credentials),
        endpoints: _.cloneDeep(this.endpoints),
        eventData: _.cloneDeep(this.eventData),
      });
    }
  },
  methods: {
    revert() {
      // restore the previously saved configuration
      let stored = this.restore();
      this.credentials.accessKey = stored.credentials.accessKey;
      this.credentials.secretAccessKey = stored.credentials.secretAccessKey;
      this.credentials.sessionToken = stored.credentials.sessionToken;
      this.credentials.valid = true;
      this.endpoints.publicApiUrl = stored.endpoints.publicApiUrl;
      this.endpoints.privateApiUrl = stored.endpoints.privateApiUrl;
      this.endpoints.regionName = stored.endpoints.regionName;
      this.endpoints.valid = true;
      this.eventData.id = stored.eventData.id;
      this.eventData.valid = true;
      this.changed = false;
    },
    restore() {
      // return the stored or an empty configuration object
      let data = window.sessionStorage.getItem(sessionKey);
      let configuration = {
        changed: false,
      };
      if (data) {
        let stored = JSON.parse(data);
        configuration.credentials = stored.credentials;
        configuration.endpoints = stored.endpoints;
        configuration.eventData = stored.eventData;
      } else {
        configuration.credentials = {
          accessKey: "",
          secretAccessKey: "",
          sessionToken: "",
          valid: false,
        };
        configuration.endpoints = {
          publicApiUrl: "",
          privateApiUrl: "",
          regionName: "",
          valid: false,
        };
        configuration.eventData = {
          id: "",
          valid: false,
        };
      }
      return configuration;
    },
    use() {
      // called from the 'use' button
      let data = {
        // strip the reactive proxy from the object
        credentials: _.cloneDeep(this.credentials),
        endpoints: _.cloneDeep(this.endpoints),
        eventData: _.cloneDeep(this.eventData),
      };
      // store the data on the browser session
      window.sessionStorage.setItem(sessionKey, JSON.stringify(data));
      // no longer changed
      this.changed = false;
      // emit the event upstream
      this.$emit("use", data);
    },
    credentialsChangeHandler(event) {
      // update the changed flag
      this.changed = true;
      if (event.valid) {
        // keep the credentials if they're valid
        this.credentials.accessKey = event.accessKey;
        this.credentials.secretAccessKey = event.secretAccessKey;
        this.credentials.sessionToken = event.sessionToken;
      }
    },
    endpointsChangeHandler(event) {
      // update the changed flag
      this.changed = true;
      if (event.valid) {
        // keep the endpoints if they're valid
        this.endpoints.publicApiUrl = event.publicApiUrl;
        this.endpoints.privateApiUrl = event.privateApiUrl;
        this.endpoints.regionName = event.regionName;
      }
    },
    eventDataChangeHandler(event) {
      // update the changed flag
      this.changed = true;
      if (event.valid) {
        // keep the event data if it's valid
        this.eventData.id = event.id;
      }
    },
  },
};
</script>
