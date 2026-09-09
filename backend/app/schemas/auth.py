from __future__ import annotations

from pydantic import EmailStr, Field

from app.schemas.commun import SchemaEntree


class Connexion(SchemaEntree):
    email: EmailStr
    mot_de_passe: str = Field(min_length=1, max_length=128)


class ChangementMotDePasse(SchemaEntree):
    ancien_mot_de_passe: str = Field(min_length=1, max_length=128)
    nouveau_mot_de_passe: str = Field(min_length=12, max_length=128)
