from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import RessourceIntrouvable
from app.models.template import Template
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

    template = templates.get_avec_arborescence(template_id)
    if template is None:
        raise RessourceIntrouvable("Trame introuvable.")

    publication_template.exiger_transition(template.statut, publication_template.PUBLIEE)

    publication_template.exiger_structure_publiable(
        [len(section.questions) for section in template.sections]
    )

    template.statut = publication_template.PUBLIEE
    template.publie_le = datetime.now(UTC)

    session.flush()
    return template
