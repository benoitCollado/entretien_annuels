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


def test_collaborateur_ne_possede_aucune_permission_d_administration(
    session: Session,
) -> None:
    role = RoleRepository(session).get_par_code(CodeRole.COLLABORATEUR.value)
    assert role is not None
    assert role.codes_permissions() == {
        CodePermission.ENTRETIEN_LIRE.value,
        CodePermission.EXPORT_LIRE.value,
    }

    assert not any(
        code.startswith(("utilisateur:", "role:", "template:", "campagne:"))
        for code in role.codes_permissions()
    )
