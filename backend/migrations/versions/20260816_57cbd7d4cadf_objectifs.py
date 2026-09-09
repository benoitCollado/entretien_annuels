from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "57cbd7d4cadf"
down_revision: str | None = "81ffaec36551"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "objectif",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entretien_origine_id", sa.Uuid(), nullable=False),
        sa.Column("entretien_evaluation_id", sa.Uuid(), nullable=True),
        sa.Column("objectif_parent_id", sa.Uuid(), nullable=True),
        sa.Column("collaborateur_id", sa.Uuid(), nullable=False),
        sa.Column("libelle", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("indicateur", sa.Text(), nullable=True),
        sa.Column("echeance", sa.Date(), nullable=True),
        sa.Column(
            "statut", sa.String(length=20), server_default=sa.text("'EN_COURS'"), nullable=False
        ),
        sa.Column("niveau_atteinte", sa.SmallInteger(), nullable=True),
        sa.Column("commentaire_evaluation", sa.Text(), nullable=True),
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
        sa.CheckConstraint(
            "(statut = 'EN_COURS' AND entretien_evaluation_id IS NULL AND niveau_atteinte IS NULL) OR (statut <> 'EN_COURS' AND entretien_evaluation_id IS NOT NULL)",
            name=op.f("ck_objectif_evaluation_coherente"),
        ),
        sa.CheckConstraint(
            "statut IN ('EN_COURS', 'ATTEINT', 'PARTIEL', 'NON_ATTEINT')",
            name=op.f("ck_objectif_statut_valide"),
        ),
        sa.CheckConstraint(
            "entretien_evaluation_id IS NULL OR entretien_evaluation_id <> entretien_origine_id",
            name=op.f("ck_objectif_origine_et_evaluation_distinctes"),
        ),
        sa.CheckConstraint(
            "niveau_atteinte IS NULL OR (niveau_atteinte BETWEEN 0 AND 100)",
            name=op.f("ck_objectif_niveau_atteinte_valide"),
        ),
        sa.ForeignKeyConstraint(
            ["collaborateur_id"],
            ["utilisateur.id"],
            name=op.f("fk_objectif_collaborateur_id_utilisateur"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["entretien_evaluation_id"],
            ["entretien.id"],
            name=op.f("fk_objectif_entretien_evaluation_id_entretien"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["entretien_origine_id"],
            ["entretien.id"],
            name=op.f("fk_objectif_entretien_origine_id_entretien"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["objectif_parent_id"],
            ["objectif.id"],
            name=op.f("fk_objectif_objectif_parent_id_objectif"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_objectif")),
    )
    op.create_index(
        "ix_objectif_collaborateur", "objectif", ["collaborateur_id", "statut"], unique=False
    )
    op.create_index(
        "ix_objectif_entretien_origine", "objectif", ["entretien_origine_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_objectif_entretien_origine", table_name="objectif")
    op.drop_index("ix_objectif_collaborateur", table_name="objectif")
    op.drop_table("objectif")
