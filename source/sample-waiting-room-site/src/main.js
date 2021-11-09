// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/*jshint esversion: 6 */

import { createApp } from 'vue';
import { createStore } from 'vuex'
import App from './App.vue';
import router from './router'

const store = createStore({
    state() {
        return {
            publicApiUrl: "",
            eventId: "",
            requestId: null,
            myPosition: 0,
            queuePosition: 0,
            token: null,
            receipt: null,
            commerceApiUrl: "",
            launchQueryParameters: ""
        }
    },
    mutations: {
        setRequestId(state, id) {
            state.requestId = id;
        },
        setMyPosition(state, position) {
            state.myPosition = position;
        },
        setQueuePosition(state, position) {
            state.queuePosition = position;
        },
        setToken(state, token) {
            state.token = token;
        },
        setPublicApiUrl(state, url) {
            state.publicApiUrl = url;
        },
        setEventId(state, id) {
            state.eventId = id;
        },
        setReceipt(state, receipt) {
            state.receipt = receipt;
        },
        setCommerceApiUrl(state, url) {
            state.commerceApiUrl = url;
        }
        ,
        setLaunchQueryParameters(state, query) {
            state.launchQueryParameters = query;
        }
    },
    getters:
    {
        hasRequestId(state) {
            return state.requestId !== null;
        },
        hasQueuePosition(state) {
            return state.myPosition > 0;
        },
        hasToken(state) {
            return state.token !== null;
        },
        hasReceipt(state) {
            return state.receipt !== null;
        }
    }
});

const app = createApp(App)
app.use(router);
app.use(store);
app.mount('#app');
