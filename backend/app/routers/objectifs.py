from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependances import AdresseClient, SessionDep, UtilisateurCourant, exige_permission
from app.schemas.objectif import EvaluationEcrite, ObjectifLu
from app.services.processus import gerer_objectifs

router = APIRouter(tags=["objectifs"])


@router.post(
    "/objectifs/{objectif_id}/evaluation",
    response_model=ObjectifLu,
    dependencies=[Depends(exige_permission("objectif:fixer"))],
    summary="Évaluer un objectif de l'année précédente",
)
def evaluer(
    objectif_id: UUID,
    donnees: EvaluationEcrite,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    adresse_ip: AdresseClient,
) -> ObjectifLu:
    objectif = gerer_objectifs.evaluer(
        session,
        auteur=utilisateur,
        objectif_id=objectif_id,
        entretien_id=donnees.entretien_id,
        statut=donnees.statut,
        niveau_atteinte=donnees.niveau_atteinte,
        commentaire=donnees.commentaire,
        adresse_ip=adresse_ip,
    )
    return ObjectifLu.model_validate(objectif)


@router.get(
    "/collaborateurs/{collaborateur_id}/objectifs",
    response_model=list[ObjectifLu],
    dependencies=[Depends(exige_permission("entretien:lire"))],
    summary="Parcours d'un collaborateur, toutes années",
)
def historique(
    collaborateur_id: UUID,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
) -> list[ObjectifLu]:
    objectifs = gerer_objectifs.historique(
        session, lecteur=utilisateur, collaborateur_id=collaborateur_id
    )
    return [ObjectifLu.model_validate(o) for o in objectifs]
