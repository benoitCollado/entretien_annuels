from __future__ import annotations

from datetime import datetime

from app.core.exceptions import ConflitMetier
from app.services.regles.transitions_entretien import (
    COLLABORATEUR,
    ENTRETIEN_REALISE,
    MANAGER,
)


def peut_signer(statut: str, role: str | None) -> bool:
    return statut == ENTRETIEN_REALISE and role in (COLLABORATEUR, MANAGER)


def exiger_droit_de_signer(statut: str, role: str | None) -> None:
    if role not in (COLLABORATEUR, MANAGER):
        raise ConflitMetier(
            "Seuls le collaborateur et le manager de cet entretien peuvent le signer.",
            details=[{"role": role}],
        )
    if statut != ENTRETIEN_REALISE:
        raise ConflitMetier(
            "L'entretien doit avoir été réalisé pour être signé.",
            details=[{"statut": statut, "attendu": ENTRETIEN_REALISE}],
        )


def deja_signe(
    role: str,
    signe_collaborateur_le: datetime | None,
    signe_manager_le: datetime | None,
) -> bool:
    horodatage = signe_collaborateur_le if role == COLLABORATEUR else signe_manager_le
    return horodatage is not None


def exiger_signature_unique(
    role: str,
    signe_collaborateur_le: datetime | None,
    signe_manager_le: datetime | None,
) -> None:
    if deja_signe(role, signe_collaborateur_le, signe_manager_le):
        raise ConflitMetier(
            "Vous avez déjà signé cet entretien.",
            details=[{"role": role}],
        )


def double_signature_acquise(
    signe_collaborateur_le: datetime | None,
    signe_manager_le: datetime | None,
) -> bool:
    return signe_collaborateur_le is not None and signe_manager_le is not None


def observation_autorisee(role: str) -> bool:
    return role == COLLABORATEUR
