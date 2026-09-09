from __future__ import annotations

from fastapi import APIRouter

from app.config import obtenir_parametres
from app.core.dependances import SessionDep
from app.schemas.sante import SanteLue, SantePreteLue
from app.services.processus import verifier_sante

router = APIRouter(tags=["sante"])


@router.get("/health", response_model=SanteLue, summary="Liveness")
def sante() -> SanteLue:
    parametres = obtenir_parametres()
    return SanteLue(
        statut="ok",
        application=parametres.nom_application,
        environnement=parametres.environnement,
    )


@router.get("/health/ready", response_model=SantePreteLue, summary="Readiness")
def sante_prete(session: SessionDep) -> SantePreteLue:
    return SantePreteLue(**verifier_sante.executer(session))
