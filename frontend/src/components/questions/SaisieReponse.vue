<script setup lang="ts">
import { computed } from 'vue'

import type { QuestionInstanciee } from '@/types/api'

const props = defineProps<{
  question: QuestionInstanciee
  valeur: Record<string, unknown> | null
  modifiable: boolean
  manquante?: boolean
}>()

const emet = defineEmits<{ saisir: [valeur: Record<string, unknown> | null] }>()

const options = computed<string[]>(
  () => (props.question.configuration.options as string[]) ?? [],
)
const minimum = computed(() => (props.question.configuration.minimum as number) ?? 1)
const maximum = computed(() =>
  props.question.type_question === 'note_5'
    ? 5
    : ((props.question.configuration.maximum as number) ?? 5),
)

const echelle = computed(() =>
  Array.from({ length: maximum.value - minimum.value + 1 }, (_, i) => minimum.value + i),
)

function lire<T>(cle: string): T | undefined {
  return props.valeur?.[cle] as T | undefined
}

const texte = computed(() => lire<string>('contenu') ?? '')
const note = computed(() => lire<number>('note') ?? null)
const option = computed(() => lire<string>('option') ?? '')
const choisies = computed<string[]>(() => lire<string[]>('options') ?? [])
const ouiNon = computed(() => lire<boolean>('valeur'))
const dateSaisie = computed(() => lire<string>('date') ?? '')

function emettreTexte(contenu: string): void {
  emet('saisir', contenu.trim() === '' ? null : { contenu })
}

function basculerOption(valeur: string): void {
  const suivantes = choisies.value.includes(valeur)
    ? choisies.value.filter((o) => o !== valeur)
    : [...choisies.value, valeur]
  emet('saisir', suivantes.length === 0 ? null : { options: suivantes })
}

const identifiant = computed(() => `question-${props.question.id}`)
</script>

<template>
  <div
    class="rounded-lg border p-4"
    :class="manquante ? 'border-red-400 bg-red-50' : 'border-slate-200 bg-white'"
  >
    <label :for="identifiant" class="block text-sm font-medium text-slate-900">
      {{ question.libelle }}
      <span v-if="question.obligatoire" class="text-red-600" aria-label="obligatoire">*</span>
      <span
        v-if="question.est_ad_hoc"
        class="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-xs font-normal text-amber-800"
      >
        ajoutée
      </span>
    </label>
    <p v-if="question.aide" class="mt-1 text-xs text-slate-500">{{ question.aide }}</p>

    <p v-if="manquante" class="mt-1 text-xs font-medium text-red-700">
      Cette question est obligatoire.
    </p>

    <div class="mt-3">
      <textarea
        v-if="question.type_question === 'texte_libre'"
        :id="identifiant"
        :value="texte"
        :disabled="!modifiable"
        rows="4"
        class="w-full rounded border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-50"
        @input="emettreTexte(($event.target as HTMLTextAreaElement).value)"
      />

      <input
        v-else-if="question.type_question === 'texte_court'"
        :id="identifiant"
        :value="texte"
        :disabled="!modifiable"
        type="text"
        class="w-full rounded border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-50"
        @input="emettreTexte(($event.target as HTMLInputElement).value)"
      />

      <div
        v-else-if="question.type_question === 'echelle' || question.type_question === 'note_5'"
        role="radiogroup"
        :aria-labelledby="identifiant"
        class="flex flex-wrap gap-2"
      >
        <button
          v-for="valeur in echelle"
          :key="valeur"
          type="button"
          role="radio"
          :aria-checked="note === valeur"
          :disabled="!modifiable"
          class="h-10 w-10 rounded-full border text-sm font-medium disabled:opacity-50"
          :class="
            note === valeur
              ? 'border-slate-900 bg-slate-900 text-white'
              : 'border-slate-300 bg-white text-slate-700 hover:border-slate-500'
          "
          @click="emet('saisir', note === valeur ? null : { note: valeur })"
        >
          {{ valeur }}
        </button>
      </div>

      <div v-else-if="question.type_question === 'choix_unique'" class="space-y-2">
        <label
          v-for="choix in options"
          :key="choix"
          class="flex items-center gap-2 text-sm text-slate-700"
        >
          <input
            type="radio"
            :name="identifiant"
            :value="choix"
            :checked="option === choix"
            :disabled="!modifiable"
            @change="emet('saisir', { option: choix })"
          />
          {{ choix }}
        </label>
      </div>

      <div v-else-if="question.type_question === 'choix_multiple'" class="space-y-2">
        <label
          v-for="choix in options"
          :key="choix"
          class="flex items-center gap-2 text-sm text-slate-700"
        >
          <input
            type="checkbox"
            :value="choix"
            :checked="choisies.includes(choix)"
            :disabled="!modifiable"
            @change="basculerOption(choix)"
          />
          {{ choix }}
        </label>
      </div>

      <div v-else-if="question.type_question === 'oui_non'" class="flex gap-2">
        <button
          v-for="choix in [true, false]"
          :key="String(choix)"
          type="button"
          :disabled="!modifiable"
          class="rounded border px-4 py-2 text-sm font-medium disabled:opacity-50"
          :class="
            ouiNon === choix
              ? 'border-slate-900 bg-slate-900 text-white'
              : 'border-slate-300 bg-white text-slate-700'
          "
          @click="emet('saisir', ouiNon === choix ? null : { valeur: choix })"
        >
          {{ choix ? 'Oui' : 'Non' }}
        </button>
      </div>

      <input
        v-else-if="question.type_question === 'date'"
        :id="identifiant"
        :value="dateSaisie"
        :disabled="!modifiable"
        type="date"
        class="rounded border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-50"
        @input="
          emet(
            'saisir',
            ($event.target as HTMLInputElement).value
              ? { date: ($event.target as HTMLInputElement).value }
              : null,
          )
        "
      />

      <p v-else class="text-sm text-amber-700">
        Type de question non pris en charge par cette version de l'interface
        ({{ question.type_question }}).
      </p>
    </div>
  </div>
</template>
