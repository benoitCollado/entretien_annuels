"""Accès aux données des utilisateurs."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select

from app.models.utilisateur import Utilisateur
from app.repositories.base import BaseRepository


class UtilisateurRepository(BaseRepository[Utilisateur]):
    modele = Utilisateur

    # --- Lectures unitaires ------------------------------------------------
    def get_par_email(self, email: str) -> Utilisateur | None:
        """Recherche insensible à la casse : la colonne est en CITEXT, la
        comparaison est donc faite par PostgreSQL, sans `lower()` applicatif."""
        stmt = select(Utilisateur).where(
            Utilisateur.email == email,
            Utilisateur.archived_at.is_(None),
        )
        return self.session.scalars(stmt).one_or_none()

    def get_actif(self, id_: UUID) -> Utilisateur | None:
        """Utilisateur utilisable : ni archivé, ni désactivé."""
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
        """Inclut volontairement les comptes archivés : réutiliser l'adresse
        d'un salarié parti casserait l'unicité en base."""
        stmt = select(Utilisateur.id).where(Utilisateur.email == email)
        if sauf_id is not None:
            stmt = stmt.where(Utilisateur.id != sauf_id)
        return self.session.scalar(select(stmt.exists())) or False

    # --- Listes ------------------------------------------------------------
    def _base_liste(self, manager_id: UUID | None) -> Select[tuple[Utilisateur]]:
        """Fabrique du filtre commun.

        `manager_id` non nul restreint au périmètre d'encadrement direct : c'est
        le contrôle de **portée**, appliqué en SQL et non après coup en Python.
        """
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

    # --- Hiérarchie --------------------------------------------------------
    def chaine_hierarchique(self, utilisateur_id: UUID, profondeur_max: int = 20) -> list[UUID]:
        """Identifiants des managers successifs, du plus proche au plus lointain.

        Sert à la détection de cycle. La remontée est bornée : sur une base déjà
        corrompue par un cycle, une boucle non bornée ne se terminerait jamais.
        """
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
