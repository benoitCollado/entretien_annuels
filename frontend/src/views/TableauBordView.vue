<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { ErreurHttp } from '@/api/client'
import { tableauBordApi } from '@/api/entretiens'
import AppEntete from '@/components/AppEntete.vue'
import BadgeStatut from '@/components/entretien/BadgeStatut.vue'
import { useCampagnesStore } from '@/stores/campagnes'
import type { TableauDeBord } from '@/types/api'

const campagnes = useCampagnesStore()
const campagneChoisie = ref<string>('')
const tableau = ref<TableauDeBord | null>(null)
const chargement = ref(false)
const erreur = ref<string | null>(null)

onMounted(async () => {
  await campagnes.charger()
  const ouverte = campagnes.elements.find((c) => c.statut === 'OUVERTE')
  campagneChoisie.value = ouverte?.id ?? campagnes.elements[0]?.id ?? ''
})

watch(campagneChoisie, async (id) => {
  if (!id) {
    tableau.value = null
    return
  }
  chargement.value = true
  erreur.value = null
  try {
    tableau.value = await tableauBordApi.parCampagne(id)
  } catch (e) {
    erreur.value = e instanceof ErreurHttp ? e.message : 'Chargement impossible.'
    tableau.value = null
  } finally {
    chargement.value = false
  }
})

const pourcentage = computed(() => Math.round((tableau.value?.taux_avancement ?? 0) * 100))

function part(nombre: number): string {
  const total = tableau.value?.total ?? 0
  return total === 0 ? '0%' : `${(nombre / total) * 100}%`
}
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <AppEntete />
    <section class="mx-auto max-w-4xl px-4 py-8">
      <h1 class="text-2xl font-semibold text-slate-900">Suivi des campagnes</h1>

      <label class="mt-6 block text-sm font-medium text-slate-700">
        Campagne
        <select
          v-model="campagneChoisie"
          class="mt-1 block w-full rounded border border-slate-300 px-3 py-2 text-sm"
        >
          <option v-for="campagne in campagnes.elements" :key="campagne.id" :value="campagne.id">
            {{ campagne.libelle }} ({{ campagne.annee }})
          </option>
        </select>
      </label>

      <p v-if="chargement" class="mt-6 text-sm text-slate-500">Chargement…</p>
      <p
        v-else-if="erreur"
        role="alert"
        class="mt-6 rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
      >
        {{ erreur }}
      </p>

      <template v-else-if="tableau">
        <div class="mt-6 grid gap-4 sm:grid-cols-3">
          <div class="rounded-lg border border-slate-200 bg-white p-4">
            <p class="text-sm text-slate-500">Entretiens</p>
            <p class="mt-1 text-2xl font-semibold text-slate-900">{{ tableau.total }}</p>
          </div>
          <div class="rounded-lg border border-slate-200 bg-white p-4">
            <p class="text-sm text-slate-500">Terminés</p>
            <p class="mt-1 text-2xl font-semibold text-slate-900">{{ tableau.termines }}</p>
          </div>
          <div class="rounded-lg border border-slate-200 bg-white p-4">
            <p class="text-sm text-slate-500">Avancement</p>
            <p class="mt-1 text-2xl font-semibold text-slate-900">{{ pourcentage }} %</p>
          </div>
        </div>

        <p
          v-if="tableau.echue"
          class="mt-4 rounded border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
        >
          Échéance dépassée depuis le {{ tableau.date_limite }}.
        </p>

        <h2 class="mt-8 text-lg font-semibold text-slate-900">Répartition</h2>
        <div
          v-if="tableau.total > 0"
          class="mt-3 flex h-3 overflow-hidden rounded-full bg-slate-100"
          role="img"
          :aria-label="`${tableau.termines} entretiens terminés sur ${tableau.total}`"
        >
          <div
            v-for="ligne in tableau.par_statut"
            :key="ligne.statut"
            class="bg-slate-400 first:bg-slate-300 last:bg-emerald-500"
            :style="{ width: part(ligne.nombre) }"
          />
        </div>

        <ul class="mt-4 space-y-2">
          <li
            v-for="ligne in tableau.par_statut"
            :key="ligne.statut"
            class="flex items-center justify-between rounded border border-slate-200 bg-white px-4 py-2"
          >
            <BadgeStatut :statut="ligne.statut" />
            <span class="text-sm font-medium text-slate-900">{{ ligne.nombre }}</span>
          </li>
        </ul>

        <template v-if="tableau.en_retard.length > 0">
          <h2 class="mt-8 text-lg font-semibold text-slate-900">
            En retard ({{ tableau.en_retard.length }})
          </h2>
          <ul class="mt-3 space-y-2">
            <li
              v-for="entretien in tableau.en_retard"
              :key="entretien.id"
              class="flex items-center justify-between rounded border border-amber-200 bg-amber-50 px-4 py-2"
            >
              <span class="text-sm text-slate-800">
                {{ entretien.collaborateur.nom_complet }}
                <span class="text-slate-500">— {{ entretien.manager.nom_complet }}</span>
              </span>
              <BadgeStatut :statut="entretien.statut" />
            </li>
          </ul>
        </template>

        <p class="mt-8 text-xs text-slate-400">
          Ce tableau ne donne accès à aucune réponse d'entretien : seuls les statuts et les
          horodatages y figurent.
        </p>
      </template>
    </section>
  </div>
</template>
