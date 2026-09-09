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
        assert corps["email"] == "jean@example.com"

    def test_le_jeton_ne_figure_pas_dans_le_corps(self, client: TestClient, creer_compte) -> None:
        creer_compte(email="corps@example.com")
        reponse = client.post(
            "/auth/login",
            json={"email": "corps@example.com", "mot_de_passe": MOT_DE_PASSE_TEST},
        )

        assert "access_token" not in reponse.text
        assert "mot_de_passe" not in reponse.text

    def test_le_cookie_est_httponly_et_samesite(self, client: TestClient, creer_compte) -> None:
        creer_compte(email="cookie@example.com")
        reponse = client.post(
            "/auth/login",
            json={"email": "cookie@example.com", "mot_de_passe": MOT_DE_PASSE_TEST},
        )

        entete = reponse.headers["set-cookie"].lower()
        assert "jeton=" in entete
        assert "httponly" in entete
        assert "samesite=strict" in entete
        assert "path=/" in entete

    def test_le_cookie_suffit_pour_les_appels_suivants(
        self, client: TestClient, creer_compte
    ) -> None:
        creer_compte(email="suite@example.com")
        client.post(
            "/auth/login",
            json={"email": "suite@example.com", "mot_de_passe": MOT_DE_PASSE_TEST},
        )

        # Aucun en-tête d'autorisation : seul le cookie est présenté.
        reponse = client.get("/auth/me")
        assert reponse.status_code == 200
        assert reponse.json()["email"] == "suite@example.com"

    def test_un_echec_ne_pose_aucun_cookie(self, client: TestClient, creer_compte) -> None:
        creer_compte(email="echec@example.com")
        reponse = client.post(
            "/auth/login", json={"email": "echec@example.com", "mot_de_passe": "faux"}
        )

        assert reponse.status_code == 401
        assert "set-cookie" not in reponse.headers

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


class TestDeconnexion:
    def test_la_deconnexion_efface_le_cookie(self, client: TestClient, creer_compte) -> None:
        creer_compte(email="sortie@example.com")
        client.post(
            "/auth/login",
            json={"email": "sortie@example.com", "mot_de_passe": MOT_DE_PASSE_TEST},
        )
        assert client.get("/auth/me").status_code == 200

        reponse = client.post("/auth/logout")

        assert reponse.status_code == 204
        assert client.get("/auth/me").status_code == 401

    def test_se_deconnecter_sans_session_aboutit(self, client: TestClient) -> None:
        # Un cookie expiré ne peut pas être effacé par le client : la route doit
        # répondre même sans session valide.
        assert client.post("/auth/logout").status_code == 204


class TestOrigine:
    def test_une_ecriture_depuis_une_autre_origine_est_refusee(
        self, client: TestClient, creer_compte
    ) -> None:
        creer_compte(email="csrf@example.com")
        client.post(
            "/auth/login",
            json={"email": "csrf@example.com", "mot_de_passe": MOT_DE_PASSE_TEST},
        )

        reponse = client.post("/auth/logout", headers={"Origin": "https://site-malveillant.test"})

        assert reponse.status_code == 403
        assert "Origine" in reponse.json()["message"]

    def test_une_ecriture_depuis_l_origine_du_front_est_acceptee(self, client: TestClient) -> None:
        reponse = client.post("/auth/logout", headers={"Origin": "http://localhost:5173"})
        assert reponse.status_code == 204

    def test_une_lecture_depuis_une_autre_origine_reste_possible(self, client: TestClient) -> None:
        # Une lecture ne modifie rien : c'est CORS qui décide si le navigateur
        # laissera la réponse être lue, pas ce contrôle.
        reponse = client.get("/health", headers={"Origin": "https://site-malveillant.test"})
        assert reponse.status_code != 403
