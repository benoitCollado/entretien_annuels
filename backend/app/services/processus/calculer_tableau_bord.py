from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import RessourceIntrouvable
from app.models.campagne import Campagne
from app.models.entretien import Entretien
from app.repositories.campagne_repository import CampagneRepository
from app.repositories.entretien_repository import EntretienRepository
from app.services.regles import transitions_entretien

STATUTS_TERMINES = frozenset({transitions_entretien.SIGNE, transitions_entretien.CLOTURE})


@dataclass(slots=True)
class TableauDeBord:
    campagne: Campagne
    par_statut: dict[str, int] = field(default_factory=dict)
    total: int = 0
    termines: int = 0
    taux_avancement: float = 0.0
    en_retard: list[Entretien] = field(default_factory=list)
    echue: bool = False


def executer(
    session: Session,
    *,
    campagne_id: UUID,
    aujourdhui: date | None = None,
) -> TableauDeBord:
    aujourdhui = aujourdhui or datetime.now(UTC).date()

    campagne = CampagneRepository(session).get(campagne_id)
    if campagne is None:
        raise RessourceIntrouvable("Campagne introuvable.")

    entretiens = EntretienRepository(session)
    par_statut = entretiens.compter_par_statut(campagne.id)

    total = sum(
        nombre for statut, nombre in par_statut.items() if statut != transitions_entretien.ANNULE
    )
    termines = sum(par_statut.get(statut, 0) for statut in STATUTS_TERMINES)

    echue = campagne.est_echue(aujourdhui)
    en_retard = entretiens.lister_en_retard(campagne.id, campagne.date_limite) if echue else []

    return TableauDeBord(
        campagne=campagne,
        par_statut=par_statut,
        total=total,
        termines=termines,
        taux_avancement=(termines / total) if total else 0.0,
        en_retard=en_retard,
        echue=echue,
    )
