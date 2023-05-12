import { createRouter, createWebHistory } from 'vue-router'
import RunView from '@/views/RunView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Home',
      redirect: '/wells'
    },
    {
      path: '/wells',
      name: 'RunView',
      component: RunView,
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/AboutView.vue')
    },
    {
      path: "/login",
      name: 'login',
      component: () => import('../views/LoginView.vue')
    }
  ]
})

export default router
