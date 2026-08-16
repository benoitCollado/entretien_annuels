import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { gardeAuthentification } from '@/router/guards'

const routes: RouteRecordRaw[] = [
  {
    path: '/connexion',
    name: 'connexion',
    component: () => import('@/views/ConnexionView.vue'),
    meta: { publique: true },
  },
  {
    path: '/',
    redirect: { name: 'utilisateurs' },
  },
  {
    path: '/utilisateurs',
    name: 'utilisateurs',
    component: () => import('@/views/UtilisateursView.vue'),
    meta: { permission: 'utilisateur:lire' },
  },
  {
    path: '/interdit',
    name: 'interdit',
    component: () => import('@/views/InterditView.vue'),
  },
  {
    path: '/:chemin(.*)*',
    redirect: { name: 'utilisateurs' },
  },
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach(gardeAuthentification)

export default router
