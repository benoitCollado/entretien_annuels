from __future__ import annotations

from collections.abc import Callable, Generator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import cookies
from app.core.exceptions import AccesRefuse, NonAuthentifie
from app.core.securite import decoder_jeton
from app.database import obtenir_fabrique_sessions
from app.models.utilisateur import Utilisateur
from app.repositories.utilisateur_repository import UtilisateurRepository


def get_db() -> Generator[Session, None, None]:
    session = obtenir_fabrique_sessions()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


SessionDep = Annotated[Session, Depends(get_db)]

_schema_bearer = HTTPBearer(auto_error=False)


def utilisateur_courant(
    request: Request,
    session: SessionDep,
    identifiants: Annotated[HTTPAuthorizationCredentials | None, Depends(_schema_bearer)] = None,
) -> Utilisateur:
    entete = f"Bearer {identifiants.credentials}" if identifiants is not None else None
    jeton = cookies.lire_jeton(request, entete)
    if jeton is None:
        raise NonAuthentifie("Authentification requise")

    utilisateur_id, version_jeton = decoder_jeton(jeton)

    utilisateur = UtilisateurRepository(session).get_actif(utilisateur_id)
    if utilisateur is None:
        raise NonAuthentifie("Session invalide")

    if utilisateur.version_jeton != version_jeton:
        raise NonAuthentifie("Session révoquée")

    return utilisateur


UtilisateurCourant = Annotated[Utilisateur, Depends(utilisateur_courant)]


def exige_permission(code_permission: str) -> Callable[[Utilisateur], Utilisateur]:

    def dependance(utilisateur: UtilisateurCourant) -> Utilisateur:
        if code_permission not in utilisateur.codes_permissions():
            raise AccesRefuse(f"Permission requise : {code_permission}")
        return utilisateur

    return dependance


def exige_role(code_role: str) -> Callable[[Utilisateur], Utilisateur]:
    """Contrôle par rôle, pour ce qui ne relève d'aucune permission métier.

    Le journal d'audit n'a pas de permission dédiée dans le référentiel : en
    créer une imposerait une migration. Le rôle suffit ici, la lecture du
    journal étant une prérogative d'administration et non un acte métier.
    """

    def dependance(utilisateur: UtilisateurCourant) -> Utilisateur:
        if code_role not in utilisateur.codes_roles():
            raise AccesRefuse(f"Rôle requis : {code_role}")
        return utilisateur

    return dependance


def adresse_client(request: Request) -> str | None:
    return request.client.host if request.client else None


AdresseClient = Annotated[str | None, Depends(adresse_client)]
