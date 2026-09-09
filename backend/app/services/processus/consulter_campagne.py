from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import RessourceIntrouvable
from app.models.campagne import Campagne
from app.repositories.campagne_repository import CampagneRepository


def consulter(session: Session, *, campagne_id: UUID) -> Campagne:
    campagne = CampagneRepository(session).get(campagne_id)
    if campagne is None:
        raise RessourceIntrouvable("Campagne introuvable.")
    return campagne


def lister(
    session: Session,
    *,
    statut: str | None = None,
    annee: int | None = None,
    type_entretien: str | None = None,
    limite: int = 50,
    decalage: int = 0,
) -> tuple[list[Campagne], int]:
    campagnes = CampagneRepository(session)
    lignes = campagnes.lister_filtre(
        statut=statut,
        annee=annee,
        type_entretien=type_entretien,
        limite=limite,
        decalage=decalage,
    )
    total = campagnes.compter(statut=statut, annee=annee, type_entretien=type_entretien)
    return lignes, total
