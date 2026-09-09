from __future__ import annotations

from fastapi import Request, Response

from app.config import obtenir_parametres

PREFIXE_BEARER = "bearer "


def poser_jeton(reponse: Response, jeton: str, duree_secondes: int) -> None:
    parametres = obtenir_parametres()
    reponse.set_cookie(
        key=parametres.cookie_jeton,
        value=jeton,
        max_age=duree_secondes,
        httponly=True,
        secure=parametres.cookie_est_securise,
        samesite=parametres.cookie_samesite,
        path="/",
    )


def effacer_jeton(reponse: Response) -> None:
    parametres = obtenir_parametres()
    reponse.delete_cookie(
        key=parametres.cookie_jeton,
        httponly=True,
        secure=parametres.cookie_est_securise,
        samesite=parametres.cookie_samesite,
        path="/",
    )


def lire_jeton(request: Request, entete: str | None) -> str | None:
    """Le jeton vient du cookie, ou de l'en-tête pour un appelant non navigateur.

    L'en-tête est examiné en premier : un identifiant présenté explicitement doit
    l'emporter sur le cookie, que le navigateur joint sans que l'appelant le
    demande. Un navigateur n'envoie jamais d'en-tête ici, il utilise le cookie.
    """
    if entete and entete.lower().startswith(PREFIXE_BEARER):
        depuis_entete = entete[len(PREFIXE_BEARER) :].strip()
        if depuis_entete:
            return depuis_entete
    return request.cookies.get(obtenir_parametres().cookie_jeton) or None
