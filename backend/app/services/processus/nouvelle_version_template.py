from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflitMetier, RessourceIntrouvable
from app.models.template import QuestionTemplate, SectionTemplate, Template
from app.models.utilisateur import Utilisateur
from app.repositories.template_repository import TemplateRepository
from app.services.regles import publication_template


def executer(
    session: Session,
    *,
    auteur: Utilisateur,
    template_id: UUID,
) -> Template:
    templates = TemplateRepository(session)

    origine = templates.get_avec_arborescence(template_id)
    if origine is None:
        raise RessourceIntrouvable("Trame introuvable.")

    if publication_template.est_modifiable(origine.statut):
        raise ConflitMetier(
            "Cette trame est encore en brouillon : modifiez-la directement "
            "plutôt que d'en créer une version."
        )

    version = publication_template.version_suivante(templates.derniere_version(origine.nom))

    copie = Template(
        nom=origine.nom,
        description=origine.description,
        type_entretien=origine.type_entretien,
        version=version,
        statut=publication_template.BROUILLON,
        template_parent_id=origine.id,
        redige_par_id=auteur.id,
        sections=[
            SectionTemplate(
                titre=section.titre,
                description=section.description,
                ordre=section.ordre,
                questions=[
                    QuestionTemplate(
                        libelle=question.libelle,
                        aide=question.aide,
                        type_question=question.type_question,
                        cible=question.cible,
                        obligatoire=question.obligatoire,
                        ordre=question.ordre,
                        configuration=dict(question.configuration),
                    )
                    for question in section.questions
                ],
            )
            for section in origine.sections
        ],
    )

    return templates.ajouter(copie)
