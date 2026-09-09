from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from app.models.questionnaire import Question, Section
from app.models.reponse import Reponse
from app.repositories.base import BaseRepository


class ReponseRepository(BaseRepository[Reponse]):
    modele = Reponse

    def _du_questionnaire(self, questionnaire_id: UUID) -> Select[tuple[Reponse]]:
        return (
            select(Reponse)
            .join(Question, Question.id == Reponse.question_id)
            .join(Section, Section.id == Question.section_id)
            .where(Section.questionnaire_id == questionnaire_id)
        )

    def lister_du_questionnaire(
        self,
        questionnaire_id: UUID,
        auteurs_autorises: list[UUID] | None,
    ) -> list[Reponse]:
        if auteurs_autorises is not None and len(auteurs_autorises) == 0:
            return []

        stmt = self._du_questionnaire(questionnaire_id).options(selectinload(Reponse.auteur))
        if auteurs_autorises is not None:
            stmt = stmt.where(Reponse.auteur_id.in_(auteurs_autorises))

        return list(self.session.scalars(stmt))

    def get_par_question_et_auteur(self, question_id: UUID, auteur_id: UUID) -> Reponse | None:
        stmt = select(Reponse).where(
            Reponse.question_id == question_id, Reponse.auteur_id == auteur_id
        )
        return self.session.scalars(stmt).one_or_none()

    def ids_questions_repondues(self, questionnaire_id: UUID, auteur_id: UUID) -> set[UUID]:
        stmt = (
            select(Reponse.question_id)
            .join(Question, Question.id == Reponse.question_id)
            .join(Section, Section.id == Question.section_id)
            .where(
                Section.questionnaire_id == questionnaire_id,
                Reponse.auteur_id == auteur_id,
                Reponse.valeur.isnot(None),
            )
        )
        return set(self.session.scalars(stmt))

    def compter_du_questionnaire(self, questionnaire_id: UUID, auteur_id: UUID) -> int:
        stmt = (
            self._du_questionnaire(questionnaire_id)
            .with_only_columns(func.count(Reponse.id))
            .where(Reponse.auteur_id == auteur_id)
        )
        return self.session.scalar(stmt) or 0

    def question_appartient_au_questionnaire(
        self, question_id: UUID, questionnaire_id: UUID
    ) -> bool:
        stmt = (
            select(Question.id)
            .join(Section, Section.id == Question.section_id)
            .where(Question.id == question_id, Section.questionnaire_id == questionnaire_id)
        )
        return self.session.scalar(select(stmt.exists())) or False
