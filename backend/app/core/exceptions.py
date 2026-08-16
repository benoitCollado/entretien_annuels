"""Exceptions métier.

Aucune connaissance de FastAPI ici : chaque exception porte le code HTTP qui lui
correspond, et un unique handler fait la traduction (addendum §5.3). Les routers
n'écrivent **jamais** de `HTTPException` pour un motif métier.
"""

from __future__ import annotations

from typing import Any


class ErreurMetier(Exception):
    code_http: int = 400

    def __init__(self, message: str, details: list[Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: list[Any] = details or []


class RessourceIntrouvable(ErreurMetier):
    code_http = 404


class AccesRefuse(ErreurMetier):
    code_http = 403


class NonAuthentifie(ErreurMetier):
    code_http = 401


class ConflitMetier(ErreurMetier):
    code_http = 409


class DonneesInvalides(ErreurMetier):
    code_http = 422


class TropDeTentatives(ErreurMetier):
    code_http = 429
