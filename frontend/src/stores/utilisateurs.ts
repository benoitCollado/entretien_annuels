/** Liste des utilisateurs — état seulement, aucun appel réseau direct. */

import { defineStore } from 'pinia'
import { ref } from 'vue'

import { ErreurHttp } from '@/api/client'
import { utilisateursApi } from '@/api/utilisateurs'
import type { Utilisateur } from '@/types/api'

export const useUtilisateursStore = defineStore('utilisateurs', () => {
  const elements = ref<Utilisateur[]>([])
  const total = ref(0)
  const chargement = ref(false)
  const erreur = ref<string | null>(null)

  async function charger(limite = 50, decalage = 0): Promise<void> {
    chargement.value = true
    erreur.value = null
    try {
      const page = await utilisateursApi.lister(limite, decalage)
      elements.value = page.elements
      total.value = page.total
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Impossible de charger les utilisateurs.'
    } finally {
      chargement.value = false
    }
  }

  return { elements, total, chargement, erreur, charger }
})
