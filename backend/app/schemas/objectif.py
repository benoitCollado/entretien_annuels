from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.models.enums import StatutObjectif
from app.schemas.commun import SchemaEntree, SchemaSortie


class ObjectifEcrit(SchemaEntree):
    libelle: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    indicateur: str | None = Field(default=None, max_length=2000)
    echeance: date | None = None
    objectif_parent_id: UUID | None = None


class EvaluationEcrite(SchemaEntree):
    entretien_id: UUID
    statut: StatutObjectif
    niveau_atteinte: int | None = Field(default=None, ge=0, le=100)
    commentaire: str | None = Field(default=None, max_length=5000)


class ObjectifLu(SchemaSortie):
    id: UUID
    entretien_origine_id: UUID
    entretien_evaluation_id: UUID | None
    objectif_parent_id: UUID | None
    collaborateur_id: UUID
    libelle: str
    description: str | None
    indicateur: str | None
    echeance: date | None
    statut: str
    niveau_atteinte: int | None
    commentaire_evaluation: str | None
    created_at: datetime


class ObjectifsDeLEntretien(SchemaSortie):
    fixes: list[ObjectifLu]
    a_evaluer: list[ObjectifLu]


class SignatureEcrite(SchemaEntree):
    observation: str | None = Field(default=None, max_length=5000)
