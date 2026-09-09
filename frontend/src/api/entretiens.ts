import { requete, telecharger } from '@/api/client'
import type {
  Cible,
  Commentaire,
  Entretien,
  EntretienResume,
  Objectif,
  ObjectifsDeLEntretien,
  Page,
  Questionnaire,
  StatutObjectif,
  TableauDeBord,
  TypeQuestion,
} from '@/types/api'

export interface FiltreEntretiens {
  campagne_id?: string
  statut?: string
  limite?: number
  decalage?: number
}

export interface EntretienCree {
  campagne_id: string
  collaborateur_id: string
  template_id: string
  manager_id?: string | null
  date_planifiee?: string | null
}

export interface ReponseEcrite {
  question_id: string
  valeur: Record<string, unknown> | null
}

export interface ObjectifEcrit {
  libelle: string
  description?: string | null
  indicateur?: string | null
  echeance?: string | null
  objectif_parent_id?: string | null
}

export interface EvaluationEcrite {

  entretien_id: string
  statut: StatutObjectif
  niveau_atteinte?: number | null
  commentaire?: string | null
}

export interface QuestionAdHocEcrite {
  section_id: string
  libelle: string
  type_question: TypeQuestion
  cible: Cible
  obligatoire: boolean
  aide: string | null
  configuration: Record<string, unknown>
}

function chaineDeRequete(filtre: FiltreEntretiens): string {
  const parametres = new URLSearchParams()

  for (const [cle, valeur] of Object.entries(filtre)) {
    if (valeur !== undefined && valeur !== null && valeur !== '') {
      parametres.set(cle, String(valeur))
    }
  }
  const chaine = parametres.toString()
  return chaine ? `?${chaine}` : ''
}

export const entretiensApi = {
  lister(filtre: FiltreEntretiens = {}): Promise<Page<EntretienResume>> {
    return requete<Page<EntretienResume>>(`/entretiens${chaineDeRequete(filtre)}`)
  },

  recuperer(id: string): Promise<Entretien> {
    return requete<Entretien>(`/entretiens/${id}`)
  },

  questionnaire(id: string): Promise<Questionnaire> {
    return requete<Questionnaire>(`/entretiens/${id}/questionnaire`)
  },

  creer(donnees: EntretienCree): Promise<Entretien> {
    return requete<Entretien>('/entretiens', { methode: 'POST', corps: donnees })
  },

  enregistrerBrouillon(id: string, reponses: ReponseEcrite[]): Promise<Questionnaire> {
    return requete<Questionnaire>(`/entretiens/${id}/reponses`, {
      methode: 'PUT',
      corps: { reponses },
    })
  },

  soumettre(id: string): Promise<Entretien> {
    return requete<Entretien>(`/entretiens/${id}/soumettre`, { methode: 'POST' })
  },

  ouvrirRevue(id: string): Promise<Entretien> {
    return requete<Entretien>(`/entretiens/${id}/revue`, { methode: 'POST' })
  },

  cloturerEchange(id: string): Promise<Entretien> {
    return requete<Entretien>(`/entretiens/${id}/cloturer-echange`, { methode: 'POST' })
  },

  annuler(id: string, motif: string): Promise<Entretien> {
    return requete<Entretien>(`/entretiens/${id}/annuler`, {
      methode: 'POST',
      corps: { motif },
    })
  },

  ajouterQuestion(id: string, donnees: QuestionAdHocEcrite): Promise<Questionnaire> {
    return requete<Questionnaire>(`/entretiens/${id}/questions`, {
      methode: 'POST',
      corps: donnees,
    })
  },

  commenter(id: string, questionId: string, contenu: string): Promise<Commentaire> {
    return requete<Commentaire>(`/entretiens/${id}/questions/${questionId}/commentaires`, {
      methode: 'POST',
      corps: { contenu },
    })
  },

  signer(id: string, observation?: string | null): Promise<Entretien> {
    return requete<Entretien>(`/entretiens/${id}/signer`, {
      methode: 'POST',
      corps: { observation: observation ?? null },
    })
  },

  cloturer(id: string): Promise<Entretien> {
    return requete<Entretien>(`/entretiens/${id}/cloturer`, { methode: 'POST' })
  },

  objectifs(id: string): Promise<ObjectifsDeLEntretien> {
    return requete<ObjectifsDeLEntretien>(`/entretiens/${id}/objectifs`)
  },

  fixerObjectif(id: string, donnees: ObjectifEcrit): Promise<Objectif> {
    return requete<Objectif>(`/entretiens/${id}/objectifs`, { methode: 'POST', corps: donnees })
  },

  evaluerObjectif(objectifId: string, donnees: EvaluationEcrite): Promise<Objectif> {
    return requete<Objectif>(`/objectifs/${objectifId}/evaluation`, {
      methode: 'POST',
      corps: donnees,
    })
  },

  exporterPdf(id: string): Promise<{ contenu: Blob; nomFichier: string }> {
    return telecharger(`/entretiens/${id}/export`)
  },

  ecrireSynthese(id: string, contenu: string): Promise<Commentaire> {
    return requete<Commentaire>(`/entretiens/${id}/synthese`, {
      methode: 'POST',
      corps: { contenu },
    })
  },
}

export const tableauBordApi = {

  parCampagne(campagneId: string): Promise<TableauDeBord> {
    return requete<TableauDeBord>(`/tableau-bord/campagnes/${campagneId}`)
  },
}
