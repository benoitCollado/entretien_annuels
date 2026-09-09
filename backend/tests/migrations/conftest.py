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
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def remplacer_base(url: str, nom_base: str) -> str:
    base, _, _ = url.rpartition("/")
    return f"{base}/{nom_base}"


def config_alembic(url: str) -> Config:
    config = Config(str(RACINE_BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(RACINE_BACKEND / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    return config


def repertoire_scripts() -> ScriptDirectory:
    return ScriptDirectory.from_config(config_alembic("postgresql://ignore/ignore"))


def revisions_existantes() -> list[str]:
    return [rev.revision for rev in reversed(list(repertoire_scripts().walk_revisions()))]


def fichiers_de_migration() -> list[Path]:
    if not DOSSIER_VERSIONS.is_dir():
        return []
    return sorted(p for p in DOSSIER_VERSIONS.glob("*.py") if p.name != "__init__.py")


def _url_administration() -> str | None:
    if admin := os.environ.get("DATABASE_ADMIN_URL"):
        return url_psycopg(admin)
    if principale := os.environ.get("DATABASE_URL"):
        return remplacer_base(url_psycopg(principale), "postgres")
    return None


@pytest.fixture
def url_base_vierge() -> Iterator[str]:
    url_admin = _url_administration()
    if url_admin is None:
        pytest.skip("DATABASE_URL ou DATABASE_ADMIN_URL absent : PostgreSQL requis")

    nom = f"mig_{uuid4().hex[:12]}"
    try:
        connexion = psycopg.connect(url_admin, autocommit=True, connect_timeout=5)
    except psycopg.OperationalError as exc:  # pragma: no cover
        pytest.skip(f"PostgreSQL injoignable : {exc}")

    with connexion:
        connexion.execute(f'CREATE DATABASE "{nom}"')
        try:
            yield remplacer_base(url_admin, nom).replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        finally:
            connexion.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (nom,),
            )
            connexion.execute(f'DROP DATABASE IF EXISTS "{nom}"')


@pytest.fixture
def exige_des_revisions() -> None:
    if not fichiers_de_migration():
        pytest.skip("aucune migration dans migrations/versions/ : rien à vérifier")
