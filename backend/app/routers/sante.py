"""Sondes de disponibilité.

Note de couche : ce module n'importe rien de SQLAlchemy ni des modèles. La
session arrive déjà annotée via `SessionDep`.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.config import obtenir_parametres
from app.core.dependances import SessionDep
from app.schemas.sante import SanteLue, SantePreteLue
from app.services.processus import verifier_sante

router = APIRouter(tags=["sante"])


@router.get("/health", response_model=SanteLue, summary="Liveness")
def sante() -> SanteLue:
    """Le processus répond-il ? Aucune dépendance externe n'est sollicitée :
    c'est ce que Docker interroge pour décider de redémarrer le conteneur."""
    parametres = obtenir_parametres()
    return SanteLue(
        statut="ok",
        application=parametres.nom_application,
        environnement=parametres.environnement,
    )


@router.get("/health/ready", response_model=SantePreteLue, summary="Readiness")
def sante_prete(session: SessionDep) -> SantePreteLue:
    """Les dépendances répondent-elles ? Renvoie 200 avec un statut `degrade`
    plutôt qu'une erreur : c'est un diagnostic, pas un échec de requête."""
    return SantePreteLue(**verifier_sante.executer(session))
