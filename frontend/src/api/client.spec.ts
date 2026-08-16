/** Tests de la couche HTTP : jeton, erreurs, session expirée. */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ErreurHttp, effacerJeton, ecrireJeton, requete } from '@/api/client'

function reponse(statut: number, corps: unknown): Response {
  return new Response(corps === null ? null : JSON.stringify(corps), {
    status: statut,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('couche HTTP', () => {
  beforeEach(() => {
    localStorage.clear()
    effacerJeton()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("ajoute l'en-tête d'autorisation quand un jeton est présent", async () => {
    const appel = vi.fn().mockResolvedValue(reponse(200, { ok: true }))
    vi.stubGlobal('fetch', appel)
    ecrireJeton('jeton-abc')

    await requete('/auth/me')

    const entetes = appel.mock.calls[0][1].headers as Record<string, string>
    expect(entetes.Authorization).toBe('Bearer jeton-abc')
  })

  it("n'ajoute pas d'en-tête sans jeton", async () => {
    const appel = vi.fn().mockResolvedValue(reponse(200, {}))
    vi.stubGlobal('fetch', appel)

    await requete('/health')

    const entetes = appel.mock.calls[0][1].headers as Record<string, string>
    expect(entetes.Authorization).toBeUndefined()
  })

  it('transforme une erreur métier en ErreurHttp', async () => {
    // `mockImplementation` et non `mockResolvedValue` : le corps d'une Response
    // ne se lit qu'une fois, réutiliser la même instance ferait échouer le
    // second appel sur un corps déjà consommé.
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

  it('efface le jeton et signale la session expirée sur un 401', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reponse(401, { message: 'Session expirée' })))
    ecrireJeton('jeton-perime')
    const ecouteur = vi.fn()
    window.addEventListener('session:expiree', ecouteur)

    await expect(requete('/utilisateurs')).rejects.toThrow()

    expect(localStorage.getItem('jeton')).toBeNull()
    expect(ecouteur).toHaveBeenCalled()
    window.removeEventListener('session:expiree', ecouteur)
  })

  it('ne signale pas de session expirée sur la route de connexion', async () => {
    // Sur `/auth/login`, un 401 est une réponse métier normale : rediriger
    // ferait boucler l'écran de connexion sur lui-même.
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reponse(401, { message: 'Identifiants' })))
    const ecouteur = vi.fn()
    window.addEventListener('session:expiree', ecouteur)

    await expect(requete('/auth/login', { sansRedirection: true })).rejects.toThrow()

    expect(ecouteur).not.toHaveBeenCalled()
    window.removeEventListener('session:expiree', ecouteur)
  })
})
