from __future__ import annotations

from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import obtenir_parametres


@lru_cache
def obtenir_moteur() -> Engine:
    parametres = obtenir_parametres()
    return create_engine(
        parametres.database_url,
        echo=parametres.database_echo,
        pool_pre_ping=True,
        future=True,
    )


@lru_cache
def obtenir_fabrique_sessions() -> sessionmaker[Session]:
    return sessionmaker(bind=obtenir_moteur(), autoflush=False, expire_on_commit=False)
