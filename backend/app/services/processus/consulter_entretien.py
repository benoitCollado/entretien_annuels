from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AccesRefuse, RessourceIntrouvable
from app.models.entretien import Entretien
from app.models.utilisateur import Utilisateur
from app.repositories.entretien_repository import EntretienRepository

ROLE_RH = "RH"
ROLE_MANAGER = "MANAGER"


def lister(
    session: Session,
    *,
    lecteur: Utilisateur,
    campagne_id: UUID | None = None,
    statut: str | None = None,
    limite: int = 50,
    decalage: int = 0,
) -> tuple[list[Entretien], int]:
    roles = lecteur.codes_roles()
    entretiens = EntretienRepository(session)

    if ROLE_RH in roles:
        filtres = {}
    elif ROLE_MANAGER in roles:
        filtres = {"collaborateur_id": lecteur.id, "manager_id": lecteur.id}
    else:
        filtres = {"collaborateur_id": lecteur.id}

    lignes = entretiens.lister_filtre(
        campagne_id=campagne_id, statut=statut, limite=limite, decalage=decalage, **filtres
    )
    total = entretiens.compter(campagne_id=campagne_id, statut=statut, **filtres)
    return lignes, total


def consulter(session: Session, *, lecteur: Utilisateur, entretien_id: UUID) -> Entretien:
    entretien = EntretienRepository(session).get_avec_questionnaire(entretien_id)
    if entretien is None:
        raise RessourceIntrouvable("Entretien introuvable.")

    est_partie_prenante = lecteur.id in (entretien.collaborateur_id, entretien.manager_id)
    if not est_partie_prenante and ROLE_RH not in lecteur.codes_roles():
        raise AccesRefuse("Cet entretien ne vous concerne pas.")

    return entretien
