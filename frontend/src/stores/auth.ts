/**
 * État de session.
 *
 * ⚠️ Ce store **n'appelle jamais `fetch`** : il passe par `src/api/` (§7.4).
 * C'est ce qui permet de le tester en simulant la couche API, sans serveur ni
 * requête réseau.
 */

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { authApi } from '@/api/auth'
import { ecrireJeton, effacerJeton, lireJeton } from '@/api/client'
import type { Utilisateur } from '@/types/api'

export const useAuthStore = defineStore('auth', () => {
  const utilisateur = ref<Utilisateur | null>(null)
  const jeton = ref<string | null>(lireJeton())
  const chargement = ref(false)

  const estConnecte = computed(() => jeton.value !== null)
  const permissions = computed(() => new Set(utilisateur.value?.permissions ?? []))
  const roles = computed(() => (utilisateur.value?.roles ?? []).map((r) => r.code))

  /**
   * Contrôle d'affichage uniquement.
   *
   * Le serveur reste la **seule autorité** : masquer un bouton évite d'inviter
   * l'utilisateur à une action qui échouerait, mais ne protège rien.
   */
  function peut(permission: string): boolean {
    return permissions.value.has(permission)
  }

  async function connexion(email: string, motDePasse: string): Promise<void> {
    chargement.value = true
    try {
      const reponse = await authApi.connexion(email, motDePasse)
      jeton.value = reponse.access_token
      ecrireJeton(reponse.access_token)
      utilisateur.value = await authApi.profil()
    } finally {
      chargement.value = false
    }
  }

  /** Recharge le profil au démarrage si un jeton est déjà présent. */
  async function restaurer(): Promise<void> {
    if (!jeton.value || utilisateur.value) return
    try {
      utilisateur.value = await authApi.profil()
    } catch {
      // Jeton expiré ou révoqué : on repart d'une session vierge.
      deconnexion()
    }
  }

  function deconnexion(): void {
    utilisateur.value = null
    jeton.value = null
    effacerJeton()
  }

  return {
    utilisateur,
    jeton,
    chargement,
    estConnecte,
    permissions,
    roles,
    peut,
    connexion,
    restaurer,
    deconnexion,
  }
})
