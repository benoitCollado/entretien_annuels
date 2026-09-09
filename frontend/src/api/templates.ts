import { requete } from '@/api/client'
import type { Page, Referentiel, SectionEcrite, Template, TemplateResume } from '@/types/api'

export const templatesApi = {
  lister(statut?: string, limite = 50, decalage = 0): Promise<Page<TemplateResume>> {
    const parametres = new URLSearchParams({
      limite: String(limite),
      decalage: String(decalage),
    })
    if (statut) parametres.set('statut', statut)
    return requete<Page<TemplateResume>>(`/templates?${parametres}`)
  },

  consulter(id: string): Promise<Template> {
    return requete<Template>(`/templates/${id}`)
  },

  referentiel(): Promise<Referentiel> {
    return requete<Referentiel>('/templates/referentiel')
  },

  creer(nom: string, typeEntretien: string, description: string | null): Promise<Template> {
    return requete<Template>('/templates', {
      methode: 'POST',
      corps: { nom, type_entretien: typeEntretien, description },
    })
  },

  definirStructure(id: string, sections: SectionEcrite[]): Promise<Template> {
    return requete<Template>(`/templates/${id}/structure`, {
      methode: 'PUT',
      corps: { sections },
    })
  },

  publier(id: string): Promise<Template> {
    return requete<Template>(`/templates/${id}/publier`, { methode: 'POST' })
  },

  nouvelleVersion(id: string): Promise<Template> {
    return requete<Template>(`/templates/${id}/nouvelle-version`, { methode: 'POST' })
  },
}
