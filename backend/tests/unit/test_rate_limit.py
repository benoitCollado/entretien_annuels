from __future__ import annotations

import pytest
import redis

from app.core import rate_limit


def test_la_cle_distingue_ip_et_adresse() -> None:
    assert rate_limit.cle_connexion("10.0.0.1", "a@x.fr") != rate_limit.cle_connexion(
        "10.0.0.2", "a@x.fr"
    )
    assert rate_limit.cle_connexion("10.0.0.1", "a@x.fr") != rate_limit.cle_connexion(
        "10.0.0.1", "b@x.fr"
    )
    assert rate_limit.cle_connexion("10.0.0.1", "A@X.FR") == rate_limit.cle_connexion(
        "10.0.0.1", "a@x.fr"
    )


def test_ip_absente_donne_une_cle_stable() -> None:
    assert rate_limit.cle_connexion(None, "a@x.fr") == rate_limit.cle_connexion(None, "a@x.fr")
    assert "inconnue" in rate_limit.cle_connexion(None, "a@x.fr")


def test_absence_de_redis_laisse_passer(monkeypatch: pytest.MonkeyPatch) -> None:

    def tombe_en_panne() -> redis.Redis:
        raise redis.ConnectionError("Redis simulé indisponible")

    monkeypatch.setattr(rate_limit, "obtenir_client", tombe_en_panne)

    rate_limit.exiger_sous_limite("cle:test", maximum=0, fenetre_secondes=60)
    rate_limit.reinitialiser("cle:test")
    assert rate_limit.cache_repond() is False
