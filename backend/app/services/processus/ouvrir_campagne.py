from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import DonneesInvalides, RessourceIntrouvable
from app.models.campagne import Campagne
from app.models.utilisateur import Utilisateur
from app.repositories.campagne_repository import CampagneRepository
from app.repositories.template_repository import TemplateRepository
from app.services.regles import coherence_campagne, publication_template


def executer(
    session: Session,
    *,
    auteur: Utilisateur,
    campagne_id: UUID,
    aujourdhui: date | None = None,
) -> Campagne:
    campagnes = CampagneRepository(session)
    aujourdhui = aujourdhui or datetime.now(UTC).date()

    campagne = campagnes.get(campagne_id)
    if campagne is None:
        raise RessourceIntrouvable("Campagne introuvable.")

    coherence_campagne.exiger_transition(campagne.statut, coherence_campagne.OUVERTE)

    if coherence_campagne.est_echue(campagne.date_limite, aujourdhui):
        raise DonneesInvalides(
            f"L'échéance du {campagne.date_limite} est déjà passée. "
            "Reportez la date limite avant d'ouvrir la campagne."
        )

    templates = TemplateRepository(session)
    disponibles = templates.compter(
        statut=publication_template.PUBLIEE, type_entretien=campagne.type_entretien
    )
    if disponibles == 0:
        raise DonneesInvalides(
            f"Aucune trame publiée de type {campagne.type_entretien} : "
            "publiez-en une avant d'ouvrir la campagne."
        )

    campagne.statut = coherence_campagne.OUVERTE
    campagne.ouverte_le = datetime.now(UTC)
    campagne.ouverte_par_id = auteur.id

    session.flush()
    return campagne
