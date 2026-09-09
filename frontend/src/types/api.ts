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

export interface Page<T> {
  elements: T[]
  total: number
  limite: number
  decalage: number
}

export interface ErreurApi {
  message: string
  details: unknown[]
}

export type TypeQuestion =
  | 'texte_libre'
  | 'texte_court'
  | 'echelle'
  | 'choix_unique'
  | 'choix_multiple'
  | 'oui_non'
  | 'date'
  | 'note_5'

export type Cible = 'COLLABORATEUR' | 'MANAGER' | 'PARTAGEE'
export type TypeEntretien = 'ANNUEL' | 'PROFESSIONNEL'
export type StatutTemplate = 'BROUILLON' | 'PUBLIEE' | 'ARCHIVEE'
export type StatutCampagne = 'BROUILLON' | 'OUVERTE' | 'CLOTUREE'

export interface Question {
  id: string
  libelle: string
  aide: string | null
  type_question: TypeQuestion
  cible: Cible
  obligatoire: boolean
  ordre: number
  configuration: Record<string, unknown>
}

export interface Section {
  id: string
  titre: string
  description: string | null
  ordre: number
  questions: Question[]
}

export interface TemplateResume {
  id: string
  nom: string
  description: string | null
  type_entretien: TypeEntretien
  version: number
  statut: StatutTemplate
  publie_le: string | null
  created_at: string
  nombre_sections: number
  nombre_questions: number
  est_modifiable: boolean
}

export interface Template extends TemplateResume {
  template_parent_id: string | null
  sections: Section[]
}

export interface QuestionEcrite {
  libelle: string
  type_question: TypeQuestion
  cible: Cible
  obligatoire: boolean
  aide: string | null
  configuration: Record<string, unknown>
}

export interface SectionEcrite {
  titre: string
  description: string | null
  questions: QuestionEcrite[]
}

export interface Referentiel {
  types_question: TypeQuestion[]
  cibles: Cible[]
  types_entretien: TypeEntretien[]
  statuts_template: StatutTemplate[]
}

export interface Campagne {
  id: string
  libelle: string
  description: string | null
  annee: number
  type_entretien: TypeEntretien
  date_ouverture: string
  date_limite: string
  statut: StatutCampagne
  ouverte_le: string | null
  cloturee_le: string | null
  created_at: string
  accepte_des_entretiens: boolean
}

export type StatutEntretien =
  | 'BROUILLON'
  | 'PLANIFIE'
  | 'PREPARATION'
  | 'SOUMIS_COLLABORATEUR'
  | 'REVUE_MANAGER'
  | 'ENTRETIEN_REALISE'
  | 'SIGNE'
  | 'CLOTURE'
  | 'ANNULE'

export type RoleActeur = 'COLLABORATEUR' | 'MANAGER' | 'RH'

export interface Acteur {
  id: string
  nom_complet: string
  email: string
}

export interface EntretienResume {
  id: string
  campagne_id: string
  type_entretien: TypeEntretien
  statut: StatutEntretien
  date_planifiee: string | null
  collaborateur: Acteur
  manager: Acteur
  soumis_collaborateur_le: string | null
  revue_ouverte_le: string | null
  realise_le: string | null

  signe_collaborateur_le: string | null
  signe_manager_le: string | null
  cloture_le: string | null
  created_at: string
}

export interface Entretien extends EntretienResume {
  motif_annulation: string | null
  observation_collaborateur: string | null

  mon_role: RoleActeur | null

  transitions_possibles: string[]
}

export interface QuestionInstanciee extends Question {
  est_ad_hoc: boolean
}

export interface SectionInstanciee {
  id: string
  titre: string
  description: string | null
  ordre: number
  questions: QuestionInstanciee[]
}

export interface Reponse {
  question_id: string
  auteur_id: string
  valeur: Record<string, unknown> | null
  updated_at: string
}

export interface Commentaire {
  id: string
  question_id: string | null
  auteur_id: string
  auteur_nom: string
  contenu: string
  est_synthese: boolean
  created_at: string
}

export interface Questionnaire {
  id: string
  entretien_id: string
  titre: string
  template_version: number
  statut_entretien: StatutEntretien
  sections: SectionInstanciee[]

  reponses: Reponse[]
  commentaires: Commentaire[]

  contenu_masque: boolean
}

export interface StatutCompte {
  statut: StatutEntretien
  nombre: number
}

export interface TableauDeBord {
  campagne_id: string
  campagne_libelle: string
  annee: number
  date_limite: string
  echue: boolean
  total: number
  termines: number
  taux_avancement: number
  par_statut: StatutCompte[]
  en_retard: EntretienResume[]
}

export type StatutObjectif = 'EN_COURS' | 'ATTEINT' | 'PARTIEL' | 'NON_ATTEINT'

export interface Objectif {
  id: string
  entretien_origine_id: string

  entretien_evaluation_id: string | null
  objectif_parent_id: string | null
  collaborateur_id: string
  libelle: string
  description: string | null
  indicateur: string | null
  echeance: string | null
  statut: StatutObjectif
  niveau_atteinte: number | null
  commentaire_evaluation: string | null
  created_at: string
}

export interface ObjectifsDeLEntretien {

  fixes: Objectif[]

  a_evaluer: Objectif[]
}
