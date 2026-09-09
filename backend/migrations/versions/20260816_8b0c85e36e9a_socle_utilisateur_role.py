from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "8b0c85e36e9a"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    op.create_table(
        "permission",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("libelle", sa.String(length=150), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permission")),
        sa.UniqueConstraint("code", name=op.f("uq_permission_code")),
    )
    op.create_table(
        "role",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("libelle", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role")),
        sa.UniqueConstraint("code", name=op.f("uq_role_code")),
    )
    op.create_table(
        "utilisateur",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("mot_de_passe_hash", sa.String(length=255), nullable=False),
        sa.Column("nom", sa.String(length=100), nullable=False),
        sa.Column("prenom", sa.String(length=100), nullable=False),
        sa.Column("poste", sa.String(length=120), nullable=True),
        sa.Column("service", sa.String(length=120), nullable=True),
        sa.Column("date_entree", sa.Date(), nullable=True),
        sa.Column("manager_id", sa.Uuid(), nullable=True),
        sa.Column("version_jeton", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("actif", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "manager_id IS NULL OR manager_id <> id",
            name=op.f("ck_utilisateur_pas_son_manager"),
        ),
        sa.ForeignKeyConstraint(
            ["manager_id"],
            ["utilisateur.id"],
            name=op.f("fk_utilisateur_manager_id_utilisateur"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_utilisateur")),
        sa.UniqueConstraint("email", name=op.f("uq_utilisateur_email")),
    )
    op.create_index(op.f("ix_utilisateur_manager_id"), "utilisateur", ["manager_id"], unique=False)
    op.create_table(
        "role_permission",
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permission.id"],
            name=op.f("fk_role_permission_permission_id_permission"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["role.id"],
            name=op.f("fk_role_permission_role_id_role"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id", name=op.f("pk_role_permission")),
    )
    op.create_table(
        "utilisateur_role",
        sa.Column("utilisateur_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column(
            "attribue_le",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["role.id"],
            name=op.f("fk_utilisateur_role_role_id_role"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["utilisateur_id"],
            ["utilisateur.id"],
            name=op.f("fk_utilisateur_role_utilisateur_id_utilisateur"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("utilisateur_id", "role_id", name=op.f("pk_utilisateur_role")),
    )


def downgrade() -> None:
    op.drop_table("utilisateur_role")
    op.drop_table("role_permission")
    op.drop_index(op.f("ix_utilisateur_manager_id"), table_name="utilisateur")
    op.drop_table("utilisateur")
    op.drop_table("role")
    op.drop_table("permission")

    op.execute("DROP EXTENSION IF EXISTS citext")
