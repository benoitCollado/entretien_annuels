from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Select, func, select

from app.models.campagne import Campagne
from app.repositories.base import BaseRepository


class CampagneRepository(BaseRepository[Campagne]):
    modele = Campagne

    def get_par_annee_et_type(self, annee: int, type_entretien: str) -> Campagne | None:
        stmt = select(Campagne).where(
            Campagne.annee == annee, Campagne.type_entretien == type_entretien
        )
        return self.session.scalars(stmt).one_or_none()

    def _base_liste(
        self, *, statut: str | None, annee: int | None, type_entretien: str | None
    ) -> Select[tuple[Campagne]]:
        stmt = select(Campagne)
        if statut is not None:
            stmt = stmt.where(Campagne.statut == statut)
        if annee is not None:
            stmt = stmt.where(Campagne.annee == annee)
        if type_entretien is not None:
            stmt = stmt.where(Campagne.type_entretien == type_entretien)
        return stmt

    def lister_filtre(
        self,
        *,
        statut: str | None = None,
        annee: int | None = None,
        type_entretien: str | None = None,
        limite: int = 50,
        decalage: int = 0,
    ) -> list[Campagne]:
        stmt = (
            self._base_liste(statut=statut, annee=annee, type_entretien=type_entretien)
            .order_by(Campagne.annee.desc(), Campagne.libelle)
            .limit(limite)
            .offset(decalage)
        )
        return list(self.session.scalars(stmt))

    def compter(
        self,
        *,
        statut: str | None = None,
        annee: int | None = None,
        type_entretien: str | None = None,
    ) -> int:
        stmt = self._base_liste(
            statut=statut, annee=annee, type_entretien=type_entretien
        ).with_only_columns(func.count(Campagne.id))
        return self.session.scalar(stmt) or 0

    def lister_echues_ouvertes(self, aujourdhui: date) -> list[Campagne]:
        stmt = (
            select(Campagne)
            .where(Campagne.statut == "OUVERTE", Campagne.date_limite < aujourdhui)
            .order_by(Campagne.date_limite)
        )
        return list(self.session.scalars(stmt))

    def get_ouverte(self, id_: UUID) -> Campagne | None:
        stmt = select(Campagne).where(Campagne.id == id_, Campagne.statut == "OUVERTE")
        return self.session.scalars(stmt).one_or_none()
