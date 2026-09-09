from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from uuid_utils.compat import uuid7

revision: str = "a3f1c0d84b27"
down_revision: str | None = "57cbd7d4cadf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS: dict[str, str] = {
    "objectif:fixer": "Fixer et évaluer des objectifs",
    "export:lire": "Exporter un compte rendu en PDF",
}

ATTRIBUTIONS: dict[str, tuple[str, ...]] = {
    "ADMIN": tuple(PERMISSIONS),
    "RH": ("export:lire",),
    "MANAGER": ("objectif:fixer", "export:lire"),
    "COLLABORATEUR": ("export:lire",),
}

table_permission = sa.table(
    "permission",
    sa.column("id", sa.Uuid()),
    sa.column("code", sa.String()),
    sa.column("libelle", sa.String()),
)
table_role = sa.table("role", sa.column("id", sa.Uuid()), sa.column("code", sa.String()))
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

    connexion = op.get_bind()
    ids_role = {
        code: identifiant
        for identifiant, code in connexion.execute(
            sa.select(table_role.c.id, table_role.c.code).where(
                table_role.c.code.in_(list(ATTRIBUTIONS))
            )
        )
    }

    liaisons = [
        {"role_id": ids_role[code_role], "permission_id": ids_permission[code_permission]}
        for code_role, codes in ATTRIBUTIONS.items()
        if code_role in ids_role
        for code_permission in codes
    ]
    if liaisons:
        op.bulk_insert(table_role_permission, liaisons)


def downgrade() -> None:
    connexion = op.get_bind()
    codes = list(PERMISSIONS)
    sous_requete = sa.select(table_permission.c.id).where(table_permission.c.code.in_(codes))
    connexion.execute(
        table_role_permission.delete().where(
            table_role_permission.c.permission_id.in_(sous_requete)
        )
    )
    connexion.execute(table_permission.delete().where(table_permission.c.code.in_(codes)))
