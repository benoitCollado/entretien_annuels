import { requete } from '@/api/client'
import type { Jeton, Utilisateur } from '@/types/api'

export const authApi = {
  /** `sansRedirection` : sur cet appel, un 401 est une réponse attendue. */
  connexion(email: string, motDePasse: string): Promise<Jeton> {
    return requete<Jeton>('/auth/login', {
      methode: 'POST',
      corps: { email, mot_de_passe: motDePasse },
      sansRedirection: true,
    })
  },

  profil(): Promise<Utilisateur> {
    return requete<Utilisateur>('/auth/me')
  },
}
