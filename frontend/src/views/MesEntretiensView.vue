<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink } from 'vue-router'

import AppEntete from '@/components/AppEntete.vue'
import BadgeStatut from '@/components/entretien/BadgeStatut.vue'
import { useAuthStore } from '@/stores/auth'
import { useEntretiensStore } from '@/stores/entretiens'
import type { EntretienResume } from '@/types/api'

const entretiens = useEntretiensStore()
const auth = useAuthStore()

onMounted(() => entretiens.charger())

function actionAttendue(entretien: EntretienResume): string {
  const jeSuisLeCollaborateur = entretien.collaborateur.id === auth.utilisateur?.id
  switch (entretien.statut) {
    case 'PLANIFIE':
    case 'PREPARATION':
      return jeSuisLeCollaborateur ? 'À vous de remplir' : 'En attente du collaborateur'
    case 'SOUMIS_COLLABORATEUR':
      return jeSuisLeCollaborateur ? 'Transmis, en attente du manager' : 'À vous de relire'
    case 'REVUE_MANAGER':
      return 'Échange en cours'
    case 'ENTRETIEN_REALISE':
      return 'En attente de signature'
    default:
      return '—'
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <AppEntete />
    <section class="mx-auto max-w-5xl px-4 py-8">
      <h1 class="text-2xl font-semibold text-slate-900">Mes entretiens</h1>

      <p v-if="entretiens.chargement" class="mt-6 text-sm text-slate-500">Chargement…</p>

      <p
        v-else-if="entretiens.erreur"
        role="alert"
        class="mt-6 rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
      >
        {{ entretiens.erreur }}
      </p>

      <p v-else-if="entretiens.elements.length === 0" class="mt-6 text-sm text-slate-500">
        Aucun entretien pour le moment.
      </p>

      <ul v-else class="mt-6 space-y-3">
        <li
          v-for="entretien in entretiens.elements"
          :key="entretien.id"
          class="rounded-lg border border-slate-200 bg-white p-4"
        >
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p class="font-medium text-slate-900">
                {{ entretien.collaborateur.nom_complet }}
                <span class="font-normal text-slate-500">
                  · {{ entretien.type_entretien === 'ANNUEL' ? 'Annuel' : 'Professionnel' }}
                </span>
              </p>
              <p class="mt-1 text-sm text-slate-600">
                Manager : {{ entretien.manager.nom_complet }}
                <span v-if="entretien.date_planifiee"> · le {{ entretien.date_planifiee }}</span>
              </p>
              <p class="mt-1 text-sm text-slate-500">{{ actionAttendue(entretien) }}</p>
            </div>

            <div class="flex items-center gap-3">
              <BadgeStatut :statut="entretien.statut" />
              <RouterLink
                :to="{ name: 'entretien', params: { id: entretien.id } }"
                class="rounded bg-slate-900 px-3 py-1.5 text-sm font-medium text-white"
              >
                Ouvrir
              </RouterLink>
            </div>
          </div>
        </li>
      </ul>
    </section>
  </div>
</template>
