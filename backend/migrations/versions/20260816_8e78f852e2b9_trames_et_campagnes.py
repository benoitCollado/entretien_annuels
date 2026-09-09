from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "8e78f852e2b9"
down_revision: str | None = "4e2bb21d65e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "campagne",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("libelle", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("annee", sa.SmallInteger(), nullable=False),
        sa.Column("type_entretien", sa.String(length=20), nullable=False),
        sa.Column("date_ouverture", sa.Date(), nullable=False),
        sa.Column("date_limite", sa.Date(), nullable=False),
        sa.Column(
            "statut", sa.String(length=20), server_default=sa.text("'BROUILLON'"), nullable=False
        ),
        sa.Column("ouverte_par_id", sa.Uuid(), nullable=True),
        sa.Column("ouverte_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cloturee_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "statut IN ('BROUILLON', 'OUVERTE', 'CLOTUREE')", name=op.f("ck_campagne_statut_valide")
        ),
        sa.CheckConstraint(
            "type_entretien IN ('ANNUEL', 'PROFESSIONNEL')",
            name=op.f("ck_campagne_type_entretien_valide"),
        ),
        sa.CheckConstraint("annee BETWEEN 2000 AND 2200", name=op.f("ck_campagne_annee_plausible")),
        sa.CheckConstraint(
            "date_limite > date_ouverture", name=op.f("ck_campagne_dates_coherentes")
        ),
        sa.ForeignKeyConstraint(
            ["ouverte_par_id"],
            ["utilisateur.id"],
            name=op.f("fk_campagne_ouverte_par_id_utilisateur"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campagne")),
        sa.UniqueConstraint("annee", "type_entretien", name="uq_campagne_annee_type"),
    )
    op.create_index(
        op.f("ix_campagne_ouverte_par_id"), "campagne", ["ouverte_par_id"], unique=False
    )
    op.create_table(
        "template",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nom", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type_entretien", sa.String(length=20), nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "statut", sa.String(length=20), server_default=sa.text("'BROUILLON'"), nullable=False
        ),
        sa.Column("template_parent_id", sa.Uuid(), nullable=True),
        sa.Column("redige_par_id", sa.Uuid(), nullable=True),
        sa.Column("publie_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "statut IN ('BROUILLON', 'PUBLIEE', 'ARCHIVEE')", name=op.f("ck_template_statut_valide")
        ),
        sa.CheckConstraint(
            "type_entretien IN ('ANNUEL', 'PROFESSIONNEL')",
            name=op.f("ck_template_type_entretien_valide"),
        ),
        sa.CheckConstraint("version >= 1", name=op.f("ck_template_version_positive")),
        sa.ForeignKeyConstraint(
            ["redige_par_id"],
            ["utilisateur.id"],
            name=op.f("fk_template_redige_par_id_utilisateur"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["template_parent_id"],
            ["template.id"],
            name=op.f("fk_template_template_parent_id_template"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_template")),
        sa.UniqueConstraint("nom", "version", name="uq_template_nom_version"),
    )
    op.create_index(op.f("ix_template_redige_par_id"), "template", ["redige_par_id"], unique=False)
    op.create_index(
        op.f("ix_template_template_parent_id"), "template", ["template_parent_id"], unique=False
    )
    op.create_table(
        "section_template",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("template_id", sa.Uuid(), nullable=False),
        sa.Column("titre", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ordre", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("ordre >= 0", name=op.f("ck_section_template_ordre_positif")),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["template.id"],
            name=op.f("fk_section_template_template_id_template"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_section_template")),
        sa.UniqueConstraint(
            "template_id",
            "ordre",
            deferrable=True,
            initially="DEFERRED",
            name="uq_section_template_ordre",
        ),
    )
    op.create_index(
        op.f("ix_section_template_template_id"), "section_template", ["template_id"], unique=False
    )
    op.create_table(
        "question_template",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("section_template_id", sa.Uuid(), nullable=False),
        sa.Column("libelle", sa.Text(), nullable=False),
        sa.Column("aide", sa.Text(), nullable=True),
        sa.Column("type_question", sa.String(length=30), nullable=False),
        sa.Column("cible", sa.String(length=20), nullable=False),
        sa.Column("obligatoire", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("ordre", sa.SmallInteger(), nullable=False),
        sa.Column(
            "configuration",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "cible IN ('COLLABORATEUR', 'MANAGER', 'PARTAGEE')",
            name=op.f("ck_question_template_cible_valide"),
        ),
        sa.CheckConstraint(
            "jsonb_typeof(configuration) = 'object'",
            name=op.f("ck_question_template_configuration_objet"),
        ),
        sa.CheckConstraint(
            "type_question IN ('texte_libre', 'texte_court', 'echelle', 'choix_unique', 'choix_multiple', 'oui_non', 'date', 'note_5')",
            name=op.f("ck_question_template_type_question_valide"),
        ),
        sa.CheckConstraint("ordre >= 0", name=op.f("ck_question_template_ordre_positif")),
        sa.ForeignKeyConstraint(
            ["section_template_id"],
            ["section_template.id"],
            name=op.f("fk_question_template_section_template_id_section_template"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_question_template")),
        sa.UniqueConstraint(
            "section_template_id",
            "ordre",
            deferrable=True,
            initially="DEFERRED",
            name="uq_question_template_ordre",
        ),
    )
    op.create_index(
        op.f("ix_question_template_section_template_id"),
        "question_template",
        ["section_template_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_question_template_section_template_id"), table_name="question_template")
    op.drop_table("question_template")
    op.drop_index(op.f("ix_section_template_template_id"), table_name="section_template")
    op.drop_table("section_template")
    op.drop_index(op.f("ix_template_template_parent_id"), table_name="template")
    op.drop_index(op.f("ix_template_redige_par_id"), table_name="template")
    op.drop_table("template")
    op.drop_index(op.f("ix_campagne_ouverte_par_id"), table_name="campagne")
    op.drop_table("campagne")
