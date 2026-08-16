"""Processus — US-02. Endpoint appelant : `PUT /utilisateurs/{id}/roles`."""

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

    # 1. Portée : on ne modifie pas ses propres rôles, dans un sens comme dans
    #    l'autre — ni se retirer un accès par mégarde, ni s'en octroyer un.
    rbac.exiger_pas_auto_modification(auteur.id, utilisateur_id)

    utilisateur = utilisateurs.get_non_archive(utilisateur_id)
    if utilisateur is None:
        raise RessourceIntrouvable("Utilisateur introuvable.")

    # 2. Règles : les rôles existent, et l'auteur a le droit de les conférer.
    roles = roles_repo.lister_par_codes(codes_roles)
    rbac.exiger_roles_connus(codes_roles, [role.code for role in roles])
    rbac.exiger_attribution_autorisee(auteur.codes_roles(), codes_roles)

    # 3. Effets : remplacement complet, et non ajout — l'appelant décrit l'état
    #    voulu, ce qui rend l'opération idempotente.
    utilisateur.roles = list(roles)
    # Les permissions effectives changent : les jetons en cours doivent être
    # renouvelés pour que le changement prenne effet immédiatement.
    utilisateur.version_jeton += 1

    session.flush()
    return utilisateur
