"""Processus — US-02. Endpoint appelant : `GET /utilisateurs`.

Le périmètre est décidé par une règle pure puis **appliqué en SQL** par le
repository. Aucun utilisateur hors périmètre ne remonte en Python, ce qui écarte
tout risque de filtrage oublié dans la couche de présentation.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.utilisateur import Utilisateur
from app.repositories.utilisateur_repository import UtilisateurRepository
from app.services.regles import portee_hierarchique


def executer(
    session: Session,
    *,
    auteur: Utilisateur,
    limite: int = 50,
    decalage: int = 0,
) -> tuple[list[Utilisateur], int]:
    """Retourne `(utilisateurs, total)` pour la pagination."""
    perimetre = portee_hierarchique.perimetre_de_lecture(auteur.codes_roles(), auteur.id)

    utilisateurs = UtilisateurRepository(session)
    lignes = utilisateurs.lister_filtre(manager_id=perimetre, limite=limite, decalage=decalage)
    total = utilisateurs.compter(manager_id=perimetre)
    return lignes, total
