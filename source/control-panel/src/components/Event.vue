<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is responsible for collecting the event ID from the user -->

<template>
  <!-- wrap everything in a flexbox -->
  <div class="d-flex flex-column">
    <label class="h6">Event ID</label>
    <!-- connect the input to the data model and input change handler -->
    <div class="input-group mb-2">
      <input
        type="text"
        class="form-control"
        placeholder="required"
        v-model="eventData.id"
        @input="validateInput"
      />
    </div>
  </div>
</template>

<script>
import _ from "lodash";
import { reactive } from "vue";
export default {
  props: ["event-data"],
  data() {
    // create the data model from the default property value
    return {
      valid: false,
      localEventData: reactive(this.eventData),
    };
  },
  emits: ["inputChanged"],
  mounted() {
    this.validateInput();
  },
  methods: {
    validateInput() {
      // update the valid flag based on test results
      this.valid =
        typeof this.localEventData.id === "string" &&
        this.localEventData.id.length > 0;
      let event = _.cloneDeep(this.localEventData);
      event.valid = this.valid;
      // emit an event upstream the event ID has changed
      this.$emit("inputChanged", event);
    },
  },
};
</script>
