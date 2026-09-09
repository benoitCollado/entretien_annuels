<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppEntete from '@/components/AppEntete.vue'
import SectionEditeur from '@/components/trame/SectionEditeur.vue'
import { useEditeurTrameStore } from '@/stores/editeurTrame'

const editeur = useEditeurTrameStore()
const route = useRoute()
const router = useRouter()

onMounted(() => editeur.charger(route.params.id as string))

async function publier() {
  if (await editeur.publier()) {
    await router.push({ name: 'trames' })
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <AppEntete />

    <main class="mx-auto max-w-4xl p-6">
      <p v-if="editeur.chargement" class="text-sm text-slate-500">Chargement…</p>

      <template v-else-if="editeur.trame">
        <div class="mb-4 flex items-start justify-between gap-4">
          <div>
            <h1 class="text-lg font-semibold text-slate-900">
              {{ editeur.trame.nom }}
              <span class="text-slate-400">v{{ editeur.trame.version }}</span>
            </h1>
            <p class="text-sm text-slate-500">
              {{ editeur.trame.type_entretien }} · {{ editeur.trame.statut }} ·
              {{ editeur.nombreQuestions }} question(s)
            </p>
          </div>
          <RouterLink :to="{ name: 'trames' }" class="text-sm text-slate-600 underline">
            Retour
          </RouterLink>
        </div>

        <div
          v-if="!editeur.modifiable"
          class="mb-4 rounded-md border border-slate-200 bg-white p-3 text-sm text-slate-600"
        >
          Cette trame est <strong>publiée</strong>, donc immuable. Pour la faire évoluer, créez-en
          une nouvelle version depuis la liste — les entretiens déjà instanciés ne seront pas
          affectés.
        </div>

        <p v-if="editeur.erreur" role="alert" class="mb-4 text-sm text-red-600">
          {{ editeur.erreur }}
        </p>

        <div class="grid gap-4">
          <SectionEditeur
            v-for="(_, index) in editeur.sections"
            :key="index"
            v-model="editeur.sections[index]"
            :index="index"
            :total="editeur.sections.length"
            :referentiel="editeur.referentiel"
            :modifiable="editeur.modifiable"
            @supprimer="editeur.supprimerSection(index)"
            @deplacer="(sens) => editeur.deplacerSection(index, sens)"
            @ajouter-question="editeur.ajouterQuestion(index)"
            @supprimer-question="(iq) => editeur.supprimerQuestion(index, iq)"
            @deplacer-question="(iq, sens) => editeur.deplacerQuestion(index, iq, sens)"
            @changer-type="(iq, type) => editeur.changerType(index, iq, type)"
          />

          <p v-if="editeur.sections.length === 0" class="text-sm text-slate-500">
            Aucune section pour l'instant.
          </p>

          <button
            v-if="editeur.modifiable"
            type="button"
            class="justify-self-start rounded-md border border-slate-300 bg-white px-4 py-2 text-sm hover:bg-slate-50"
            @click="editeur.ajouterSection()"
          >
            + Ajouter une section
          </button>
        </div>

        <div
          v-if="editeur.modifiable"
          class="mt-6 flex items-center gap-3 border-t border-slate-200 pt-4"
        >
          <button
            type="button"
            :disabled="editeur.enregistrement"
            class="rounded-md bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
            @click="editeur.enregistrer()"
          >
            {{ editeur.enregistrement ? 'Enregistrement…' : 'Enregistrer' }}
          </button>

          <button
            type="button"
            :disabled="editeur.enregistrement || editeur.motifNonPubliable !== null"
            class="rounded-md border border-emerald-600 px-4 py-2 text-sm text-emerald-700 disabled:opacity-40"
            :title="editeur.motifNonPubliable ?? 'Publier la trame'"
            @click="publier"
          >
            Publier
          </button>

          <span v-if="editeur.motifNonPubliable" class="text-sm text-amber-700">
            {{ editeur.motifNonPubliable }}
          </span>
        </div>
      </template>

      <p v-else-if="editeur.erreur" role="alert" class="text-sm text-red-600">
        {{ editeur.erreur }}
      </p>
    </main>
  </div>
</template>
