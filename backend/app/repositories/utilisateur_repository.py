from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select

from app.models.utilisateur import Utilisateur
from app.repositories.base import BaseRepository


class UtilisateurRepository(BaseRepository[Utilisateur]):
    modele = Utilisateur

    def get_par_email(self, email: str) -> Utilisateur | None:
        stmt = select(Utilisateur).where(
            Utilisateur.email == email,
            Utilisateur.archived_at.is_(None),
        )
        return self.session.scalars(stmt).one_or_none()

    def get_actif(self, id_: UUID) -> Utilisateur | None:
        stmt = select(Utilisateur).where(
            Utilisateur.id == id_,
            Utilisateur.actif.is_(True),
            Utilisateur.archived_at.is_(None),
        )
        return self.session.scalars(stmt).one_or_none()

    def get_non_archive(self, id_: UUID) -> Utilisateur | None:
        stmt = select(Utilisateur).where(
            Utilisateur.id == id_,
            Utilisateur.archived_at.is_(None),
        )
        return self.session.scalars(stmt).one_or_none()

    def email_existe(self, email: str, sauf_id: UUID | None = None) -> bool:
        stmt = select(Utilisateur.id).where(Utilisateur.email == email)
        if sauf_id is not None:
            stmt = stmt.where(Utilisateur.id != sauf_id)
        return self.session.scalar(select(stmt.exists())) or False

    def _base_liste(self, manager_id: UUID | None) -> Select[tuple[Utilisateur]]:
        stmt = select(Utilisateur).where(Utilisateur.archived_at.is_(None))
        if manager_id is not None:
            stmt = stmt.where(Utilisateur.manager_id == manager_id)
        return stmt

    def lister_filtre(
        self,
        *,
        manager_id: UUID | None = None,
        limite: int = 50,
        decalage: int = 0,
    ) -> list[Utilisateur]:
        stmt = (
            self._base_liste(manager_id)
            .order_by(Utilisateur.nom, Utilisateur.prenom)
            .limit(limite)
            .offset(decalage)
        )
        return list(self.session.scalars(stmt))

    def compter(self, *, manager_id: UUID | None = None) -> int:
        stmt = self._base_liste(manager_id).with_only_columns(func.count(Utilisateur.id))
        return self.session.scalar(stmt) or 0

    def chaine_hierarchique(self, utilisateur_id: UUID, profondeur_max: int = 20) -> list[UUID]:
        chaine: list[UUID] = []
        courant: UUID | None = utilisateur_id

        for _ in range(profondeur_max):
            stmt = select(Utilisateur.manager_id).where(Utilisateur.id == courant)
            courant = self.session.scalar(stmt)
            if courant is None or courant in chaine:
                break
            chaine.append(courant)

        return chaine

    def lister_equipe(self, manager_id: UUID) -> list[Utilisateur]:
        stmt = (
            select(Utilisateur)
            .where(
                Utilisateur.manager_id == manager_id,
                Utilisateur.archived_at.is_(None),
            )
            .order_by(Utilisateur.nom, Utilisateur.prenom)
        )
        return list(self.session.scalars(stmt))
