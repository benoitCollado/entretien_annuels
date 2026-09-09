from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, cle_primaire_uuid
from app.models.enums import Cible, TypeQuestion, valeurs_sql

if TYPE_CHECKING:
    from app.models.commentaire import Commentaire
    from app.models.entretien import Entretien
    from app.models.reponse import Reponse


class Questionnaire(Base):
    __tablename__ = "questionnaire"
    __table_args__ = (
        UniqueConstraint("entretien_id", name="uq_questionnaire_entretien"),
        CheckConstraint("template_version >= 1", name="version_positive"),
    )

    id: Mapped[uuid.UUID] = cle_primaire_uuid()
    entretien_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("entretien.id", ondelete="CASCADE"), nullable=False
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("template.id", ondelete="SET NULL"), nullable=True
    )
    template_version: Mapped[int] = mapped_column(Integer, nullable=False)
    titre: Mapped[str] = mapped_column(String(150), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    entretien: Mapped[Entretien] = relationship(back_populates="questionnaire")
    sections: Mapped[list[Section]] = relationship(
        back_populates="questionnaire",
        cascade="all, delete-orphan",
        order_by="Section.ordre",
    )
    commentaires: Mapped[list[Commentaire]] = relationship(
        back_populates="questionnaire", cascade="all, delete-orphan"
    )

    def toutes_les_questions(self) -> list[Question]:
        return [question for section in self.sections for question in section.questions]


class Section(Base):
    __tablename__ = "section"
    __table_args__ = (
        UniqueConstraint(
            "questionnaire_id",
            "ordre",
            name="uq_section_ordre",
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint("ordre >= 0", name="ordre_positif"),
    )

    id: Mapped[uuid.UUID] = cle_primaire_uuid()
    questionnaire_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("questionnaire.id", ondelete="CASCADE"), nullable=False
    )
    titre: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ordre: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    questionnaire: Mapped[Questionnaire] = relationship(back_populates="sections")
    questions: Mapped[list[Question]] = relationship(
        back_populates="section", cascade="all, delete-orphan", order_by="Question.ordre"
    )


class Question(Base):
    __tablename__ = "question"
    __table_args__ = (
        UniqueConstraint(
            "section_id",
            "ordre",
            name="uq_question_ordre",
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint(
            f"type_question IN ({valeurs_sql(TypeQuestion)})", name="type_question_valide"
        ),
        CheckConstraint(f"cible IN ({valeurs_sql(Cible)})", name="cible_valide"),
        CheckConstraint("ordre >= 0", name="ordre_positif"),
        CheckConstraint("jsonb_typeof(configuration) = 'object'", name="configuration_objet"),
        Index("ix_question_section_ordre", "section_id", "ordre"),
    )

    id: Mapped[uuid.UUID] = cle_primaire_uuid()
    section_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("section.id", ondelete="CASCADE"), nullable=False
    )
    question_template_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("question_template.id", ondelete="SET NULL"),
        nullable=True,
    )
    ajoutee_par_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("utilisateur.id", ondelete="SET NULL"), nullable=True
    )

    libelle: Mapped[str] = mapped_column(Text, nullable=False)
    aide: Mapped[str | None] = mapped_column(Text, nullable=True)
    type_question: Mapped[str] = mapped_column(String(30), nullable=False)
    cible: Mapped[str] = mapped_column(String(20), nullable=False)
    obligatoire: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    ordre: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    section: Mapped[Section] = relationship(back_populates="questions")
    reponses: Mapped[list[Reponse]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )

    @property
    def est_ad_hoc(self) -> bool:
        return self.question_template_id is None
