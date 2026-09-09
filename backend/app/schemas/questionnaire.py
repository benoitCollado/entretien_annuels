from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.enums import Cible, TypeQuestion
from app.schemas.commun import SchemaEntree, SchemaSortie


class ReponseEcrite(SchemaEntree):
    question_id: UUID
    valeur: dict[str, Any] | None = None


class BrouillonEcrit(SchemaEntree):
    reponses: list[ReponseEcrite] = Field(min_length=1)


class QuestionAdHocEcrite(SchemaEntree):
    section_id: UUID
    libelle: str = Field(min_length=1, max_length=2000)
    type_question: TypeQuestion
    cible: Cible
    obligatoire: bool = False
    aide: str | None = Field(default=None, max_length=2000)
    configuration: dict[str, Any] = Field(default_factory=dict)


class CommentaireEcrit(SchemaEntree):
    contenu: str = Field(min_length=1, max_length=5000)


class SyntheseEcrite(SchemaEntree):
    contenu: str = Field(min_length=1, max_length=10000)


class ReponseLue(SchemaSortie):
    question_id: UUID
    auteur_id: UUID
    valeur: dict[str, Any] | None
    updated_at: datetime


class CommentaireLu(SchemaSortie):
    id: UUID
    question_id: UUID | None
    auteur_id: UUID
    auteur_nom: str
    contenu: str
    est_synthese: bool
    created_at: datetime


class QuestionInstanciee(SchemaSortie):
    id: UUID
    libelle: str
    aide: str | None
    type_question: str
    cible: str
    obligatoire: bool
    ordre: int
    configuration: dict[str, Any]
    est_ad_hoc: bool


class SectionInstanciee(SchemaSortie):
    id: UUID
    titre: str
    description: str | None
    ordre: int
    questions: list[QuestionInstanciee]


class QuestionnaireLu(SchemaSortie):
    id: UUID
    entretien_id: UUID
    titre: str
    template_version: int
    statut_entretien: str
    sections: list[SectionInstanciee]
    reponses: list[ReponseLue]
    commentaires: list[CommentaireLu]
    contenu_masque: bool

    @classmethod
    def depuis_vue(cls, vue) -> QuestionnaireLu:
        return cls(
            id=vue.questionnaire.id,
            entretien_id=vue.entretien.id,
            titre=vue.questionnaire.titre,
            template_version=vue.questionnaire.template_version,
            statut_entretien=vue.entretien.statut,
            sections=[
                SectionInstanciee(
                    id=section.id,
                    titre=section.titre,
                    description=section.description,
                    ordre=section.ordre,
                    questions=[
                        QuestionInstanciee(
                            id=question.id,
                            libelle=question.libelle,
                            aide=question.aide,
                            type_question=question.type_question,
                            cible=question.cible,
                            obligatoire=question.obligatoire,
                            ordre=question.ordre,
                            configuration=question.configuration,
                            est_ad_hoc=question.est_ad_hoc,
                        )
                        for question in section.questions
                    ],
                )
                for section in vue.questionnaire.sections
            ],
            reponses=[
                ReponseLue(
                    question_id=reponse.question_id,
                    auteur_id=reponse.auteur_id,
                    valeur=reponse.valeur,
                    updated_at=reponse.updated_at,
                )
                for reponse in vue.reponses
            ],
            commentaires=[
                CommentaireLu(
                    id=commentaire.id,
                    question_id=commentaire.question_id,
                    auteur_id=commentaire.auteur_id,
                    auteur_nom=commentaire.auteur.nom_complet,
                    contenu=commentaire.contenu,
                    est_synthese=commentaire.est_synthese,
                    created_at=commentaire.created_at,
                )
                for commentaire in vue.commentaires
            ],
            contenu_masque=vue.contenu_masque,
        )
