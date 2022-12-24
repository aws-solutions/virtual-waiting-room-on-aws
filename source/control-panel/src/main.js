// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/*jshint esversion: 6 */

import { createApp } from 'vue';
import { createStore } from 'vuex';
import App from './App.vue';
import _ from 'lodash';

const store = createStore({
  state() {
    return {
        expiredTokens: undefined,
        servingCounter: undefined,
        waitingRoomSize: undefined,
        activeTokens: undefined,
    };
  },
  mutations: {
    setExpiredTokens(state, value) {
        state.expiredTokens = value;
    },
    setServingCounter(state, value) {
        state.servingCounter = value;
    },
    setWaitingRoomSize(state, value) {
        state.waitingRoomSize = value;
    },
    setActiveTokens(state, value) {
      state.activeTokens = value;
    },
  },
  getters:
  {
    getRemainingCounter(state) {
        if (_.isNil(state.servingCounter) || _.isNil(state.waitingRoomSize) || _.isNil(state.activeTokens) || _.isNil(state.expiredTokens)) {
          return undefined;
        } else {
          return state.servingCounter - (state.waitingRoomSize + state.activeTokens + state.expiredTokens);
        }
    },
  }
});

const app = createApp(App);
app.use(store);
app.mount('#app');
