from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from uuid_utils.compat import uuid7

revision: str = "4e2bb21d65e6"
down_revision: str | None = "8b0c85e36e9a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS: dict[str, str] = {
    "utilisateur:lire": "Consulter les utilisateurs",
    "utilisateur:creer": "Créer un utilisateur",
    "utilisateur:modifier": "Modifier un utilisateur",
    "utilisateur:archiver": "Archiver un utilisateur",
    "role:lire": "Consulter les rôles",
    "role:attribuer": "Attribuer un rôle",
}

ROLES: dict[str, tuple[str, tuple[str, ...]]] = {
    "ADMIN": ("Administrateur", tuple(PERMISSIONS)),
    "RH": (
        "Responsable RH",
        ("utilisateur:lire", "utilisateur:creer", "utilisateur:modifier", "role:lire"),
    ),
    "MANAGER": ("Manager", ("utilisateur:lire", "role:lire")),
    "COLLABORATEUR": ("Collaborateur", ()),
}

table_permission = sa.table(
    "permission",
    sa.column("id", sa.Uuid()),
    sa.column("code", sa.String()),
    sa.column("libelle", sa.String()),
)
table_role = sa.table(
    "role",
    sa.column("id", sa.Uuid()),
    sa.column("code", sa.String()),
    sa.column("libelle", sa.String()),
)
table_role_permission = sa.table(
    "role_permission",
    sa.column("role_id", sa.Uuid()),
    sa.column("permission_id", sa.Uuid()),
)


def upgrade() -> None:
    ids_permission = {code: uuid7() for code in PERMISSIONS}
    op.bulk_insert(
        table_permission,
        [
            {"id": ids_permission[code], "code": code, "libelle": libelle}
            for code, libelle in PERMISSIONS.items()
        ],
    )

    ids_role = {code: uuid7() for code in ROLES}
    op.bulk_insert(
        table_role,
        [
            {"id": ids_role[code], "code": code, "libelle": libelle}
            for code, (libelle, _) in ROLES.items()
        ],
    )

    liaisons = [
        {"role_id": ids_role[code_role], "permission_id": ids_permission[code_permission]}
        for code_role, (_, codes) in ROLES.items()
        for code_permission in codes
    ]
    if liaisons:
        op.bulk_insert(table_role_permission, liaisons)


def downgrade() -> None:
    connexion = op.get_bind()
    connexion.execute(table_role_permission.delete())
    connexion.execute(table_role.delete().where(table_role.c.code.in_(list(ROLES))))
    connexion.execute(
        table_permission.delete().where(table_permission.c.code.in_(list(PERMISSIONS)))
    )
