import { requete } from '@/api/client'
import type { Utilisateur } from '@/types/api'

export const authApi = {

  // La réponse ne contient aucun jeton : le serveur le place dans un cookie
  // HttpOnly et renvoie le profil, ce qui évite un aller-retour vers /auth/me.
  connexion(email: string, motDePasse: string): Promise<Utilisateur> {
    return requete<Utilisateur>('/auth/login', {
      methode: 'POST',
      corps: { email, mot_de_passe: motDePasse },
      sansRedirection: true,
    })
  },

  // Seul le serveur peut effacer un cookie HttpOnly.
  deconnexion(): Promise<void> {
    return requete<void>('/auth/logout', { methode: 'POST', sansRedirection: true })
  },

  profil(): Promise<Utilisateur> {
    return requete<Utilisateur>('/auth/me', { sansRedirection: true })
  },
}
