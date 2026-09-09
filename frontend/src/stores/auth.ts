import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { authApi } from '@/api/auth'
import type { Utilisateur } from '@/types/api'

export const useAuthStore = defineStore('auth', () => {
  const utilisateur = ref<Utilisateur | null>(null)
  const chargement = ref(false)
  // Le cookie de session est HttpOnly : rien ici ne peut le lire. Le seul moyen
  // de savoir si une session existe est de le demander au serveur, et ce drapeau
  // évite de le refaire à chaque navigation.
  const verifiee = ref(false)

  const estConnecte = computed(() => utilisateur.value !== null)
  const permissions = computed(() => new Set(utilisateur.value?.permissions ?? []))
  const roles = computed(() => (utilisateur.value?.roles ?? []).map((r) => r.code))

  function peut(permission: string): boolean {
    return permissions.value.has(permission)
  }

  async function connexion(email: string, motDePasse: string): Promise<void> {
    chargement.value = true
    try {
      utilisateur.value = await authApi.connexion(email, motDePasse)
      verifiee.value = true
    } finally {
      chargement.value = false
    }
  }

  async function restaurer(): Promise<void> {
    if (verifiee.value) return
    try {
      utilisateur.value = await authApi.profil()
    } catch {

      utilisateur.value = null
    } finally {
      verifiee.value = true
    }
  }

  async function deconnexion(): Promise<void> {
    // Seul le serveur peut effacer le cookie ; l'état local ne suffirait pas.
    try {
      await authApi.deconnexion()
    } finally {
      oublier()
    }
  }

  // Session déjà close côté serveur : inutile de rappeler l'API.
  function oublier(): void {
    utilisateur.value = null
    verifiee.value = true
  }

  return {
    utilisateur,
    chargement,
    verifiee,
    estConnecte,
    permissions,
    roles,
    peut,
    connexion,
    restaurer,
    deconnexion,
    oublier,
  }
})
