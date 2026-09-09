import type { ErreurApi } from '@/types/api'

const BASE_URL = import.meta.env.VITE_API_URL ?? '/api'

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

function signalerSessionExpiree(): void {
  window.dispatchEvent(new CustomEvent('session:expiree'))
}

interface Options {
  methode?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  corps?: unknown

  sansRedirection?: boolean
}

// Le jeton vit dans un cookie HttpOnly : il est invisible ici et le navigateur
// le joint lui-même. `credentials: 'include'` couvre le cas où l'API est servie
// depuis une autre origine que le client.
const OPTIONS_COMMUNES: RequestInit = { credentials: 'include' }

export async function requete<T>(chemin: string, options: Options = {}): Promise<T> {
  const { methode = 'GET', corps, sansRedirection = false } = options

  const reponse = await fetch(`${BASE_URL}${chemin}`, {
    ...OPTIONS_COMMUNES,
    method: methode,
    headers: { 'Content-Type': 'application/json' },
    body: corps === undefined ? undefined : JSON.stringify(corps),
  })

  if (reponse.status === 401 && !sansRedirection) {
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

export async function telecharger(
  chemin: string,
): Promise<{ contenu: Blob; nomFichier: string }> {
  const reponse = await fetch(`${BASE_URL}${chemin}`, OPTIONS_COMMUNES)

  if (reponse.status === 401) {
    signalerSessionExpiree()
  }
  if (!reponse.ok) {
    const erreur = await lireErreur(reponse)
    throw new ErreurHttp(reponse.status, erreur.message, erreur.details)
  }

  return {
    contenu: await reponse.blob(),
    nomFichier: nomDepuisEntete(reponse.headers.get('content-disposition')),
  }
}

function nomDepuisEntete(entete: string | null): string {
  const trouve = entete?.match(/filename="([^"]+)"/)
  return trouve?.[1] ?? 'compte-rendu.pdf'
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
