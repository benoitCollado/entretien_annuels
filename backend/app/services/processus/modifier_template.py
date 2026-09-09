from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflitMetier, RessourceIntrouvable
from app.models.template import Template
from app.models.utilisateur import Utilisateur
from app.repositories.template_repository import TemplateRepository
from app.services.regles import publication_template


def executer(
    session: Session,
    *,
    auteur: Utilisateur,
    template_id: UUID,
    nom: str | None = None,
    description: str | None = None,
    champs_fournis: set[str] | None = None,
) -> Template:
    fournis = champs_fournis if champs_fournis is not None else set()
    templates = TemplateRepository(session)

    template = templates.get_avec_arborescence(template_id)
    if template is None:
        raise RessourceIntrouvable("Trame introuvable.")

    publication_template.exiger_modifiable(template.statut)

    if "nom" in fournis and nom is not None and nom != template.nom:
        if templates.derniere_version(nom) > 0:
            raise ConflitMetier(f"Une trame nommée « {nom} » existe déjà.")
        template.nom = nom

    if "description" in fournis:
        template.description = description

    session.flush()
    return template
