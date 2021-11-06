<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this is the top-level SFC for the control panel -->

<template>
  <!-- wrap everything in a flexbox with one column -->
  <div class="d-flex flex-column">
    <Banner />
    <!-- respond to configuration events coming upstream -->
    <Configuration @use="configurationUpdate" />
    <p class="m-2">&nbsp;</p>
    <!-- send the configuration downstream -->
    <Counters :configuration="configuration" />
    <p class="m-2">&nbsp;</p>
    <!-- send the configuration downstream -->
    <Controls :configuration="configuration" />
    <p class="m-2">&nbsp;</p>
  </div>
</template>

<script>
import Banner from "./components/Banner.vue";
import Controls from "./components/Controls.vue";
import Configuration from "./components/Configuration.vue";
import Counters from "./components/Counters.vue";
export default {
  name: "App",
  data() {
    // default data model
    return {
      configuration: {
        endpoints: {
          valid: false,
        },
        credentials: {
          valid: false,
        },
        eventData: {
          valid: false,
        },
      },
    };
  },
  created() {
    document.title = "AWS Virtual Waiting Room Control Panel";
  },
  components: { Banner, Configuration, Controls, Counters },
  methods: {
    configurationUpdate(event) {
      // update the configuration used by downstream components
      this.configuration.endpoints = event.endpoints;
      this.configuration.credentials = event.credentials;
      this.configuration.eventData = event.eventData;
    },
  },
};
</script>

<style>
@import "~bootstrap/dist/css/bootstrap.min.css";
</style>
