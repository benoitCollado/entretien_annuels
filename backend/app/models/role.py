"""Référentiel RBAC : rôles, permissions et tables de liaison."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, cle_primaire_uuid

if TYPE_CHECKING:
    from app.models.utilisateur import Utilisateur

utilisateur_role = Table(
    "utilisateur_role",
    Base.metadata,
    Column(
        "utilisateur_id",
        Uuid(as_uuid=True),
        ForeignKey("utilisateur.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        Uuid(as_uuid=True),
        ForeignKey("role.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("attribue_le", DateTime(timezone=True), nullable=False, server_default=text("now()")),
)

role_permission = Table(
    "role_permission",
    Base.metadata,
    Column(
        "role_id",
        Uuid(as_uuid=True),
        ForeignKey("role.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        Uuid(as_uuid=True),
        ForeignKey("permission.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Permission(Base):
    __tablename__ = "permission"

    id: Mapped[uuid.UUID] = cle_primaire_uuid()
    code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    libelle: Mapped[str] = mapped_column(String(150), nullable=False)

    roles: Mapped[list[Role]] = relationship(
        secondary=role_permission, back_populates="permissions"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Permission {self.code}>"


class Role(Base):
    __tablename__ = "role"

    id: Mapped[uuid.UUID] = cle_primaire_uuid()
    code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    libelle: Mapped[str] = mapped_column(String(100), nullable=False)

    # `selectin` : les permissions sont systématiquement nécessaires pour
    # évaluer le RBAC, autant les charger en une requête supplémentaire plutôt
    # qu'une par rôle.
    permissions: Mapped[list[Permission]] = relationship(
        secondary=role_permission, back_populates="roles", lazy="selectin"
    )
    utilisateurs: Mapped[list[Utilisateur]] = relationship(
        secondary=utilisateur_role, back_populates="roles"
    )

    def codes_permissions(self) -> set[str]:
        return {permission.code for permission in self.permissions}

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Role {self.code}>"
