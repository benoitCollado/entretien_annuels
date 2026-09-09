from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
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
from app.models.enums import Cible, StatutTemplate, TypeEntretien, TypeQuestion, valeurs_sql


class Template(Base):
    __tablename__ = "template"
    __table_args__ = (
        UniqueConstraint("nom", "version", name="uq_template_nom_version"),
        CheckConstraint(
            f"type_entretien IN ({valeurs_sql(TypeEntretien)})",
            name="type_entretien_valide",
        ),
        CheckConstraint(
            f"statut IN ({valeurs_sql(StatutTemplate)})",
            name="statut_valide",
        ),
        CheckConstraint("version >= 1", name="version_positive"),
    )

    id: Mapped[uuid.UUID] = cle_primaire_uuid()
    nom: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type_entretien: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    statut: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'BROUILLON'")
    )

    template_parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("template.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    redige_par_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("utilisateur.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    publie_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    sections: Mapped[list[SectionTemplate]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="SectionTemplate.ordre",
    )
    parent: Mapped[Template | None] = relationship(remote_side="Template.id")

    @property
    def est_modifiable(self) -> bool:
        return self.statut == StatutTemplate.BROUILLON

    def nombre_questions(self) -> int:
        return sum(len(section.questions) for section in self.sections)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Template {self.nom} v{self.version} ({self.statut})>"


class SectionTemplate(Base):
    __tablename__ = "section_template"
    __table_args__ = (
        UniqueConstraint(
            "template_id",
            "ordre",
            name="uq_section_template_ordre",
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint("ordre >= 0", name="ordre_positif"),
    )

    id: Mapped[uuid.UUID] = cle_primaire_uuid()
    template_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("template.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    titre: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ordre: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    template: Mapped[Template] = relationship(back_populates="sections")
    questions: Mapped[list[QuestionTemplate]] = relationship(
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="QuestionTemplate.ordre",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SectionTemplate {self.ordre}. {self.titre}>"


class QuestionTemplate(Base):
    __tablename__ = "question_template"
    __table_args__ = (
        UniqueConstraint(
            "section_template_id",
            "ordre",
            name="uq_question_template_ordre",
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint(
            f"type_question IN ({valeurs_sql(TypeQuestion)})",
            name="type_question_valide",
        ),
        CheckConstraint(f"cible IN ({valeurs_sql(Cible)})", name="cible_valide"),
        CheckConstraint("ordre >= 0", name="ordre_positif"),
        CheckConstraint("jsonb_typeof(configuration) = 'object'", name="configuration_objet"),
    )

    id: Mapped[uuid.UUID] = cle_primaire_uuid()
    section_template_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("section_template.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
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

    section: Mapped[SectionTemplate] = relationship(back_populates="questions")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<QuestionTemplate {self.ordre}. {self.libelle[:30]}>"
