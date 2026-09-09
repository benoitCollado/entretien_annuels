<script setup lang="ts">
import { ref } from 'vue'

import type { EvaluationEcrite, ObjectifEcrit } from '@/api/entretiens'
import type { Objectif, StatutObjectif } from '@/types/api'

defineProps<{
  fixes: Objectif[]
  aEvaluer: Objectif[]
  modifiable: boolean
}>()

const emet = defineEmits<{
  fixer: [donnees: ObjectifEcrit]
  evaluer: [objectifId: string, donnees: Omit<EvaluationEcrite, 'entretien_id'>]
}>()

const nouveau = ref<ObjectifEcrit>({ libelle: '', indicateur: '', echeance: null })
const enCoursDEvaluation = ref<string | null>(null)
const evaluation = ref<{ statut: StatutObjectif; niveau_atteinte: number | null }>({
  statut: 'ATTEINT',
  niveau_atteinte: null,
})

const LIBELLES: Record<StatutObjectif, string> = {
  EN_COURS: 'En cours',
  ATTEINT: 'Atteint',
  PARTIEL: 'Partiellement atteint',
  NON_ATTEINT: 'Non atteint',
}

const COULEURS: Record<StatutObjectif, string> = {
  EN_COURS: 'bg-slate-100 text-slate-700',
  ATTEINT: 'bg-emerald-100 text-emerald-800',
  PARTIEL: 'bg-amber-100 text-amber-800',
  NON_ATTEINT: 'bg-red-100 text-red-800',
}

function ajouter(): void {
  if (!nouveau.value.libelle.trim()) return
  emet('fixer', { ...nouveau.value })
  nouveau.value = { libelle: '', indicateur: '', echeance: null }
}

function confirmerEvaluation(objectifId: string): void {
  emet('evaluer', objectifId, { ...evaluation.value })
  enCoursDEvaluation.value = null
  evaluation.value = { statut: 'ATTEINT', niveau_atteinte: null }
}
</script>

<template>
  <section class="space-y-8">
    <div v-if="aEvaluer.length > 0">
      <h2 class="text-lg font-semibold text-slate-900">Objectifs de l'année précédente</h2>
      <p class="mt-1 text-sm text-slate-500">
        Rappelés automatiquement depuis l'entretien précédent.
      </p>

      <ul class="mt-4 space-y-3">
        <li
          v-for="objectif in aEvaluer"
          :key="objectif.id"
          class="rounded-lg border border-slate-200 bg-white p-4"
        >
          <p class="font-medium text-slate-900">{{ objectif.libelle }}</p>
          <p v-if="objectif.indicateur" class="mt-1 text-sm text-slate-600">
            Indicateur : {{ objectif.indicateur }}
          </p>
          <p v-if="objectif.echeance" class="mt-1 text-sm text-slate-500">
            Échéance : {{ objectif.echeance }}
          </p>

          <div v-if="modifiable" class="mt-3">
            <button
              v-if="enCoursDEvaluation !== objectif.id"
              type="button"
              class="rounded border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700"
              @click="enCoursDEvaluation = objectif.id"
            >
              Évaluer
            </button>

            <div v-else class="flex flex-wrap items-end gap-3">
              <label class="text-sm text-slate-700">
                Résultat
                <select
                  v-model="evaluation.statut"
                  class="mt-1 block rounded border border-slate-300 px-2 py-1.5 text-sm"
                >
                  <option value="ATTEINT">Atteint</option>
                  <option value="PARTIEL">Partiellement atteint</option>
                  <option value="NON_ATTEINT">Non atteint</option>
                </select>
              </label>
              <label class="text-sm text-slate-700">
                Niveau (%)
                <input
                  v-model.number="evaluation.niveau_atteinte"
                  type="number"
                  min="0"
                  max="100"
                  class="mt-1 block w-24 rounded border border-slate-300 px-2 py-1.5 text-sm"
                />
              </label>
              <button
                type="button"
                class="rounded bg-slate-900 px-3 py-1.5 text-sm font-medium text-white"
                @click="confirmerEvaluation(objectif.id)"
              >
                Valider
              </button>
              <button
                type="button"
                class="text-sm text-slate-500 underline"
                @click="enCoursDEvaluation = null"
              >
                Annuler
              </button>
            </div>
          </div>
        </li>
      </ul>
    </div>

    <div v-if="fixes.length > 0 || modifiable">
      <h2 class="text-lg font-semibold text-slate-900">Objectifs pour l'année à venir</h2>

      <ul v-if="fixes.length > 0" class="mt-4 space-y-3">
        <li
          v-for="objectif in fixes"
          :key="objectif.id"
          class="rounded-lg border border-slate-200 bg-white p-4"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="font-medium text-slate-900">{{ objectif.libelle }}</p>
              <p v-if="objectif.indicateur" class="mt-1 text-sm text-slate-600">
                Indicateur : {{ objectif.indicateur }}
              </p>
              <p v-if="objectif.echeance" class="mt-1 text-sm text-slate-500">
                Échéance : {{ objectif.echeance }}
              </p>
            </div>
            <span
              class="shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium"
              :class="COULEURS[objectif.statut]"
            >
              {{ LIBELLES[objectif.statut] }}
            </span>
          </div>
        </li>
      </ul>

      <p v-else class="mt-3 text-sm text-slate-500">Aucun objectif fixé pour l'instant.</p>

      <div v-if="modifiable" class="mt-4 space-y-2 rounded-lg border border-slate-200 p-4">
        <input
          v-model="nouveau.libelle"
          type="text"
          placeholder="Intitulé de l'objectif"
          class="w-full rounded border border-slate-300 px-3 py-2 text-sm"
        />
        <div class="flex flex-wrap gap-2">
          <input
            v-model="nouveau.indicateur"
            type="text"
            placeholder="Indicateur de mesure"
            class="flex-1 rounded border border-slate-300 px-3 py-2 text-sm"
          />
          <input
            v-model="nouveau.echeance"
            type="date"
            class="rounded border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <button
          type="button"
          :disabled="!nouveau.libelle.trim()"
          class="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
          @click="ajouter"
        >
          Ajouter l'objectif
        </button>
      </div>
    </div>
  </section>
</template>
