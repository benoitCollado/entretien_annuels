"""Schémas des sondes de disponibilité."""

from __future__ import annotations

from typing import Literal

from app.schemas.commun import SchemaSortie


class SanteLue(SchemaSortie):
    statut: Literal["ok"]
    application: str
    environnement: str


class SantePreteLue(SchemaSortie):
    statut: Literal["ok", "degrade"]
    base: Literal["ok", "injoignable"]
    cache: Literal["ok", "injoignable"]
