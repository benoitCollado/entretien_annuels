from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator, model_validator

from app.models.utilisateur import Utilisateur
from app.schemas.commun import SchemaEntree, SchemaSortie

LONGUEUR_MOT_DE_PASSE_MIN = 12


class RoleLu(SchemaSortie):
    code: str
    libelle: str


class UtilisateurLu(SchemaSortie):
    id: UUID
    email: EmailStr
    nom: str
    prenom: str
    nom_complet: str
    poste: str | None = None
    service: str | None = None
    date_entree: date | None = None
    manager_id: UUID | None = None
    actif: bool
    created_at: datetime
    roles: list[RoleLu]
    permissions: list[str]

    @classmethod
    def depuis_modele(cls, utilisateur: Utilisateur) -> UtilisateurLu:
        return cls(
            id=utilisateur.id,
            email=utilisateur.email,
            nom=utilisateur.nom,
            prenom=utilisateur.prenom,
            nom_complet=utilisateur.nom_complet,
            poste=utilisateur.poste,
            service=utilisateur.service,
            date_entree=utilisateur.date_entree,
            manager_id=utilisateur.manager_id,
            actif=utilisateur.actif,
            created_at=utilisateur.created_at,
            roles=[RoleLu(code=r.code, libelle=r.libelle) for r in utilisateur.roles],
            permissions=sorted(utilisateur.codes_permissions()),
        )


class UtilisateurCree(SchemaEntree):
    email: EmailStr
    mot_de_passe: str = Field(min_length=LONGUEUR_MOT_DE_PASSE_MIN, max_length=128)
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    poste: str | None = Field(default=None, max_length=120)
    service: str | None = Field(default=None, max_length=120)
    date_entree: date | None = None
    manager_id: UUID | None = None
    roles: list[str] = Field(default_factory=lambda: ["COLLABORATEUR"], min_length=1)

    @field_validator("roles")
    @classmethod
    def _roles_uniques(cls, valeur: list[str]) -> list[str]:
        return sorted(set(valeur))


class UtilisateurModifie(SchemaEntree):
    email: EmailStr | None = None
    nom: str | None = Field(default=None, min_length=1, max_length=100)
    prenom: str | None = Field(default=None, min_length=1, max_length=100)
    poste: str | None = Field(default=None, max_length=120)
    service: str | None = Field(default=None, max_length=120)
    date_entree: date | None = None
    manager_id: UUID | None = None
    actif: bool | None = None

    @model_validator(mode="after")
    def _au_moins_un_champ(self) -> UtilisateurModifie:
        if not self.model_fields_set:
            raise ValueError("Aucun champ à modifier.")
        return self


class RolesAttribues(SchemaEntree):
    roles: list[str] = Field(min_length=1)

    @field_validator("roles")
    @classmethod
    def _roles_uniques(cls, valeur: list[str]) -> list[str]:
        return sorted(set(valeur))
