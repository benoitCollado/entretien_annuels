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
    redirect: { name: 'mes-entretiens' },
  },
  {
    path: '/entretiens',
    name: 'mes-entretiens',
    component: () => import('@/views/MesEntretiensView.vue'),
    meta: { permission: 'entretien:lire' },
  },
  {
    path: '/entretiens/:id',
    name: 'entretien',
    component: () => import('@/views/EntretienView.vue'),

    meta: { permission: 'entretien:lire' },
  },
  {
    path: '/tableau-bord',
    name: 'tableau-bord',
    component: () => import('@/views/TableauBordView.vue'),
    meta: { permission: 'tableau_bord:lire' },
  },
  {
    path: '/utilisateurs',
    name: 'utilisateurs',
    component: () => import('@/views/UtilisateursView.vue'),
    meta: { permission: 'utilisateur:lire' },
  },
  {
    path: '/trames',
    name: 'trames',
    component: () => import('@/views/TramesView.vue'),
    meta: { permission: 'template:lire' },
  },
  {
    path: '/trames/:id',
    name: 'trame-editeur',
    component: () => import('@/views/TrameEditeurView.vue'),

    meta: { permission: 'template:lire' },
  },
  {
    path: '/campagnes',
    name: 'campagnes',
    component: () => import('@/views/CampagnesView.vue'),
    meta: { permission: 'campagne:lire' },
  },
  {
    path: '/interdit',
    name: 'interdit',
    component: () => import('@/views/InterditView.vue'),
  },
  {
    path: '/:chemin(.*)*',
    redirect: { name: 'mes-entretiens' },
  },
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach(gardeAuthentification)

export default router
