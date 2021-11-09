import { createRouter, createWebHistory } from 'vue-router';
import Home from '../views/Home.vue';
import WaitingRoom from '../views/WaitingRoom.vue';
import CheckOut from '../views/CheckOut.vue';

const routes = [
  {
    path: '/',
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
