"""Le référentiel en base correspond-il aux énumérations du code ?

La migration `4e2bb21d65e6` fige volontairement les rôles et permissions, pour
rester reproductible dans le temps. La contrepartie est un risque de divergence
avec `app.models.enums` : ce test est la contrepartie de ce choix.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.models.enums import (
    LIBELLES_PERMISSION,
    LIBELLES_ROLE,
    PERMISSIONS_PAR_ROLE,
    CodePermission,
    CodeRole,
)
from app.repositories.role_repository import RoleRepository

pytestmark = pytest.mark.integration


def test_tous_les_roles_du_code_existent_en_base(session: Session) -> None:
    codes_en_base = {role.code for role in RoleRepository(session).lister_tous()}
    assert codes_en_base == {role.value for role in CodeRole}


def test_toutes_les_permissions_du_code_existent_en_base(session: Session) -> None:
    codes_en_base = {p.code for p in RoleRepository(session).lister_permissions()}
    assert codes_en_base == {p.value for p in CodePermission}


@pytest.mark.parametrize("code_role", sorted(CodeRole))
def test_attribution_des_permissions_conforme(session: Session, code_role: CodeRole) -> None:
    """C'est ce test qui échoue si quelqu'un modifie `PERMISSIONS_PAR_ROLE` sans
    écrire la migration correspondante."""
    role = RoleRepository(session).get_par_code(code_role.value)
    assert role is not None, f"rôle {code_role} absent de la base"

    attendues = {p.value for p in PERMISSIONS_PAR_ROLE[code_role]}
    assert role.codes_permissions() == attendues


def test_libelles_renseignes(session: Session) -> None:
    for role in RoleRepository(session).lister_tous():
        assert role.libelle == LIBELLES_ROLE[CodeRole(role.code)]
    for permission in RoleRepository(session).lister_permissions():
        assert permission.libelle == LIBELLES_PERMISSION[CodePermission(permission.code)]


def test_admin_possede_toutes_les_permissions(session: Session) -> None:
    role = RoleRepository(session).get_par_code(CodeRole.ADMIN.value)
    assert role is not None
    assert role.codes_permissions() == {p.value for p in CodePermission}


def test_collaborateur_ne_possede_aucune_permission(session: Session) -> None:
    """Un collaborateur accède à ses propres données par des endpoints dédiés,
    jamais par les permissions d'administration."""
    role = RoleRepository(session).get_par_code(CodeRole.COLLABORATEUR.value)
    assert role is not None
    assert role.codes_permissions() == set()
