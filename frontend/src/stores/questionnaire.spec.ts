import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ErreurHttp } from '@/api/client'
import { entretiensApi } from '@/api/entretiens'
import { useQuestionnaireStore } from '@/stores/questionnaire'
import type { Entretien, Questionnaire, QuestionInstanciee, StatutEntretien } from '@/types/api'

vi.mock('@/api/entretiens', () => ({
  entretiensApi: {
    recuperer: vi.fn(),
    questionnaire: vi.fn(),
    enregistrerBrouillon: vi.fn(),
    soumettre: vi.fn(),
    ouvrirRevue: vi.fn(),
    cloturerEchange: vi.fn(),
    commenter: vi.fn(),
    ecrireSynthese: vi.fn(),
    objectifs: vi.fn(),
    fixerObjectif: vi.fn(),
    evaluerObjectif: vi.fn(),
    signer: vi.fn(),
    cloturer: vi.fn(),
    exporterPdf: vi.fn(),
  },
}))

const MOI = 'id-collaborateur'
const MANAGER = 'id-manager'
const Q_COLLAB = 'q-collab'
const Q_MANAGER = 'q-manager'
const Q_PARTAGEE = 'q-partagee'

function question(id: string, cible: 'COLLABORATEUR' | 'MANAGER' | 'PARTAGEE'): QuestionInstanciee {
  return {
    id,
    libelle: `Question ${id}`,
    aide: null,
    type_question: 'texte_libre',
    cible,
    obligatoire: true,
    ordre: 1,
    configuration: {},
    est_ad_hoc: false,
  }
}

function entretien(statut: StatutEntretien, monRole: 'COLLABORATEUR' | 'MANAGER'): Entretien {
  const acteur = (id: string) => ({ id, nom_complet: id, email: `${id}@x.fr` })
  return {
    id: 'e1',
    campagne_id: 'c1',
    type_entretien: 'ANNUEL',
    statut,
    date_planifiee: null,
    collaborateur: acteur(MOI),
    manager: acteur(MANAGER),
    soumis_collaborateur_le: null,
    revue_ouverte_le: null,
    realise_le: null,
    signe_collaborateur_le: null,
    signe_manager_le: null,
    cloture_le: null,
    created_at: '2026-01-01T00:00:00Z',
    motif_annulation: null,
    observation_collaborateur: null,
    mon_role: monRole,
    transitions_possibles: [],
  }
}

function questionnaire(
  statut: StatutEntretien,
  reponses: Questionnaire['reponses'],
  contenuMasque = false,
): Questionnaire {
  return {
    id: 'q1',
    entretien_id: 'e1',
    titre: 'Entretien annuel',
    template_version: 1,
    statut_entretien: statut,
    sections: [
      {
        id: 's1',
        titre: 'Bilan',
        description: null,
        ordre: 1,
        questions: [
          question(Q_COLLAB, 'COLLABORATEUR'),
          question(Q_PARTAGEE, 'PARTAGEE'),
          question(Q_MANAGER, 'MANAGER'),
        ],
      },
    ],
    reponses,
    commentaires: [],
    contenu_masque: contenuMasque,
  }
}

