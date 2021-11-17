<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is a view for checking out through the secured API -->

<template>
  <div class="d-flex flex-column w-50 mx-auto border border-dark border-2 rounded mt-2 bg-secondary text-white">
    <div class="text-center lead mb-2">Secure Check Out System</div>
    <div class="text-center mb-2">
      You can complete the purchase of your widget now! This component will
      request an authentication token from the AWS Virtual Waiting Room API and
      call the site's protected API to finish.
    </div>
    <div class="d-flex flex-column justify-content-center">
      <AuthorizationToken class="w-75 mx-auto m-2" />
    </div>
    <div class="d-flex flex-row">
      <CompletePurchase class="w-50 m-2" />
      <PurchaseReceipt class="w-50 m-2" />
    </div>
        <div class="d-flex flex-row mx-auto mb-2">
      <button
        type="button"
        class="btn btn-primary m-2"
        v-on:click="restartWaitingRoom"
      >
        Start over
      </button>
    </div>

  </div>
</template>

<script>
import AuthorizationToken from "@/components/AuthorizationToken.vue";
import CompletePurchase from "@/components/CompletePurchase.vue";
import PurchaseReceipt from "@/components/PurchaseReceipt.vue";
export default {
  name: "CheckOut",
  methods: {
    restartWaitingRoom() {
      // add the query parameters from the launch page
      const query = this.$store.state.launchQueryParameters;
      // reload
      window.location = `index.html${query}`;
    }
  },
  components: {
    AuthorizationToken,
    CompletePurchase,
    PurchaseReceipt
  },
};
</script>
