from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

METHODES_SURES = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})


def enregistrer(app: FastAPI, origines: Iterable[str]) -> None:
    """Refuse les écritures venues d'une autre origine.

    Le jeton voyage désormais dans un cookie, que le navigateur joint de
    lui-même : un formulaire hébergé sur un autre site pourrait donc déclencher
    une écriture au nom de l'utilisateur. L'attribut SameSite du cookie ferme
    déjà ce chemin ; ce contrôle est la seconde barrière, côté serveur.

    Une requête sans en-tête Origin n'est pas rejetée : elle ne vient pas d'un
    navigateur, donc pas d'une page tierce. C'est le cas des clients d'API et
    des tests.
    """
    autorisees = frozenset(origines)

    @app.middleware("http")
    async def _verifier_origine(
        request: Request, appel_suivant: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method not in METHODES_SURES:
            origine = request.headers.get("origin")
            if origine is not None and origine not in autorisees:
                return JSONResponse(
                    status_code=403,
                    content={"message": "Origine non autorisée.", "details": []},
                )
        return await appel_suivant(request)
