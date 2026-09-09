from __future__ import annotations

import os

MOT_DE_PASSE_TEST = "MotDePasseDeTest2026!"
SECRET_KEY_TEST = "cle-de-test-de-plus-de-32-caracteres-ok"

os.environ.setdefault("SECRET_KEY", SECRET_KEY_TEST)
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://ignore:ignore@localhost:5432/ignore")

from collections.abc import Iterator  # noqa: E402
from uuid import uuid4  # noqa: E402

import psycopg  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import Engine, create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.config import Parametres  # noqa: E402
from app.core.dependances import get_db  # noqa: E402
from app.core.securite import creer_jeton, hacher_mot_de_passe  # noqa: E402
from app.main import creer_application  # noqa: E402
from app.models.utilisateur import Utilisateur  # noqa: E402
from app.repositories.role_repository import RoleRepository  # noqa: E402
from app.repositories.utilisateur_repository import UtilisateurRepository  # noqa: E402
from tests.migrations.conftest import (  # noqa: E402
    config_alembic,
    remplacer_base,
    url_psycopg,
)


def _url_administration() -> str | None:
    if admin := os.environ.get("DATABASE_ADMIN_URL"):
        return url_psycopg(admin)
    if principale := os.environ.get("DATABASE_URL"):
        return remplacer_base(url_psycopg(principale), "postgres")
    return None


@pytest.fixture(scope="session")
def url_base_test() -> Iterator[str]:
    url_admin = _url_administration()
    if url_admin is None:
        pytest.skip("DATABASE_URL ou DATABASE_ADMIN_URL absent : PostgreSQL requis")

    nom = f"test_{uuid4().hex[:12]}"
    try:
        connexion = psycopg.connect(url_admin, autocommit=True, connect_timeout=5)
    except psycopg.OperationalError as exc:  # pragma: no cover
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
    for module in (
        "app.config",
        "app.core.securite",
        "app.routers.sante",
        "app.services.processus.authentifier",
    ):
        monkeypatch.setattr(f"{module}.obtenir_parametres", lambda: parametres, raising=False)


@pytest.fixture(autouse=True)
def _sans_rate_limit(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("rate_limit"):
        return
    monkeypatch.setattr("app.core.rate_limit.exiger_sous_limite", lambda *a, **k: None)
    monkeypatch.setattr("app.core.rate_limit.reinitialiser", lambda *a, **k: None)


@pytest.fixture(autouse=True)
def _fabrique_de_sessions_de_test(monkeypatch: pytest.MonkeyPatch, session: Session) -> None:
    fabrique = sessionmaker(bind=session.connection(), join_transaction_mode="create_savepoint")
    monkeypatch.setattr("app.database.obtenir_fabrique_sessions", lambda: fabrique)


@pytest.fixture
def application(session: Session, parametres: Parametres) -> FastAPI:
    app = creer_application(parametres)

    def session_de_test() -> Iterator[Session]:
        point = session.begin_nested()
        try:
            yield session
            point.commit()
        except Exception:
            point.rollback()
            raise

    app.dependency_overrides[get_db] = session_de_test
    return app


@pytest.fixture
def client(application: FastAPI) -> Iterator[TestClient]:
    with TestClient(application) as client:
        yield client


@pytest.fixture
def creer_compte(session: Session):
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
def entetes_de(session: Session):
    """Jeton d'un compte, présenté en en-tête.

    La connexion pose désormais un cookie sur le client, partagé par tous les
    appels. Frapper /auth/login ici ferait qu'un test manipulant plusieurs
    comptes verrait le dernier connecté l'emporter sur l'en-tête attendu. Le
    jeton est donc forgé directement, ce qui garde chaque en-tête indépendant.
    """

    def _entetes(email: str, mot_de_passe: str = MOT_DE_PASSE_TEST) -> dict[str, str]:
        utilisateur = UtilisateurRepository(session).get_par_email(email)
        assert utilisateur is not None, f"compte introuvable : {email}"
        jeton, _ = creer_jeton(utilisateur.id, utilisateur.version_jeton)
        return {"Authorization": f"Bearer {jeton}"}

    return _entetes
