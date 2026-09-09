import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import SaisieReponse from '@/components/questions/SaisieReponse.vue'
import type { QuestionInstanciee, TypeQuestion } from '@/types/api'

function question(
  type: TypeQuestion,
  configuration: Record<string, unknown> = {},
): QuestionInstanciee {
  return {
    id: 'q1',
    libelle: 'Une question',
    aide: null,
    type_question: type,
    cible: 'COLLABORATEUR',
    obligatoire: true,
    ordre: 1,
    configuration,
    est_ad_hoc: false,
  }
}

function monter(q: QuestionInstanciee, valeur: Record<string, unknown> | null = null) {
  return mount(SaisieReponse, {
    props: { question: q, valeur, modifiable: true },
  })
}

function derniereValeur(composant: ReturnType<typeof monter>) {
  const emissions = composant.emitted('saisir')
  return emissions?.[emissions.length - 1]?.[0]
}

describe('forme des valeurs émises', () => {
  it('texte libre émet { contenu }', async () => {
    const composant = monter(question('texte_libre'))
    await composant.find('textarea').setValue('Mon bilan')
    expect(derniereValeur(composant)).toEqual({ contenu: 'Mon bilan' })
  })

  it('un texte vidé émet null plutôt qu’une chaîne vide', async () => {

    const composant = monter(question('texte_libre'), { contenu: 'x' })
    await composant.find('textarea').setValue('   ')
    expect(derniereValeur(composant)).toBeNull()
  })

  it('échelle émet { note }', async () => {
    const composant = monter(question('echelle', { minimum: 1, maximum: 5 }))
    const boutons = composant.findAll('button[role="radio"]')
    expect(boutons).toHaveLength(5)
    await boutons[3].trigger('click')
    expect(derniereValeur(composant)).toEqual({ note: 4 })
  })

  it('échelle respecte les bornes de la configuration', () => {
    const composant = monter(question('echelle', { minimum: 0, maximum: 10 }))
    expect(composant.findAll('button[role="radio"]')).toHaveLength(11)
  })

  it('note_5 ignore la configuration et reste bornée à 5', () => {
    const composant = monter(question('note_5', { maximum: 99 }))
    expect(composant.findAll('button[role="radio"]')).toHaveLength(5)
  })

  it('choix unique émet { option }', async () => {
    const composant = monter(question('choix_unique', { options: ['A', 'B'] }))
    await composant.findAll('input[type="radio"]')[1].trigger('change')
    expect(derniereValeur(composant)).toEqual({ option: 'B' })
  })

  it('choix multiple émet { options } et cumule', async () => {
    const composant = monter(question('choix_multiple', { options: ['A', 'B', 'C'] }), {
      options: ['A'],
    })
    await composant.findAll('input[type="checkbox"]')[2].trigger('change')
    expect(derniereValeur(composant)).toEqual({ options: ['A', 'C'] })
  })

  it('oui/non émet { valeur } booléen', async () => {
    const composant = monter(question('oui_non'))
    await composant.findAll('button')[1].trigger('click')
    expect(derniereValeur(composant)).toEqual({ valeur: false })
  })

  it('date émet { date }', async () => {
    const composant = monter(question('date'))
    await composant.find('input[type="date"]').setValue('2026-03-15')
    expect(derniereValeur(composant)).toEqual({ date: '2026-03-15' })
  })
})

describe('affichage', () => {
  it('désactive les contrôles quand la saisie est fermée', () => {
    const composant = mount(SaisieReponse, {
      props: { question: question('texte_libre'), valeur: null, modifiable: false },
    })
    expect(composant.find('textarea').attributes('disabled')).toBeDefined()
  })

  it('signale une question obligatoire non remplie', () => {
    const composant = mount(SaisieReponse, {
      props: {
        question: question('texte_libre'),
        valeur: null,
        modifiable: true,
        manquante: true,
      },
    })
    expect(composant.text()).toContain('obligatoire')
  })

  it('annonce un type inconnu au lieu d’afficher un champ muet', () => {
    const composant = monter(question('type_futur' as TypeQuestion))
    expect(composant.text()).toContain('non pris en charge')
  })
})
