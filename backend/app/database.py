"""Moteur et fabrique de sessions.

Exécution **synchrone** assumée (§7.1) : pas de `MissingGreenlet`, débogage
direct, écosystème mature. Corollaire : les endpoints se déclarent avec `def` et
non `async def`, pour que FastAPI les exécute dans un threadpool. Un `async def`
contenant un appel SQLAlchemy synchrone gèlerait la boucle d'événements.
"""

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
        # Vérifie la connexion avant usage : indispensable quand PostgreSQL
        # redémarre sous l'application.
        pool_pre_ping=True,
        future=True,
    )


@lru_cache
def obtenir_fabrique_sessions() -> sessionmaker[Session]:
    return sessionmaker(bind=obtenir_moteur(), autoflush=False, expire_on_commit=False)
