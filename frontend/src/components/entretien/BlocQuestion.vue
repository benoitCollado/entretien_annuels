<script setup lang="ts">
import { ref } from 'vue'

import SaisieReponse from '@/components/questions/SaisieReponse.vue'
import type { Commentaire, QuestionInstanciee, Reponse } from '@/types/api'

defineProps<{
  question: QuestionInstanciee
  valeur: Record<string, unknown> | null
  modifiable: boolean
  manquante: boolean
  aSaisir: boolean
  reponsesAutrui: Reponse[]
  commentaires: Commentaire[]
  peutCommenter: boolean
  nomAutrui: string
}>()

const emet = defineEmits<{
  saisir: [valeur: Record<string, unknown> | null]
  commenter: [contenu: string]
}>()

const nouveauCommentaire = ref('')

function envoyer(): void {
  const contenu = nouveauCommentaire.value.trim()
  if (!contenu) return
  emet('commenter', contenu)
  nouveauCommentaire.value = ''
}

function afficher(valeur: Record<string, unknown> | null): string {
  if (!valeur) return '—'
  if (typeof valeur.contenu === 'string') return valeur.contenu
  if (typeof valeur.note === 'number') return `${valeur.note}`
  if (typeof valeur.option === 'string') return valeur.option
  if (Array.isArray(valeur.options)) return (valeur.options as string[]).join(', ')
  if (typeof valeur.valeur === 'boolean') return valeur.valeur ? 'Oui' : 'Non'
  if (typeof valeur.date === 'string') return valeur.date
  return '—'
}
</script>

<template>
  <article class="space-y-3">
    <SaisieReponse
      v-if="aSaisir"
      :question="question"
      :valeur="valeur"
      :modifiable="modifiable"
      :manquante="manquante"
      @saisir="emet('saisir', $event)"
    />

    <div v-else class="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <p class="text-sm font-medium text-slate-700">{{ question.libelle }}</p>
      <p class="mt-1 text-xs text-slate-500">Question destinée à l'autre participant.</p>
    </div>

    <div
      v-for="reponse in reponsesAutrui"
      :key="reponse.auteur_id"
      class="ml-4 rounded-lg border-l-4 border-indigo-300 bg-indigo-50 px-4 py-3"
    >
      <p class="text-xs font-semibold uppercase tracking-wide text-indigo-700">
        {{ nomAutrui }}
      </p>
      <p class="mt-1 whitespace-pre-line text-sm text-slate-800">{{ afficher(reponse.valeur) }}</p>
    </div>

    <div
      v-for="commentaire in commentaires"
      :key="commentaire.id"
      class="ml-4 rounded-lg bg-amber-50 px-4 py-3"
    >
      <p class="text-xs font-semibold text-amber-800">{{ commentaire.auteur_nom }}</p>
      <p class="mt-1 whitespace-pre-line text-sm text-slate-800">{{ commentaire.contenu }}</p>
    </div>

    <div v-if="peutCommenter" class="ml-4 flex gap-2">
      <input
        v-model="nouveauCommentaire"
        type="text"
        placeholder="Ajouter un commentaire…"
        class="flex-1 rounded border border-slate-300 px-3 py-1.5 text-sm"
        @keyup.enter="envoyer"
      />
      <button
        type="button"
        :disabled="!nouveauCommentaire.trim()"
        class="rounded bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-40"
        @click="envoyer"
      >
        Commenter
      </button>
    </div>
  </article>
</template>
