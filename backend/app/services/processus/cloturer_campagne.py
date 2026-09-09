from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import RessourceIntrouvable
from app.models.campagne import Campagne
from app.models.utilisateur import Utilisateur
from app.repositories.campagne_repository import CampagneRepository
from app.services.regles import coherence_campagne


def executer(
    session: Session,
    *,
    auteur: Utilisateur,
    campagne_id: UUID,
) -> Campagne:
    campagnes = CampagneRepository(session)

    campagne = campagnes.get(campagne_id)
    if campagne is None:
        raise RessourceIntrouvable("Campagne introuvable.")

    coherence_campagne.exiger_transition(campagne.statut, coherence_campagne.CLOTUREE)

    campagne.statut = coherence_campagne.CLOTUREE
    campagne.cloturee_le = datetime.now(UTC)

    session.flush()
    return campagne
