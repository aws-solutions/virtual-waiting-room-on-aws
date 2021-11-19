<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<template>
  <div>
    <router-view />
  </div>
</template>

<script>
export default {
  name: "App",
  created() {
    document.title = "Sample Waiting Room Site";
  },
  mounted() {
    // add specific query parameters to the vuex store
    if (document.location.search) {
      const parameters = new URLSearchParams(document.location.search);
      this.$store.commit("setLaunchQueryParameters", document.location.search);
      // public api for entering waiting room, checking status, etc.
      const publicApiUrl = parameters.get("publicApiUrl");
      // event ID for this waiting room configuration
      const eventId = parameters.get("eventId");
      // customer's API protected by waiting room authorizer
      const commerceApiUrl = parameters.get("commerceApiUrl");
      // specifies if user should automatically advance out of the waiting room
      const passThru = parameters.get("passThru");
      if (publicApiUrl) {
        this.$store.commit("setPublicApiUrl", publicApiUrl);
      }
      if (eventId) {
        this.$store.commit("setEventId", eventId);
      }
      if (commerceApiUrl) {
        this.$store.commit("setCommerceApiUrl", commerceApiUrl);
      }
      if (passThru) {
        this.$store.commit("setPassThru");
      }
    }
  },
};
</script>

<style>
@import "~bootstrap/dist/css/bootstrap.min.css";
</style>
