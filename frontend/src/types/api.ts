/**
 * Types du contrat HTTP.
 *
 * À terme, ce fichier sera **généré depuis l'OpenAPI** de FastAPI avec
 * `openapi-typescript` : un seul contrat, aucune dérive possible entre le front
 * et le back (§7.4). Il est écrit à la main pour l'instant, le temps que la
 * surface d'API se stabilise.
 */

export interface Role {
  code: string
  libelle: string
}

export interface Utilisateur {
  id: string
  email: string
  nom: string
  prenom: string
  nom_complet: string
  poste: string | null
  service: string | null
  date_entree: string | null
  manager_id: string | null
  actif: boolean
  created_at: string
  roles: Role[]
  permissions: string[]
}

export interface Jeton {
  access_token: string
  token_type: string
  expires_in: number
}

export interface Page<T> {
  elements: T[]
  total: number
  limite: number
  decalage: number
}

/** Forme unique des erreurs, produite par `core.gestion_erreurs` côté API. */
export interface ErreurApi {
  message: string
  details: unknown[]
}
