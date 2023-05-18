import { createRouter, createWebHistory } from 'vue-router'
import WellsByStatus from '@/views/WellsByStatus.vue'
import WellsByRun from '@/views/WellsByRun.vue'

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
      name: 'WellsByStatus',
      component: WellsByStatus,
    },
    {
      path: '/run/:runName',
      name: 'WellsByRun',
      component: WellsByRun,
      props: true
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
