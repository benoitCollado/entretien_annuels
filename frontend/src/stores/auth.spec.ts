/**
 * Tests du store de session.
 *
 * La couche `src/api/` est simulée : c'est précisément ce que permet la règle
 * du §7.4 — un store qui appellerait `fetch` directement ne serait pas testable
 * ainsi.
 */

import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import type { Utilisateur } from '@/types/api'

function profilFactice(surcharges: Partial<Utilisateur> = {}): Utilisateur {
  return {
    id: '01930000-0000-7000-8000-000000000001',
    email: 'claire@example.com',
    nom: 'Bernard',
    prenom: 'Claire',
    nom_complet: 'Claire Bernard',
    poste: 'Responsable RH',
    service: 'Ressources humaines',
    date_entree: null,
    manager_id: null,
    actif: true,
    created_at: '2026-01-01T00:00:00Z',
    roles: [{ code: 'RH', libelle: 'Responsable RH' }],
    permissions: ['utilisateur:lire', 'utilisateur:creer'],
    ...surcharges,
  }
}

describe('store auth', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('démarre déconnecté sans jeton stocké', () => {
    expect(useAuthStore().estConnecte).toBe(false)
  })

  it('stocke le jeton et charge le profil après connexion', async () => {
    vi.spyOn(authApi, 'connexion').mockResolvedValue({
      access_token: 'jeton-abc',
      token_type: 'bearer',
      expires_in: 3600,
    })
    vi.spyOn(authApi, 'profil').mockResolvedValue(profilFactice())

    const store = useAuthStore()
    await store.connexion('claire@example.com', 'MotDePasse')

    expect(store.estConnecte).toBe(true)
    expect(localStorage.getItem('jeton')).toBe('jeton-abc')
    expect(store.utilisateur?.nom_complet).toBe('Claire Bernard')
    expect(store.roles).toEqual(['RH'])
  })

  it('remet le chargement à zéro même quand la connexion échoue', async () => {
    vi.spyOn(authApi, 'connexion').mockRejectedValue(new Error('401'))

    const store = useAuthStore()
    await expect(store.connexion('x@example.com', 'faux')).rejects.toThrow()

    expect(store.chargement).toBe(false)
    expect(store.estConnecte).toBe(false)
  })

  it('autorise selon les permissions du profil', async () => {
    vi.spyOn(authApi, 'profil').mockResolvedValue(profilFactice())

    const store = useAuthStore()
    store.jeton = 'jeton-abc'
    await store.restaurer()

    expect(store.peut('utilisateur:lire')).toBe(true)
    expect(store.peut('utilisateur:archiver')).toBe(false)
  })

  it("n'accorde rien de plus à un administrateur côté client", async () => {
    // Le front ne réplique pas la logique du serveur : il lit les permissions
    // effectives renvoyées par l'API, sans les déduire du rôle.
    vi.spyOn(authApi, 'profil').mockResolvedValue(
      profilFactice({ roles: [{ code: 'ADMIN', libelle: 'Administrateur' }], permissions: [] }),
    )

    const store = useAuthStore()
    store.jeton = 'jeton-abc'
    await store.restaurer()

    expect(store.peut('utilisateur:lire')).toBe(false)
  })

  it('vide la session quand le profil est refusé', async () => {
    vi.spyOn(authApi, 'profil').mockRejectedValue(new Error('401'))
    localStorage.setItem('jeton', 'jeton-perime')

    const store = useAuthStore()
    store.jeton = 'jeton-perime'
    await store.restaurer()

    expect(store.estConnecte).toBe(false)
    expect(localStorage.getItem('jeton')).toBeNull()
  })

  it('efface le jeton à la déconnexion', () => {
    localStorage.setItem('jeton', 'jeton-abc')
    const store = useAuthStore()
    store.jeton = 'jeton-abc'

    store.deconnexion()

    expect(store.estConnecte).toBe(false)
    expect(store.utilisateur).toBeNull()
    expect(localStorage.getItem('jeton')).toBeNull()
  })
})
