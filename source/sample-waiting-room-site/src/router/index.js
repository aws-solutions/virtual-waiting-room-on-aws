// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/*jshint esversion: 6 */

import { createRouter, createWebHistory } from 'vue-router';
import Home from '../views/Home.vue';
import WaitingRoom from '../views/WaitingRoom.vue';
import CheckOut from '../views/CheckOut.vue';

// routes determine which view component to show based on the address

const routes = [
  {
    path: '/',
    alias: "/index.html",
    name: 'Home',
    component: Home,
  },
  {
    path: '/waitingroom',
    name: 'Waiting Room',
    component: WaitingRoom,
  },
  {
    path: '/checkout',
    name: 'Check Out',
    component: CheckOut,
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

export default router;
