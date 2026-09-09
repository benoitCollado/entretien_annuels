from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Parametres, obtenir_parametres
from app.core import gestion_erreurs, protection_csrf
from app.routers import (
    audit,
    auth,
    campagnes,
    entretiens,
    objectifs,
    sante,
    tableau_bord,
    templates,
    utilisateurs,
)


def creer_application(parametres: Parametres | None = None) -> FastAPI:
    parametres = parametres or obtenir_parametres()

    logging.basicConfig(
        level=parametres.niveau_log,
        format="%(asctime)s %(levelname)-8s %(name)s :: %(message)s",
    )

    # En production, le nginx du conteneur `web` expose l'API sous /api/ et
    # retire ce préfixe avant de relayer. L'application ne le voit donc jamais
    # dans ses chemins, mais Swagger UI, lui, construit l'URL de la
    # spécification depuis le navigateur : sans `root_path`, il demande
    # /openapi.json, reçoit l'index.html du frontend et refuse de s'afficher.
    racine = "/api" if parametres.est_production else ""

    app = FastAPI(
        title=parametres.nom_application,
        version="0.1.0",
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
        root_path=racine,
    )

    # Enregistré avant CORS : le middleware ajouté en dernier est le plus
    # extérieur, donc un refus d'origine ressort avec ses en-têtes CORS.
    protection_csrf.enregistrer(app, parametres.origines_cors)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=parametres.origines_cors,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    gestion_erreurs.enregistrer(app)

    app.include_router(sante.router)
    app.include_router(auth.router)
    app.include_router(utilisateurs.router)
    app.include_router(templates.router)
    app.include_router(campagnes.router)
    app.include_router(entretiens.router)
    app.include_router(tableau_bord.router)
    app.include_router(objectifs.router)
    app.include_router(audit.router)

    return app


app = creer_application()
