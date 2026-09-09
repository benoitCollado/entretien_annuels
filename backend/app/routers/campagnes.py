from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependances import SessionDep, UtilisateurCourant, exige_permission
from app.schemas.campagne import CampagneCreee, CampagneLue
from app.schemas.commun import Page
from app.services.processus import (
    cloturer_campagne,
    consulter_campagne,
    creer_campagne,
    ouvrir_campagne,
)

router = APIRouter(prefix="/campagnes", tags=["campagnes"])


@router.get(
    "",
    response_model=Page[CampagneLue],
    dependencies=[Depends(exige_permission("campagne:lire"))],
    summary="Lister les campagnes",
)
def lister(
    session: SessionDep,
    statut: Annotated[str | None, Query()] = None,
    annee: Annotated[int | None, Query(ge=2000, le=2200)] = None,
    type_entretien: Annotated[str | None, Query()] = None,
    limite: Annotated[int, Query(ge=1, le=200)] = 50,
    decalage: Annotated[int, Query(ge=0)] = 0,
) -> Page[CampagneLue]:
    lignes, total = consulter_campagne.lister(
        session,
        statut=statut,
        annee=annee,
        type_entretien=type_entretien,
        limite=limite,
        decalage=decalage,
    )
    return Page(
        elements=[CampagneLue.depuis_modele(ligne) for ligne in lignes],
        total=total,
        limite=limite,
        decalage=decalage,
    )


@router.get(
    "/{campagne_id}",
    response_model=CampagneLue,
    dependencies=[Depends(exige_permission("campagne:lire"))],
    summary="Consulter une campagne",
)
def consulter(campagne_id: UUID, session: SessionDep) -> CampagneLue:
    return CampagneLue.depuis_modele(consulter_campagne.consulter(session, campagne_id=campagne_id))


@router.post(
    "",
    response_model=CampagneLue,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exige_permission("campagne:creer"))],
    summary="Créer une campagne en brouillon",
)
def creer(
    donnees: CampagneCreee, session: SessionDep, utilisateur: UtilisateurCourant
) -> CampagneLue:
    campagne = creer_campagne.executer(
        session,
        auteur=utilisateur,
        libelle=donnees.libelle,
        annee=donnees.annee,
        type_entretien=donnees.type_entretien.value,
        date_ouverture=donnees.date_ouverture,
        date_limite=donnees.date_limite,
        description=donnees.description,
    )
    return CampagneLue.depuis_modele(campagne)


@router.post(
    "/{campagne_id}/ouvrir",
    response_model=CampagneLue,
    dependencies=[Depends(exige_permission("campagne:ouvrir"))],
    summary="Ouvrir une campagne",
)
def ouvrir(campagne_id: UUID, session: SessionDep, utilisateur: UtilisateurCourant) -> CampagneLue:
    campagne = ouvrir_campagne.executer(session, auteur=utilisateur, campagne_id=campagne_id)
    return CampagneLue.depuis_modele(campagne)


@router.post(
    "/{campagne_id}/cloturer",
    response_model=CampagneLue,
    dependencies=[Depends(exige_permission("campagne:cloturer"))],
    summary="Clôturer une campagne",
)
def cloturer(
    campagne_id: UUID, session: SessionDep, utilisateur: UtilisateurCourant
) -> CampagneLue:
    campagne = cloturer_campagne.executer(session, auteur=utilisateur, campagne_id=campagne_id)
    return CampagneLue.depuis_modele(campagne)
