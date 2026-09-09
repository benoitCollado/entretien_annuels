import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ErreurHttp, requete } from '@/api/client'

function reponse(statut: number, corps: unknown): Response {
  return new Response(corps === null ? null : JSON.stringify(corps), {
    status: statut,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('couche HTTP', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("n'envoie jamais d'en-tête d'autorisation", async () => {
    const appel = vi.fn().mockResolvedValue(reponse(200, { ok: true }))
    vi.stubGlobal('fetch', appel)

    await requete('/auth/me')

    const entetes = appel.mock.calls[0][1].headers as Record<string, string>
    expect(entetes.Authorization).toBeUndefined()
  })

  it('laisse le navigateur joindre le cookie de session', async () => {
    const appel = vi.fn().mockResolvedValue(reponse(200, {}))
    vi.stubGlobal('fetch', appel)

    await requete('/health')

    expect(appel.mock.calls[0][1].credentials).toBe('include')
  })

  it('ne touche pas au stockage local', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reponse(200, {})))

    await requete('/auth/me')

    expect(localStorage.length).toBe(0)
  })

  it('transforme une erreur métier en ErreurHttp', async () => {

    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockImplementation(async () =>
          reponse(403, { message: 'Permission requise : utilisateur:lire', details: [] }),
        ),
    )

    await expect(requete('/utilisateurs')).rejects.toThrowError(ErreurHttp)
    await expect(requete('/utilisateurs')).rejects.toThrow('Permission requise')

    const erreur: unknown = await requete('/utilisateurs').catch((e: unknown) => e)
    expect(erreur).toBeInstanceOf(ErreurHttp)
    expect((erreur as ErreurHttp).statut).toBe(403)
  })

  it('sait lire le format de validation de FastAPI', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          reponse(422, { detail: [{ msg: 'Champ obligatoire', loc: ['body', 'email'] }] }),
        ),
    )

    await expect(requete('/utilisateurs')).rejects.toThrow('Champ obligatoire')
  })

  it('signale la session expirée sur un 401', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reponse(401, { message: 'Session expirée' })))
    const ecouteur = vi.fn()
    window.addEventListener('session:expiree', ecouteur)

    await expect(requete('/utilisateurs')).rejects.toThrow()

    expect(ecouteur).toHaveBeenCalled()
    window.removeEventListener('session:expiree', ecouteur)
  })

  it('ne signale pas de session expirée sur la route de connexion', async () => {

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reponse(401, { message: 'Identifiants' })))
    const ecouteur = vi.fn()
    window.addEventListener('session:expiree', ecouteur)

    await expect(requete('/auth/login', { sansRedirection: true })).rejects.toThrow()

    expect(ecouteur).not.toHaveBeenCalled()
    window.removeEventListener('session:expiree', ecouteur)
  })
})