async function monter(
  e: Entretien,
  q: Questionnaire,
  monId = MOI,
): Promise<ReturnType<typeof useQuestionnaireStore>> {
  vi.mocked(entretiensApi.recuperer).mockResolvedValue(e)
  vi.mocked(entretiensApi.questionnaire).mockResolvedValue(q)
  const store = useQuestionnaireStore()
  await store.charger('e1', monId)
  return store
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('confidentialité — le store obéit au serveur', () => {
  it('n’invente rien quand le serveur masque', async () => {

    const store = await monter(
      entretien('PREPARATION', 'MANAGER'),
      questionnaire('PREPARATION', [], true),
      MANAGER,
    )

    expect(store.contenuMasque).toBe(true)
    expect(store.reponsesDe(Q_COLLAB, MANAGER)).toEqual([])
  })

  it('ne filtre pas de lui-même ce que le serveur a transmis', async () => {

    const store = await monter(
      entretien('SOUMIS_COLLABORATEUR', 'MANAGER'),
      questionnaire('SOUMIS_COLLABORATEUR', [
        {
          question_id: Q_COLLAB,
          auteur_id: MOI,
          valeur: { contenu: 'Projet livré' },
          updated_at: '2026-01-02T00:00:00Z',
        },
      ]),
      MANAGER,
    )

    expect(store.contenuMasque).toBe(false)
    expect(store.reponsesDe(Q_COLLAB, MANAGER)).toHaveLength(1)
  })

  it('sépare mes réponses de celles des autres', async () => {
    const store = await monter(
      entretien('REVUE_MANAGER', 'COLLABORATEUR'),
      questionnaire('REVUE_MANAGER', [
        {
          question_id: Q_PARTAGEE,
          auteur_id: MOI,
          valeur: { contenu: 'la mienne' },
          updated_at: '2026-01-02T00:00:00Z',
        },
        {
          question_id: Q_PARTAGEE,
          auteur_id: MANAGER,
          valeur: { contenu: 'celle du manager' },
          updated_at: '2026-01-03T00:00:00Z',
        },
      ]),
    )

    expect(store.brouillon[Q_PARTAGEE]).toEqual({ contenu: 'la mienne' })
    expect(store.reponsesDe(Q_PARTAGEE, MOI)).toHaveLength(1)
    expect(store.reponsesDe(Q_PARTAGEE, MOI)[0].auteur_id).toBe(MANAGER)
  })
})

describe('questions qui me concernent', () => {
  it('le collaborateur voit les siennes et les partagées', async () => {
    const store = await monter(
      entretien('PREPARATION', 'COLLABORATEUR'),
      questionnaire('PREPARATION', []),
    )
    expect(store.estAMoi(question(Q_COLLAB, 'COLLABORATEUR'))).toBe(true)
    expect(store.estAMoi(question(Q_PARTAGEE, 'PARTAGEE'))).toBe(true)
    expect(store.estAMoi(question(Q_MANAGER, 'MANAGER'))).toBe(false)
  })

  it('le manager voit les siennes et les partagées', async () => {
    const store = await monter(
      entretien('SOUMIS_COLLABORATEUR', 'MANAGER'),
      questionnaire('SOUMIS_COLLABORATEUR', []),
      MANAGER,
    )
    expect(store.estAMoi(question(Q_MANAGER, 'MANAGER'))).toBe(true)
    expect(store.estAMoi(question(Q_COLLAB, 'COLLABORATEUR'))).toBe(false)
  })
})

describe('modifiabilité', () => {
  it('le collaborateur saisit avant la soumission', async () => {
    const store = await monter(
      entretien('PREPARATION', 'COLLABORATEUR'),
      questionnaire('PREPARATION', []),
    )
    expect(store.modifiable).toBe(true)
  })

  it('la soumission ferme la saisie du collaborateur', async () => {

    const store = await monter(
      entretien('SOUMIS_COLLABORATEUR', 'COLLABORATEUR'),
      questionnaire('SOUMIS_COLLABORATEUR', []),
    )
    expect(store.modifiable).toBe(false)
  })
})

describe('saisie', () => {
  it('une valeur saisie marque le formulaire modifié', async () => {
    const store = await monter(
      entretien('PLANIFIE', 'COLLABORATEUR'),
      questionnaire('PLANIFIE', []),
    )
    expect(store.modifie).toBe(false)
    store.saisir(Q_COLLAB, { contenu: 'essai' })
    expect(store.modifie).toBe(true)
    expect(store.aRepondu(Q_COLLAB)).toBe(true)
  })

  it('une valeur vide ne compte pas comme une réponse', async () => {
    const store = await monter(
      entretien('PLANIFIE', 'COLLABORATEUR'),
      questionnaire('PLANIFIE', []),
    )
    store.saisir(Q_COLLAB, { contenu: '' })
    expect(store.aRepondu(Q_COLLAB)).toBe(false)
    store.saisir(Q_PARTAGEE, null)
    expect(store.aRepondu(Q_PARTAGEE)).toBe(false)
  })
})

describe('soumission refusée', () => {
  it('surligne les questions nommées par le serveur', async () => {
    const store = await monter(
      entretien('PREPARATION', 'COLLABORATEUR'),
      questionnaire('PREPARATION', []),
    )
    vi.mocked(entretiensApi.soumettre).mockRejectedValue(
      new ErreurHttp(422, 'Des questions obligatoires sont sans réponse.', [
        { question_id: Q_COLLAB, libelle: 'Question q-collab' },
      ]),
    )

    expect(await store.soumettre(MOI)).toBe(false)
    expect(store.manquantes).toEqual([Q_COLLAB])
    expect(store.erreur).toContain('obligatoires')
  })

  it('ne retient pas les détails sans identifiant de question', async () => {
    const store = await monter(
      entretien('PREPARATION', 'COLLABORATEUR'),
      questionnaire('PREPARATION', []),
    )
    vi.mocked(entretiensApi.soumettre).mockRejectedValue(
      new ErreurHttp(409, 'Transition impossible.', [{ statut: 'SIGNE' }]),
    )

    expect(await store.soumettre(MOI)).toBe(false)
    expect(store.manquantes).toEqual([])
  })
})

describe('signature', () => {
  function entretienRealise(
    monRole: 'COLLABORATEUR' | 'MANAGER',
    signatures: { collaborateur?: string | null; manager?: string | null } = {},
  ): Entretien {
    return {
      ...entretien('ENTRETIEN_REALISE', monRole),
      signe_collaborateur_le: signatures.collaborateur ?? null,
      signe_manager_le: signatures.manager ?? null,
    }
  }

  it('propose la signature une fois l’entretien réalisé', async () => {
    const store = await monter(
      entretienRealise('COLLABORATEUR'),
      questionnaire('ENTRETIEN_REALISE', []),
    )
    expect(store.peutSigner).toBe(true)
    expect(store.dejaSigne).toBe(false)
  })

  it('ne propose plus la signature à qui a déjà signé', async () => {

    const store = await monter(
      entretienRealise('COLLABORATEUR', { collaborateur: '2026-03-01T10:00:00Z' }),
      questionnaire('ENTRETIEN_REALISE', []),
    )
    expect(store.dejaSigne).toBe(true)
    expect(store.peutSigner).toBe(false)
  })

  it('la signature de l’un ne bloque pas celle de l’autre', async () => {
    const store = await monter(
      entretienRealise('MANAGER', { collaborateur: '2026-03-01T10:00:00Z' }),
      questionnaire('ENTRETIEN_REALISE', []),
      MANAGER,
    )
    expect(store.peutSigner).toBe(true)
  })

  it('ne propose pas la signature avant que l’entretien soit réalisé', async () => {
    const store = await monter(
      entretien('REVUE_MANAGER', 'COLLABORATEUR'),
      questionnaire('REVUE_MANAGER', []),
    )
    expect(store.peutSigner).toBe(false)
  })

  it('remonte le refus du serveur sans le masquer', async () => {
    const store = await monter(
      entretienRealise('COLLABORATEUR'),
      questionnaire('ENTRETIEN_REALISE', []),
    )
    vi.mocked(entretiensApi.signer).mockRejectedValue(
      new ErreurHttp(409, 'Vous avez déjà signé cet entretien.'),
    )
    expect(await store.signer(null, MOI)).toBe(false)
    expect(store.erreur).toContain('déjà signé')
  })
})

describe('export', () => {
  it('n’est proposé qu’à partir de SIGNE', async () => {
    const avant = await monter(
      entretien('ENTRETIEN_REALISE', 'COLLABORATEUR'),
      questionnaire('ENTRETIEN_REALISE', []),
    )
    expect(avant.peutExporter).toBe(false)
  })

  it('est proposé sur un entretien signé puis clôturé', async () => {
    for (const statut of ['SIGNE', 'CLOTURE'] as const) {
      setActivePinia(createPinia())
      const store = await monter(entretien(statut, 'COLLABORATEUR'), questionnaire(statut, []))
      expect(store.peutExporter).toBe(true)
    }
  })
})

describe('objectifs', () => {
  it('sépare les objectifs fixés de ceux à évaluer', async () => {
    vi.mocked(entretiensApi.objectifs).mockResolvedValue({
      fixes: [{ libelle: 'Objectif N+1' } as never],
      a_evaluer: [{ libelle: 'Objectif N-1' } as never],
    })
    const store = await monter(
      entretien('REVUE_MANAGER', 'MANAGER'),
      questionnaire('REVUE_MANAGER', []),
      MANAGER,
    )
    expect(store.objectifsFixes).toHaveLength(1)
    expect(store.objectifsAEvaluer).toHaveLength(1)
  })

  it('un échec sur les objectifs n’empêche pas d’afficher le questionnaire', async () => {

    vi.mocked(entretiensApi.objectifs).mockRejectedValue(new ErreurHttp(403, 'Refusé'))
    const store = await monter(
      entretien('REVUE_MANAGER', 'MANAGER'),
      questionnaire('REVUE_MANAGER', []),
      MANAGER,
    )
    expect(store.questionnaire).not.toBeNull()
    expect(store.objectifsFixes).toEqual([])
  })

  it('n’ouvre la gestion des objectifs qu’au manager, pendant l’échange', async () => {
    const manager = await monter(
      entretien('REVUE_MANAGER', 'MANAGER'),
      questionnaire('REVUE_MANAGER', []),
      MANAGER,
    )
    expect(manager.peutGererLesObjectifs).toBe(true)

    setActivePinia(createPinia())
    const collaborateur = await monter(
      entretien('REVUE_MANAGER', 'COLLABORATEUR'),
      questionnaire('REVUE_MANAGER', []),
    )
    expect(collaborateur.peutGererLesObjectifs).toBe(false)
  })

  it('l’évaluation vise l’entretien courant, jamais celui d’origine', async () => {

    vi.mocked(entretiensApi.objectifs).mockResolvedValue({ fixes: [], a_evaluer: [] })
    const store = await monter(
      entretien('REVUE_MANAGER', 'MANAGER'),
      questionnaire('REVUE_MANAGER', []),
      MANAGER,
    )
    vi.mocked(entretiensApi.evaluerObjectif).mockResolvedValue({} as never)

    await store.evaluerObjectif('obj-1', { statut: 'ATTEINT', niveau_atteinte: 100 })

    expect(entretiensApi.evaluerObjectif).toHaveBeenCalledWith('obj-1', {
      statut: 'ATTEINT',
      niveau_atteinte: 100,
      entretien_id: 'e1',
    })
  })
})
