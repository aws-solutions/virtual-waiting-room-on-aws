<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is responsible for displaying the result of the secured
API call to purchase/reserve the widget -->

<template>
  <div class="d-flex flex-column border border-2 border-dark rounded p-2">
    <!-- display a header with the last connection status -->
    <div class="text-center lead mb-2">Purchase Receipt</div>
    <div class="mb-2">This compartment shows the receipt from your purchase.</div>
    <div>
      <div
        v-if="!receipt"
        class="alert alert-secondary"
        role="alert"
      >
        Waiting for your transaction to complete
      </div>
      <div
        v-if="receipt"
        class="alert alert-success"
        role="alert"
      >
        Complete!
      </div>
      <small v-if="receipt">
        {{ receipt }}
      </small>
    </div>
  </div>
</template>

<script>
export default {
  name: "PurchaseReceipt",
  computed: {
    // response from the secure API is stored on the vuex state
    receipt() {
      return this.$store.state.receipt;
    },
  },
};
</script>
