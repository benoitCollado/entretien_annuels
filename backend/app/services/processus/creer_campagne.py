from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import ConflitMetier
from app.models.campagne import Campagne
from app.models.utilisateur import Utilisateur
from app.repositories.campagne_repository import CampagneRepository
from app.services.regles import coherence_campagne


def executer(
    session: Session,
    *,
    auteur: Utilisateur,
    libelle: str,
    annee: int,
    type_entretien: str,
    date_ouverture: date,
    date_limite: date,
    description: str | None = None,
) -> Campagne:
    campagnes = CampagneRepository(session)

    coherence_campagne.exiger_dates_coherentes(date_ouverture, date_limite)
    coherence_campagne.exiger_annee_coherente(annee, date_ouverture)

    if campagnes.get_par_annee_et_type(annee, type_entretien) is not None:
        raise ConflitMetier(f"Une campagne {type_entretien} existe déjà pour {annee}.")

    return campagnes.ajouter(
        Campagne(
            libelle=libelle,
            description=description,
            annee=annee,
            type_entretien=type_entretien,
            date_ouverture=date_ouverture,
            date_limite=date_limite,
            statut=coherence_campagne.BROUILLON,
        )
    )
