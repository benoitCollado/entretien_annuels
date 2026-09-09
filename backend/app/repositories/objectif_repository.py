from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.enums import StatutObjectif
from app.models.objectif import Objectif
from app.repositories.base import BaseRepository


class ObjectifRepository(BaseRepository[Objectif]):
    modele = Objectif

    def lister_de_l_entretien(self, entretien_id: UUID) -> list[Objectif]:
        stmt = (
            select(Objectif)
            .where(Objectif.entretien_origine_id == entretien_id)
            .order_by(Objectif.created_at)
        )
        return list(self.session.scalars(stmt))

    def lister_a_evaluer(self, collaborateur_id: UUID, entretien_exclu: UUID) -> list[Objectif]:
        stmt = (
            select(Objectif)
            .options(selectinload(Objectif.entretien_origine))
            .where(
                Objectif.collaborateur_id == collaborateur_id,
                Objectif.statut == StatutObjectif.EN_COURS,
                Objectif.entretien_origine_id != entretien_exclu,
            )
            .order_by(Objectif.echeance.nulls_last(), Objectif.created_at)
        )
        return list(self.session.scalars(stmt))

    def lister_du_collaborateur(self, collaborateur_id: UUID) -> list[Objectif]:
        stmt = (
            select(Objectif)
            .where(Objectif.collaborateur_id == collaborateur_id)
            .order_by(Objectif.created_at.desc())
        )
        return list(self.session.scalars(stmt))
