from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AccesRefuse, ConflitMetier, RessourceIntrouvable
from app.models.entretien import Entretien
from app.models.enums import StatutObjectif
from app.models.objectif import Objectif
from app.models.utilisateur import Utilisateur
from app.repositories.audit_repository import AuditRepository
from app.repositories.entretien_repository import EntretienRepository
from app.repositories.objectif_repository import ObjectifRepository
from app.services.regles import immutabilite, transitions_entretien

ROLE_RH = "RH"
STATUTS_OUVERTS = frozenset(
    {transitions_entretien.REVUE_MANAGER, transitions_entretien.ENTRETIEN_REALISE}
)


def _charger(session: Session, entretien_id: UUID) -> Entretien:
    entretien = EntretienRepository(session).get_avec_questionnaire(entretien_id)
    if entretien is None:
        raise RessourceIntrouvable("Entretien introuvable.")
    return entretien


def _exiger_manager(
    session: Session, entretien: Entretien, auteur: Utilisateur, adresse_ip: str | None
) -> None:
    if entretien.role_de(auteur.id) != transitions_entretien.MANAGER:
        AuditRepository(session).tracer_refus(
            utilisateur_id=auteur.id,
            entretien_id=entretien.id,
            statut_avant=entretien.statut,
            donnees={"motif": "gestion des objectifs hors rôle manager"},
            adresse_ip=adresse_ip,
        )
        raise AccesRefuse("Seul le manager de cet entretien peut gérer ses objectifs.")


def consulter(
    session: Session,
    *,
    lecteur: Utilisateur,
    entretien_id: UUID,
) -> tuple[list[Objectif], list[Objectif]]:
    entretien = _charger(session, entretien_id)
    if entretien.role_de(lecteur.id) is None and ROLE_RH not in lecteur.codes_roles():
        raise AccesRefuse("Cet entretien ne vous concerne pas.")

    objectifs = ObjectifRepository(session)
    return (
        objectifs.lister_de_l_entretien(entretien.id),
        objectifs.lister_a_evaluer(entretien.collaborateur_id, entretien.id),
    )


def fixer(
    session: Session,
    *,
    auteur: Utilisateur,
    entretien_id: UUID,
    libelle: str,
    description: str | None = None,
    indicateur: str | None = None,
    echeance: date | None = None,
    objectif_parent_id: UUID | None = None,
    adresse_ip: str | None = None,
) -> Objectif:
    entretien = _charger(session, entretien_id)
    _exiger_manager(session, entretien, auteur, adresse_ip)

    immutabilite.exiger_non_gele(entretien.statut, "Un objectif")

    if entretien.statut not in STATUTS_OUVERTS:
        raise ConflitMetier(
            "Les objectifs se fixent pendant l'échange, une fois la revue ouverte.",
            details=[{"statut": entretien.statut, "attendus": sorted(STATUTS_OUVERTS)}],
        )

    objectifs = ObjectifRepository(session)

    parent = None
    if objectif_parent_id is not None:
        parent = objectifs.get(objectif_parent_id)
        if parent is None:
            raise RessourceIntrouvable("Objectif d'origine introuvable.")
        if parent.collaborateur_id != entretien.collaborateur_id:
            raise ConflitMetier("Cet objectif appartient à un autre collaborateur.")

    objectif = objectifs.ajouter(
        Objectif(
            entretien_origine_id=entretien.id,
            collaborateur_id=entretien.collaborateur_id,
            objectif_parent_id=parent.id if parent else None,
            libelle=libelle,
            description=description,
            indicateur=indicateur,
            echeance=echeance,
            statut=StatutObjectif.EN_COURS,
        )
    )
    session.flush()

    AuditRepository(session).tracer(
        action="OBJECTIF_FIXE",
        utilisateur_id=auteur.id,
        entretien_id=entretien.id,
        statut_avant=entretien.statut,
        donnees={"objectif_id": str(objectif.id), "reconduction": parent is not None},
        adresse_ip=adresse_ip,
    )
    return objectif


def evaluer(
    session: Session,
    *,
    auteur: Utilisateur,
    objectif_id: UUID,
    entretien_id: UUID,
    statut: str,
    niveau_atteinte: int | None = None,
    commentaire: str | None = None,
    adresse_ip: str | None = None,
) -> Objectif:
    objectifs = ObjectifRepository(session)
    objectif = objectifs.get(objectif_id)
    if objectif is None:
        raise RessourceIntrouvable("Objectif introuvable.")

    entretien = _charger(session, entretien_id)
    _exiger_manager(session, entretien, auteur, adresse_ip)
    immutabilite.exiger_non_gele(entretien.statut, "Une évaluation d'objectif")

    if objectif.collaborateur_id != entretien.collaborateur_id:
        raise AccesRefuse("Cet objectif appartient à un autre collaborateur.")

    if objectif.entretien_origine_id == entretien.id:
        raise ConflitMetier(
            "Un objectif ne s'évalue pas dans l'entretien où il a été fixé.",
        )
    if objectif.est_evalue:
        raise ConflitMetier(
            "Cet objectif a déjà été évalué.",
            details=[{"statut": objectif.statut}],
        )
    if statut == StatutObjectif.EN_COURS:
        raise ConflitMetier("Une évaluation doit conclure : atteint, partiel ou non atteint.")

    objectif.statut = statut
    objectif.entretien_evaluation_id = entretien.id
    objectif.niveau_atteinte = niveau_atteinte
    objectif.commentaire_evaluation = commentaire

    AuditRepository(session).tracer(
        action="OBJECTIF_EVALUE",
        utilisateur_id=auteur.id,
        entretien_id=entretien.id,
        statut_avant=entretien.statut,
        donnees={"objectif_id": str(objectif.id), "resultat": statut},
        adresse_ip=adresse_ip,
    )

    session.flush()
    return objectif


def historique(
    session: Session,
    *,
    lecteur: Utilisateur,
    collaborateur_id: UUID,
) -> list[Objectif]:
    if lecteur.id != collaborateur_id and ROLE_RH not in lecteur.codes_roles():
        cible = session.get(Utilisateur, collaborateur_id)
        if cible is None or cible.manager_id != lecteur.id:
            raise AccesRefuse("Ce collaborateur n'est pas dans votre périmètre.")

    return ObjectifRepository(session).lister_du_collaborateur(collaborateur_id)
