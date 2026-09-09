<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

function surSessionExpiree() {
  // La session est déjà close côté serveur : on oublie le profil sans rappeler
  // /auth/logout, qui n'aurait plus rien à effacer.
  auth.oublier()
  void router.push({ name: 'connexion' })
}

onMounted(() => window.addEventListener('session:expiree', surSessionExpiree))
onUnmounted(() => window.removeEventListener('session:expiree', surSessionExpiree))
</script>

<template>
  <RouterView />
</template>
