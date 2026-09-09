from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Uuid, text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, cle_primaire_uuid
from app.models.enums import Action, valeurs_sql

if TYPE_CHECKING:
    from app.models.utilisateur import Utilisateur


class JournalAudit(Base):
    __tablename__ = "journal_audit"
    __table_args__ = (
        CheckConstraint(f"action IN ({valeurs_sql(Action)})", name="action_valide"),
        Index("ix_audit_entretien_horodatage", "entretien_id", "horodatage"),
    )

    id: Mapped[uuid.UUID] = cle_primaire_uuid()
    entretien_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("entretien.id", ondelete="SET NULL"), nullable=True
    )
    utilisateur_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("utilisateur.id", ondelete="SET NULL"), nullable=True
    )

    action: Mapped[str] = mapped_column(String(40), nullable=False)
    statut_avant: Mapped[str | None] = mapped_column(String(30), nullable=True)
    statut_apres: Mapped[str | None] = mapped_column(String(30), nullable=True)

    donnees: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    adresse_ip: Mapped[str | None] = mapped_column(INET, nullable=True)

    horodatage: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    utilisateur: Mapped[Utilisateur | None] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<JournalAudit {self.action} {self.statut_avant}→{self.statut_apres}>"
