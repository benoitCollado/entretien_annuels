from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select

from app.models.questionnaire import Question, Section
from app.repositories.base import BaseRepository


class QuestionRepository(BaseRepository[Question]):
    modele = Question

    def lister_du_questionnaire(self, questionnaire_id: UUID) -> list[Question]:
        stmt = (
            select(Question)
            .join(Section, Section.id == Question.section_id)
            .where(Section.questionnaire_id == questionnaire_id)
            .order_by(Section.ordre, Question.ordre)
        )
        return list(self.session.scalars(stmt))

    def get_section(self, section_id: UUID) -> Section | None:
        return self.session.get(Section, section_id)

    def prochain_ordre(self, section_id: UUID) -> int:
        stmt = select(func.max(Question.ordre)).where(Question.section_id == section_id)
        maximum = self.session.scalar(stmt)
        return 0 if maximum is None else maximum + 1

    def section_appartient_au_questionnaire(self, section_id: UUID, questionnaire_id: UUID) -> bool:
        stmt = select(Section.id).where(
            Section.id == section_id, Section.questionnaire_id == questionnaire_id
        )
        return self.session.scalar(select(stmt.exists())) or False
