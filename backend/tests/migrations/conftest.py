"""Fixtures des tests de migration : base jetable et configuration Alembic."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

RACINE_BACKEND = Path(__file__).resolve().parents[2]
DOSSIER_VERSIONS = RACINE_BACKEND / "migrations" / "versions"


def url_psycopg(url: str) -> str:
    """`postgresql+psycopg://…` → `postgresql://…`.

    SQLAlchemy accepte le nom du pilote dans l'URL, psycopg non.
    """
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def remplacer_base(url: str, nom_base: str) -> str:
    base, _, _ = url.rpartition("/")
    return f"{base}/{nom_base}"


def config_alembic(url: str) -> Config:
    """Configuration Alembic pointant sur une URL donnée.

    `script_location` est rendu absolu : les tests peuvent alors s'exécuter
    depuis n'importe quel répertoire courant.
    """
    config = Config(str(RACINE_BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(RACINE_BACKEND / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    return config


def repertoire_scripts() -> ScriptDirectory:
    return ScriptDirectory.from_config(config_alembic("postgresql://ignore/ignore"))


def revisions_existantes() -> list[str]:
    """Identifiants de toutes les révisions, de la plus ancienne à la plus récente."""
    return [rev.revision for rev in reversed(list(repertoire_scripts().walk_revisions()))]


def fichiers_de_migration() -> list[Path]:
    if not DOSSIER_VERSIONS.is_dir():
        return []
    return sorted(p for p in DOSSIER_VERSIONS.glob("*.py") if p.name != "__init__.py")


# ---------------------------------------------------------------------------
# Base jetable
# ---------------------------------------------------------------------------
def _url_administration() -> str | None:
    """URL vers une base de maintenance, pour émettre CREATE/DROP DATABASE."""
    if admin := os.environ.get("DATABASE_ADMIN_URL"):
        return url_psycopg(admin)
    if principale := os.environ.get("DATABASE_URL"):
        return remplacer_base(url_psycopg(principale), "postgres")
    return None


@pytest.fixture
def url_base_vierge() -> Iterator[str]:
    """Crée une base PostgreSQL neuve, la fournit, puis la détruit.

    Une base **par test** : c'est le seul moyen de garantir qu'un test de
    descente n'empoisonne pas le suivant. Le coût (~150 ms) est négligeable au
    regard de la fiabilité gagnée.
    """
    url_admin = _url_administration()
    if url_admin is None:
        pytest.skip("DATABASE_URL ou DATABASE_ADMIN_URL absent : PostgreSQL requis")

    nom = f"mig_{uuid4().hex[:12]}"
    try:
        # autocommit obligatoire : CREATE DATABASE refuse de s'exécuter dans
        # une transaction.
        connexion = psycopg.connect(url_admin, autocommit=True, connect_timeout=5)
    except psycopg.OperationalError as exc:  # pragma: no cover - dépend de l'hôte
        pytest.skip(f"PostgreSQL injoignable : {exc}")

    with connexion:
        connexion.execute(f'CREATE DATABASE "{nom}"')
        try:
            yield remplacer_base(url_admin, nom).replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        finally:
            # SQLAlchemy laisse des connexions ouvertes dans son pool ; sans
            # cette coupure, DROP DATABASE échoue sur « is being accessed by
            # other users ».
            connexion.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (nom,),
            )
            connexion.execute(f'DROP DATABASE IF EXISTS "{nom}"')


@pytest.fixture
def exige_des_revisions() -> None:
    """Ignore le test tant qu'aucune migration n'a été écrite."""
    if not fichiers_de_migration():
        pytest.skip("aucune migration dans migrations/versions/ : rien à vérifier")
