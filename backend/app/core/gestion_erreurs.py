"""Traduction des erreurs métier en réponses HTTP — le seul endroit qui le fait."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import ErreurMetier, NonAuthentifie

logger = logging.getLogger("app.erreurs")


def enregistrer(app: FastAPI) -> None:
    @app.exception_handler(ErreurMetier)
    async def _erreur_metier(_: Request, exc: ErreurMetier) -> JSONResponse:
        entetes = {}
        if isinstance(exc, NonAuthentifie):
            # Exigé par la RFC 9110 sur une 401 ; c'est ce qui indique au client
            # quel schéma d'authentification employer.
            entetes["WWW-Authenticate"] = "Bearer"
        return JSONResponse(
            status_code=exc.code_http,
            content={"message": exc.message, "details": exc.details},
            headers=entetes,
        )

    @app.exception_handler(Exception)
    async def _erreur_inattendue(_: Request, exc: Exception) -> JSONResponse:
        # La trace part dans les logs, jamais dans la réponse : un message
        # détaillé renseignerait un attaquant sur la structure interne.
        logger.exception("Erreur non gérée", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"message": "Erreur interne du serveur", "details": []},
        )
