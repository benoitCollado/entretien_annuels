"""Bases communes des schémas — la « vue » du MVC (§7.2).

Le schéma décide de **ce qui est exposé, et surtout de ce qui ne l'est pas**.
C'est là que se matérialisent les règles de confidentialité côté sortie, en
complément du filtre SQL côté entrée.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SchemaEntree(BaseModel):
    # `extra="forbid"` : un champ inconnu est une erreur, pas une donnée
    # silencieusement ignorée. C'est ce qui empêche un client de tenter de
    # forcer un champ qui ne lui est pas destiné (§7.3).
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SchemaSortie(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ReponseErreur(BaseModel):
    """Forme unique des erreurs, produite par `core.gestion_erreurs`."""

    message: str
    details: list = Field(default_factory=list)


class Page[T](SchemaSortie):
    elements: list[T]
    total: int
    limite: int
    decalage: int
