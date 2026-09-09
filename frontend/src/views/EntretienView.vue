<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import AppEntete from '@/components/AppEntete.vue'
import BadgeStatut from '@/components/entretien/BadgeStatut.vue'
import BlocObjectifs from '@/components/entretien/BlocObjectifs.vue'
import BlocQuestion from '@/components/entretien/BlocQuestion.vue'
import { useAuthStore } from '@/stores/auth'
import { useQuestionnaireStore } from '@/stores/questionnaire'

const route = useRoute()
const auth = useAuthStore()
const store = useQuestionnaireStore()

const monId = computed(() => auth.utilisateur?.id ?? '')
const messageSucces = ref<string | null>(null)
const syntheseSaisie = ref('')
const observation = ref('')
const formulaireSignature = ref(false)

watch(
  () => route.params.id,
  (id) => {
    if (typeof id === 'string') store.charger(id, monId.value)
  },
  { immediate: true },
)

onUnmounted(() => store.reinitialiser())

const entretien = computed(() => store.entretien)
const questionnaire = computed(() => store.questionnaire)

const nomAutrui = computed(() =>
  store.monRole === 'COLLABORATEUR'
    ? (entretien.value?.manager.nom_complet ?? 'Le manager')
    : (entretien.value?.collaborateur.nom_complet ?? 'Le collaborateur'),
)

const peutCommenter = computed(
  () =>
    store.monRole === 'MANAGER' &&
    ['SOUMIS_COLLABORATEUR', 'REVUE_MANAGER', 'ENTRETIEN_REALISE'].includes(
      entretien.value?.statut ?? '',
    ),
)

const peutSoumettre = computed(
  () => store.monRole === 'COLLABORATEUR' && store.modifiable && !store.contenuMasque,
)

const transitions = computed(() => entretien.value?.transitions_possibles ?? [])

async function enregistrer(): Promise<void> {
  messageSucces.value = null
  if (await store.enregistrer(monId.value)) {
    messageSucces.value = 'Brouillon enregistré.'
  }
}

async function soumettre(): Promise<void> {
  messageSucces.value = null
  if (
    !window.confirm(
      'Une fois transmises, vos réponses ne seront plus modifiables et deviendront visibles par votre manager. Confirmer ?',
    )
  ) {
    return
  }
  if (await store.soumettre(monId.value)) {
    messageSucces.value = 'Vos réponses ont été transmises à votre manager.'
  }
}

async function ouvrirRevue(): Promise<void> {
  messageSucces.value = null
  await store.transitionner('ouvrirRevue', monId.value)
}

async function cloturerEchange(): Promise<void> {
  messageSucces.value = null
  await store.transitionner('cloturerEchange', monId.value)
}

async function signer(): Promise<void> {
  messageSucces.value = null
  if (
    !window.confirm(
      'Signer engage définitivement : après la double signature, plus aucune modification ne sera possible. Confirmer ?',
    )
  ) {
    return
  }
  const texte = observation.value.trim()
  if (await store.signer(texte === '' ? null : texte, monId.value)) {
    observation.value = ''
    formulaireSignature.value = false
    messageSucces.value =
      store.entretien?.statut === 'SIGNE'
        ? 'Entretien signé par les deux parties.'
        : "Votre signature est enregistrée. En attente de l'autre partie."
  }
}

async function cloturer(): Promise<void> {
  messageSucces.value = null
  if (await store.cloturer(monId.value)) {
    messageSucces.value = 'Entretien clôturé.'
  }
}

async function exporter(): Promise<void> {
  messageSucces.value = null
  if (await store.exporterPdf()) {
    messageSucces.value = 'Compte rendu téléchargé.'
  }
}

