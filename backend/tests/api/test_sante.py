"""Sondes de disponibilité."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_liveness(client: TestClient) -> None:
    reponse = client.get("/health")
    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "ok"


def test_liveness_ne_demande_pas_d_authentification(client: TestClient) -> None:
    """Docker interroge cette route sans jeton : la protéger rendrait le
    healthcheck du conteneur inopérant."""
    assert "Authorization" not in client.headers
    assert client.get("/health").status_code == 200


def test_readiness_expose_l_etat_des_dependances(client: TestClient) -> None:
    corps = client.get("/health/ready").json()
    assert corps["base"] == "ok"
    assert corps["statut"] in {"ok", "degrade"}
