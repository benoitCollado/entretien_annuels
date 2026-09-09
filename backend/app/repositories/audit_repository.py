from __future__ import annotations

import ipaddress
import logging
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import selectinload

from app.models.audit import JournalAudit
from app.repositories.base import BaseRepository

logger = logging.getLogger("app.audit")


def normaliser_adresse(adresse: str | None) -> str | None:
    if adresse is None:
        return None
    try:
        return str(ipaddress.ip_address(adresse))
    except ValueError:
        logger.debug("Adresse non exploitable pour l'audit : %r", adresse)
        return None


class AuditRepository(BaseRepository[JournalAudit]):
    modele = JournalAudit

    def tracer(
        self,
        *,
        action: str,
        utilisateur_id: UUID | None = None,
        entretien_id: UUID | None = None,
        statut_avant: str | None = None,
        statut_apres: str | None = None,
        donnees: dict[str, Any] | None = None,
        adresse_ip: str | None = None,
    ) -> JournalAudit:
        return self.ajouter(
            JournalAudit(
                action=action,
                utilisateur_id=utilisateur_id,
                entretien_id=entretien_id,
                statut_avant=statut_avant,
                statut_apres=statut_apres,
                donnees=donnees,
                adresse_ip=normaliser_adresse(adresse_ip),
            )
        )

    def journal(
        self,
        *,
        entretien_id: UUID | None = None,
        utilisateur_id: UUID | None = None,
        action: str | None = None,
        limite: int = 50,
        decalage: int = 0,
    ) -> tuple[Sequence[JournalAudit], int]:
        criteres: list[ColumnElement[bool]] = []
        if entretien_id is not None:
            criteres.append(JournalAudit.entretien_id == entretien_id)
        if utilisateur_id is not None:
            criteres.append(JournalAudit.utilisateur_id == utilisateur_id)
        if action is not None:
            criteres.append(JournalAudit.action == action)

        total = (
            self.session.scalar(select(func.count()).select_from(JournalAudit).where(*criteres))
            or 0
        )
        stmt = (
            select(JournalAudit)
            .options(selectinload(JournalAudit.utilisateur))
            .where(*criteres)
            .order_by(JournalAudit.horodatage.desc())
            .limit(limite)
            .offset(decalage)
        )
        return self.session.scalars(stmt).all(), total

    def lister_de_l_entretien(self, entretien_id: UUID, limite: int = 100) -> list[JournalAudit]:
        stmt = (
            select(JournalAudit)
            .options(selectinload(JournalAudit.utilisateur))
            .where(JournalAudit.entretien_id == entretien_id)
            .order_by(JournalAudit.horodatage.desc())
            .limit(limite)
        )
        return list(self.session.scalars(stmt))

    def tracer_refus(
        self,
        *,
        utilisateur_id: UUID | None,
        entretien_id: UUID | None,
        statut_avant: str | None = None,
        donnees: dict[str, Any] | None = None,
        adresse_ip: str | None = None,
    ) -> None:
        from app.database import obtenir_fabrique_sessions

        try:
            with obtenir_fabrique_sessions()() as session:
                AuditRepository(session).tracer(
                    action="ACCES_REFUSE",
                    utilisateur_id=utilisateur_id,
                    entretien_id=entretien_id,
                    statut_avant=statut_avant,
                    donnees=donnees,
                    adresse_ip=adresse_ip,
                )
                session.commit()
        except Exception:  # pragma: no cover
            logger.warning(
                "Trace d'accès refusé non enregistrée (utilisateur=%s, entretien=%s).",
                utilisateur_id,
                entretien_id,
                exc_info=True,
            )

    def compter_par_action(self, entretien_id: UUID, action: str) -> int:
        stmt = select(JournalAudit.id).where(
            JournalAudit.entretien_id == entretien_id, JournalAudit.action == action
        )
        return len(list(self.session.scalars(stmt)))
