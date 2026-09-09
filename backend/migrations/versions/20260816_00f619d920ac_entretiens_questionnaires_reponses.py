from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "00f619d920ac"
down_revision: str | None = "fb952e1d49d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "entretien",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campagne_id", sa.Uuid(), nullable=False),
        sa.Column("collaborateur_id", sa.Uuid(), nullable=False),
        sa.Column("manager_id", sa.Uuid(), nullable=False),
        sa.Column("type_entretien", sa.String(length=20), nullable=False),
        sa.Column(
            "statut", sa.String(length=30), server_default=sa.text("'BROUILLON'"), nullable=False
        ),
        sa.Column("date_planifiee", sa.Date(), nullable=True),
        sa.Column("soumis_collaborateur_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revue_ouverte_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column("realise_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signe_collaborateur_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signe_manager_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cloture_le", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observation_collaborateur", sa.Text(), nullable=True),
        sa.Column("motif_annulation", sa.Text(), nullable=True),
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
            "statut IN ('BROUILLON', 'PLANIFIE', 'PREPARATION', 'SOUMIS_COLLABORATEUR', 'REVUE_MANAGER', 'ENTRETIEN_REALISE', 'SIGNE', 'CLOTURE', 'ANNULE')",
            name=op.f("ck_entretien_statut_valide"),
        ),
        sa.CheckConstraint(
            "type_entretien IN ('ANNUEL', 'PROFESSIONNEL')",
            name=op.f("ck_entretien_type_entretien_valide"),
        ),
        sa.CheckConstraint(
            "collaborateur_id <> manager_id", name=op.f("ck_entretien_acteurs_distincts")
        ),
        sa.ForeignKeyConstraint(
            ["campagne_id"],
            ["campagne.id"],
            name=op.f("fk_entretien_campagne_id_campagne"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["collaborateur_id"],
            ["utilisateur.id"],
            name=op.f("fk_entretien_collaborateur_id_utilisateur"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["manager_id"],
            ["utilisateur.id"],
            name=op.f("fk_entretien_manager_id_utilisateur"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_entretien")),
        sa.UniqueConstraint("campagne_id", "collaborateur_id", name="uq_entretien_campagne_collab"),
    )
    op.create_index(
        "ix_entretien_campagne_statut", "entretien", ["campagne_id", "statut"], unique=False
    )
    op.create_index(
        op.f("ix_entretien_collaborateur_id"), "entretien", ["collaborateur_id"], unique=False
    )
    op.create_index(
        "ix_entretien_manager_statut", "entretien", ["manager_id", "statut"], unique=False
    )
    op.create_table(
        "journal_audit",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entretien_id", sa.Uuid(), nullable=True),
        sa.Column("utilisateur_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("statut_avant", sa.String(length=30), nullable=True),
        sa.Column("statut_apres", sa.String(length=30), nullable=True),
        sa.Column("donnees", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("adresse_ip", postgresql.INET(), nullable=True),
        sa.Column(
            "horodatage",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "action IN ('ASSIGNATION', 'PREMIERE_SAISIE', 'ENREGISTREMENT_BROUILLON', 'SOUMISSION_COLLABORATEUR', 'OUVERTURE_REVUE', 'COMMENTAIRE', 'SYNTHESE', 'CLOTURE_ECHANGE', 'SIGNATURE', 'CLOTURE', 'ANNULATION', 'QUESTION_AD_HOC', 'ACCES_REFUSE', 'CONSULTATION')",
            name=op.f("ck_journal_audit_action_valide"),
        ),
        sa.ForeignKeyConstraint(
            ["entretien_id"],
            ["entretien.id"],
            name=op.f("fk_journal_audit_entretien_id_entretien"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["utilisateur_id"],
            ["utilisateur.id"],
            name=op.f("fk_journal_audit_utilisateur_id_utilisateur"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_journal_audit")),
    )
    op.create_index(
        "ix_audit_entretien_horodatage",
        "journal_audit",
        ["entretien_id", "horodatage"],
        unique=False,
    )
    op.create_table(
        "questionnaire",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entretien_id", sa.Uuid(), nullable=False),
        sa.Column("template_id", sa.Uuid(), nullable=True),
        sa.Column("template_version", sa.Integer(), nullable=False),
        sa.Column("titre", sa.String(length=150), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("template_version >= 1", name=op.f("ck_questionnaire_version_positive")),
        sa.ForeignKeyConstraint(
            ["entretien_id"],
            ["entretien.id"],
            name=op.f("fk_questionnaire_entretien_id_entretien"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["template.id"],
            name=op.f("fk_questionnaire_template_id_template"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_questionnaire")),
        sa.UniqueConstraint("entretien_id", name="uq_questionnaire_entretien"),
    )
    op.create_table(
        "section",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("questionnaire_id", sa.Uuid(), nullable=False),
        sa.Column("titre", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ordre", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("ordre >= 0", name=op.f("ck_section_ordre_positif")),
        sa.ForeignKeyConstraint(
            ["questionnaire_id"],
            ["questionnaire.id"],
            name=op.f("fk_section_questionnaire_id_questionnaire"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_section")),
        sa.UniqueConstraint(
            "questionnaire_id",
            "ordre",
            deferrable=True,
            initially="DEFERRED",
            name="uq_section_ordre",
        ),
    )
    op.create_table(
        "question",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.Uuid(), nullable=False),
        sa.Column("question_template_id", sa.Uuid(), nullable=True),
        sa.Column("ajoutee_par_id", sa.Uuid(), nullable=True),
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
            name=op.f("ck_question_cible_valide"),
        ),
        sa.CheckConstraint(
            "jsonb_typeof(configuration) = 'object'", name=op.f("ck_question_configuration_objet")
        ),
        sa.CheckConstraint(
            "type_question IN ('texte_libre', 'texte_court', 'echelle', 'choix_unique', 'choix_multiple', 'oui_non', 'date', 'note_5')",
            name=op.f("ck_question_type_question_valide"),
        ),
        sa.CheckConstraint("ordre >= 0", name=op.f("ck_question_ordre_positif")),
        sa.ForeignKeyConstraint(
            ["ajoutee_par_id"],
            ["utilisateur.id"],
            name=op.f("fk_question_ajoutee_par_id_utilisateur"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["question_template_id"],
            ["question_template.id"],
            name=op.f("fk_question_question_template_id_question_template"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["section_id"],
            ["section.id"],
            name=op.f("fk_question_section_id_section"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_question")),
        sa.UniqueConstraint(
            "section_id", "ordre", deferrable=True, initially="DEFERRED", name="uq_question_ordre"
        ),
    )
    op.create_index("ix_question_section_ordre", "question", ["section_id", "ordre"], unique=False)
    op.create_table(
        "commentaire",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("questionnaire_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=True),
        sa.Column("auteur_id", sa.Uuid(), nullable=False),
        sa.Column("contenu", sa.Text(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["auteur_id"],
            ["utilisateur.id"],
            name=op.f("fk_commentaire_auteur_id_utilisateur"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["question.id"],
            name=op.f("fk_commentaire_question_id_question"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["questionnaire_id"],
            ["questionnaire.id"],
            name=op.f("fk_commentaire_questionnaire_id_questionnaire"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_commentaire")),
    )
    op.create_index(
        "ix_commentaire_questionnaire", "commentaire", ["questionnaire_id"], unique=False
    )
    op.create_table(
        "reponse",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("auteur_id", sa.Uuid(), nullable=False),
        sa.Column("valeur", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.CheckConstraint("jsonb_typeof(valeur) = 'object'", name=op.f("ck_reponse_valeur_objet")),
        sa.ForeignKeyConstraint(
            ["auteur_id"],
            ["utilisateur.id"],
            name=op.f("fk_reponse_auteur_id_utilisateur"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["question.id"],
            name=op.f("fk_reponse_question_id_question"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reponse")),
        sa.UniqueConstraint("question_id", "auteur_id", name="uq_reponse_question_auteur"),
    )
    op.create_index(
        "ix_reponse_question_auteur", "reponse", ["question_id", "auteur_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_reponse_question_auteur", table_name="reponse")
    op.drop_table("reponse")
    op.drop_index("ix_commentaire_questionnaire", table_name="commentaire")
    op.drop_table("commentaire")
    op.drop_index("ix_question_section_ordre", table_name="question")
    op.drop_table("question")
    op.drop_table("section")
    op.drop_table("questionnaire")
    op.drop_index("ix_audit_entretien_horodatage", table_name="journal_audit")
    op.drop_table("journal_audit")
    op.drop_index("ix_entretien_manager_statut", table_name="entretien")
    op.drop_index(op.f("ix_entretien_collaborateur_id"), table_name="entretien")
    op.drop_index("ix_entretien_campagne_statut", table_name="entretien")
    op.drop_table("entretien")
