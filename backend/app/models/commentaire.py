from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, HorodatageMixin, cle_primaire_uuid

if TYPE_CHECKING:
    from app.models.questionnaire import Questionnaire
    from app.models.utilisateur import Utilisateur


class Commentaire(Base, HorodatageMixin):
    __tablename__ = "commentaire"
    __table_args__ = (Index("ix_commentaire_questionnaire", "questionnaire_id"),)

    id: Mapped[uuid.UUID] = cle_primaire_uuid()
    questionnaire_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("questionnaire.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("question.id", ondelete="CASCADE"), nullable=True
    )
    auteur_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("utilisateur.id", ondelete="RESTRICT"), nullable=False
    )
    contenu: Mapped[str] = mapped_column(Text, nullable=False)

    questionnaire: Mapped[Questionnaire] = relationship(back_populates="commentaires")
    auteur: Mapped[Utilisateur] = relationship()

    @property
    def est_synthese(self) -> bool:
        return self.question_id is None
