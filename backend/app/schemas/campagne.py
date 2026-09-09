from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field, model_validator

from app.models.enums import TypeEntretien
from app.schemas.commun import SchemaEntree, SchemaSortie


class CampagneCreee(SchemaEntree):
    libelle: str = Field(min_length=1, max_length=150)
    annee: int = Field(ge=2000, le=2200)
    type_entretien: TypeEntretien
    date_ouverture: date
    date_limite: date
    description: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _dates_coherentes(self) -> CampagneCreee:
        if self.date_limite <= self.date_ouverture:
            raise ValueError("La date limite doit être postérieure à la date d'ouverture.")
        return self


class CampagneLue(SchemaSortie):
    id: UUID
    libelle: str
    description: str | None
    annee: int
    type_entretien: str
    date_ouverture: date
    date_limite: date
    statut: str
    ouverte_le: datetime | None
    cloturee_le: datetime | None
    created_at: datetime
    accepte_des_entretiens: bool

    @classmethod
    def depuis_modele(cls, campagne) -> CampagneLue:
        return cls(
            id=campagne.id,
            libelle=campagne.libelle,
            description=campagne.description,
            annee=campagne.annee,
            type_entretien=campagne.type_entretien,
            date_ouverture=campagne.date_ouverture,
            date_limite=campagne.date_limite,
            statut=campagne.statut,
            ouverte_le=campagne.ouverte_le,
            cloturee_le=campagne.cloturee_le,
            created_at=campagne.created_at,
            accepte_des_entretiens=campagne.accepte_des_entretiens,
        )
