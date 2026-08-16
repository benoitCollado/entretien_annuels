"""UTILISATEUR — identité, rattachement hiérarchique et révocation de jeton."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, String, Uuid, text
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ArchivableMixin, Base, HorodatageMixin, cle_primaire_uuid
from app.models.role import Role, utilisateur_role


class Utilisateur(Base, HorodatageMixin, ArchivableMixin):
    __tablename__ = "utilisateur"
    __table_args__ = (
        # US-02 : un utilisateur ne peut pas être son propre manager.
        # Les cycles plus longs (A encadre B qui encadre A) ne sont pas
        # exprimables en CHECK sous PostgreSQL — sous-requêtes interdites. Ils
        # sont portés par `services/regles/portee_hierarchique.py`. Limite
        # documentée plutôt que masquée.
        CheckConstraint("manager_id IS NULL OR manager_id <> id", name="pas_son_manager"),
    )

    id: Mapped[uuid.UUID] = cle_primaire_uuid()

    # CITEXT : l'unicité est insensible à la casse sans que le code applicatif
    # ait à écrire `lower(email)` partout.
    email: Mapped[str] = mapped_column(CITEXT(), nullable=False, unique=True)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    poste: Mapped[str | None] = mapped_column(String(120), nullable=True)
    service: Mapped[str | None] = mapped_column(String(120), nullable=True)
    date_entree: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Facultatif : le dirigeant n'a pas de manager. `SET NULL` et non `CASCADE` :
    # archiver un manager ne doit jamais faire disparaître son équipe.
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("utilisateur.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Révocation de JWT sans denylist (§7.3) : le numéro est embarqué dans le
    # jeton et comparé à chaque requête. L'utilisateur étant de toute façon
    # chargé à chaque requête, la vérification ne coûte aucune requête de plus.
    version_jeton: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    manager: Mapped[Utilisateur | None] = relationship(
        remote_side="Utilisateur.id", back_populates="equipe"
    )
    equipe: Mapped[list[Utilisateur]] = relationship(back_populates="manager")

    roles: Mapped[list[Role]] = relationship(
        secondary=utilisateur_role, back_populates="utilisateurs", lazy="selectin"
    )

    @property
    def nom_complet(self) -> str:
        return f"{self.prenom} {self.nom}"

    def codes_roles(self) -> set[str]:
        return {role.code for role in self.roles}

    def codes_permissions(self) -> set[str]:
        """Union des permissions de tous les rôles portés."""
        return {code for role in self.roles for code in role.codes_permissions()}

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Utilisateur {self.email}>"
