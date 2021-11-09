<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is responsible for retrieving and displaying
the current serving counter of the waiting room -->

<template>
  <div class="d-flex flex-column border border-2 rounded p-2">
    <!-- display a header with the last connection status -->
    <div class="text-center lead mb-2">Complete Purchase</div>
    <div class="mb-2">This compartment shows the status of your purchase.</div>
    <div>
      <div
        v-if="!hasToken && readyForCheckOut"
        class="alert alert-secondary"
        role="alert"
      >
        Waiting for your transaction token
      </div>
      <div
        v-if="hasToken && !purchaseFailed"
        class="alert alert-warning"
        role="alert"
      >
        You are ready to purchase
      </div>
      <div v-if="purchaseFailed" class="alert alert-danger" role="alert">
        An error occurred during the transaction
      </div>
    </div>
    <div class="d-flex flex-row mx-auto mb-2">
      <button
        type="button"
        class="btn btn-success m-2"
        v-on:click="completePurchase"
        v-bind:disabled="!hasToken || purchaseFailed || receipt"
      >
        {{ hasToken ? "Purchase now" : "Waiting for transaction token" }}
      </button>
    </div>
  </div>
</template>

<script>
import { mapGetters } from "vuex";
import axios from "axios";
import axiosRetry from "axios-retry";
const maxApiRetries = 3;
export default {
  name: "AuthorizationToken",
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
  data() {
    return {
      purchaseFailed: false,
    };
  },
  methods: {
    completePurchase() {
      const client = axios.create({
        validateStatus: function (status) {
          return status === 200;
        },
      });
      axiosRetry(client, {
        retries: maxApiRetries,
        retryDelay: axiosRetry.exponentialDelay,
        retryCondition: function (state) {
          return state.response.status !== 200;
        },
      });
      const resource = `${this.commerceApiUrl}/checkout`;
      const headers = {
        "Content-Type": "application/json",
        Authorization: this.token,
      };
      const store = this.$store;
      const component = this;
      client
        .get(resource, {
          headers: headers,
        })
        .then(function (response) {
          console.log(response);
          store.commit("setReceipt", response.data);
        })
        .catch(function (error) {
          console.log(error);
          component.purchaseFailed = true;
        });
    },
  },
};
</script>
