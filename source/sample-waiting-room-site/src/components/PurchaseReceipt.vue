<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is responsible for retrieving and displaying
the current serving counter of the waiting room -->

<template>
  <div class="d-flex flex-column border border-2 rounded p-2">
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
import { mapGetters } from "vuex";
export default {
  name: "PurchaseReceipt",
  computed: {
    // mix the getters into computed with object spread operator
    ...mapGetters(["hasRequestId", "hasQueuePosition", "hasToken"]),
    myPosition() {
      return this.$store.state.myPosition;
    },
    queuePosition() {
      return this.$store.state.queuePosition;
    },
    commerceApiUrl() {
      return this.$store.state.commerceApiUrl;
    },
    token() {
      return this.$store.state.token;
    },
    receipt() {
      return this.$store.state.receipt;
    },
    readyForCheckOut() {
      return this.hasRequestId && this.myPosition <= this.queuePosition;
    },
  },
};
</script>
