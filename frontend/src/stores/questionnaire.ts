import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ErreurHttp } from '@/api/client'
import {
  entretiensApi,
  type EvaluationEcrite,
  type ObjectifEcrit,
  type ReponseEcrite,
} from '@/api/entretiens'
import type { Entretien, Objectif, Questionnaire, QuestionInstanciee } from '@/types/api'

export const useQuestionnaireStore = defineStore('questionnaire', () => {
  const entretien = ref<Entretien | null>(null)
  const questionnaire = ref<Questionnaire | null>(null)
  const chargement = ref(false)
  const enregistrement = ref(false)
  const erreur = ref<string | null>(null)

  const manquantes = ref<string[]>([])

  const brouillon = ref<Record<string, Record<string, unknown> | null>>({})
  const modifie = ref(false)

  const objectifsFixes = ref<Objectif[]>([])
  const objectifsAEvaluer = ref<Objectif[]>([])

  const monRole = computed(() => entretien.value?.mon_role ?? null)
  const statut = computed(() => entretien.value?.statut ?? null)

  const contenuMasque = computed(() => questionnaire.value?.contenu_masque ?? false)

  function estAMoi(question: QuestionInstanciee): boolean {
    if (monRole.value === 'COLLABORATEUR') {
      return question.cible === 'COLLABORATEUR' || question.cible === 'PARTAGEE'
    }
    if (monRole.value === 'MANAGER') {
      return question.cible === 'MANAGER' || question.cible === 'PARTAGEE'
    }
    return false
  }

  const modifiable = computed(() => {
    if (!entretien.value) return false
    if (monRole.value === 'COLLABORATEUR') {
      return ['PLANIFIE', 'PREPARATION'].includes(entretien.value.statut)
    }
    if (monRole.value === 'MANAGER') {
      return ['PLANIFIE', 'PREPARATION', 'SOUMIS_COLLABORATEUR', 'REVUE_MANAGER'].includes(
        entretien.value.statut,
      )
    }
    return false
  })

  function mesReponses(monId: string): Record<string, Record<string, unknown> | null> {
    const par: Record<string, Record<string, unknown> | null> = {}
    for (const reponse of questionnaire.value?.reponses ?? []) {
      if (reponse.auteur_id === monId) par[reponse.question_id] = reponse.valeur
    }
    return par
  }

  function reponsesDe(question_id: string, sauf: string) {
    return (questionnaire.value?.reponses ?? []).filter(
      (r) => r.question_id === question_id && r.auteur_id !== sauf,
    )
  }

  function commentairesDe(question_id: string) {
    return (questionnaire.value?.commentaires ?? []).filter((c) => c.question_id === question_id)
  }

  const synthese = computed(() =>
    (questionnaire.value?.commentaires ?? []).find((c) => c.est_synthese),
  )

  const dejaSigne = computed(() => {
    if (!entretien.value) return false
    return monRole.value === 'COLLABORATEUR'
      ? entretien.value.signe_collaborateur_le !== null
      : entretien.value.signe_manager_le !== null
  })

  const peutSigner = computed(() => {
    if (!entretien.value || entretien.value.statut !== 'ENTRETIEN_REALISE') return false
    if (monRole.value !== 'COLLABORATEUR' && monRole.value !== 'MANAGER') return false
    return !dejaSigne.value
  })

  const peutExporter = computed(() => ['SIGNE', 'CLOTURE'].includes(entretien.value?.statut ?? ''))

  const peutGererLesObjectifs = computed(
    () =>
      monRole.value === 'MANAGER' &&
      ['REVUE_MANAGER', 'ENTRETIEN_REALISE'].includes(entretien.value?.statut ?? ''),
  )

  async function charger(entretienId: string, monId: string): Promise<void> {
    chargement.value = true
    erreur.value = null
    manquantes.value = []
    try {

      entretien.value = await entretiensApi.recuperer(entretienId)
      questionnaire.value = await entretiensApi.questionnaire(entretienId)
      brouillon.value = mesReponses(monId)
      modifie.value = false
      await chargerObjectifs()
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Chargement impossible.'
    } finally {
      chargement.value = false
    }
  }

  function saisir(questionId: string, valeur: Record<string, unknown> | null): void {
    brouillon.value = { ...brouillon.value, [questionId]: valeur }
    modifie.value = true
  }

  function aRepondu(questionId: string): boolean {
    const valeur = brouillon.value[questionId]
    if (valeur === null || valeur === undefined) return false
    return Object.values(valeur).some(
      (v) => v !== null && v !== undefined && v !== '' && !(Array.isArray(v) && v.length === 0),
    )
  }

  function aEnvoyer(): ReponseEcrite[] {
    return Object.entries(brouillon.value).map(([question_id, valeur]) => ({
      question_id,
      valeur,
    }))
  }

  async function enregistrer(monId: string): Promise<boolean> {
    const reponses = aEnvoyer()
    if (reponses.length === 0) return true
    enregistrement.value = true
    erreur.value = null
    try {
      questionnaire.value = await entretiensApi.enregistrerBrouillon(entretien.value!.id, reponses)

      entretien.value = await entretiensApi.recuperer(entretien.value!.id)
      brouillon.value = mesReponses(monId)
      modifie.value = false
      return true
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Enregistrement impossible.'
      return false
    } finally {
      enregistrement.value = false
    }
  }

  async function soumettre(monId: string): Promise<boolean> {
    if (modifie.value && !(await enregistrer(monId))) return false
    erreur.value = null
    manquantes.value = []
    try {
      entretien.value = await entretiensApi.soumettre(entretien.value!.id)
      questionnaire.value = await entretiensApi.questionnaire(entretien.value.id)
      return true
    } catch (e) {
      if (e instanceof ErreurHttp) {
        erreur.value = e.message
        manquantes.value = (e.details ?? [])
          .map((d) => (d as { question_id?: string }).question_id)
          .filter((id): id is string => typeof id === 'string')
      } else {
        erreur.value = 'Validation impossible.'
      }
      return false
    }
  }

  async function transitionner(
    action: 'ouvrirRevue' | 'cloturerEchange',
    monId: string,
  ): Promise<boolean> {
    erreur.value = null
    try {
      entretien.value = await entretiensApi[action](entretien.value!.id)
      questionnaire.value = await entretiensApi.questionnaire(entretien.value.id)
      brouillon.value = mesReponses(monId)
      return true
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Action impossible.'
      return false
    }
  }

  async function commenter(questionId: string, contenu: string): Promise<boolean> {
    erreur.value = null
    try {
      await entretiensApi.commenter(entretien.value!.id, questionId, contenu)
      questionnaire.value = await entretiensApi.questionnaire(entretien.value!.id)
      return true
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Commentaire impossible.'
      return false
    }
  }

  async function ecrireSynthese(contenu: string): Promise<boolean> {
    erreur.value = null
    try {
      await entretiensApi.ecrireSynthese(entretien.value!.id, contenu)
      questionnaire.value = await entretiensApi.questionnaire(entretien.value!.id)
      return true
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Synthèse impossible.'
      return false
    }
  }

  async function chargerObjectifs(): Promise<void> {
    if (!entretien.value) return
    try {
      const vue = await entretiensApi.objectifs(entretien.value.id)
      objectifsFixes.value = vue.fixes
      objectifsAEvaluer.value = vue.a_evaluer
    } catch {

      objectifsFixes.value = []
      objectifsAEvaluer.value = []
    }
  }

  async function fixerObjectif(donnees: ObjectifEcrit): Promise<boolean> {
    erreur.value = null
    try {
      await entretiensApi.fixerObjectif(entretien.value!.id, donnees)
      await chargerObjectifs()
      return true
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Objectif non enregistré.'
      return false
    }
  }

  async function evaluerObjectif(
    objectifId: string,
    donnees: Omit<EvaluationEcrite, 'entretien_id'>,
  ): Promise<boolean> {
    erreur.value = null
    try {
      await entretiensApi.evaluerObjectif(objectifId, {
        ...donnees,

        entretien_id: entretien.value!.id,
      })
      await chargerObjectifs()
      return true
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Évaluation impossible.'
      return false
    }
  }

  async function signer(observation: string | null, monId: string): Promise<boolean> {
    erreur.value = null
    try {
      entretien.value = await entretiensApi.signer(entretien.value!.id, observation)
      questionnaire.value = await entretiensApi.questionnaire(entretien.value.id)
      brouillon.value = mesReponses(monId)
      return true
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Signature impossible.'
      return false
    }
  }

  async function cloturer(monId: string): Promise<boolean> {
    erreur.value = null
    try {
      entretien.value = await entretiensApi.cloturer(entretien.value!.id)
      questionnaire.value = await entretiensApi.questionnaire(entretien.value.id)
      brouillon.value = mesReponses(monId)
      return true
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Clôture impossible.'
      return false
    }
  }

  async function exporterPdf(): Promise<boolean> {
    erreur.value = null
    try {
      const { contenu, nomFichier } = await entretiensApi.exporterPdf(entretien.value!.id)
      const url = URL.createObjectURL(contenu)
      const lien = document.createElement('a')
      lien.href = url
      lien.download = nomFichier
      lien.click()
      URL.revokeObjectURL(url)
      return true
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Export impossible.'
      return false
    }
  }

  function reinitialiser(): void {
    entretien.value = null
    questionnaire.value = null
    brouillon.value = {}
    modifie.value = false
    erreur.value = null
    manquantes.value = []
    objectifsFixes.value = []
    objectifsAEvaluer.value = []
  }

  return {
    entretien,
    questionnaire,
    chargement,
    enregistrement,
    erreur,
    manquantes,
    brouillon,
    modifie,
    monRole,
    statut,
    contenuMasque,
    modifiable,
    synthese,
    objectifsFixes,
    objectifsAEvaluer,
    dejaSigne,
    peutSigner,
    peutExporter,
    peutGererLesObjectifs,
    estAMoi,
    aRepondu,
    reponsesDe,
    commentairesDe,
    charger,
    saisir,
    enregistrer,
    soumettre,
    transitionner,
    commenter,
    ecrireSynthese,
    chargerObjectifs,
    fixerObjectif,
    evaluerObjectif,
    signer,
    cloturer,
    exporterPdf,
    reinitialiser,
  }
})
