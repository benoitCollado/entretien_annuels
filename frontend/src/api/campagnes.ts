import { requete } from '@/api/client'
import type { Campagne, Page } from '@/types/api'

export interface CampagneEcrite {
  libelle: string
  annee: number
  type_entretien: string
  date_ouverture: string
  date_limite: string
  description: string | null
}

export const campagnesApi = {
  lister(limite = 50, decalage = 0): Promise<Page<Campagne>> {
    return requete<Page<Campagne>>(`/campagnes?limite=${limite}&decalage=${decalage}`)
  },

  creer(donnees: CampagneEcrite): Promise<Campagne> {
    return requete<Campagne>('/campagnes', { methode: 'POST', corps: donnees })
  },

  ouvrir(id: string): Promise<Campagne> {
    return requete<Campagne>(`/campagnes/${id}/ouvrir`, { methode: 'POST' })
  },

  cloturer(id: string): Promise<Campagne> {
    return requete<Campagne>(`/campagnes/${id}/cloturer`, { methode: 'POST' })
  },
}
