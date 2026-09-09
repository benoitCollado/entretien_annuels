from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, HorodatageMixin, cle_primaire_uuid
from app.models.enums import StatutObjectif, valeurs_sql

if TYPE_CHECKING:
    from app.models.entretien import Entretien
    from app.models.utilisateur import Utilisateur


class Objectif(Base, HorodatageMixin):
    __tablename__ = "objectif"
    __table_args__ = (
        CheckConstraint(f"statut IN ({valeurs_sql(StatutObjectif)})", name="statut_valide"),
        CheckConstraint(
            "niveau_atteinte IS NULL OR (niveau_atteinte BETWEEN 0 AND 100)",
            name="niveau_atteinte_valide",
        ),
        CheckConstraint(
            "(statut = 'EN_COURS' AND entretien_evaluation_id IS NULL"
            " AND niveau_atteinte IS NULL)"
            " OR (statut <> 'EN_COURS' AND entretien_evaluation_id IS NOT NULL)",
            name="evaluation_coherente",
        ),
        CheckConstraint(
            "entretien_evaluation_id IS NULL OR entretien_evaluation_id <> entretien_origine_id",
            name="origine_et_evaluation_distinctes",
        ),
        Index("ix_objectif_collaborateur", "collaborateur_id", "statut"),
        Index("ix_objectif_entretien_origine", "entretien_origine_id"),
    )

    id: Mapped[uuid.UUID] = cle_primaire_uuid()

    entretien_origine_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("entretien.id", ondelete="RESTRICT"), nullable=False
    )
    entretien_evaluation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("entretien.id", ondelete="RESTRICT"), nullable=True
    )
    objectif_parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("objectif.id", ondelete="SET NULL"), nullable=True
    )
    collaborateur_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("utilisateur.id", ondelete="RESTRICT"), nullable=False
    )

    libelle: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    indicateur: Mapped[str | None] = mapped_column(Text, nullable=True)
    echeance: Mapped[date | None] = mapped_column(Date, nullable=True)

    statut: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text(f"'{StatutObjectif.EN_COURS}'")
    )
    niveau_atteinte: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    commentaire_evaluation: Mapped[str | None] = mapped_column(Text, nullable=True)

    entretien_origine: Mapped[Entretien] = relationship(
        foreign_keys=[entretien_origine_id], back_populates="objectifs_fixes"
    )
    entretien_evaluation: Mapped[Entretien | None] = relationship(
        foreign_keys=[entretien_evaluation_id], back_populates="objectifs_evalues"
    )
    collaborateur: Mapped[Utilisateur] = relationship(foreign_keys=[collaborateur_id])

    @property
    def est_evalue(self) -> bool:
        return self.statut != StatutObjectif.EN_COURS

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Objectif {self.libelle[:30]!r} {self.statut}>"
