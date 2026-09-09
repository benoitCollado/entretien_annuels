from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependances import SessionDep, exige_permission
from app.schemas.entretien import TableauDeBordLu
from app.services.processus import calculer_tableau_bord

router = APIRouter(prefix="/tableau-bord", tags=["tableau-bord"])


@router.get(
    "/campagnes/{campagne_id}",
    response_model=TableauDeBordLu,
    dependencies=[Depends(exige_permission("tableau_bord:lire"))],
    summary="Avancement d'une campagne",
)
def avancement(campagne_id: UUID, session: SessionDep) -> TableauDeBordLu:
    return TableauDeBordLu.depuis_modele(
        calculer_tableau_bord.executer(session, campagne_id=campagne_id)
    )
