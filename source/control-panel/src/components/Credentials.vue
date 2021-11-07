<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- This SFC is responsible collecting credentials for making calls to the private API -->

<template>
  <!-- create a label and input for access key, secret key and session token -->
  <div class="d-flex flex-column">
    <label class="h6">Access key</label>
    <div class="input-group mb-2">
      <!-- connect each input to the component's data and provide an input change handler -->
      <input
        type="text"
        class="form-control"
        placeholder="required"
        v-model="formCredentials.accessKey"
        @input="validateInput"
      />
    </div>
    <label class="h6">Secret access key</label>
    <div class="input-group mb-2">
      <input
        type="password"
        class="form-control"
        placeholder="required"
        v-model="formCredentials.secretAccessKey"
        @input="validateInput"
      />
    </div>
    <label class="h6">Session token</label>
    <div class="input-group mb-2">
      <input
        type="text"
        class="form-control"
        placeholder="optional"
        v-model="formCredentials.sessionToken"
        @input="validateInput"
      />
    </div>
  </div>
</template>

<script>
import _ from "lodash";
import { reactive } from "vue";
export default {
  name: "Credentials",
  props: ["credentials"],
  data() {
    let configuration = {
      valid: false,
      formCredentials: reactive(this.credentials),
    };
    return configuration;
  },
  emits: ["inputChanged"],
  mounted() {
    this.validateInput();
  },
  methods: {
    validateInput() {
      // set the valid flag based on tests
      this.valid =
        typeof this.formCredentials.accessKey === "string" &&
        typeof this.formCredentials.secretAccessKey === "string" &&
        this.formCredentials.accessKey.length > 0 &&
        this.formCredentials.secretAccessKey.length > 0;
      let event = _.cloneDeep(this.formCredentials);
      event.valid = this.valid;
      // emit an event upstream that the credentials have changed
      this.$emit("inputChanged", event);
    },
  },
};
</script>
