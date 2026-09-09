from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AccesRefuse, DonneesInvalides, RessourceIntrouvable
from app.models.entretien import Entretien
from app.models.utilisateur import Utilisateur
from app.repositories.audit_repository import AuditRepository
from app.repositories.entretien_repository import EntretienRepository
from app.services.regles import signature, transitions_entretien

ROLE_RH = "RH"


def executer(
    session: Session,
    *,
    signataire: Utilisateur,
    entretien_id: UUID,
    observation: str | None = None,
    adresse_ip: str | None = None,
) -> Entretien:
    entretien = EntretienRepository(session).get_avec_questionnaire(entretien_id)
    if entretien is None:
        raise RessourceIntrouvable("Entretien introuvable.")

    audit = AuditRepository(session)
    statut_avant = entretien.statut

    role = entretien.role_de(signataire.id)
    if role is None:
        audit.tracer_refus(
            utilisateur_id=signataire.id,
            entretien_id=entretien.id,
            statut_avant=statut_avant,
            donnees={"motif": "signature par un tiers"},
            adresse_ip=adresse_ip,
        )
        raise AccesRefuse(
            "Seuls le collaborateur et le manager de cet entretien peuvent le signer."
        )

    signature.exiger_droit_de_signer(statut_avant, role)
    signature.exiger_signature_unique(
        role, entretien.signe_collaborateur_le, entretien.signe_manager_le
    )

    maintenant = datetime.now(UTC)
    if role == transitions_entretien.COLLABORATEUR:
        entretien.signe_collaborateur_le = maintenant
        if observation:
            entretien.observation_collaborateur = observation
    else:
        if observation:
            raise DonneesInvalides(
                "L'observation est réservée au collaborateur (droit de réserve).",
                details=[{"role": role}],
            )
        entretien.signe_manager_le = maintenant

    complete = signature.double_signature_acquise(
        entretien.signe_collaborateur_le, entretien.signe_manager_le
    )
    if complete:
        transitions_entretien.exiger_transition(statut_avant, transitions_entretien.SIGNE, role)
        entretien.statut = transitions_entretien.SIGNE

    audit.tracer(
        action="SIGNATURE",
        utilisateur_id=signataire.id,
        entretien_id=entretien.id,
        statut_avant=statut_avant,
        statut_apres=entretien.statut if complete else None,
        donnees={
            "role": role,
            "double_signature": complete,
            "avec_observation": bool(observation),
        },
        adresse_ip=adresse_ip,
    )

    session.flush()
    return entretien


def cloturer(
    session: Session,
    *,
    auteur: Utilisateur,
    entretien_id: UUID,
    adresse_ip: str | None = None,
) -> Entretien:
    entretien = EntretienRepository(session).get_avec_questionnaire(entretien_id)
    if entretien is None:
        raise RessourceIntrouvable("Entretien introuvable.")

    statut_avant = entretien.statut
    if ROLE_RH not in auteur.codes_roles():
        AuditRepository(session).tracer_refus(
            utilisateur_id=auteur.id,
            entretien_id=entretien.id,
            statut_avant=statut_avant,
            donnees={"motif": "clôture par un non-RH"},
            adresse_ip=adresse_ip,
        )
        raise AccesRefuse("Seul le service RH peut clôturer un entretien.")

    transitions_entretien.exiger_transition(
        statut_avant, transitions_entretien.CLOTURE, transitions_entretien.RH
    )

    entretien.statut = transitions_entretien.CLOTURE
    entretien.cloture_le = datetime.now(UTC)

    AuditRepository(session).tracer(
        action="CLOTURE",
        utilisateur_id=auteur.id,
        entretien_id=entretien.id,
        statut_avant=statut_avant,
        statut_apres=entretien.statut,
        adresse_ip=adresse_ip,
    )

    session.flush()
    return entretien
