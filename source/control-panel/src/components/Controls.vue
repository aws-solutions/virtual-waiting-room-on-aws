<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- This SFC is responsible for containing the control components -->

<template>
<!-- add child components to a flexbox -->
  <div class="d-flex flex-column w-50 mx-auto">
    <!-- pass the default configuration property down to the children -->
    <IncrementServingCounter :configuration="configuration" />
    <ResetWaitingRoom :configuration="configuration" />
  </div>
</template>

<script>
import IncrementServingCounter from "./IncrementServingCounter.vue";
import ResetWaitingRoom from "./ResetWaitingRoom.vue";
export default {
  name: "Controls",
  components: { IncrementServingCounter, ResetWaitingRoom },
  props: ["configuration"],
};
</script>
