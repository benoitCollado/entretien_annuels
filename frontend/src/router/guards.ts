import type { NavigationGuardWithThis, RouteLocationNormalized } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {

    publique?: boolean

    permission?: string
  }
}

export const gardeAuthentification: NavigationGuardWithThis<undefined> = async (
  vers: RouteLocationNormalized,
) => {
  const auth = useAuthStore()

  // Le cookie étant illisible depuis le navigateur, l'existence d'une session
  // se vérifie auprès du serveur avant toute décision. L'appel n'a lieu qu'une
  // fois par chargement de page.
  await auth.restaurer()

  if (vers.meta.publique) {
    return auth.estConnecte && vers.name === 'connexion' ? { name: 'utilisateurs' } : true
  }

  if (!auth.estConnecte) {
    return { name: 'connexion', query: { redirection: vers.fullPath } }
  }

  if (vers.meta.permission && !auth.peut(vers.meta.permission)) {
    return { name: 'interdit' }
  }

  return true
}
