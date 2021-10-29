<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- This SFC is responsible collecting endpoints for
making calls to the public and private API -->

<template>
  <!-- wrap everything in a flexbox -->
  <div class="d-flex flex-column">
    <!-- add a label and input for each field -->
    <label class="h6">Public API URL</label>
    <!-- connect each input to the data model and input change handler -->
    <div class="input-group mb-2">
      <input
        type="text"
        class="form-control"
        placeholder="required"
        v-model="formEndpoints.publicApiUrl"
        @input="validateInput"
      />
    </div>
    <label class="h6">Private API URL</label>
    <div class="input-group mb-2">
      <input
        type="text"
        class="form-control"
        placeholder="required"
        v-model="formEndpoints.privateApiUrl"
        @input="validateInput"
      />
    </div>
    <label class="h6">AWS region name</label>
    <div class="input-group mb-2">
      <input
        type="text"
        class="form-control"
        placeholder="required"
        v-model="formEndpoints.regionName"
        @input="validateInput"
      />
    </div>
  </div>
</template>

<script>
import _ from "lodash";
import { reactive } from 'vue'
export default {
  props: ["endpoints"],
  data() {
    // create initial endpoint data from upstream property
    return {
      valid: false,
      formEndpoints: reactive(this.endpoints),
    };
  },
  emits: ["inputChanged"],
  methods: {
    validateInput() {
      // update the valid flag based on tests
      this.valid =
        typeof this.formEndpoints.publicApiUrl === "string" &&
        typeof this.formEndpoints.privateApiUrl === "string" &&
        typeof this.formEndpoints.regionName === "string" &&
        this.formEndpoints.publicApiUrl.length > 0 &&
        this.formEndpoints.privateApiUrl.length > 0 &&
        this.formEndpoints.regionName.length > 0;
      let event = _.cloneDeep(this.formEndpoints);
      event.valid = this.valid;
      // emit an event upstream that endpoints have changed
      this.$emit("inputChanged", event);
    },
  },
};
</script>
