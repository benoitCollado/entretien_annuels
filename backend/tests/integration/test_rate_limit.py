from __future__ import annotations

from collections.abc import Iterator

import pytest
import redis
from fastapi.testclient import TestClient

from app.config import Parametres
from app.core import rate_limit

pytestmark = [pytest.mark.integration, pytest.mark.rate_limit]

EMAIL = "limite@example.com"
MAUVAIS = "mot-de-passe-incorrect"


@pytest.fixture(autouse=True)
def _redis_propre(parametres: Parametres) -> Iterator[None]:
    rate_limit.obtenir_client.cache_clear()
    try:
        client = rate_limit.obtenir_client()
        client.ping()
    except redis.RedisError as exc:  # pragma: no cover
        pytest.skip(f"Redis injoignable : {exc}")

    cle = rate_limit.cle_connexion("testclient", EMAIL)
    client.delete(cle)
    yield
    client.delete(cle)
    rate_limit.obtenir_client.cache_clear()


def test_le_seuil_bloque_les_tentatives(
    client: TestClient, creer_compte, parametres: Parametres
) -> None:
    creer_compte(email=EMAIL)
    maximum = parametres.connexion_tentatives_max

    for tentative in range(maximum):
        reponse = client.post("/auth/login", json={"email": EMAIL, "mot_de_passe": MAUVAIS})
        assert reponse.status_code == 401, f"tentative {tentative + 1} : {reponse.text}"

    depassement = client.post("/auth/login", json={"email": EMAIL, "mot_de_passe": MAUVAIS})
    assert depassement.status_code == 429
    assert "tentatives" in depassement.json()["message"].lower()


def test_une_connexion_reussie_remet_le_compteur_a_zero(
    client: TestClient, creer_compte, parametres: Parametres
) -> None:
    from tests.conftest import MOT_DE_PASSE_TEST

    creer_compte(email=EMAIL)

    for _ in range(parametres.connexion_tentatives_max - 1):
        client.post("/auth/login", json={"email": EMAIL, "mot_de_passe": MAUVAIS})

    reussite = client.post("/auth/login", json={"email": EMAIL, "mot_de_passe": MOT_DE_PASSE_TEST})
    assert reussite.status_code == 200

    apres = client.post("/auth/login", json={"email": EMAIL, "mot_de_passe": MAUVAIS})
    assert apres.status_code == 401
