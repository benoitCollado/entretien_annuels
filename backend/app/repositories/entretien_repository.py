from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from app.models.entretien import Entretien
from app.models.questionnaire import Question, Questionnaire, Section
from app.repositories.base import BaseRepository


class EntretienRepository(BaseRepository[Entretien]):
    modele = Entretien

    def get_avec_questionnaire(self, id_: UUID) -> Entretien | None:
        stmt = (
            select(Entretien)
            .options(
                selectinload(Entretien.questionnaire)
                .selectinload(Questionnaire.sections)
                .selectinload(Section.questions),
                selectinload(Entretien.collaborateur),
                selectinload(Entretien.manager),
            )
            .where(Entretien.id == id_, Entretien.archived_at.is_(None))
        )
        return self.session.scalars(stmt).one_or_none()

    def get_non_archive(self, id_: UUID) -> Entretien | None:
        stmt = select(Entretien).where(Entretien.id == id_, Entretien.archived_at.is_(None))
        return self.session.scalars(stmt).one_or_none()

    def existe_pour_campagne(self, campagne_id: UUID, collaborateur_id: UUID) -> bool:
        stmt = select(Entretien.id).where(
            Entretien.campagne_id == campagne_id,
            Entretien.collaborateur_id == collaborateur_id,
        )
        return self.session.scalar(select(stmt.exists())) or False

    def _base_liste(
        self,
        *,
        collaborateur_id: UUID | None,
        manager_id: UUID | None,
        campagne_id: UUID | None,
        statut: str | None,
    ) -> Select[tuple[Entretien]]:
        stmt = select(Entretien).where(Entretien.archived_at.is_(None))

        if collaborateur_id is not None and manager_id is not None:
            stmt = stmt.where(
                (Entretien.collaborateur_id == collaborateur_id)
                | (Entretien.manager_id == manager_id)
            )
        elif collaborateur_id is not None:
            stmt = stmt.where(Entretien.collaborateur_id == collaborateur_id)
        elif manager_id is not None:
            stmt = stmt.where(Entretien.manager_id == manager_id)

        if campagne_id is not None:
            stmt = stmt.where(Entretien.campagne_id == campagne_id)
        if statut is not None:
            stmt = stmt.where(Entretien.statut == statut)
        return stmt

    def lister_filtre(
        self,
        *,
        collaborateur_id: UUID | None = None,
        manager_id: UUID | None = None,
        campagne_id: UUID | None = None,
        statut: str | None = None,
        limite: int = 50,
        decalage: int = 0,
    ) -> list[Entretien]:
        stmt = (
            self._base_liste(
                collaborateur_id=collaborateur_id,
                manager_id=manager_id,
                campagne_id=campagne_id,
                statut=statut,
            )
            .options(selectinload(Entretien.collaborateur), selectinload(Entretien.manager))
            .order_by(Entretien.date_planifiee.desc().nullslast(), Entretien.created_at.desc())
            .limit(limite)
            .offset(decalage)
        )
        return list(self.session.scalars(stmt))

    def compter(
        self,
        *,
        collaborateur_id: UUID | None = None,
        manager_id: UUID | None = None,
        campagne_id: UUID | None = None,
        statut: str | None = None,
    ) -> int:
        stmt = self._base_liste(
            collaborateur_id=collaborateur_id,
            manager_id=manager_id,
            campagne_id=campagne_id,
            statut=statut,
        ).with_only_columns(func.count(Entretien.id))
        return self.session.scalar(stmt) or 0

    def compter_par_statut(self, campagne_id: UUID) -> dict[str, int]:
        stmt = (
            select(Entretien.statut, func.count(Entretien.id))
            .where(Entretien.campagne_id == campagne_id, Entretien.archived_at.is_(None))
            .group_by(Entretien.statut)
        )
        return dict(self.session.execute(stmt).all())

    def lister_en_retard(self, campagne_id: UUID, date_limite: date) -> list[Entretien]:
        stmt = (
            select(Entretien)
            .options(selectinload(Entretien.collaborateur), selectinload(Entretien.manager))
            .where(
                Entretien.campagne_id == campagne_id,
                Entretien.archived_at.is_(None),
                Entretien.statut.notin_(["SIGNE", "CLOTURE", "ANNULE"]),
            )
            .order_by(Entretien.statut)
        )
        return list(self.session.scalars(stmt))

    def compter_questions(self, questionnaire_id: UUID) -> int:
        stmt = (
            select(func.count(Question.id))
            .join(Section, Section.id == Question.section_id)
            .where(Section.questionnaire_id == questionnaire_id)
        )
        return self.session.scalar(stmt) or 0