async function envoyerSynthese(): Promise<void> {
  const contenu = syntheseSaisie.value.trim()
  if (!contenu) return
  if (await store.ecrireSynthese(contenu)) {
    syntheseSaisie.value = ''
    messageSucces.value = 'Synthèse enregistrée.'
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <AppEntete />
    <section class="mx-auto max-w-3xl px-4 py-8">
      <p v-if="store.chargement" class="text-sm text-slate-500">Chargement…</p>

      <p
        v-else-if="!entretien"
        role="alert"
        class="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
      >
        {{ store.erreur ?? 'Entretien introuvable.' }}
      </p>

      <template v-else>
        <header class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 class="text-2xl font-semibold text-slate-900">
              {{ questionnaire?.titre ?? 'Entretien' }}
            </h1>
            <p class="mt-1 text-sm text-slate-600">
              {{ entretien.collaborateur.nom_complet }} · manager
              {{ entretien.manager.nom_complet }}
            </p>
            <p v-if="questionnaire" class="mt-1 text-xs text-slate-400">
              Trame version {{ questionnaire.template_version }} — figée à la création
            </p>
          </div>
          <BadgeStatut :statut="entretien.statut" />
        </header>

        <p
          v-if="store.contenuMasque"
          class="mt-6 rounded border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-900"
        >
          <strong>Réponses non encore transmises.</strong>
          Les réponses de {{ nomAutrui }} ne seront visibles qu'après validation de sa part. Vous
          pouvez préparer les vôtres dès maintenant.
        </p>

        <p
          v-if="store.erreur"
          role="alert"
          class="mt-4 rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
        >
          {{ store.erreur }}
        </p>

        <p
          v-if="messageSucces"
          role="status"
          class="mt-4 rounded border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
        >
          {{ messageSucces }}
        </p>

        <div v-if="questionnaire" class="mt-8 space-y-10">
          <section v-for="section in questionnaire.sections" :key="section.id">
            <h2 class="text-lg font-semibold text-slate-900">{{ section.titre }}</h2>
            <p v-if="section.description" class="mt-1 text-sm text-slate-600">
              {{ section.description }}
            </p>

            <div class="mt-4 space-y-6">
              <BlocQuestion
                v-for="question in section.questions"
                :key="question.id"
                :question="question"
                :valeur="store.brouillon[question.id] ?? null"
                :modifiable="store.modifiable"
                :manquante="store.manquantes.includes(question.id)"
                :a-saisir="store.estAMoi(question)"
                :reponses-autrui="store.reponsesDe(question.id, monId)"
                :commentaires="store.commentairesDe(question.id)"
                :peut-commenter="peutCommenter"
                :nom-autrui="nomAutrui"
                @saisir="store.saisir(question.id, $event)"
                @commenter="store.commenter(question.id, $event)"
              />
            </div>
          </section>

          <BlocObjectifs
            v-if="
              store.objectifsFixes.length ||
              store.objectifsAEvaluer.length ||
              store.peutGererLesObjectifs
            "
            :fixes="store.objectifsFixes"
            :a-evaluer="store.objectifsAEvaluer"
            :modifiable="store.peutGererLesObjectifs"
            @fixer="store.fixerObjectif($event)"
            @evaluer="(id, donnees) => store.evaluerObjectif(id, donnees)"
          />

          <section v-if="entretien.signe_collaborateur_le || entretien.signe_manager_le">
            <h2 class="text-lg font-semibold text-slate-900">Signatures</h2>
            <ul class="mt-3 space-y-2 text-sm text-slate-700">
              <li>
                {{ entretien.collaborateur.nom_complet }} :
                <span v-if="entretien.signe_collaborateur_le" class="font-medium text-emerald-700">
                  signé
                </span>
                <span v-else class="text-slate-400">en attente</span>
              </li>
              <li>
                {{ entretien.manager.nom_complet }} :
                <span v-if="entretien.signe_manager_le" class="font-medium text-emerald-700">
                  signé
                </span>
                <span v-else class="text-slate-400">en attente</span>
              </li>
            </ul>
            <div
              v-if="entretien.observation_collaborateur"
              class="mt-3 rounded-lg bg-slate-100 px-4 py-3"
            >
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-600">
                Observation du collaborateur
              </p>
              <p class="mt-1 whitespace-pre-line text-sm text-slate-800">
                {{ entretien.observation_collaborateur }}
              </p>
            </div>
          </section>

          <section v-if="store.synthese || peutCommenter">
            <h2 class="text-lg font-semibold text-slate-900">Synthèse de l'échange</h2>
            <p
              v-if="store.synthese"
              class="mt-3 whitespace-pre-line rounded-lg bg-amber-50 px-4 py-3 text-sm text-slate-800"
            >
              {{ store.synthese.contenu }}
            </p>
            <div v-else class="mt-3">
              <textarea
                v-model="syntheseSaisie"
                rows="4"
                placeholder="Synthèse partagée de l'entretien…"
                class="w-full rounded border border-slate-300 px-3 py-2 text-sm"
              />
              <button
                type="button"
                :disabled="!syntheseSaisie.trim()"
                class="mt-2 rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
                @click="envoyerSynthese"
              >
                Enregistrer la synthèse
              </button>
            </div>
          </section>
        </div>

        <footer
          class="sticky bottom-0 mt-10 flex flex-wrap gap-3 border-t border-slate-200 bg-white py-4"
        >
          <button
            v-if="store.modifiable"
            type="button"
            :disabled="store.enregistrement || !store.modifie"
            class="rounded border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 disabled:opacity-40"
            @click="enregistrer"
          >
            {{ store.enregistrement ? 'Enregistrement…' : 'Enregistrer le brouillon' }}
          </button>

          <button
            v-if="peutSoumettre"
            type="button"
            class="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white"
            @click="soumettre"
          >
            Valider et transmettre au manager
          </button>

          <button
            v-if="transitions.includes('REVUE_MANAGER')"
            type="button"
            class="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white"
            @click="ouvrirRevue"
          >
            Ouvrir la revue
          </button>

          <button
            v-if="transitions.includes('ENTRETIEN_REALISE')"
            type="button"
            class="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white"
            @click="cloturerEchange"
          >
            Clôturer l'échange
          </button>

          <template v-if="store.peutSigner">
            <div v-if="formulaireSignature" class="flex w-full flex-col gap-2">
              <textarea
                v-if="store.monRole === 'COLLABORATEUR'"
                v-model="observation"
                rows="2"
                placeholder="Observation (facultative — droit de réserve)"
                class="w-full rounded border border-slate-300 px-3 py-2 text-sm"
              />
              <div class="flex gap-2">
                <button
                  type="button"
                  class="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white"
                  @click="signer"
                >
                  Confirmer ma signature
                </button>
                <button
                  type="button"
                  class="text-sm text-slate-500 underline"
                  @click="formulaireSignature = false"
                >
                  Annuler
                </button>
              </div>
            </div>
            <button
              v-else
              type="button"
              class="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white"
              @click="formulaireSignature = true"
            >
              Signer l'entretien
            </button>
          </template>

          <span
            v-else-if="store.dejaSigne && entretien.statut === 'ENTRETIEN_REALISE'"
            class="self-center text-sm text-slate-500"
          >
            Vous avez signé — en attente de l'autre partie.
          </span>

          <button
            v-if="entretien.statut === 'SIGNE' && store.monRole === null"
            type="button"
            class="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white"
            @click="cloturer"
          >
            Clôturer l'entretien
          </button>

          <button
            v-if="store.peutExporter"
            type="button"
            class="rounded border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700"
            @click="exporter"
          >
            Télécharger le compte rendu (PDF)
          </button>

          <span v-if="store.modifie" class="self-center text-xs text-amber-700">
            Modifications non enregistrées
          </span>
        </footer>
      </template>
    </section>
  </div>
</template>
