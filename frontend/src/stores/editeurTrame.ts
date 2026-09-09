import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ErreurHttp } from '@/api/client'
import { templatesApi } from '@/api/templates'
import type { Cible, Referentiel, SectionEcrite, Template, TypeQuestion } from '@/types/api'

export interface SectionBrouillon {
  titre: string
  description: string | null
  questions: QuestionBrouillon[]
}

export interface QuestionBrouillon {
  libelle: string
  type_question: TypeQuestion
  cible: Cible
  obligatoire: boolean
  aide: string | null
  configuration: Record<string, unknown>
}

export const TYPES_A_OPTIONS: TypeQuestion[] = ['choix_unique', 'choix_multiple']
export const TYPES_A_BORNES: TypeQuestion[] = ['echelle']

export function questionVide(): QuestionBrouillon {
  return {
    libelle: '',
    type_question: 'texte_libre',
    cible: 'COLLABORATEUR',
    obligatoire: false,
    aide: null,
    configuration: {},
  }
}

export function sectionVide(): SectionBrouillon {
  return { titre: '', description: null, questions: [questionVide()] }
}

export function deplacer<T>(elements: T[], index: number, sens: -1 | 1): boolean {
  const cible = index + sens
  if (cible < 0 || cible >= elements.length) return false
  ;[elements[index], elements[cible]] = [elements[cible], elements[index]]
  return true
}

export const useEditeurTrameStore = defineStore('editeurTrame', () => {
  const trame = ref<Template | null>(null)
  const sections = ref<SectionBrouillon[]>([])
  const referentiel = ref<Referentiel | null>(null)
  const chargement = ref(false)
  const enregistrement = ref(false)
  const erreur = ref<string | null>(null)

  const modifiable = computed(() => trame.value?.est_modifiable ?? false)
  const nombreQuestions = computed(() =>
    sections.value.reduce((total, section) => total + section.questions.length, 0),
  )

  const motifNonPubliable = computed<string | null>(() => {
    if (sections.value.length === 0) return 'Ajoutez au moins une section.'
    const vide = sections.value.findIndex((s) => s.questions.length === 0)
    if (vide >= 0) return `La section ${vide + 1} ne comporte aucune question.`
    const sansTitre = sections.value.findIndex((s) => !s.titre.trim())
    if (sansTitre >= 0) return `La section ${sansTitre + 1} n'a pas de titre.`
    const sansLibelle = sections.value.some((s) => s.questions.some((q) => !q.libelle.trim()))
    if (sansLibelle) return 'Une question est sans libellé.'
    return null
  })

  async function charger(id: string): Promise<void> {
    chargement.value = true
    erreur.value = null
    try {
      const [detail, ref_] = await Promise.all([
        templatesApi.consulter(id),
        templatesApi.referentiel(),
      ])
      trame.value = detail
      referentiel.value = ref_

      sections.value = detail.sections.map((section) => ({
        titre: section.titre,
        description: section.description,
        questions: section.questions.map((question) => ({
          libelle: question.libelle,
          type_question: question.type_question,
          cible: question.cible,
          obligatoire: question.obligatoire,
          aide: question.aide,
          configuration: { ...question.configuration },
        })),
      }))
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Chargement impossible.'
    } finally {
      chargement.value = false
    }
  }

  function ajouterSection(): void {
    sections.value.push(sectionVide())
  }

  function supprimerSection(index: number): void {
    sections.value.splice(index, 1)
  }

  function deplacerSection(index: number, sens: -1 | 1): void {
    deplacer(sections.value, index, sens)
  }

  function ajouterQuestion(indexSection: number): void {
    sections.value[indexSection].questions.push(questionVide())
  }

  function supprimerQuestion(indexSection: number, indexQuestion: number): void {
    sections.value[indexSection].questions.splice(indexQuestion, 1)
  }

  function deplacerQuestion(indexSection: number, indexQuestion: number, sens: -1 | 1): void {
    deplacer(sections.value[indexSection].questions, indexQuestion, sens)
  }

  function changerType(indexSection: number, indexQuestion: number, type: TypeQuestion): void {
    const question = sections.value[indexSection].questions[indexQuestion]
    question.type_question = type
    if (TYPES_A_OPTIONS.includes(type)) {
      question.configuration = { options: ['', ''] }
    } else if (TYPES_A_BORNES.includes(type)) {
      question.configuration = { minimum: 1, maximum: 5 }
    } else {
      question.configuration = {}
    }
  }

  function versStructure(): SectionEcrite[] {
    return sections.value.map((section) => ({
      titre: section.titre,
      description: section.description,
      questions: section.questions.map((question) => ({
        libelle: question.libelle,
        type_question: question.type_question,
        cible: question.cible,
        obligatoire: question.obligatoire,
        aide: question.aide,
        configuration: question.configuration,
      })),
    }))
  }

  async function enregistrer(): Promise<boolean> {
    if (!trame.value) return false
    enregistrement.value = true
    erreur.value = null
    try {
      trame.value = await templatesApi.definirStructure(trame.value.id, versStructure())
      return true
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Enregistrement impossible.'
      return false
    } finally {
      enregistrement.value = false
    }
  }

  async function publier(): Promise<boolean> {
    if (!trame.value) return false
    enregistrement.value = true
    erreur.value = null
    try {

      trame.value = await templatesApi.definirStructure(trame.value.id, versStructure())
      trame.value = await templatesApi.publier(trame.value.id)
      return true
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Publication impossible.'
      return false
    } finally {
      enregistrement.value = false
    }
  }

  return {
    trame,
    sections,
    referentiel,
    chargement,
    enregistrement,
    erreur,
    modifiable,
    nombreQuestions,
    motifNonPubliable,
    charger,
    ajouterSection,
    supprimerSection,
    deplacerSection,
    ajouterQuestion,
    supprimerQuestion,
    deplacerQuestion,
    changerType,
    versStructure,
    enregistrer,
    publier,
  }
})
