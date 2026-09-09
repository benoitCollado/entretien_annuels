from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "b7d2e91f5a04"
down_revision: str | None = "a3f1c0d84b27"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONTRAINTE = "action_valide"

ACTIONS_AVANT = (
    "ASSIGNATION",
    "PREMIERE_SAISIE",
    "ENREGISTREMENT_BROUILLON",
    "SOUMISSION_COLLABORATEUR",
    "OUVERTURE_REVUE",
    "COMMENTAIRE",
    "SYNTHESE",
    "CLOTURE_ECHANGE",
    "SIGNATURE",
    "CLOTURE",
    "ANNULATION",
    "QUESTION_AD_HOC",
    "ACCES_REFUSE",
    "CONSULTATION",
)
ACTIONS_APRES = (*ACTIONS_AVANT, "OBJECTIF_FIXE", "OBJECTIF_EVALUE", "EXPORT_PDF")


def _condition(actions: tuple[str, ...]) -> str:
    valeurs = ", ".join(f"'{action}'" for action in actions)
    return f"action IN ({valeurs})"


def upgrade() -> None:
    op.drop_constraint(CONTRAINTE, "journal_audit", type_="check")
    op.create_check_constraint(CONTRAINTE, "journal_audit", _condition(ACTIONS_APRES))


def downgrade() -> None:
    valeurs = ", ".join(
        f"'{action}'" for action in ("OBJECTIF_FIXE", "OBJECTIF_EVALUE", "EXPORT_PDF")
    )
    op.execute(f"DELETE FROM journal_audit WHERE action IN ({valeurs})")

    op.drop_constraint(CONTRAINTE, "journal_audit", type_="check")
    op.create_check_constraint(CONTRAINTE, "journal_audit", _condition(ACTIONS_AVANT))
