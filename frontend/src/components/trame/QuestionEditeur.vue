<script setup lang="ts">
import { computed } from 'vue'

import { TYPES_A_BORNES, TYPES_A_OPTIONS, type QuestionBrouillon } from '@/stores/editeurTrame'
import type { Cible, Referentiel, TypeQuestion } from '@/types/api'

const question = defineModel<QuestionBrouillon>({ required: true })

defineProps<{
  index: number
  total: number
  referentiel: Referentiel | null
  modifiable: boolean
}>()

const emet = defineEmits<{
  supprimer: []
  deplacer: [sens: -1 | 1]
  changerType: [type: TypeQuestion]
}>()

const aDesOptions = computed(() => TYPES_A_OPTIONS.includes(question.value.type_question))
const aDesBornes = computed(() => TYPES_A_BORNES.includes(question.value.type_question))

const options = computed<string[]>({
  get: () => (question.value.configuration.options as string[]) ?? [],
  set: (valeur) => {
    question.value.configuration = { ...question.value.configuration, options: valeur }
  },
})

const minimum = computed<number>({
  get: () => (question.value.configuration.minimum as number) ?? 1,
  set: (valeur) => {
    question.value.configuration = { ...question.value.configuration, minimum: Number(valeur) }
  },
})

const maximum = computed<number>({
  get: () => (question.value.configuration.maximum as number) ?? 5,
  set: (valeur) => {
    question.value.configuration = { ...question.value.configuration, maximum: Number(valeur) }
  },
})

const libellesCible: Record<Cible, string> = {
  COLLABORATEUR: 'Collaborateur',
  MANAGER: 'Manager',
  PARTAGEE: 'Les deux',
}
</script>

<template>
  <div class="rounded-md border border-slate-200 bg-slate-50 p-3">
    <div class="flex items-start gap-2">
      <span class="mt-2 text-xs font-medium text-slate-400">{{ index + 1 }}.</span>

      <div class="grid flex-1 gap-2">
        <input
          v-model="question.libelle"
          :disabled="!modifiable"
          placeholder="Libellé de la question"
          class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100"
        />

        <div class="flex flex-wrap gap-2">
          <select
            :value="question.type_question"
            :disabled="!modifiable"
            class="rounded-md border border-slate-300 px-2 py-1.5 text-sm disabled:bg-slate-100"
            @change="
              emet('changerType', ($event.target as HTMLSelectElement).value as TypeQuestion)
            "
          >
            <option v-for="type in referentiel?.types_question ?? []" :key="type" :value="type">
              {{ type }}
            </option>
          </select>

          <select
            v-model="question.cible"
            :disabled="!modifiable"
            class="rounded-md border border-slate-300 px-2 py-1.5 text-sm disabled:bg-slate-100"
          >
            <option v-for="cible in referentiel?.cibles ?? []" :key="cible" :value="cible">
              {{ libellesCible[cible] ?? cible }}
            </option>
          </select>

          <label class="flex items-center gap-1.5 text-sm text-slate-700">
            <input v-model="question.obligatoire" type="checkbox" :disabled="!modifiable" />
            Obligatoire
          </label>
        </div>

        <div v-if="aDesOptions" class="grid gap-1">
          <span class="text-xs font-medium text-slate-600">Options (au moins deux)</span>
          <div v-for="(_, i) in options" :key="i" class="flex gap-2">
            <input
              :value="options[i]"
              :disabled="!modifiable"
              class="flex-1 rounded-md border border-slate-300 px-2 py-1 text-sm disabled:bg-slate-100"
              @input="
                options = options.map((o, j) =>
                  j === i ? ($event.target as HTMLInputElement).value : o,
                )
              "
            />
            <button
              v-if="modifiable && options.length > 2"
              type="button"
              class="text-xs text-red-600"
              @click="options = options.filter((_, j) => j !== i)"
            >
              Retirer
            </button>
          </div>
          <button
            v-if="modifiable"
            type="button"
            class="justify-self-start text-xs text-slate-600 underline"
            @click="options = [...options, '']"
          >
            Ajouter une option
          </button>
        </div>

        <div v-if="aDesBornes" class="flex gap-3">
          <label class="text-sm">
            <span class="mr-1 text-slate-600">Min</span>
            <input
              v-model.number="minimum"
              type="number"
              :disabled="!modifiable"
              class="w-20 rounded-md border border-slate-300 px-2 py-1 disabled:bg-slate-100"
            />
          </label>
          <label class="text-sm">
            <span class="mr-1 text-slate-600">Max</span>
            <input
              v-model.number="maximum"
              type="number"
              :disabled="!modifiable"
              class="w-20 rounded-md border border-slate-300 px-2 py-1 disabled:bg-slate-100"
            />
          </label>
        </div>
      </div>

      <div v-if="modifiable" class="flex flex-col gap-1">
        <button
          type="button"
          :disabled="index === 0"
          class="rounded border border-slate-300 px-2 text-xs disabled:opacity-30"
          title="Monter"
          @click="emet('deplacer', -1)"
        >
          ↑
        </button>
        <button
          type="button"
          :disabled="index === total - 1"
          class="rounded border border-slate-300 px-2 text-xs disabled:opacity-30"
          title="Descendre"
          @click="emet('deplacer', 1)"
        >
          ↓
        </button>
        <button
          type="button"
          class="rounded border border-red-200 px-2 text-xs text-red-600"
          title="Supprimer"
          @click="emet('supprimer')"
        >
          ✕
        </button>
      </div>
    </div>
  </div>
</template>
