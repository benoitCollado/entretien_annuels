import { requete } from '@/api/client'
import type { Page, Utilisateur } from '@/types/api'

export const utilisateursApi = {
  lister(limite = 50, decalage = 0): Promise<Page<Utilisateur>> {
    return requete<Page<Utilisateur>>(`/utilisateurs?limite=${limite}&decalage=${decalage}`)
  },
}
