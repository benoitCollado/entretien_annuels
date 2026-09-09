from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import RessourceIntrouvable
from app.models.utilisateur import Utilisateur
from app.repositories.role_repository import RoleRepository
from app.repositories.utilisateur_repository import UtilisateurRepository
from app.services.regles import rbac


def executer(
    session: Session,
    *,
    auteur: Utilisateur,
    utilisateur_id: UUID,
    codes_roles: list[str],
) -> Utilisateur:
    utilisateurs = UtilisateurRepository(session)
    roles_repo = RoleRepository(session)

    rbac.exiger_pas_auto_modification(auteur.id, utilisateur_id)

    utilisateur = utilisateurs.get_non_archive(utilisateur_id)
    if utilisateur is None:
        raise RessourceIntrouvable("Utilisateur introuvable.")

    roles = roles_repo.lister_par_codes(codes_roles)
    rbac.exiger_roles_connus(codes_roles, [role.code for role in roles])
    rbac.exiger_attribution_autorisee(auteur.codes_roles(), codes_roles)

    utilisateur.roles = list(roles)
    utilisateur.version_jeton += 1

    session.flush()
    return utilisateur
