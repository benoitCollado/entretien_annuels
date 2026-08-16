/**
 * Couche HTTP — le **seul** endroit du front qui parle à l'API.
 *
 * Règle d'organisation du §7.4 : les stores Pinia n'appellent jamais `fetch`
 * directement. Cette isolation rend les stores testables avec des appels
 * simulés, et concentre en un point la gestion du jeton et des erreurs.
 */

import type { ErreurApi } from '@/types/api'

const BASE_URL = import.meta.env.VITE_API_URL ?? '/api'
const CLE_JETON = 'jeton'

/** Erreur métier remontée par l'API, avec son code HTTP. */
export class ErreurHttp extends Error {
  constructor(
    public readonly statut: number,
    message: string,
    public readonly details: unknown[] = [],
  ) {
    super(message)
    this.name = 'ErreurHttp'
  }
}

export function lireJeton(): string | null {
  return localStorage.getItem(CLE_JETON)
}

export function ecrireJeton(jeton: string): void {
  localStorage.setItem(CLE_JETON, jeton)
}

export function effacerJeton(): void {
  localStorage.removeItem(CLE_JETON)
}

/**
 * Signale une session devenue invalide.
 *
 * La couche HTTP ne connaît pas le routeur : elle émet un événement, et c'est
 * `App.vue` qui décide de rediriger. Sans cette indirection, `client.ts`
 * dépendrait du routeur, qui dépend des vues, qui dépendent des stores, qui
 * dépendent de `client.ts`.
 */
function signalerSessionExpiree(): void {
  window.dispatchEvent(new CustomEvent('session:expiree'))
}

interface Options {
  methode?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  corps?: unknown
  /** Requêtes d'authentification : un 401 y est une réponse métier normale. */
  sansRedirection?: boolean
}

export async function requete<T>(chemin: string, options: Options = {}): Promise<T> {
  const { methode = 'GET', corps, sansRedirection = false } = options

  const entetes: Record<string, string> = { 'Content-Type': 'application/json' }
  const jeton = lireJeton()
  if (jeton) {
    entetes.Authorization = `Bearer ${jeton}`
  }

  const reponse = await fetch(`${BASE_URL}${chemin}`, {
    method: methode,
    headers: entetes,
    body: corps === undefined ? undefined : JSON.stringify(corps),
  })

  if (reponse.status === 401 && !sansRedirection) {
    // Le jeton n'a pas de rafraîchissement (§7.3) : un 401 signifie que la
    // session est terminée, il n'y a rien à rejouer.
    effacerJeton()
    signalerSessionExpiree()
  }

  if (!reponse.ok) {
    const erreur = await lireErreur(reponse)
    throw new ErreurHttp(reponse.status, erreur.message, erreur.details)
  }

  if (reponse.status === 204) {
    return undefined as T
  }
  return (await reponse.json()) as T
}

async function lireErreur(reponse: Response): Promise<ErreurApi> {
  try {
    const corps = await reponse.json()
    if (typeof corps?.message === 'string') {
      return { message: corps.message, details: corps.details ?? [] }
    }
    // 422 de FastAPI : la validation Pydantic remonte sous `detail`, dans une
    // forme différente des erreurs métier.
    if (Array.isArray(corps?.detail)) {
      const premier = corps.detail[0]
      return { message: premier?.msg ?? 'Données invalides', details: corps.detail }
    }
  } catch {
    // Corps vide ou non-JSON : on retombe sur un message générique.
  }
  return { message: `Erreur ${reponse.status}`, details: [] }
}
