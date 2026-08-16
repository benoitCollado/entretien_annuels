"""Authentification de bout en bout — US-01."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import MOT_DE_PASSE_TEST

pytestmark = pytest.mark.integration


class TestConnexion:
    def test_connexion_reussie(self, client: TestClient, creer_compte) -> None:
        creer_compte(email="jean@example.com")
        reponse = client.post(
            "/auth/login",
            json={"email": "jean@example.com", "mot_de_passe": MOT_DE_PASSE_TEST},
        )
        assert reponse.status_code == 200
        corps = reponse.json()
        assert corps["token_type"] == "bearer"
        assert corps["expires_in"] > 0
        assert corps["access_token"]

    def test_adresse_insensible_a_la_casse(self, client: TestClient, creer_compte) -> None:
        creer_compte(email="jean2@example.com")
        reponse = client.post(
            "/auth/login",
            json={"email": "JEAN2@EXAMPLE.COM", "mot_de_passe": MOT_DE_PASSE_TEST},
        )
        assert reponse.status_code == 200

    def test_mauvais_mot_de_passe(self, client: TestClient, creer_compte) -> None:
        creer_compte(email="jean3@example.com")
        reponse = client.post(
            "/auth/login", json={"email": "jean3@example.com", "mot_de_passe": "faux"}
        )
        assert reponse.status_code == 401

    def test_message_identique_que_le_compte_existe_ou_non(
        self, client: TestClient, creer_compte
    ) -> None:
        """Pas d'énumération de comptes (§7.3) : la réponse ne doit pas
        permettre de savoir si l'adresse est connue."""
        creer_compte(email="connu@example.com")

        connu = client.post(
            "/auth/login", json={"email": "connu@example.com", "mot_de_passe": "faux"}
        )
        inconnu = client.post(
            "/auth/login", json={"email": "inconnu@example.com", "mot_de_passe": "faux"}
        )

        assert connu.status_code == inconnu.status_code == 401
        assert connu.json()["message"] == inconnu.json()["message"]

    def test_compte_desactive_refuse(self, client: TestClient, creer_compte) -> None:
        creer_compte(email="inactif@example.com", actif=False)
        reponse = client.post(
            "/auth/login",
            json={"email": "inactif@example.com", "mot_de_passe": MOT_DE_PASSE_TEST},
        )
        assert reponse.status_code == 401

    def test_champ_inconnu_refuse(self, client: TestClient) -> None:
        """`extra="forbid"` : un champ non prévu est une erreur, pas une donnée
        silencieusement ignorée."""
        reponse = client.post(
            "/auth/login",
            json={"email": "a@example.com", "mot_de_passe": "x", "admin": True},
        )
        assert reponse.status_code == 422


class TestProfil:
    def test_profil_de_l_utilisateur_connecte(
        self, client: TestClient, creer_compte, entetes_de
    ) -> None:
        creer_compte(email="rh@example.com", roles=["RH"])
        reponse = client.get("/auth/me", headers=entetes_de("rh@example.com"))

        assert reponse.status_code == 200
        corps = reponse.json()
        assert corps["email"] == "rh@example.com"
        assert [r["code"] for r in corps["roles"]] == ["RH"]
        assert "utilisateur:lire" in corps["permissions"]

    def test_le_hash_n_est_jamais_expose(
        self, client: TestClient, creer_compte, entetes_de
    ) -> None:
        """Le schéma de sortie décide de ce qui franchit la frontière HTTP."""
        creer_compte(email="discret@example.com")
        corps = client.get("/auth/me", headers=entetes_de("discret@example.com")).json()

        assert "mot_de_passe_hash" not in corps
        assert "version_jeton" not in corps

    def test_sans_jeton(self, client: TestClient) -> None:
        reponse = client.get("/auth/me")
        assert reponse.status_code == 401
        assert reponse.headers.get("WWW-Authenticate") == "Bearer"

    def test_jeton_invalide(self, client: TestClient) -> None:
        reponse = client.get("/auth/me", headers={"Authorization": "Bearer n.importe.quoi"})
        assert reponse.status_code == 401


class TestRevocation:
    def test_incrementer_la_version_invalide_le_jeton(
        self, client: TestClient, session: Session, creer_compte, entetes_de
    ) -> None:
        """Mécanisme de révocation sans denylist (§7.3).

        C'est ce test qui prouve qu'un compte désactivé perd l'accès
        immédiatement, sans attendre l'expiration de son jeton.
        """
        compte = creer_compte(email="revoque@example.com")
        entetes = entetes_de("revoque@example.com")

        assert client.get("/auth/me", headers=entetes).status_code == 200

        compte.version_jeton += 1
        session.flush()

        reponse = client.get("/auth/me", headers=entetes)
        assert reponse.status_code == 401
        assert "révoquée" in reponse.json()["message"]

    def test_desactiver_le_compte_coupe_l_acces(
        self, client: TestClient, session: Session, creer_compte, entetes_de
    ) -> None:
        compte = creer_compte(email="coupe@example.com")
        entetes = entetes_de("coupe@example.com")

        compte.actif = False
        session.flush()

        assert client.get("/auth/me", headers=entetes).status_code == 401
