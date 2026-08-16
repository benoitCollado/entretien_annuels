"""Administration des comptes de bout en bout — US-02.

Deux mécanismes distincts y sont éprouvés (§6.1) :
  - le **RBAC** : « ce rôle peut-il faire cette action ? » ;
  - la **portée** : « cet utilisateur-là, précisément ? ».
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.conftest import MOT_DE_PASSE_TEST

pytestmark = pytest.mark.integration

NOUVEAU = {
    "email": "nouveau@example.com",
    "mot_de_passe": "UnMotDePasseAssezLong2026!",
    "nom": "Nouveau",
    "prenom": "Compte",
    "roles": ["COLLABORATEUR"],
}


class TestRbac:
    def test_admin_peut_lister(self, client: TestClient, creer_compte, entetes_de) -> None:
        creer_compte(email="admin@example.com", roles=["ADMIN"])
        reponse = client.get("/utilisateurs", headers=entetes_de("admin@example.com"))
        assert reponse.status_code == 200
        assert reponse.json()["total"] >= 1

    def test_collaborateur_ne_peut_pas_lister(
        self, client: TestClient, creer_compte, entetes_de
    ) -> None:
        creer_compte(email="simple@example.com", roles=["COLLABORATEUR"])
        reponse = client.get("/utilisateurs", headers=entetes_de("simple@example.com"))
        assert reponse.status_code == 403
        assert "utilisateur:lire" in reponse.json()["message"]

    def test_manager_ne_peut_pas_creer(self, client: TestClient, creer_compte, entetes_de) -> None:
        """Un manager consulte son équipe mais n'administre pas les comptes."""
        creer_compte(email="chef@example.com", roles=["MANAGER"])
        reponse = client.post("/utilisateurs", json=NOUVEAU, headers=entetes_de("chef@example.com"))
        assert reponse.status_code == 403

    def test_sans_jeton(self, client: TestClient) -> None:
        assert client.get("/utilisateurs").status_code == 401


class TestPortee:
    def test_manager_ne_voit_que_son_equipe(
        self, client: TestClient, creer_compte, entetes_de
    ) -> None:
        """La restriction est appliquée en SQL, pas après coup en Python."""
        manager = creer_compte(email="chef2@example.com", roles=["MANAGER"])
        creer_compte(email="membre1@example.com", manager_id=manager.id)
        creer_compte(email="membre2@example.com", manager_id=manager.id)
        creer_compte(email="etranger@example.com")

        corps = client.get("/utilisateurs", headers=entetes_de("chef2@example.com")).json()
        adresses = {u["email"] for u in corps["elements"]}

        assert corps["total"] == 2
        assert adresses == {"membre1@example.com", "membre2@example.com"}
        assert "etranger@example.com" not in adresses

    def test_rh_voit_tout_le_monde(self, client: TestClient, creer_compte, entetes_de) -> None:
        creer_compte(email="rh2@example.com", roles=["RH"])
        creer_compte(email="autre@example.com")

        corps = client.get("/utilisateurs", headers=entetes_de("rh2@example.com")).json()
        assert {"rh2@example.com", "autre@example.com"} <= {u["email"] for u in corps["elements"]}


class TestCreation:
    def test_creation_par_un_rh(self, client: TestClient, creer_compte, entetes_de) -> None:
        creer_compte(email="rh3@example.com", roles=["RH"])
        reponse = client.post("/utilisateurs", json=NOUVEAU, headers=entetes_de("rh3@example.com"))

        assert reponse.status_code == 201, reponse.text
        corps = reponse.json()
        assert corps["email"] == "nouveau@example.com"
        assert [r["code"] for r in corps["roles"]] == ["COLLABORATEUR"]

        # Le compte créé peut se connecter immédiatement.
        connexion = client.post(
            "/auth/login",
            json={"email": "nouveau@example.com", "mot_de_passe": NOUVEAU["mot_de_passe"]},
        )
        assert connexion.status_code == 200

    def test_adresse_deja_utilisee(self, client: TestClient, creer_compte, entetes_de) -> None:
        creer_compte(email="rh4@example.com", roles=["RH"])
        creer_compte(email="occupe@example.com")

        reponse = client.post(
            "/utilisateurs",
            json={**NOUVEAU, "email": "occupe@example.com"},
            headers=entetes_de("rh4@example.com"),
        )
        assert reponse.status_code == 409

    def test_role_inconnu(self, client: TestClient, creer_compte, entetes_de) -> None:
        creer_compte(email="rh5@example.com", roles=["RH"])
        reponse = client.post(
            "/utilisateurs",
            json={**NOUVEAU, "roles": ["SUPERVISEUR"]},
            headers=entetes_de("rh5@example.com"),
        )
        assert reponse.status_code == 422

    def test_rh_ne_peut_pas_creer_un_admin(
        self, client: TestClient, creer_compte, entetes_de
    ) -> None:
        """Escalade de privilèges : le RH possède `utilisateur:creer`, mais ne
        doit pas pouvoir fabriquer un administrateur."""
        creer_compte(email="rh6@example.com", roles=["RH"])
        reponse = client.post(
            "/utilisateurs",
            json={**NOUVEAU, "roles": ["ADMIN"]},
            headers=entetes_de("rh6@example.com"),
        )
        assert reponse.status_code == 403

    def test_mot_de_passe_trop_court(self, client: TestClient, creer_compte, entetes_de) -> None:
        creer_compte(email="rh7@example.com", roles=["RH"])
        reponse = client.post(
            "/utilisateurs",
            json={**NOUVEAU, "mot_de_passe": "court"},
            headers=entetes_de("rh7@example.com"),
        )
        assert reponse.status_code == 422


