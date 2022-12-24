<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- This SFC is responsible for showing the remaining counter -->

<template>
  <!-- wrap everything in the flexbox -->
  <div class="d-flex flex-column mb-2 p-4 border border-2 rounded">
    <p class="lead">
      <!-- show the last connect status -->
      Remaining Counter
    </p>
    <!-- show the last expired tokens count retrieved -->
    <p class="h2 m-2">{{ getRemainingCounter }}</p>
  </div>
</template>

<script>
import { mapGetters } from "vuex";
export default {
  name: "RemainingCounter",
  computed: {
    ...mapGetters(["getRemainingCounter"]),
  },
};
</script>
