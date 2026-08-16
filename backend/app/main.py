"""Création de l'application FastAPI.

⚠️ Rappel du §7.1 : tous les endpoints se déclarent avec `def`, jamais
`async def`. FastAPI exécute alors les fonctions synchrones dans un threadpool.
Un `async def` contenant un appel SQLAlchemy synchrone bloquerait la boucle
d'événements et gèlerait le serveur entier.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Parametres, obtenir_parametres
from app.core import gestion_erreurs
from app.routers import auth, sante, utilisateurs


def creer_application(parametres: Parametres | None = None) -> FastAPI:
    parametres = parametres or obtenir_parametres()

    logging.basicConfig(
        level=parametres.niveau_log,
        format="%(asctime)s %(levelname)-8s %(name)s :: %(message)s",
    )

    app = FastAPI(
        title=parametres.nom_application,
        version="0.1.0",
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    # CORS restreint à une liste explicite d'origines (§7.3) — jamais "*",
    # a fortiori avec `allow_credentials`.
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
    # Lots suivants : campagnes, templates, entretiens, questionnaires,
    # reponses, commentaires, objectifs, tableau_bord, exports.
    # Voir docs/tracabilite.md.

    return app


app = creer_application()
