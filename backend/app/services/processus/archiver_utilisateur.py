from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import DonneesInvalides, RessourceIntrouvable
from app.models.utilisateur import Utilisateur
from app.repositories.utilisateur_repository import UtilisateurRepository
from app.services.regles import portee_hierarchique, rbac


def executer(
    session: Session,
    *,
    auteur: Utilisateur,
    utilisateur_id: UUID,
) -> Utilisateur:
    utilisateurs = UtilisateurRepository(session)

    rbac.exiger_pas_auto_modification(auteur.id, utilisateur_id)

    if not portee_hierarchique.peut_gerer(auteur.codes_roles()):
        raise DonneesInvalides("Votre rôle ne permet pas d'archiver un compte.")

    utilisateur = utilisateurs.get_non_archive(utilisateur_id)
    if utilisateur is None:
        raise RessourceIntrouvable("Utilisateur introuvable.")

    utilisateur.archived_at = datetime.now(UTC)
    utilisateur.actif = False
    utilisateur.version_jeton += 1

    session.flush()
    return utilisateur
