"""donnees reference rbac

Revision ID: 4e2bb21d65e6
Revises: 8b0c85e36e9a
Create Date: 2026-08-16 19:41:00.000000

Rôles et permissions du RBAC (US-02).

Ce sont des données **structurantes** : le code s'appuie dessus pour autoriser
les actions. Elles vivent donc dans une migration, contrairement aux comptes de
démonstration qui sont créés par `app/seed.py`.

⚠️ Les valeurs sont **figées ici**, et non lues depuis `app.models.enums`. Une
migration doit rester reproductible à l'identique dans dix ans, même si les
énumérations du code ont évolué depuis. La contrepartie est un risque de
divergence : `tests/integration/test_referentiel_rbac.py` compare le contenu de
la base au contenu des énumérations et échoue si les deux s'écartent.

Les UUID sont passés par des tables typées `sa.Uuid()` et non en SQL brut :
psycopg adapte `uuid.UUID` sur PostgreSQL, mais la migration cesserait d'être
rejouable sur un autre moteur.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from uuid_utils.compat import uuid7

revision: str = "4e2bb21d65e6"
down_revision: str | None = "8b0c85e36e9a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# --- Instantané du référentiel au moment de cette migration ---------------
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

# Tables « allégées » : une migration ne doit pas dépendre des modèles ORM, qui
# continueront d'évoluer. Le typage explicite garantit la portabilité des UUID.
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
    # Les liaisons d'abord : les clés étrangères sont en CASCADE, mais être
    # explicite rend la descente lisible et indépendante de ce réglage.
    connexion.execute(table_role_permission.delete())
    connexion.execute(table_role.delete().where(table_role.c.code.in_(list(ROLES))))
    connexion.execute(
        table_permission.delete().where(table_permission.c.code.in_(list(PERMISSIONS)))
    )
