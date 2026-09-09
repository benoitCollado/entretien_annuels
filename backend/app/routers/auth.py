from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.core import cookies
from app.core.dependances import AdresseClient, SessionDep, UtilisateurCourant
from app.schemas.auth import Connexion
from app.schemas.utilisateur import UtilisateurLu
from app.services.processus import authentifier

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=UtilisateurLu,
    status_code=status.HTTP_200_OK,
    summary="S'authentifier",
)
def connexion(
    donnees: Connexion,
    session: SessionDep,
    adresse_ip: AdresseClient,
    reponse: Response,
) -> UtilisateurLu:
    utilisateur, jeton, duree = authentifier.executer(
        session,
        email=donnees.email,
        mot_de_passe=donnees.mot_de_passe,
        adresse_ip=adresse_ip,
    )
    # Le jeton part dans un cookie HttpOnly et ne figure pas dans le corps :
    # aucun script de la page ne doit pouvoir le lire.
    cookies.poser_jeton(reponse, jeton, duree)
    return UtilisateurLu.depuis_modele(utilisateur)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Fermer la session",
)
def deconnexion(reponse: Response) -> None:
    # Aucune authentification exigée : fermer une session déjà expirée doit
    # aboutir, sans quoi le client resterait avec un cookie qu'il ne peut pas
    # effacer lui-même.
    cookies.effacer_jeton(reponse)


@router.get(
    "/me",
    response_model=UtilisateurLu,
    summary="Profil de l'utilisateur connecté",
)
def profil(utilisateur: UtilisateurCourant) -> UtilisateurLu:
    return UtilisateurLu.depuis_modele(utilisateur)
