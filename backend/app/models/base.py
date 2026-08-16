"""Base déclarative, convention de nommage des contraintes et mixins."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, MetaData, Uuid, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# `uuid_utils.compat` renvoie de vrais `uuid.UUID` de la bibliothèque standard.
# Le module racine expose un type maison que SQLAlchemy refuse.
from uuid_utils.compat import uuid7

# Sans convention, PostgreSQL nomme lui-même les contraintes anonymes : les noms
# diffèrent entre le modèle et la base, `compare_metadata` produit du bruit, et
# surtout `op.drop_constraint()` en downgrade n'a aucun nom stable à viser.
# Les contraintes nommées explicitement gardent leur nom.
CONVENTION_NOMMAGE = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENTION_NOMMAGE)


def cle_primaire_uuid() -> Mapped[uuid.UUID]:
    """UUID v7 : ordonné dans le temps, donc pas de fragmentation d'index, et
    ne révèle aucune volumétrie dans les URLs (§4.4)."""
    return mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid7)


class HorodatageMixin:
    """`created_at` / `updated_at` en TIMESTAMPTZ.

    Défauts posés côté serveur avec `text("now()")` — formulation identique à ce
    que PostgreSQL renvoie à l'introspection, ce qui évite les faux positifs de
    `compare_server_default=True` dans le test de dérive.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )


class ArchivableMixin:
    """Archivage plutôt que suppression : un entretien signé est un document
    opposable, on n'efface jamais (§4.4)."""

    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
