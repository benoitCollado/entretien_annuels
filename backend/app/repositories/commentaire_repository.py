from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.commentaire import Commentaire
from app.repositories.base import BaseRepository


class CommentaireRepository(BaseRepository[Commentaire]):
    modele = Commentaire

    def lister_du_questionnaire(self, questionnaire_id: UUID) -> list[Commentaire]:
        stmt = (
            select(Commentaire)
            .options(selectinload(Commentaire.auteur))
            .where(Commentaire.questionnaire_id == questionnaire_id)
            .order_by(Commentaire.created_at)
        )
        return list(self.session.scalars(stmt))

    def get_synthese(self, questionnaire_id: UUID, auteur_id: UUID) -> Commentaire | None:
        stmt = select(Commentaire).where(
            Commentaire.questionnaire_id == questionnaire_id,
            Commentaire.auteur_id == auteur_id,
            Commentaire.question_id.is_(None),
        )
        return self.session.scalars(stmt).one_or_none()

    def existe_synthese(self, questionnaire_id: UUID) -> bool:
        stmt = select(Commentaire.id).where(
            Commentaire.questionnaire_id == questionnaire_id,
            Commentaire.question_id.is_(None),
        )
        return self.session.scalar(select(stmt.exists())) or False
