import { defineStore } from 'pinia'
import { ref } from 'vue'

import { campagnesApi, type CampagneEcrite } from '@/api/campagnes'
import { ErreurHttp } from '@/api/client'
import type { Campagne } from '@/types/api'

export const useCampagnesStore = defineStore('campagnes', () => {
  const elements = ref<Campagne[]>([])
  const total = ref(0)
  const chargement = ref(false)
  const erreur = ref<string | null>(null)

  async function charger(): Promise<void> {
    chargement.value = true
    erreur.value = null
    try {
      const page = await campagnesApi.lister()
      elements.value = page.elements
      total.value = page.total
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Chargement impossible.'
    } finally {
      chargement.value = false
    }
  }

  async function creer(donnees: CampagneEcrite): Promise<boolean> {
    erreur.value = null
    try {
      await campagnesApi.creer(donnees)
      await charger()
      return true
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Création impossible.'
      return false
    }
  }

  async function ouvrir(id: string): Promise<boolean> {
    erreur.value = null
    try {
      await campagnesApi.ouvrir(id)
      await charger()
      return true
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Ouverture impossible.'
      return false
    }
  }

  async function cloturer(id: string): Promise<boolean> {
    erreur.value = null
    try {
      await campagnesApi.cloturer(id)
      await charger()
      return true
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Clôture impossible.'
      return false
    }
  }

  return { elements, total, chargement, erreur, charger, creer, ouvrir, cloturer }
})
