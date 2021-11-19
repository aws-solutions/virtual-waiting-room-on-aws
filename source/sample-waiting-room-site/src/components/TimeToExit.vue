<!-- 
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
-->

<!-- this SFC is responsible for estimating and displaying the
remaining time this user will be in the waiting room -->

<template>
  <div class="d-flex flex-column border border-2 rounded p-2">
    <div class="text-center lead mb-2">Estimated Time to Exit</div>
    <div class="mb-2">
      This compartment shows the estimated time remaining to exit the waiting
      room and check out.
    </div>
    <div>
      <!-- display an alert for the estimate if we have that, otherwise
      we'll display a stand-by alert -->
      <div
        v-if="estimatedExitTimestamp !== 0 && myPosition > queuePosition"
        class="alert alert-primary"
        role="alert"
      >
        Exit {{ remainingTime }}
      </div>
      <div
        v-if="estimatedExitTimestamp === 0 && myPosition > queuePosition"
        class="alert alert-secondary"
        role="alert"
      >
        Stand by while estimating time to exit
      </div>
      <!-- show an alert that it's time to move out of the waiting room -->
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
import moment from "moment";
// take queue and timestamp samples every 5 seconds
const UPDATE_INTERVAL_MS = 5000;
const MAX_SAMPLES = 50;
export default {
  name: "TimeToExit",
  mixins: [VueTimers],
  // use a vue timer for periodic updates
  timers: {
    updateExitExtrapolation: {
      time: UPDATE_INTERVAL_MS,
      autostart: true,
      repeat: true
    },
  },
  // stop and restart the update timer if we leave and return
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
    // keep samples and human-readable estimate locally on the component
    return {
      samples: [],
      estimatedExitTimestamp: 0,
      remainingTime: ""
    };
  },
  computed: {
    // mix the getters into computed with object spread operator
    ...mapGetters(["hasRequestId", "hasQueuePosition", "hasToken"]),
    // local properties mapped to vuex state
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
      // update the sample and estimate from the timer
      const now = new Date().getTime();
      // create a new sample with the position and timestamp
      const item = [this.queuePosition, now];
      // add to the end
      this.samples.push(item);
      // trim the older samples from the front if needed
      while (this.samples.length > MAX_SAMPLES) {
        this.samples.shift();
      }
      // create the fit function from the samples
      const fitFunction = linearRegressionLine(linearRegression(this.samples));
      // estimate the exit timestamp for the user's line position
      const estimate = Number.parseInt(fitFunction(this.myPosition));
      if (!isNaN(estimate)) {
        this.estimatedExitTimestamp = estimate;
        // create the human-readable 
        this.remainingTime = moment().to(new Date(this.estimatedExitTimestamp));
      } else {
        this.estimatedExitTimestamp = 0;
      }
    },
  },
};
</script>
