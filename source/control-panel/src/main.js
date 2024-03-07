// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/*jshint esversion: 6 */

import { createApp } from 'vue';
import { createStore } from 'vuex';
import App from './App.vue';

const store = createStore({
    state() {
      return {
          servingCounter: undefined,  
          waitingRoomSize: undefined,
          activeTokens: undefined,
          expiredTokens: undefined,
      };
    },
    mutations: {
      setServingCounter(state, value) {
          state.servingCounter = value;
      },
      setWaitingRoomSize(state, value) {
          state.waitingRoomSize = value;
      },
      setActiveTokens(state, value) {
        state.activeTokens = value;
      },
      setExpiredTokens(state, value) {
        state.expiredTokens = value;
      },
    },
    getters:
    {
      getAvailableCounter(state) {
          if (state.servingCounter === undefined || state.waitingRoomSize === undefined || state.activeTokens === undefined || state.expiredTokens === undefined) {
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
