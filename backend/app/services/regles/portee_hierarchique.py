from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from app.core.exceptions import DonneesInvalides

ROLE_ADMIN = "ADMIN"
ROLE_RH = "RH"
ROLE_MANAGER = "MANAGER"

ROLES_PORTEE_GLOBALE = frozenset({ROLE_ADMIN, ROLE_RH})


def est_son_propre_manager(utilisateur_id: UUID, manager_id: UUID | None) -> bool:
    return manager_id is not None and manager_id == utilisateur_id


def cree_un_cycle(
    utilisateur_id: UUID,
    manager_id: UUID | None,
    ancetres_du_manager: Iterable[UUID],
) -> bool:
    if manager_id is None:
        return False
    return utilisateur_id in set(ancetres_du_manager)


def exiger_rattachement_valide(
    utilisateur_id: UUID,
    manager_id: UUID | None,
    ancetres_du_manager: Iterable[UUID] = (),
) -> None:
    if est_son_propre_manager(utilisateur_id, manager_id):
        raise DonneesInvalides("Un utilisateur ne peut pas être son propre manager.")

    if cree_un_cycle(utilisateur_id, manager_id, ancetres_du_manager):
        raise DonneesInvalides(
            "Ce rattachement créerait un cycle dans la hiérarchie.",
        )


def perimetre_de_lecture(codes_roles: Iterable[str], utilisateur_id: UUID) -> UUID | None:
    roles = set(codes_roles)
    if roles & ROLES_PORTEE_GLOBALE:
        return None
    return utilisateur_id


def peut_gerer(codes_roles: Iterable[str]) -> bool:
    return bool(set(codes_roles) & ROLES_PORTEE_GLOBALE)
