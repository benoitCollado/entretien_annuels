from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, cle_primaire_uuid
from app.models.enums import StatutCampagne, TypeEntretien, valeurs_sql

if TYPE_CHECKING:
    from app.models.utilisateur import Utilisateur


class Campagne(Base):
    __tablename__ = "campagne"
    __table_args__ = (
        CheckConstraint("date_limite > date_ouverture", name="dates_coherentes"),
        CheckConstraint(
            f"type_entretien IN ({valeurs_sql(TypeEntretien)})",
            name="type_entretien_valide",
        ),
        CheckConstraint(f"statut IN ({valeurs_sql(StatutCampagne)})", name="statut_valide"),
        CheckConstraint("annee BETWEEN 2000 AND 2200", name="annee_plausible"),
        UniqueConstraint("annee", "type_entretien", name="uq_campagne_annee_type"),
    )

    id: Mapped[uuid.UUID] = cle_primaire_uuid()
    libelle: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    annee: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    type_entretien: Mapped[str] = mapped_column(String(20), nullable=False)

    date_ouverture: Mapped[date] = mapped_column(Date, nullable=False)
    date_limite: Mapped[date] = mapped_column(Date, nullable=False)

    statut: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'BROUILLON'")
    )
    ouverte_par_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("utilisateur.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ouverte_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cloturee_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    ouverte_par: Mapped[Utilisateur | None] = relationship()

    @property
    def accepte_des_entretiens(self) -> bool:
        return self.statut == StatutCampagne.OUVERTE

    def est_echue(self, aujourdhui: date) -> bool:
        return aujourdhui > self.date_limite

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Campagne {self.libelle} {self.annee} ({self.statut})>"
