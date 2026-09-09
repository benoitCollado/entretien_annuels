import { defineStore } from 'pinia'
import { ref } from 'vue'

import { ErreurHttp } from '@/api/client'
import { templatesApi } from '@/api/templates'
import type { TemplateResume } from '@/types/api'

export const useTramesStore = defineStore('trames', () => {
  const elements = ref<TemplateResume[]>([])
  const total = ref(0)
  const chargement = ref(false)
  const erreur = ref<string | null>(null)

  async function charger(statut?: string): Promise<void> {
    chargement.value = true
    erreur.value = null
    try {
      const page = await templatesApi.lister(statut)
      elements.value = page.elements
      total.value = page.total
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Chargement impossible.'
    } finally {
      chargement.value = false
    }
  }

  async function creer(
    nom: string,
    typeEntretien: string,
    description: string | null,
  ): Promise<string | null> {
    erreur.value = null
    try {
      const trame = await templatesApi.creer(nom, typeEntretien, description)
      await charger()
      return trame.id
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Création impossible.'
      return null
    }
  }

  async function nouvelleVersion(id: string): Promise<string | null> {
    erreur.value = null
    try {
      const copie = await templatesApi.nouvelleVersion(id)
      await charger()
      return copie.id
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Versionnement impossible.'
      return null
    }
  }

  return { elements, total, chargement, erreur, charger, creer, nouvelleVersion }
})
