from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.questionnaire import Questionnaire, Section
from app.repositories.base import BaseRepository


class QuestionnaireRepository(BaseRepository[Questionnaire]):
    modele = Questionnaire

    def get_avec_arborescence(self, id_: UUID) -> Questionnaire | None:
        stmt = (
            select(Questionnaire)
            .options(selectinload(Questionnaire.sections).selectinload(Section.questions))
            .where(Questionnaire.id == id_)
        )
        return self.session.scalars(stmt).one_or_none()

    def get_par_entretien(self, entretien_id: UUID) -> Questionnaire | None:
        stmt = (
            select(Questionnaire)
            .options(selectinload(Questionnaire.sections).selectinload(Section.questions))
            .where(Questionnaire.entretien_id == entretien_id)
        )
        return self.session.scalars(stmt).one_or_none()
