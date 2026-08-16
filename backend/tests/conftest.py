"""Fixtures globales.

Stratégie d'isolation : **une base jetable par session de test**, migrée une
seule fois, puis **une transaction annulée après chaque test**. Nettement plus
rapide que de recréer le schéma à chaque test, tout en garantissant qu'un test
ne voit jamais les écritures d'un autre.

Le point délicat est que `get_db` commite en fin de requête. La session de test
est donc ouverte avec `join_transaction_mode="create_savepoint"` : les commits
de l'application deviennent des points de reprise imbriqués, et le `rollback()`
final de la transaction externe les annule tous.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from uuid import uuid4

import psycopg
import pytest
from alembic import command
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.config import Parametres
from app.core.dependances import get_db
from app.core.securite import hacher_mot_de_passe
from app.main import creer_application
from app.models.utilisateur import Utilisateur
from app.repositories.role_repository import RoleRepository
from app.repositories.utilisateur_repository import UtilisateurRepository
from tests.migrations.conftest import config_alembic, remplacer_base, url_psycopg

MOT_DE_PASSE_TEST = "MotDePasseDeTest2026!"
SECRET_KEY_TEST = "cle-de-test-de-plus-de-32-caracteres-ok"


def _url_administration() -> str | None:
    if admin := os.environ.get("DATABASE_ADMIN_URL"):
        return url_psycopg(admin)
    if principale := os.environ.get("DATABASE_URL"):
        return remplacer_base(url_psycopg(principale), "postgres")
    return None


@pytest.fixture(scope="session")
def url_base_test() -> Iterator[str]:
    """Base dédiée à la session de test, migrée puis détruite."""
    url_admin = _url_administration()
    if url_admin is None:
        pytest.skip("DATABASE_URL ou DATABASE_ADMIN_URL absent : PostgreSQL requis")

    nom = f"test_{uuid4().hex[:12]}"
    try:
        connexion = psycopg.connect(url_admin, autocommit=True, connect_timeout=5)
    except psycopg.OperationalError as exc:  # pragma: no cover - dépend de l'hôte
        pytest.skip(f"PostgreSQL injoignable : {exc}")

    with connexion:
        connexion.execute(f'CREATE DATABASE "{nom}"')
        url = remplacer_base(url_admin, nom).replace("postgresql://", "postgresql+psycopg://", 1)
        try:
            command.upgrade(config_alembic(url), "head")
            yield url
        finally:
            connexion.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (nom,),
            )
            connexion.execute(f'DROP DATABASE IF EXISTS "{nom}"')


@pytest.fixture(scope="session")
def moteur(url_base_test: str) -> Iterator[Engine]:
    moteur = create_engine(url_base_test)
    yield moteur
    moteur.dispose()


@pytest.fixture
def session(moteur: Engine) -> Iterator[Session]:
    connexion = moteur.connect()
    transaction = connexion.begin()
    session = Session(bind=connexion, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connexion.close()


@pytest.fixture
def parametres() -> Parametres:
    return Parametres(
        environnement="test",
        secret_key=SECRET_KEY_TEST,
        database_url="postgresql+psycopg://ignore/ignore",
        origines_cors=["http://localhost:5173"],
    )


@pytest.fixture(autouse=True)
def _parametres_de_test(monkeypatch: pytest.MonkeyPatch, parametres: Parametres) -> None:
    """Force les paramètres de test partout où ils sont lus.

    `obtenir_parametres` est mis en cache par `lru_cache` : sans cette
    substitution, la clé de signature réelle serait utilisée et les jetons créés
    dans les tests ne seraient pas vérifiables.
    """
    for module in (
        "app.config",
        "app.core.securite",
        "app.routers.sante",
        "app.services.processus.authentifier",
    ):
        monkeypatch.setattr(f"{module}.obtenir_parametres", lambda: parametres, raising=False)


@pytest.fixture
def application(session: Session, parametres: Parametres) -> FastAPI:
    app = creer_application(parametres)
    # L'application partage la session du test : ses écritures sont annulées
    # avec la transaction externe.
    app.dependency_overrides[get_db] = lambda: session
    return app


@pytest.fixture
def client(application: FastAPI) -> Iterator[TestClient]:
    with TestClient(application) as client:
        yield client


# ---------------------------------------------------------------------------
# Fabriques de données
# ---------------------------------------------------------------------------
@pytest.fixture
def creer_compte(session: Session):
    """Crée un utilisateur persistant avec les rôles demandés."""
    compteur = {"n": 0}

    def _creer(
        *,
        email: str | None = None,
        roles: list[str] | None = None,
        manager_id=None,
        actif: bool = True,
        mot_de_passe: str = MOT_DE_PASSE_TEST,
    ) -> Utilisateur:
        compteur["n"] += 1
        adresse = email or f"compte{compteur['n']}@example.com"
        roles_modeles = RoleRepository(session).lister_par_codes(roles or ["COLLABORATEUR"])
        utilisateur = UtilisateurRepository(session).ajouter(
            Utilisateur(
                email=adresse,
                mot_de_passe_hash=hacher_mot_de_passe(mot_de_passe),
                nom=f"Nom{compteur['n']}",
                prenom=f"Prenom{compteur['n']}",
                manager_id=manager_id,
                actif=actif,
                roles=list(roles_modeles),
            )
        )
        session.flush()
        return utilisateur

    return _creer


@pytest.fixture
def entetes_de(client: TestClient):
    """En-tête d'autorisation pour un compte donné."""

    def _entetes(email: str, mot_de_passe: str = MOT_DE_PASSE_TEST) -> dict[str, str]:
        reponse = client.post("/auth/login", json={"email": email, "mot_de_passe": mot_de_passe})
        assert reponse.status_code == 200, reponse.text
        return {"Authorization": f"Bearer {reponse.json()['access_token']}"}

    return _entetes
