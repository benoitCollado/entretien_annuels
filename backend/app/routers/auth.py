"""Contrôleur — US-01, authentification.

Contrat : valider l'entrée, appeler **un** processus, retourner un schéma de
sortie. Aucune décision métier, aucun `try/except` — les erreurs métier sont
traduites en HTTP par `core.gestion_erreurs`.

Endpoints déclarés avec `def` et non `async def` : FastAPI les exécute alors
dans un threadpool. Un `async def` contenant un appel SQLAlchemy synchrone
bloquerait la boucle d'événements et gèlerait le serveur (§7.1).
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.dependances import AdresseClient, SessionDep, UtilisateurCourant
from app.schemas.auth import Connexion, Jeton
from app.schemas.utilisateur import UtilisateurLu
from app.services.processus import authentifier

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=Jeton,
    status_code=status.HTTP_200_OK,
    summary="S'authentifier (US-01)",
)
def connexion(
    donnees: Connexion,
    session: SessionDep,
    adresse_ip: AdresseClient,
) -> Jeton:
    _, jeton, duree = authentifier.executer(
        session,
        email=donnees.email,
        mot_de_passe=donnees.mot_de_passe,
        adresse_ip=adresse_ip,
    )
    return Jeton(access_token=jeton, expires_in=duree)


@router.get(
    "/me",
    response_model=UtilisateurLu,
    summary="Profil de l'utilisateur connecté (US-01)",
)
def profil(utilisateur: UtilisateurCourant) -> UtilisateurLu:
    """Aucun processus n'est nécessaire : la dépendance a déjà chargé et validé
    l'utilisateur, y compris sa version de jeton."""
    return UtilisateurLu.depuis_modele(utilisateur)
