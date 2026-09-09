import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { templatesApi } from '@/api/templates'
import { deplacer, useEditeurTrameStore } from '@/stores/editeurTrame'
import type { Referentiel, Template } from '@/types/api'

function trameFactice(surcharges: Partial<Template> = {}): Template {
  return {
    id: 'aaaa',
    nom: 'Trame test',
    description: null,
    type_entretien: 'ANNUEL',
    version: 1,
    statut: 'BROUILLON',
    publie_le: null,
    created_at: '2026-01-01T00:00:00Z',
    nombre_sections: 1,
    nombre_questions: 2,
    est_modifiable: true,
    template_parent_id: null,
    sections: [
      {
        id: 's1',
        titre: 'Bilan',
        description: null,
        ordre: 0,
        questions: [
          {
            id: 'q1',
            libelle: 'Première',
            aide: null,
            type_question: 'texte_libre',
            cible: 'COLLABORATEUR',
            obligatoire: true,
            ordre: 0,
            configuration: {},
          },
          {
            id: 'q2',
            libelle: 'Seconde',
            aide: null,
            type_question: 'oui_non',
            cible: 'MANAGER',
            obligatoire: false,
            ordre: 1,
            configuration: {},
          },
        ],
      },
    ],
    ...surcharges,
  }
}

const REFERENTIEL: Referentiel = {
  types_question: ['texte_libre', 'echelle', 'choix_multiple', 'oui_non'],
  cibles: ['COLLABORATEUR', 'MANAGER', 'PARTAGEE'],
  types_entretien: ['ANNUEL', 'PROFESSIONNEL'],
  statuts_template: ['BROUILLON', 'PUBLIEE', 'ARCHIVEE'],
}

describe('deplacer', () => {
  it('échange deux éléments', () => {
    const elements = ['a', 'b', 'c']
    expect(deplacer(elements, 0, 1)).toBe(true)
    expect(elements).toEqual(['b', 'a', 'c'])
  })

  it('refuse de sortir du tableau', () => {
    const elements = ['a', 'b']
    expect(deplacer(elements, 0, -1)).toBe(false)
    expect(deplacer(elements, 1, 1)).toBe(false)
    expect(elements).toEqual(['a', 'b'])
  })
})

describe('store éditeur de trame', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.restoreAllMocks()
    vi.spyOn(templatesApi, 'referentiel').mockResolvedValue(REFERENTIEL)
  })

  it('charge la trame et en fait une copie locale', async () => {
    vi.spyOn(templatesApi, 'consulter').mockResolvedValue(trameFactice())
    const editeur = useEditeurTrameStore()

    await editeur.charger('aaaa')

    expect(editeur.sections).toHaveLength(1)
    expect(editeur.sections[0].questions).toHaveLength(2)
    expect(editeur.modifiable).toBe(true)
    expect(editeur.nombreQuestions).toBe(2)
  })

  it('bascule en lecture seule sur une trame publiée', async () => {
    vi.spyOn(templatesApi, 'consulter').mockResolvedValue(
      trameFactice({ statut: 'PUBLIEE', est_modifiable: false }),
    )
    const editeur = useEditeurTrameStore()
    await editeur.charger('aaaa')

    expect(editeur.modifiable).toBe(false)
  })

  describe('manipulations locales', () => {
    beforeEach(async () => {
      vi.spyOn(templatesApi, 'consulter').mockResolvedValue(trameFactice())
      await useEditeurTrameStore().charger('aaaa')
    })

    it('ajoute et supprime une section', () => {
      const editeur = useEditeurTrameStore()
      editeur.ajouterSection()
      expect(editeur.sections).toHaveLength(2)

      editeur.supprimerSection(1)
      expect(editeur.sections).toHaveLength(1)
    })

    it('déplace une question', () => {
      const editeur = useEditeurTrameStore()
      editeur.deplacerQuestion(0, 0, 1)

      expect(editeur.sections[0].questions.map((q) => q.libelle)).toEqual(['Seconde', 'Première'])
    })

    it("l'ordre du tableau est le seul ordre manipulé", () => {

      const editeur = useEditeurTrameStore()
      const structure = editeur.versStructure()

      expect(structure[0].questions[0]).not.toHaveProperty('ordre')
      expect(Object.keys(structure[0])).toEqual(['titre', 'description', 'questions'])
    })

    it('réinitialise la configuration quand le type change', () => {

      const editeur = useEditeurTrameStore()

      editeur.changerType(0, 0, 'choix_multiple')
      expect(editeur.sections[0].questions[0].configuration).toEqual({ options: ['', ''] })

      editeur.changerType(0, 0, 'echelle')
      expect(editeur.sections[0].questions[0].configuration).toEqual({ minimum: 1, maximum: 5 })

      editeur.changerType(0, 0, 'texte_libre')
      expect(editeur.sections[0].questions[0].configuration).toEqual({})
    })
  })

  describe('conditions de publication', () => {
    beforeEach(async () => {
      vi.spyOn(templatesApi, 'consulter').mockResolvedValue(trameFactice())
      await useEditeurTrameStore().charger('aaaa')
    })

    it('une trame complète est publiable', () => {
      expect(useEditeurTrameStore().motifNonPubliable).toBeNull()
    })

    it('signale une section vide', () => {
      const editeur = useEditeurTrameStore()
      editeur.ajouterSection()
      editeur.sections[1].titre = 'Vide'
      editeur.sections[1].questions = []

      expect(editeur.motifNonPubliable).toContain('section 2')
    })

    it('signale une section sans titre', () => {
      const editeur = useEditeurTrameStore()
      editeur.sections[0].titre = '  '
      expect(editeur.motifNonPubliable).toContain('titre')
    })

    it('signale une question sans libellé', () => {
      const editeur = useEditeurTrameStore()
      editeur.sections[0].questions[0].libelle = ''
      expect(editeur.motifNonPubliable).toContain('libellé')
    })
  })

  it('enregistre la structure avant de publier', async () => {

    vi.spyOn(templatesApi, 'consulter').mockResolvedValue(trameFactice())
    const definir = vi.spyOn(templatesApi, 'definirStructure').mockResolvedValue(trameFactice())
    const publier = vi
      .spyOn(templatesApi, 'publier')
      .mockResolvedValue(trameFactice({ statut: 'PUBLIEE', est_modifiable: false }))

    const editeur = useEditeurTrameStore()
    await editeur.charger('aaaa')
    editeur.sections[0].titre = 'Titre modifié'

    expect(await editeur.publier()).toBe(true)
    expect(definir).toHaveBeenCalledBefore(publier)
    expect(definir.mock.calls[0][1][0].titre).toBe('Titre modifié')
  })
})
