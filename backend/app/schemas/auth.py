"""Schémas d'authentification (US-01)."""

from __future__ import annotations

from pydantic import EmailStr, Field

from app.schemas.commun import SchemaEntree, SchemaSortie


class Connexion(SchemaEntree):
    email: EmailStr
    # Pas de longueur minimale ici : la contrainte porte sur la création du
    # compte. L'imposer à la connexion révélerait la politique de mot de passe
    # et permettrait d'écarter des tentatives sans consommer de vérification.
    mot_de_passe: str = Field(min_length=1, max_length=128)


class Jeton(SchemaSortie):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ChangementMotDePasse(SchemaEntree):
    ancien_mot_de_passe: str = Field(min_length=1, max_length=128)
    nouveau_mot_de_passe: str = Field(min_length=12, max_length=128)