class TestModification:
    def test_modification_partielle(self, client: TestClient, creer_compte, entetes_de) -> None:
        """Seuls les champs transmis sont modifiés : `poste` ne doit pas être
        effacé parce qu'il n'a pas été fourni."""
        creer_compte(email="rh8@example.com", roles=["RH"])
        cible = creer_compte(email="cible@example.com")
        cible.poste = "Technicien"

        reponse = client.patch(
            f"/utilisateurs/{cible.id}",
            json={"nom": "NouveauNom"},
            headers=entetes_de("rh8@example.com"),
        )

        assert reponse.status_code == 200
        assert reponse.json()["nom"] == "NouveauNom"
        assert reponse.json()["poste"] == "Technicien"

    def test_desactivation(self, client: TestClient, creer_compte, entetes_de) -> None:
        creer_compte(email="rh9@example.com", roles=["RH"])
        cible = creer_compte(email="adesactiver@example.com")

        reponse = client.patch(
            f"/utilisateurs/{cible.id}",
            json={"actif": False},
            headers=entetes_de("rh9@example.com"),
        )
        assert reponse.status_code == 200
        assert reponse.json()["actif"] is False

        # Le compte désactivé ne peut plus se connecter.
        connexion = client.post(
            "/auth/login",
            json={"email": "adesactiver@example.com", "mot_de_passe": MOT_DE_PASSE_TEST},
        )
        assert connexion.status_code == 401

    def test_utilisateur_introuvable(self, client: TestClient, creer_compte, entetes_de) -> None:
        creer_compte(email="rh10@example.com", roles=["RH"])
        reponse = client.patch(
            "/utilisateurs/01930000-0000-7000-8000-000000000000",
            json={"nom": "X"},
            headers=entetes_de("rh10@example.com"),
        )
        assert reponse.status_code == 404

    def test_cycle_hierarchique_refuse(self, client: TestClient, creer_compte, entetes_de) -> None:
        """Cas non couvrable par une contrainte CHECK."""
        creer_compte(email="rh11@example.com", roles=["RH"])
        chef = creer_compte(email="chef3@example.com")
        membre = creer_compte(email="membre3@example.com", manager_id=chef.id)

        reponse = client.patch(
            f"/utilisateurs/{chef.id}",
            json={"manager_id": str(membre.id)},
            headers=entetes_de("rh11@example.com"),
        )
        assert reponse.status_code == 422
        assert "cycle" in reponse.json()["message"]


class TestRolesEtArchivage:
    def test_attribution_de_roles(self, client: TestClient, creer_compte, entetes_de) -> None:
        creer_compte(email="admin2@example.com", roles=["ADMIN"])
        cible = creer_compte(email="promu@example.com")

        reponse = client.put(
            f"/utilisateurs/{cible.id}/roles",
            json={"roles": ["MANAGER", "COLLABORATEUR"]},
            headers=entetes_de("admin2@example.com"),
        )
        assert reponse.status_code == 200
        assert {r["code"] for r in reponse.json()["roles"]} == {"MANAGER", "COLLABORATEUR"}

    def test_modifier_ses_propres_roles_est_refuse(
        self, client: TestClient, creer_compte, entetes_de
    ) -> None:
        admin = creer_compte(email="admin3@example.com", roles=["ADMIN"])
        reponse = client.put(
            f"/utilisateurs/{admin.id}/roles",
            json={"roles": ["ADMIN"]},
            headers=entetes_de("admin3@example.com"),
        )
        assert reponse.status_code == 403

    def test_archivage_est_une_desactivation_pas_une_suppression(
        self, client: TestClient, creer_compte, entetes_de
    ) -> None:
        creer_compte(email="admin4@example.com", roles=["ADMIN"])
        cible = creer_compte(email="aarchiver@example.com")

        reponse = client.delete(
            f"/utilisateurs/{cible.id}", headers=entetes_de("admin4@example.com")
        )
        assert reponse.status_code == 200
        assert reponse.json()["actif"] is False

        # Le compte disparaît des listes mais existe toujours en base.
        liste = client.get("/utilisateurs", headers=entetes_de("admin4@example.com")).json()
        assert "aarchiver@example.com" not in {u["email"] for u in liste["elements"]}

    def test_rh_ne_peut_pas_archiver(self, client: TestClient, creer_compte, entetes_de) -> None:
        """`utilisateur:archiver` n'est accordée qu'à l'administrateur."""
        creer_compte(email="rh12@example.com", roles=["RH"])
        cible = creer_compte(email="protege@example.com")

        reponse = client.delete(f"/utilisateurs/{cible.id}", headers=entetes_de("rh12@example.com"))
        assert reponse.status_code == 403
