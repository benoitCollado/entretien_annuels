"""Repository générique — addendum §3.1.

Contrat de la couche : toutes les requêtes SQL vivent ici, et **rien d'autre**.
Un repository ne décide jamais si une action est permise et ne lève aucune
exception métier. Il ne commite jamais : `flush()` suffit à obtenir un
identifiant, le commit appartient à `get_db`.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Base


# Syntaxe générique PEP 695 (Python 3.12+) : plus concise que TypeVar +
# Generic, et c'est ce que ruff attend avec target-version = py312.
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
        self.session.flush()  # obtient l'identifiant sans commiter
        return instance

    def ajouter_tous(self, instances: Sequence[M]) -> None:
        self.session.add_all(instances)
        self.session.flush()
