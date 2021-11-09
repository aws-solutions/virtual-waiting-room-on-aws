<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is responsible for retrieving and displaying
the current serving counter of the waiting room -->

<template>
  <div class="d-flex flex-column border border-2 rounded p-2">
    <!-- display a header with the last connection status -->
    <div class="text-center lead mb-2">Estimated Time to Exit</div>
    <div class="mb-2">
      This compartment shows the estimated time remaining to exit the waiting
      room to check out.
    </div>
    <div>
      <div
        v-if="timeToExit !== 0 && myPosition > queuePosition"
        class="alert alert-primary"
        role="alert"
      >
        {{ new Date(timeToExit).toTimeString() }}
      </div>
      <div
        v-if="timeToExit === 0 && myPosition > queuePosition"
        class="alert alert-secondary"
        role="alert"
      >
        Stand by while estimating time to exit
      </div>
      <div
        v-if="myPosition <= queuePosition"
        class="alert alert-success"
        role="alert"
      >
        Check out now!
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from "vuex";
import { mixin as VueTimers } from "vue-timers";
import { linearRegression, linearRegressionLine } from "simple-statistics";
const UPDATE_INTERVAL_MS = 3000;
const MAX_SAMPLES = 50;
export default {
  name: "TimeToExit",
  mixins: [VueTimers],
  // use a vue timer for periodic updates
  timers: {
    updateExitExtrapolation: {
      time: UPDATE_INTERVAL_MS,
      autostart: true,
      repeat: true,
      immediate: true,
    },
  },
  unmounted() {
    if (this.timers.updateExitExtrapolation.isRunning) {
      this.$timer.stop("updateExitExtrapolation");
    }
  },
  mounted() {
    if (!this.timers.updateExitExtrapolation.isRunning) {
      this.$timer.start("updateExitExtrapolation");
    }
  },
  data() {
    return {
      samples: [],
      timeToExit: 0,
    };
  },
  computed: {
    // mix the getters into computed with object spread operator
    ...mapGetters(["hasRequestId", "hasQueuePosition", "hasToken"]),
    requestId() {
      return this.$store.state.requestId;
    },
    myPosition() {
      return this.$store.state.myPosition;
    },
    queuePosition() {
      return this.$store.state.queuePosition;
    },
  },
  methods: {
    updateExitExtrapolation() {
      const now = new Date().getTime();
      const item = [this.queuePosition, now];
      this.samples.push(item);
      while (this.samples.length > MAX_SAMPLES) {
        this.samples.shift();
      }
      // console.log(this.samples);
      const fitFunction = linearRegressionLine(linearRegression(this.samples));
      const estimate = Number.parseInt(fitFunction(this.myPosition));
      if (!isNaN(estimate)) {
        this.timeToExit = estimate;
      } else {
        this.timeToExit = 0;
      }
    },
  },
};
</script>
