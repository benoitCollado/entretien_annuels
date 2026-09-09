from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import RessourceIntrouvable
from app.models.template import Template
from app.repositories.template_repository import TemplateRepository


def consulter(session: Session, *, template_id: UUID) -> Template:
    template = TemplateRepository(session).get_avec_arborescence(template_id)
    if template is None:
        raise RessourceIntrouvable("Trame introuvable.")
    return template


def lister(
    session: Session,
    *,
    statut: str | None = None,
    type_entretien: str | None = None,
    limite: int = 50,
    decalage: int = 0,
) -> tuple[list[Template], int]:
    templates = TemplateRepository(session)
    lignes = templates.lister_filtre(
        statut=statut, type_entretien=type_entretien, limite=limite, decalage=decalage
    )
    total = templates.compter(statut=statut, type_entretien=type_entretien)
    return lignes, total
