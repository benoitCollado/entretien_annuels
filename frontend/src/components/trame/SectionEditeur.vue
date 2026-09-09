<script setup lang="ts">
import QuestionEditeur from '@/components/trame/QuestionEditeur.vue'
import type { SectionBrouillon } from '@/stores/editeurTrame'
import type { Referentiel, TypeQuestion } from '@/types/api'

const section = defineModel<SectionBrouillon>({ required: true })

defineProps<{
  index: number
  total: number
  referentiel: Referentiel | null
  modifiable: boolean
}>()

const emet = defineEmits<{
  supprimer: []
  deplacer: [sens: -1 | 1]
  ajouterQuestion: []
  supprimerQuestion: [indexQuestion: number]
  deplacerQuestion: [indexQuestion: number, sens: -1 | 1]
  changerType: [indexQuestion: number, type: TypeQuestion]
}>()
</script>

<template>
  <section class="rounded-lg border border-slate-200 bg-white p-4">
    <div class="mb-3 flex items-start gap-3">
      <span class="mt-2 text-sm font-semibold text-slate-400">{{ index + 1 }}</span>

      <div class="grid flex-1 gap-2">
        <input
          v-model="section.titre"
          :disabled="!modifiable"
          placeholder="Titre de la section"
          class="w-full rounded-md border border-slate-300 px-3 py-2 font-medium disabled:bg-slate-100"
        />
        <input
          :value="section.description ?? ''"
          :disabled="!modifiable"
          placeholder="Description (facultative)"
          class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100"
          @input="section.description = ($event.target as HTMLInputElement).value || null"
        />
      </div>

      <div v-if="modifiable" class="flex flex-col gap-1">
        <button
          type="button"
          :disabled="index === 0"
          class="rounded border border-slate-300 px-2 text-xs disabled:opacity-30"
          title="Monter la section"
          @click="emet('deplacer', -1)"
        >
          ↑
        </button>
        <button
          type="button"
          :disabled="index === total - 1"
          class="rounded border border-slate-300 px-2 text-xs disabled:opacity-30"
          title="Descendre la section"
          @click="emet('deplacer', 1)"
        >
          ↓
        </button>
        <button
          type="button"
          class="rounded border border-red-200 px-2 text-xs text-red-600"
          title="Supprimer la section"
          @click="emet('supprimer')"
        >
          ✕
        </button>
      </div>
    </div>

    <div class="grid gap-2 pl-6">
      <QuestionEditeur
        v-for="(_, indexQuestion) in section.questions"
        :key="indexQuestion"
        v-model="section.questions[indexQuestion]"
        :index="indexQuestion"
        :total="section.questions.length"
        :referentiel="referentiel"
        :modifiable="modifiable"
        @supprimer="emet('supprimerQuestion', indexQuestion)"
        @deplacer="(sens) => emet('deplacerQuestion', indexQuestion, sens)"
        @changer-type="(type) => emet('changerType', indexQuestion, type)"
      />

      <p v-if="section.questions.length === 0" class="text-sm text-amber-700">
        Cette section est vide — la trame ne pourra pas être publiée.
      </p>

      <button
        v-if="modifiable"
        type="button"
        class="justify-self-start rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
        @click="emet('ajouterQuestion')"
      >
        + Ajouter une question
      </button>
    </div>
  </section>
</template>
