<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

/**
 * La couche HTTP émet `session:expiree` sur un 401 ; c'est ici qu'on décide de
 * rediriger. Cette indirection évite que `api/client.ts` dépende du routeur.
 */
function surSessionExpiree() {
  auth.deconnexion()
  void router.push({ name: 'connexion' })
}

onMounted(() => window.addEventListener('session:expiree', surSessionExpiree))
onUnmounted(() => window.removeEventListener('session:expiree', surSessionExpiree))
</script>

<template>
  <RouterView />
</template>
