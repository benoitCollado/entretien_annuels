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

  it('démarre déconnecté tant que la session n’a pas été vérifiée', () => {
    const store = useAuthStore()
    expect(store.estConnecte).toBe(false)
    expect(store.verifiee).toBe(false)
  })

  it('retient le profil renvoyé par la connexion, sans aucun jeton', async () => {
    vi.spyOn(authApi, 'connexion').mockResolvedValue(profilFactice())

    const store = useAuthStore()
    await store.connexion('claire@example.com', 'MotDePasse')

    expect(store.estConnecte).toBe(true)
    expect(store.utilisateur?.nom_complet).toBe('Claire Bernard')
    expect(store.roles).toEqual(['RH'])
    // Le jeton est dans un cookie HttpOnly : rien ne doit en rester ici.
    expect(localStorage.length).toBe(0)
    expect(JSON.stringify(store.utilisateur)).not.toContain('access_token')
  })

  it('ne rappelle pas le serveur une fois la session vérifiée', async () => {
    const profil = vi.spyOn(authApi, 'profil').mockResolvedValue(profilFactice())

    const store = useAuthStore()
    await store.restaurer()
    await store.restaurer()

    expect(profil).toHaveBeenCalledTimes(1)
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
    await store.restaurer()

    expect(store.peut('utilisateur:lire')).toBe(true)
    expect(store.peut('utilisateur:archiver')).toBe(false)
  })

  it("n'accorde rien de plus à un administrateur côté client", async () => {

    vi.spyOn(authApi, 'profil').mockResolvedValue(
      profilFactice({ roles: [{ code: 'ADMIN', libelle: 'Administrateur' }], permissions: [] }),
    )

    const store = useAuthStore()
    await store.restaurer()

    expect(store.peut('utilisateur:lire')).toBe(false)
  })

  it('reste déconnecté quand le serveur refuse le profil', async () => {
    vi.spyOn(authApi, 'profil').mockRejectedValue(new Error('401'))

    const store = useAuthStore()
    await store.restaurer()

    expect(store.estConnecte).toBe(false)
    expect(store.verifiee).toBe(true)
  })

  it('demande au serveur de fermer la session', async () => {
    vi.spyOn(authApi, 'connexion').mockResolvedValue(profilFactice())
    const sortie = vi.spyOn(authApi, 'deconnexion').mockResolvedValue(undefined)

    const store = useAuthStore()
    await store.connexion('claire@example.com', 'MotDePasse')
    await store.deconnexion()

    // Le cookie étant HttpOnly, seul le serveur peut l'effacer.
    expect(sortie).toHaveBeenCalled()
    expect(store.estConnecte).toBe(false)
    expect(store.utilisateur).toBeNull()
  })

  it('oublie le profil localement quand la session a déjà expiré', async () => {
    vi.spyOn(authApi, 'connexion').mockResolvedValue(profilFactice())
    const sortie = vi.spyOn(authApi, 'deconnexion').mockResolvedValue(undefined)

    const store = useAuthStore()
    await store.connexion('claire@example.com', 'MotDePasse')
    store.oublier()

    expect(store.estConnecte).toBe(false)
    expect(sortie).not.toHaveBeenCalled()
  })
})
