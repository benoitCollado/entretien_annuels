from __future__ import annotations

from uuid import UUID

from app.services.regles.transitions_entretien import (
    CLOTURE,
    PLANIFIE,
    PREPARATION,
    REVUE_MANAGER,
    SIGNE,
    SOUMIS_COLLABORATEUR,
    au_moins,
)


def auteurs_lisibles(
    statut: str,
    lecteur_id: UUID,
    collaborateur_id: UUID,
    manager_id: UUID,
    lecteur_est_rh: bool,
) -> list[UUID] | None:
    if lecteur_est_rh and statut == CLOTURE:
        return None

    autorises: list[UUID] = []

    if lecteur_id in (collaborateur_id, manager_id):
        autorises.append(lecteur_id)

    if lecteur_id == manager_id and au_moins(statut, SOUMIS_COLLABORATEUR):
        autorises.append(collaborateur_id)

    if lecteur_id == collaborateur_id and au_moins(statut, REVUE_MANAGER):
        autorises.append(manager_id)

    return autorises


def peut_lire_les_reponses(
    statut: str,
    lecteur_id: UUID,
    collaborateur_id: UUID,
    manager_id: UUID,
    lecteur_est_rh: bool,
) -> bool:
    auteurs = auteurs_lisibles(statut, lecteur_id, collaborateur_id, manager_id, lecteur_est_rh)
    return auteurs is None or len(auteurs) > 0


def peut_ecrire_ses_reponses(statut: str, lecteur_id: UUID, collaborateur_id: UUID) -> bool:
    return lecteur_id == collaborateur_id and statut in {PLANIFIE, PREPARATION}


def peut_commenter(statut: str, lecteur_id: UUID, manager_id: UUID) -> bool:
    return (
        lecteur_id == manager_id
        and au_moins(statut, SOUMIS_COLLABORATEUR)
        and not au_moins(statut, SIGNE)
    )
