"""Configuration lue depuis l'environnement et validée au démarrage.

Principe du « fail fast » : une variable manquante ou aberrante fait échouer la
création de l'application, pas la première requête qui l'utilise.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Parametres(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # `ignore` et non `forbid` : le conteneur reçoit aussi les variables
        # POSTGRES_* et COMPOSE_* qui ne concernent pas l'application.
        extra="ignore",
        # Sans cela, pydantic-settings tente un `json.loads` sur les champs de
        # type complexe (ici `origines_cors`) AVANT les validateurs
        # `mode="before"`, et échoue sur une valeur séparée par des virgules.
        enable_decoding=False,
    )

    nom_application: str = "API Entretiens"
    environnement: Literal["development", "test", "staging", "production"] = "development"
    niveau_log: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    database_url: str = "postgresql+psycopg://entretiens:entretiens@db:5432/entretiens"
    database_echo: bool = False

    redis_url: str = "redis://redis:6379/0"

    # Au moins 32 caractères : une clé HS256 plus courte n'offre pas la marge de
    # sécurité attendue.
    secret_key: str = Field(min_length=32)
    algorithme_jwt: str = "HS256"
    duree_jeton_minutes: int = Field(default=60, ge=1)

    # Rate limiting de la connexion (§7.3) : 5 tentatives par 15 minutes.
    connexion_tentatives_max: int = Field(default=5, ge=1)
    connexion_fenetre_secondes: int = Field(default=900, ge=1)

    origines_cors: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    @field_validator("origines_cors", mode="before")
    @classmethod
    def _decouper_origines(cls, valeur: object) -> object:
        """Accepte `a,b` (pratique en Docker) comme `["a", "b"]` (JSON)."""
        if not isinstance(valeur, str):
            return valeur
        texte = valeur.strip()
        if texte.startswith("["):
            return json.loads(texte)
        return [origine.strip() for origine in texte.split(",") if origine.strip()]

    @property
    def est_production(self) -> bool:
        return self.environnement in {"staging", "production"}


@lru_cache
def obtenir_parametres() -> Parametres:
    return Parametres()  # type: ignore[call-arg]
