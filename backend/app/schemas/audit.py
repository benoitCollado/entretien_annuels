from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import field_validator

from app.models.audit import JournalAudit
from app.schemas.commun import SchemaSortie


class EntreeAuditLue(SchemaSortie):
    id: UUID
    horodatage: datetime
    action: str
    utilisateur_id: UUID | None
    # Aplati depuis la relation : le journal se lit ligne à ligne, exiger un
    # second appel pour mettre un nom sur chaque identifiant le rendrait
    # inutilisable.
    utilisateur_email: str | None
    entretien_id: UUID | None
    statut_avant: str | None
    statut_apres: str | None
    adresse_ip: str | None
    donnees: dict[str, Any] | None

    # La colonne est en INET : psycopg restitue un objet `ipaddress`, que
    # Pydantic refuse pour un champ `str`. La conversion doit donc être faite
    # avant validation, et non à la construction, pour couvrir aussi une
    # instanciation depuis les attributs du modèle.
    @field_validator("adresse_ip", mode="before")
    @classmethod
    def _adresse_en_texte(cls, valeur: object) -> object:
        return None if valeur is None else str(valeur)

    @classmethod
    def depuis_modele(cls, entree: JournalAudit) -> EntreeAuditLue:
        return cls(
            id=entree.id,
            horodatage=entree.horodatage,
            action=entree.action,
            utilisateur_id=entree.utilisateur_id,
            utilisateur_email=entree.utilisateur.email if entree.utilisateur else None,
            entretien_id=entree.entretien_id,
            statut_avant=entree.statut_avant,
            statut_apres=entree.statut_apres,
            adresse_ip=entree.adresse_ip,
            donnees=entree.donnees,
        )
