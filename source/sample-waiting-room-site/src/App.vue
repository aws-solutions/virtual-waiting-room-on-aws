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
  mounted() {
    // add specific query parameters to the vuex store
    if (document.location.search) {
      const parameters = new URLSearchParams(document.location.search);
      const publicApiUrl = parameters.get("publicApiUrl");
      const eventId = parameters.get("eventId");
      const commerceApiUrl = parameters.get("commerceApiUrl");
      this.$store.commit("setLaunchQueryParameters", document.location.search);
      if (publicApiUrl) {
        this.$store.commit("setPublicApiUrl", publicApiUrl);
      }
      if (eventId) {
        this.$store.commit("setEventId", eventId);
      }
      if (commerceApiUrl) {
        this.$store.commit("setCommerceApiUrl", commerceApiUrl);
      }
    }
  },
};
</script>

<style>
@import "~bootstrap/dist/css/bootstrap.min.css";
</style>
