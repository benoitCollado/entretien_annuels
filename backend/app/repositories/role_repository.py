"""Accès aux données du référentiel RBAC."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models.role import Permission, Role
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    modele = Role

    def get_par_code(self, code: str) -> Role | None:
        stmt = select(Role).where(Role.code == code)
        return self.session.scalars(stmt).one_or_none()

    def lister_par_codes(self, codes: Sequence[str]) -> list[Role]:
        """Charge plusieurs rôles en une requête.

        L'appelant compare le nombre obtenu au nombre demandé pour repérer un
        code inconnu : c'est au processus de décider quoi en faire, pas au
        repository.
        """
        if not codes:
            return []
        stmt = select(Role).where(Role.code.in_(list(codes))).order_by(Role.code)
        return list(self.session.scalars(stmt))

    def lister_tous(self) -> list[Role]:
        return list(self.session.scalars(select(Role).order_by(Role.code)))

    def lister_permissions(self) -> list[Permission]:
        return list(self.session.scalars(select(Permission).order_by(Permission.code)))
