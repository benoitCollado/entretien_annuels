"""Sonde de disponibilité de la base.

Elle vit dans la couche d'accès aux données parce qu'elle exécute du SQL, même
trivial. C'est ce qui permet au router de santé de ne rien importer de
SQLAlchemy.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger("app.sante")


class SanteRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def base_repond(self) -> bool:
        try:
            return self.session.scalar(select(1)) == 1
        except SQLAlchemyError as exc:
            logger.warning("Base injoignable : %s", exc)
            return False
