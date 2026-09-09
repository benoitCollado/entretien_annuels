<script setup lang="ts">
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const liens = [
  { nom: 'mes-entretiens', libelle: 'Mes entretiens', permission: 'entretien:lire' },
  { nom: 'tableau-bord', libelle: 'Suivi', permission: 'tableau_bord:lire' },
  { nom: 'utilisateurs', libelle: 'Utilisateurs', permission: 'utilisateur:lire' },
  { nom: 'trames', libelle: 'Trames', permission: 'template:lire' },
  { nom: 'campagnes', libelle: 'Campagnes', permission: 'campagne:lire' },
]

async function seDeconnecter() {
  auth.deconnexion()
  await router.push({ name: 'connexion' })
}
</script>

<template>
  <header class="flex items-center gap-6 border-b border-slate-200 bg-white px-6 py-3">
    <span class="font-semibold text-slate-900">Entretiens</span>

    <nav class="flex flex-1 gap-4 text-sm">
      <template v-for="lien in liens" :key="lien.nom">
        <RouterLink
          v-if="auth.peut(lien.permission)"
          :to="{ name: lien.nom }"
          class="text-slate-600 hover:text-slate-900"
          active-class="font-medium text-slate-900"
        >
          {{ lien.libelle }}
        </RouterLink>
      </template>
    </nav>

    <span v-if="auth.utilisateur" class="text-sm text-slate-600">
      {{ auth.utilisateur.nom_complet }}
      <span class="text-slate-400">({{ auth.roles.join(', ') }})</span>
    </span>
    <button
      type="button"
      class="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
      @click="seDeconnecter"
    >
      Déconnexion
    </button>
  </header>
</template>
