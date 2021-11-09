<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<template>
  <div class="d-flex flex-column w-50 mx-auto p-4 border border-2 rounded mt-2">
    <div class="text-center lead mb-2">Home</div>
    <div class="text-center mb-2">Welcome to the store!</div>
    <div v-if="!readyForCheckOut" class="text-center mb-2">
      <div class="mb-2">Click below to get in line to reserve your widget.</div>
      <div>
        <button
          @click="handleReserveButtonClick"
          type="button"
          class="btn btn-primary"
        >
          Reserve
        </button>
      </div>
    </div>
    <div v-if="readyForCheckOut" class="text-center mb-2">
      <div class="mb-2">Your place in line is now allowed to Check Out and finish.</div>
      <div>
        <button
          @click="handleCheckOutButtonClick"
          type="button"
          class="btn btn-primary"
        >
          Check out
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from "vuex";
export default {
  name: "Home",
  computed: {
    // mix the getters into computed with object spread operator
    ...mapGetters(["hasRequestId", "hasQueuePosition", "hasToken"]),
    myPosition() {
      return this.$store.state.myPosition;
    },
    queuePosition() {
      return this.$store.state.queuePosition;
    },
    readyForCheckOut() {
      return this.hasRequestId && (this.myPosition <= this.queuePosition);
    },
  },
  // props: ["model"],
  methods: {
    handleReserveButtonClick() {
      this.$router.push("/waitingroom");
    },
    handleCheckOutButtonClick() {
      this.$router.push("/checkout");
    },
  },
};
</script>
