# Journal d'audit en lecture seule (§6.4).
#
# Réservé au rôle ADMIN : le journal expose qui a consulté quoi, y compris les
# accès refusés, ce qui en fait une donnée plus sensible que les entretiens
# eux-mêmes. Aucune écriture ici — le journal ne se remplit que par les
# services métier, et rien ne doit pouvoir l'amender après coup.
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependances import SessionDep, exige_role
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import EntreeAuditLue
from app.schemas.commun import Page

router = APIRouter(prefix="/audit", tags=["audit"])

ROLE_ADMIN = "ADMIN"


@router.get(
    "",
    response_model=Page[EntreeAuditLue],
    dependencies=[Depends(exige_role(ROLE_ADMIN))],
    summary="Journal d'audit",
)
def journal(
    session: SessionDep,
    entretien_id: UUID | None = None,
    utilisateur_id: UUID | None = None,
    action: str | None = None,
    limite: int = Query(default=50, ge=1, le=500),
    decalage: int = Query(default=0, ge=0),
) -> Page[EntreeAuditLue]:
    entrees, total = AuditRepository(session).journal(
        entretien_id=entretien_id,
        utilisateur_id=utilisateur_id,
        action=action,
        limite=limite,
        decalage=decalage,
    )
    return Page(
        elements=[EntreeAuditLue.depuis_modele(entree) for entree in entrees],
        total=total,
        limite=limite,
        decalage=decalage,
    )
