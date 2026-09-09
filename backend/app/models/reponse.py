from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, HorodatageMixin, cle_primaire_uuid

if TYPE_CHECKING:
    from app.models.questionnaire import Question
    from app.models.utilisateur import Utilisateur


class Reponse(Base, HorodatageMixin):
    __tablename__ = "reponse"
    __table_args__ = (
        UniqueConstraint("question_id", "auteur_id", name="uq_reponse_question_auteur"),
        CheckConstraint("jsonb_typeof(valeur) = 'object'", name="valeur_objet"),
        Index("ix_reponse_question_auteur", "question_id", "auteur_id"),
    )

    id: Mapped[uuid.UUID] = cle_primaire_uuid()
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("question.id", ondelete="CASCADE"), nullable=False
    )
    auteur_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("utilisateur.id", ondelete="RESTRICT"), nullable=False
    )
    valeur: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    question: Mapped[Question] = relationship(back_populates="reponses")
    auteur: Mapped[Utilisateur] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Reponse q={self.question_id} par={self.auteur_id}>"
