<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is a view for the site's waiting room page -->

<template>
  <div class="d-flex flex-column w-50 mx-auto border border-2 rounded mt-2">
    <div class="text-center lead mb-2">Waiting Room</div>
    <div class="text-center mb-2">
      You will wait here until the serving position advances past your position
      in the line.
    </div>
    <div class="d-flex flex-row">
      <MyPosition class="w-50 m-2" />
      <ServingPosition class="w-50 m-2" />
    </div>
    <div class="d-flex flex-row">
      <TimeToExit class="w-50 m-2" />
      <WaitingRoomSize class="w-50 m-2" />
    </div>
    <div class="d-flex flex-row mx-auto mb-2">
      <button
        type="button"
        class="btn btn-success m-2"
        v-on:click="navigateToCheckOut"
        v-bind:disabled="!readyForCheckOut"
      >
        {{
          readyForCheckOut ? "Check out now!" : "Waiting for line to advance"
        }}
      </button>
    </div>
  </div>
</template>

<script>
import { mapGetters } from "vuex";
import MyPosition from "@/components/MyPosition.vue";
import ServingPosition from "@/components/ServingPosition.vue";
import TimeToExit from "@/components/TimeToExit.vue";
import WaitingRoomSize from "@/components/WaitingRoomSize.vue";

export default {
  name: "WaitingRoom",
  created() {
    this.$watch("readyForCheckOut", this.passThruCheckOut);
  },
  methods: {
    passThruCheckOut() {
      if (this.passThru && this.readyForCheckOut) {
        this.navigateToCheckOut();
      }
    },
    navigateToCheckOut() {
      this.$router.push("/CheckOut");
    },
  },
  computed: {
    // mix the getters into computed with object spread operator
    ...mapGetters(["hasRequestId", "hasQueuePosition", "hasToken"]),
    myPosition() {
      return this.$store.state.myPosition;
    },
    queuePosition() {
      return this.$store.state.queuePosition;
    },
    passThru() {
      return this.$store.state.passThru;
    },
    readyForCheckOut() {
      return (
        this.hasRequestId &&
        this.myPosition &&
        this.queuePosition &&
        this.myPosition <= this.queuePosition
      );
    },
  },
  components: {
    MyPosition,
    ServingPosition,
    TimeToExit,
    WaitingRoomSize,
  },
};
</script>
