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
            entetes["WWW-Authenticate"] = "Bearer"
        return JSONResponse(
            status_code=exc.code_http,
            content={"message": exc.message, "details": exc.details},
            headers=entetes,
        )

    @app.exception_handler(Exception)
    async def _erreur_inattendue(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Erreur non gérée", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"message": "Erreur interne du serveur", "details": []},
        )
