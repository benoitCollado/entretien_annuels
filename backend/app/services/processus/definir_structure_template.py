from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import RessourceIntrouvable
from app.models.template import QuestionTemplate, SectionTemplate, Template
from app.models.utilisateur import Utilisateur
from app.repositories.template_repository import TemplateRepository
from app.services.regles import publication_template


@dataclass(slots=True)
class QuestionVoulue:
    libelle: str
    type_question: str
    cible: str
    obligatoire: bool = False
    aide: str | None = None
    configuration: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SectionVoulue:
    titre: str
    questions: list[QuestionVoulue]
    description: str | None = None


def executer(
    session: Session,
    *,
    auteur: Utilisateur,
    template_id: UUID,
    sections: list[SectionVoulue],
) -> Template:
    templates = TemplateRepository(session)

    template = templates.get_avec_arborescence(template_id)
    if template is None:
        raise RessourceIntrouvable("Trame introuvable.")

    publication_template.exiger_modifiable(template.statut)

    nouvelles_sections = [
        SectionTemplate(
            titre=section.titre,
            description=section.description,
            ordre=position_section,
            questions=[
                QuestionTemplate(
                    libelle=question.libelle,
                    aide=question.aide,
                    type_question=question.type_question,
                    cible=question.cible,
                    obligatoire=question.obligatoire,
                    ordre=position_question,
                    configuration=question.configuration,
                )
                for position_question, question in enumerate(section.questions)
            ],
        )
        for position_section, section in enumerate(sections)
    ]

    templates.remplacer_sections(template, nouvelles_sections)
    return template
