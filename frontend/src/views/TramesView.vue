<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import AppEntete from '@/components/AppEntete.vue'
import { useAuthStore } from '@/stores/auth'
import { useTramesStore } from '@/stores/trames'

const auth = useAuthStore()
const trames = useTramesStore()
const router = useRouter()

const formulaireOuvert = ref(false)
const nom = ref('')
const typeEntretien = ref<'ANNUEL' | 'PROFESSIONNEL'>('ANNUEL')
const description = ref('')

onMounted(() => trames.charger())

async function creer() {
  const id = await trames.creer(nom.value, typeEntretien.value, description.value || null)
  if (id) {
    formulaireOuvert.value = false
    nom.value = ''
    description.value = ''
    await router.push({ name: 'trame-editeur', params: { id } })
  }
}

async function versionner(id: string) {
  const nouvelle = await trames.nouvelleVersion(id)
  if (nouvelle) await router.push({ name: 'trame-editeur', params: { id: nouvelle } })
}

const couleurs: Record<string, string> = {
  BROUILLON: 'bg-amber-100 text-amber-800',
  PUBLIEE: 'bg-emerald-100 text-emerald-800',
  ARCHIVEE: 'bg-slate-100 text-slate-600',
}
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <AppEntete />

    <main class="mx-auto max-w-5xl p-6">
      <div class="mb-4 flex items-center justify-between">
        <h1 class="text-lg font-semibold text-slate-900">Trames de questionnaire</h1>
        <button
          v-if="auth.peut('template:creer')"
          type="button"
          class="rounded-md bg-slate-900 px-3 py-1.5 text-sm text-white"
          @click="formulaireOuvert = !formulaireOuvert"
        >
          {{ formulaireOuvert ? 'Annuler' : 'Nouvelle trame' }}
        </button>
      </div>

      <form
        v-if="formulaireOuvert"
        class="mb-6 grid gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-3"
        @submit.prevent="creer"
      >
        <label class="text-sm">
          <span class="mb-1 block font-medium text-slate-700">Nom</span>
          <input
            v-model="nom"
            required
            class="w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
        <label class="text-sm">
          <span class="mb-1 block font-medium text-slate-700">Type d'entretien</span>
          <select
            v-model="typeEntretien"
            class="w-full rounded-md border border-slate-300 px-3 py-2"
          >
            <option value="ANNUEL">Annuel</option>
            <option value="PROFESSIONNEL">Professionnel</option>
          </select>
        </label>
        <label class="text-sm">
          <span class="mb-1 block font-medium text-slate-700">Description</span>
          <input
            v-model="description"
            class="w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
        <div class="sm:col-span-3">
          <button type="submit" class="rounded-md bg-slate-900 px-4 py-2 text-sm text-white">
            Créer en brouillon
          </button>
        </div>
      </form>

      <p v-if="trames.erreur" role="alert" class="mb-4 text-sm text-red-600">
        {{ trames.erreur }}
      </p>
      <p v-if="trames.chargement" class="text-sm text-slate-500">Chargement…</p>

      <div v-else class="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table class="w-full text-sm">
          <thead class="border-b border-slate-200 bg-slate-50 text-left text-slate-600">
            <tr>
              <th class="px-4 py-2 font-medium">Nom</th>
              <th class="px-4 py-2 font-medium">Type</th>
              <th class="px-4 py-2 font-medium">Version</th>
              <th class="px-4 py-2 font-medium">Statut</th>
              <th class="px-4 py-2 font-medium">Contenu</th>
              <th class="px-4 py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="trame in trames.elements"
              :key="trame.id"
              class="border-b border-slate-100 last:border-0"
            >
              <td class="px-4 py-2 text-slate-900">{{ trame.nom }}</td>
              <td class="px-4 py-2 text-slate-600">{{ trame.type_entretien }}</td>
              <td class="px-4 py-2 text-slate-600">v{{ trame.version }}</td>
              <td class="px-4 py-2">
                <span
                  class="rounded px-2 py-0.5 text-xs font-medium"
                  :class="couleurs[trame.statut]"
                >
                  {{ trame.statut }}
                </span>
              </td>
              <td class="px-4 py-2 text-slate-600">
                {{ trame.nombre_sections }} section(s), {{ trame.nombre_questions }} question(s)
              </td>
              <td class="px-4 py-2 text-right">
                <RouterLink
                  :to="{ name: 'trame-editeur', params: { id: trame.id } }"
                  class="text-slate-900 underline"
                >
                  {{ trame.est_modifiable ? 'Éditer' : 'Consulter' }}
                </RouterLink>
                <button
                  v-if="!trame.est_modifiable && auth.peut('template:creer')"
                  type="button"
                  class="ml-3 text-slate-600 underline"
                  @click="versionner(trame.id)"
                >
                  Nouvelle version
                </button>
              </td>
            </tr>
            <tr v-if="trames.elements.length === 0">
              <td colspan="6" class="px-4 py-6 text-center text-slate-500">
                Aucune trame pour l'instant.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p class="mt-3 text-sm text-slate-500">{{ trames.total }} trame(s)</p>
    </main>
  </div>
</template>
