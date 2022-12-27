<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- This SFC is responsible for containing the various counter child components -->

<template>
  <div class="d-flex flex-column w-50 mx-auto">
    <!-- pass the default configuration down to the children -->
    <ServingCounter :configuration="configuration" />
    <WaitingRoomSize :configuration="configuration" />
    <ActiveTokens :configuration="configuration" />
    <ExpiredTokens :configuration="configuration" />
    <RemainingCounter :configuration="configuration" />
  </div>
</template>

<script>
import ActiveTokens from "./ActiveTokens.vue";
import ExpiredTokens from "./ExpiredTokens.vue";
import ServingCounter from "./ServingCounter.vue";
import WaitingRoomSize from "./WaitingRoomSize.vue";
import RemainingCounter from "./RemainingCounter.vue";
export default {
  name: "Counters",
  components: { ActiveTokens, ExpiredTokens, ServingCounter, WaitingRoomSize, RemainingCounter },
  props: ["configuration"],
};
</script>
