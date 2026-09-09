from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Base


class BaseRepository[M: Base]:
    modele: type[M]

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id_: UUID) -> M | None:
        return self.session.get(self.modele, id_)

    def lister(self, limite: int = 100, decalage: int = 0) -> Sequence[M]:
        stmt = select(self.modele).limit(limite).offset(decalage)
        return self.session.scalars(stmt).all()

    def ajouter(self, instance: M) -> M:
        self.session.add(instance)
        self.session.flush()
        return instance

    def ajouter_tous(self, instances: Sequence[M]) -> None:
        self.session.add_all(instances)
        self.session.flush()
