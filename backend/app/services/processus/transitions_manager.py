from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AccesRefuse, DonneesInvalides, RessourceIntrouvable
from app.models.entretien import Entretien
from app.models.utilisateur import Utilisateur
from app.repositories.audit_repository import AuditRepository
from app.repositories.commentaire_repository import CommentaireRepository
from app.repositories.entretien_repository import EntretienRepository
from app.services.regles import transitions_entretien

ROLE_RH = "RH"


def _charger(session: Session, entretien_id: UUID) -> Entretien:
    entretien = EntretienRepository(session).get_avec_questionnaire(entretien_id)
    if entretien is None:
        raise RessourceIntrouvable("Entretien introuvable.")
    return entretien


def _acteur(entretien: Entretien, utilisateur: Utilisateur) -> str:
    role = entretien.role_de(utilisateur.id)
    if role is not None:
        return role
    if ROLE_RH in utilisateur.codes_roles():
        return transitions_entretien.RH
    raise AccesRefuse("Cet entretien ne vous concerne pas.")


def ouvrir_revue(
    session: Session,
    *,
    auteur: Utilisateur,
    entretien_id: UUID,
    adresse_ip: str | None = None,
) -> Entretien:
    entretien = _charger(session, entretien_id)
    statut_avant = entretien.statut

    transitions_entretien.exiger_transition(
        statut_avant, transitions_entretien.REVUE_MANAGER, _acteur(entretien, auteur)
    )

    entretien.statut = transitions_entretien.REVUE_MANAGER
    entretien.revue_ouverte_le = datetime.now(UTC)

    AuditRepository(session).tracer(
        action="OUVERTURE_REVUE",
        utilisateur_id=auteur.id,
        entretien_id=entretien.id,
        statut_avant=statut_avant,
        statut_apres=entretien.statut,
        adresse_ip=adresse_ip,
    )
    session.flush()
    return entretien


def cloturer_echange(
    session: Session,
    *,
    auteur: Utilisateur,
    entretien_id: UUID,
    adresse_ip: str | None = None,
) -> Entretien:
    entretien = _charger(session, entretien_id)
    statut_avant = entretien.statut

    transitions_entretien.exiger_transition(
        statut_avant, transitions_entretien.ENTRETIEN_REALISE, _acteur(entretien, auteur)
    )

    if entretien.questionnaire is None or not CommentaireRepository(session).existe_synthese(
        entretien.questionnaire.id
    ):
        raise DonneesInvalides("La synthèse globale est obligatoire avant de clore l'échange.")

    entretien.statut = transitions_entretien.ENTRETIEN_REALISE
    entretien.realise_le = datetime.now(UTC)

    AuditRepository(session).tracer(
        action="CLOTURE_ECHANGE",
        utilisateur_id=auteur.id,
        entretien_id=entretien.id,
        statut_avant=statut_avant,
        statut_apres=entretien.statut,
        adresse_ip=adresse_ip,
    )
    session.flush()
    return entretien


def annuler(
    session: Session,
    *,
    auteur: Utilisateur,
    entretien_id: UUID,
    motif: str,
    adresse_ip: str | None = None,
) -> Entretien:
    entretien = _charger(session, entretien_id)
    statut_avant = entretien.statut

    if not motif.strip():
        raise DonneesInvalides("Le motif d'annulation est obligatoire.")

    transitions_entretien.exiger_transition(
        statut_avant, transitions_entretien.ANNULE, _acteur(entretien, auteur)
    )

    entretien.statut = transitions_entretien.ANNULE
    entretien.motif_annulation = motif

    AuditRepository(session).tracer(
        action="ANNULATION",
        utilisateur_id=auteur.id,
        entretien_id=entretien.id,
        statut_avant=statut_avant,
        statut_apres=entretien.statut,
        donnees={"motif": motif},
        adresse_ip=adresse_ip,
    )
    session.flush()
    return entretien
