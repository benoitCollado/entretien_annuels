import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { ErreurHttp } from '@/api/client'
import { entretiensApi, type FiltreEntretiens } from '@/api/entretiens'
import type { EntretienResume } from '@/types/api'

export const useEntretiensStore = defineStore('entretiens', () => {
  const elements = ref<EntretienResume[]>([])
  const total = ref(0)
  const chargement = ref(false)
  const erreur = ref<string | null>(null)
  const filtre = ref<FiltreEntretiens>({})

  async function charger(nouveauFiltre: FiltreEntretiens = {}): Promise<void> {
    filtre.value = nouveauFiltre
    chargement.value = true
    erreur.value = null
    try {
      const page = await entretiensApi.lister(nouveauFiltre)
      elements.value = page.elements
      total.value = page.total
    } catch (e) {
      erreur.value = e instanceof ErreurHttp ? e.message : 'Chargement impossible.'
    } finally {
      chargement.value = false
    }
  }

  const aTraiter = computed(() =>
    elements.value.filter((e) =>
      ['PLANIFIE', 'PREPARATION', 'SOUMIS_COLLABORATEUR', 'REVUE_MANAGER'].includes(e.statut),
    ),
  )

  const termines = computed(() =>
    elements.value.filter((e) => ['SIGNE', 'CLOTURE'].includes(e.statut)),
  )

  return { elements, total, chargement, erreur, filtre, aTraiter, termines, charger }
})
