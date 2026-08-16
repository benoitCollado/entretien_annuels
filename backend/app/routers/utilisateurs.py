"""Contrôleur — US-02, administration des comptes.

Chaque endpoint déclare la permission qu'il exige (RBAC). Le contrôle de
**portée** — « cet utilisateur-là, précisément ? » — est appliqué dans les
processus, pas ici (§6.1).
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependances import SessionDep, UtilisateurCourant, exige_permission
from app.schemas.commun import Page
from app.schemas.utilisateur import (
    RolesAttribues,
    UtilisateurCree,
    UtilisateurLu,
    UtilisateurModifie,
)
from app.services.processus import (
    archiver_utilisateur,
    attribuer_roles,
    creer_utilisateur,
    lister_utilisateurs,
    modifier_utilisateur,
)

router = APIRouter(prefix="/utilisateurs", tags=["utilisateurs"])


@router.get(
    "",
    response_model=Page[UtilisateurLu],
    dependencies=[Depends(exige_permission("utilisateur:lire"))],
    summary="Lister les utilisateurs (US-02)",
)
def lister(
    session: SessionDep,
    utilisateur: UtilisateurCourant,
    limite: Annotated[int, Query(ge=1, le=200)] = 50,
    decalage: Annotated[int, Query(ge=0)] = 0,
) -> Page[UtilisateurLu]:
    lignes, total = lister_utilisateurs.executer(
        session, auteur=utilisateur, limite=limite, decalage=decalage
    )
    return Page(
        elements=[UtilisateurLu.depuis_modele(ligne) for ligne in lignes],
        total=total,
        limite=limite,
        decalage=decalage,
    )


@router.post(
    "",
    response_model=UtilisateurLu,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exige_permission("utilisateur:creer"))],
    summary="Créer un utilisateur (US-02)",
)
def creer(
    donnees: UtilisateurCree,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
) -> UtilisateurLu:
    cree = creer_utilisateur.executer(
        session,
        auteur=utilisateur,
        email=donnees.email,
        mot_de_passe=donnees.mot_de_passe,
        nom=donnees.nom,
        prenom=donnees.prenom,
        codes_roles=donnees.roles,
        poste=donnees.poste,
        service=donnees.service,
        date_entree=donnees.date_entree,
        manager_id=donnees.manager_id,
    )
    return UtilisateurLu.depuis_modele(cree)


@router.patch(
    "/{utilisateur_id}",
    response_model=UtilisateurLu,
    dependencies=[Depends(exige_permission("utilisateur:modifier"))],
    summary="Modifier un utilisateur (US-02)",
)
def modifier(
    utilisateur_id: UUID,
    donnees: UtilisateurModifie,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
) -> UtilisateurLu:
    modifie = modifier_utilisateur.executer(
        session,
        auteur=utilisateur,
        utilisateur_id=utilisateur_id,
        email=donnees.email,
        nom=donnees.nom,
        prenom=donnees.prenom,
        poste=donnees.poste,
        service=donnees.service,
        date_entree=donnees.date_entree,
        manager_id=donnees.manager_id,
        actif=donnees.actif,
        # Transmet la liste des champs réellement fournis, pour distinguer
        # « absent » de « mis à null ».
        champs_fournis=donnees.model_fields_set,
    )
    return UtilisateurLu.depuis_modele(modifie)


@router.put(
    "/{utilisateur_id}/roles",
    response_model=UtilisateurLu,
    dependencies=[Depends(exige_permission("role:attribuer"))],
    summary="Remplacer les rôles d'un utilisateur (US-02)",
)
def attribuer(
    utilisateur_id: UUID,
    donnees: RolesAttribues,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
) -> UtilisateurLu:
    modifie = attribuer_roles.executer(
        session,
        auteur=utilisateur,
        utilisateur_id=utilisateur_id,
        codes_roles=donnees.roles,
    )
    return UtilisateurLu.depuis_modele(modifie)


@router.delete(
    "/{utilisateur_id}",
    response_model=UtilisateurLu,
    dependencies=[Depends(exige_permission("utilisateur:archiver"))],
    summary="Archiver un utilisateur (US-02)",
)
def archiver(
    utilisateur_id: UUID,
    session: SessionDep,
    utilisateur: UtilisateurCourant,
) -> UtilisateurLu:
    """Archivage et non suppression : le compte reste rattaché à des entretiens
    signés, qui sont des documents opposables (§4.4)."""
    archive = archiver_utilisateur.executer(
        session, auteur=utilisateur, utilisateur_id=utilisateur_id
    )
    return UtilisateurLu.depuis_modele(archive)
