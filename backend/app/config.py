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
        extra="ignore",
        enable_decoding=False,
    )

    nom_application: str = "API Entretiens"
    environnement: Literal["development", "test", "staging", "production"] = "development"
    niveau_log: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    database_url: str = "postgresql+psycopg://entretiens:entretiens@db:5432/entretiens"
    database_echo: bool = False

    redis_url: str = "redis://redis:6379/0"

    secret_key: str = Field(min_length=32)
    algorithme_jwt: str = "HS256"
    duree_jeton_minutes: int = Field(default=60, ge=1)

    cookie_jeton: str = "jeton"
    cookie_samesite: Literal["lax", "strict", "none"] = "strict"
    # None : déduit de l'environnement. Un booléen explicite permet de forcer le
    # comportement sur une préproduction servie en clair.
    cookie_secure: bool | None = None

    connexion_tentatives_max: int = Field(default=5, ge=1)
    connexion_fenetre_secondes: int = Field(default=900, ge=1)

    origines_cors: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    @field_validator("origines_cors", mode="before")
    @classmethod
    def _decouper_origines(cls, valeur: object) -> object:
        if not isinstance(valeur, str):
            return valeur
        texte = valeur.strip()
        if texte.startswith("["):
            return json.loads(texte)
        return [origine.strip() for origine in texte.split(",") if origine.strip()]

    @property
    def est_production(self) -> bool:
        return self.environnement in {"staging", "production"}

    @property
    def cookie_est_securise(self) -> bool:
        return self.est_production if self.cookie_secure is None else self.cookie_secure


@lru_cache
def obtenir_parametres() -> Parametres:
    return Parametres()  # type: ignore[call-arg]
