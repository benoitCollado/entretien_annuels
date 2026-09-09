from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ArchivableMixin, Base, HorodatageMixin, cle_primaire_uuid
from app.models.enums import StatutEntretien, TypeEntretien, valeurs_sql

if TYPE_CHECKING:
    from app.models.campagne import Campagne
    from app.models.objectif import Objectif
    from app.models.questionnaire import Questionnaire
    from app.models.utilisateur import Utilisateur


class Entretien(Base, HorodatageMixin, ArchivableMixin):
    __tablename__ = "entretien"
    __table_args__ = (
        UniqueConstraint("campagne_id", "collaborateur_id", name="uq_entretien_campagne_collab"),
        CheckConstraint("collaborateur_id <> manager_id", name="acteurs_distincts"),
        CheckConstraint(f"statut IN ({valeurs_sql(StatutEntretien)})", name="statut_valide"),
        CheckConstraint(
            f"type_entretien IN ({valeurs_sql(TypeEntretien)})", name="type_entretien_valide"
        ),
        Index("ix_entretien_manager_statut", "manager_id", "statut"),
        Index("ix_entretien_campagne_statut", "campagne_id", "statut"),
    )

    id: Mapped[uuid.UUID] = cle_primaire_uuid()

    campagne_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("campagne.id", ondelete="RESTRICT"), nullable=False
    )
    collaborateur_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("utilisateur.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    manager_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("utilisateur.id", ondelete="RESTRICT"), nullable=False
    )

    type_entretien: Mapped[str] = mapped_column(String(20), nullable=False)
    statut: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=text("'BROUILLON'")
    )
    date_planifiee: Mapped[date | None] = mapped_column(Date, nullable=True)

    soumis_collaborateur_le: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revue_ouverte_le: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    realise_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    signe_collaborateur_le: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    signe_manager_le: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cloture_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    observation_collaborateur: Mapped[str | None] = mapped_column(Text, nullable=True)
    motif_annulation: Mapped[str | None] = mapped_column(Text, nullable=True)

    campagne: Mapped[Campagne] = relationship()
    collaborateur: Mapped[Utilisateur] = relationship(foreign_keys=[collaborateur_id])
    manager: Mapped[Utilisateur] = relationship(foreign_keys=[manager_id])
    questionnaire: Mapped[Questionnaire | None] = relationship(
        back_populates="entretien", cascade="all, delete-orphan", uselist=False
    )
    objectifs_fixes: Mapped[list[Objectif]] = relationship(
        back_populates="entretien_origine",
        foreign_keys="Objectif.entretien_origine_id",
    )
    objectifs_evalues: Mapped[list[Objectif]] = relationship(
        back_populates="entretien_evaluation",
        foreign_keys="Objectif.entretien_evaluation_id",
    )

    def role_de(self, utilisateur_id: uuid.UUID) -> str | None:
        if utilisateur_id == self.collaborateur_id:
            return "COLLABORATEUR"
        if utilisateur_id == self.manager_id:
            return "MANAGER"
        return None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Entretien {self.id} ({self.statut})>"
