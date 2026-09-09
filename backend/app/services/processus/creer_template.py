from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import ConflitMetier
from app.models.template import Template
from app.models.utilisateur import Utilisateur
from app.repositories.template_repository import TemplateRepository


def executer(
    session: Session,
    *,
    auteur: Utilisateur,
    nom: str,
    type_entretien: str,
    description: str | None = None,
) -> Template:
    templates = TemplateRepository(session)

    if templates.derniere_version(nom) > 0:
        raise ConflitMetier(
            f"Une trame nommée « {nom} » existe déjà. "
            "Créez-en une nouvelle version pour la faire évoluer."
        )

    return templates.ajouter(
        Template(
            nom=nom,
            description=description,
            type_entretien=type_entretien,
            version=1,
            statut="BROUILLON",
            redige_par_id=auteur.id,
        )
    )
