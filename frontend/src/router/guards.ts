import type { NavigationGuardWithThis, RouteLocationNormalized } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    /** Accessible sans session. */
    publique?: boolean
    /** Permission exigée pour afficher la vue. */
    permission?: string
  }
}

/**
 * Garde d'authentification et de permission.
 *
 * ⚠️ Confort d'affichage, **pas** un contrôle de sécurité : le serveur reste la
 * seule autorité. Cette garde évite d'ouvrir une page qui n'afficherait qu'une
 * erreur 403, elle ne protège aucune donnée.
 */
export const gardeAuthentification: NavigationGuardWithThis<undefined> = async (
  vers: RouteLocationNormalized,
) => {
  const auth = useAuthStore()

  if (vers.meta.publique) {
    // Déjà connecté : inutile de réafficher l'écran de connexion.
    return auth.estConnecte && vers.name === 'connexion' ? { name: 'utilisateurs' } : true
  }

  if (!auth.estConnecte) {
    return { name: 'connexion', query: { redirection: vers.fullPath } }
  }

  // Le profil porte les permissions : il doit être chargé avant de les évaluer.
  await auth.restaurer()

  if (!auth.estConnecte) {
    return { name: 'connexion', query: { redirection: vers.fullPath } }
  }

  if (vers.meta.permission && !auth.peut(vers.meta.permission)) {
    return { name: 'interdit' }
  }

  return true
}
