from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.models.enums import Cible, StatutTemplate, TypeEntretien, TypeQuestion
from app.schemas.commun import SchemaEntree, SchemaSortie

TYPES_A_OPTIONS = {TypeQuestion.CHOIX_UNIQUE, TypeQuestion.CHOIX_MULTIPLE}
TYPES_A_BORNES = {TypeQuestion.ECHELLE}


class QuestionEcrite(SchemaEntree):
    libelle: str = Field(min_length=1, max_length=2000)
    type_question: TypeQuestion
    cible: Cible
    obligatoire: bool = False
    aide: str | None = Field(default=None, max_length=2000)
    configuration: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _configuration_coherente(self) -> QuestionEcrite:
        if self.type_question in TYPES_A_OPTIONS:
            options = self.configuration.get("options")
            if not isinstance(options, list) or len(options) < 2:
                raise ValueError(
                    f"Une question de type {self.type_question.value} exige une "
                    "liste `options` d'au moins deux entrées."
                )
            if len(set(map(str, options))) != len(options):
                raise ValueError("Les options doivent être distinctes.")

        if self.type_question in TYPES_A_BORNES:
            minimum = self.configuration.get("minimum", 1)
            maximum = self.configuration.get("maximum", 5)
            if not isinstance(minimum, int) or not isinstance(maximum, int):
                raise ValueError("Les bornes d'une échelle doivent être entières.")
            if minimum >= maximum:
                raise ValueError("Le minimum d'une échelle doit être inférieur au maximum.")

        return self


class SectionEcrite(SchemaEntree):
    titre: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    questions: list[QuestionEcrite] = Field(min_length=1)


class StructureEcrite(SchemaEntree):
    sections: list[SectionEcrite] = Field(min_length=1)

    @field_validator("sections")
    @classmethod
    def _titres_distincts(cls, sections: list[SectionEcrite]) -> list[SectionEcrite]:
        titres = [section.titre.strip().lower() for section in sections]
        if len(set(titres)) != len(titres):
            raise ValueError("Deux sections ne peuvent pas porter le même titre.")
        return sections


class TemplateCree(SchemaEntree):
    nom: str = Field(min_length=1, max_length=150)
    type_entretien: TypeEntretien
    description: str | None = Field(default=None, max_length=2000)


class TemplateModifie(SchemaEntree):
    nom: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _au_moins_un_champ(self) -> TemplateModifie:
        if not self.model_fields_set:
            raise ValueError("Aucun champ à modifier.")
        return self


class QuestionLue(SchemaSortie):
    id: UUID
    libelle: str
    aide: str | None
    type_question: str
    cible: str
    obligatoire: bool
    ordre: int
    configuration: dict[str, Any]


class SectionLue(SchemaSortie):
    id: UUID
    titre: str
    description: str | None
    ordre: int
    questions: list[QuestionLue]


class TemplateResume(SchemaSortie):
    id: UUID
    nom: str
    description: str | None
    type_entretien: str
    version: int
    statut: str
    publie_le: datetime | None
    created_at: datetime
    nombre_sections: int
    nombre_questions: int
    est_modifiable: bool

    @classmethod
    def depuis_modele(cls, template) -> TemplateResume:
        return cls(
            id=template.id,
            nom=template.nom,
            description=template.description,
            type_entretien=template.type_entretien,
            version=template.version,
            statut=template.statut,
            publie_le=template.publie_le,
            created_at=template.created_at,
            nombre_sections=len(template.sections),
            nombre_questions=template.nombre_questions(),
            est_modifiable=template.est_modifiable,
        )


class TemplateLu(TemplateResume):
    template_parent_id: UUID | None
    sections: list[SectionLue]

    @classmethod
    def depuis_modele(cls, template) -> TemplateLu:
        return cls(
            id=template.id,
            nom=template.nom,
            description=template.description,
            type_entretien=template.type_entretien,
            version=template.version,
            statut=template.statut,
            publie_le=template.publie_le,
            created_at=template.created_at,
            nombre_sections=len(template.sections),
            nombre_questions=template.nombre_questions(),
            est_modifiable=template.est_modifiable,
            template_parent_id=template.template_parent_id,
            sections=[
                SectionLue(
                    id=section.id,
                    titre=section.titre,
                    description=section.description,
                    ordre=section.ordre,
                    questions=[
                        QuestionLue(
                            id=question.id,
                            libelle=question.libelle,
                            aide=question.aide,
                            type_question=question.type_question,
                            cible=question.cible,
                            obligatoire=question.obligatoire,
                            ordre=question.ordre,
                            configuration=question.configuration,
                        )
                        for question in section.questions
                    ],
                )
                for section in template.sections
            ],
        )


class ReferentielQuestions(SchemaSortie):
    types_question: list[str]
    cibles: list[str]
    types_entretien: list[str]
    statuts_template: list[str]

    @classmethod
    def actuel(cls) -> ReferentielQuestions:
        return cls(
            types_question=[t.value for t in TypeQuestion],
            cibles=[c.value for c in Cible],
            types_entretien=[t.value for t in TypeEntretien],
            statuts_template=[s.value for s in StatutTemplate],
        )
