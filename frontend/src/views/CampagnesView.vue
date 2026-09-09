<script setup lang="ts">
import { onMounted, ref } from 'vue'

import AppEntete from '@/components/AppEntete.vue'
import { useAuthStore } from '@/stores/auth'
import { useCampagnesStore } from '@/stores/campagnes'

const auth = useAuthStore()
const campagnes = useCampagnesStore()

const formulaireOuvert = ref(false)
const anneeCourante = new Date().getFullYear()
const formulaire = ref({
  libelle: '',
  annee: anneeCourante,
  type_entretien: 'ANNUEL',
  date_ouverture: `${anneeCourante}-01-01`,
  date_limite: `${anneeCourante}-12-31`,
  description: null as string | null,
})

onMounted(() => campagnes.charger())

async function creer() {
  if (await campagnes.creer({ ...formulaire.value })) {
    formulaireOuvert.value = false
    formulaire.value.libelle = ''
  }
}

const couleurs: Record<string, string> = {
  BROUILLON: 'bg-amber-100 text-amber-800',
  OUVERTE: 'bg-emerald-100 text-emerald-800',
  CLOTUREE: 'bg-slate-100 text-slate-600',
}
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <AppEntete />

    <main class="mx-auto max-w-5xl p-6">
      <div class="mb-4 flex items-center justify-between">
        <h1 class="text-lg font-semibold text-slate-900">Campagnes</h1>
        <button
          v-if="auth.peut('campagne:creer')"
          type="button"
          class="rounded-md bg-slate-900 px-3 py-1.5 text-sm text-white"
          @click="formulaireOuvert = !formulaireOuvert"
        >
          {{ formulaireOuvert ? 'Annuler' : 'Nouvelle campagne' }}
        </button>
      </div>

      <form
        v-if="formulaireOuvert"
        class="mb-6 grid gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-2"
        @submit.prevent="creer"
      >
        <label class="text-sm">
          <span class="mb-1 block font-medium text-slate-700">Libellé</span>
          <input
            v-model="formulaire.libelle"
            required
            class="w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
        <label class="text-sm">
          <span class="mb-1 block font-medium text-slate-700">Type</span>
          <select
            v-model="formulaire.type_entretien"
            class="w-full rounded-md border border-slate-300 px-3 py-2"
          >
            <option value="ANNUEL">Annuel</option>
            <option value="PROFESSIONNEL">Professionnel</option>
          </select>
        </label>
        <label class="text-sm">
          <span class="mb-1 block font-medium text-slate-700">Ouverture</span>
          <input
            v-model="formulaire.date_ouverture"
            type="date"
            required
            class="w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
        <label class="text-sm">
          <span class="mb-1 block font-medium text-slate-700">Échéance</span>
          <input
            v-model="formulaire.date_limite"
            type="date"
            required
            class="w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
        <label class="text-sm">
          <span class="mb-1 block font-medium text-slate-700">Année</span>
          <input
            v-model.number="formulaire.annee"
            type="number"
            required
            class="w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
        <div class="sm:col-span-2">
          <button type="submit" class="rounded-md bg-slate-900 px-4 py-2 text-sm text-white">
            Créer en brouillon
          </button>
        </div>
      </form>

      <p v-if="campagnes.erreur" role="alert" class="mb-4 text-sm text-red-600">
        {{ campagnes.erreur }}
      </p>
      <p v-if="campagnes.chargement" class="text-sm text-slate-500">Chargement…</p>

      <div v-else class="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table class="w-full text-sm">
          <thead class="border-b border-slate-200 bg-slate-50 text-left text-slate-600">
            <tr>
              <th class="px-4 py-2 font-medium">Libellé</th>
              <th class="px-4 py-2 font-medium">Année</th>
              <th class="px-4 py-2 font-medium">Type</th>
              <th class="px-4 py-2 font-medium">Période</th>
              <th class="px-4 py-2 font-medium">Statut</th>
              <th class="px-4 py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="campagne in campagnes.elements"
              :key="campagne.id"
              class="border-b border-slate-100 last:border-0"
            >
              <td class="px-4 py-2 text-slate-900">{{ campagne.libelle }}</td>
              <td class="px-4 py-2 text-slate-600">{{ campagne.annee }}</td>
              <td class="px-4 py-2 text-slate-600">{{ campagne.type_entretien }}</td>
              <td class="px-4 py-2 text-slate-600">
                {{ campagne.date_ouverture }} → {{ campagne.date_limite }}
              </td>
              <td class="px-4 py-2">
                <span
                  class="rounded px-2 py-0.5 text-xs font-medium"
                  :class="couleurs[campagne.statut]"
                >
                  {{ campagne.statut }}
                </span>
              </td>
              <td class="px-4 py-2 text-right">
                <button
                  v-if="campagne.statut === 'BROUILLON' && auth.peut('campagne:ouvrir')"
                  type="button"
                  class="text-emerald-700 underline"
                  @click="campagnes.ouvrir(campagne.id)"
                >
                  Ouvrir
                </button>
                <button
                  v-if="campagne.statut === 'OUVERTE' && auth.peut('campagne:cloturer')"
                  type="button"
                  class="text-slate-600 underline"
                  @click="campagnes.cloturer(campagne.id)"
                >
                  Clôturer
                </button>
              </td>
            </tr>
            <tr v-if="campagnes.elements.length === 0">
              <td colspan="6" class="px-4 py-6 text-center text-slate-500">
                Aucune campagne pour l'instant.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p class="mt-3 text-sm text-slate-500">{{ campagnes.total }} campagne(s)</p>
    </main>
  </div>
</template>
