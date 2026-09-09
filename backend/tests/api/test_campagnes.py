from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

STRUCTURE = {
    "sections": [
        {
            "titre": "Bilan",
            "questions": [
                {
                    "libelle": "Vos réussites ?",
                    "type_question": "texte_libre",
                    "cible": "COLLABORATEUR",
                }
            ],
        }
    ]
}


@pytest.fixture
def entetes_rh(creer_compte, entetes_de) -> dict[str, str]:
    creer_compte(email="rh.campagnes@example.com", roles=["RH"])
    return entetes_de("rh.campagnes@example.com")


@pytest.fixture
def trame_publiee(client: TestClient, entetes_rh) -> str:
    identifiant = client.post(
        "/templates",
        json={"nom": "Trame campagne", "type_entretien": "ANNUEL"},
        headers=entetes_rh,
    ).json()["id"]
    client.put(f"/templates/{identifiant}/structure", json=STRUCTURE, headers=entetes_rh)
    client.post(f"/templates/{identifiant}/publier", headers=entetes_rh)
    return identifiant


def _campagne(annee: int = 2040, **surcharges) -> dict:
    base = {
        "libelle": f"Campagne {annee}",
        "annee": annee,
        "type_entretien": "ANNUEL",
        "date_ouverture": f"{annee}-01-01",
        "date_limite": f"{annee}-12-31",
    }
    return {**base, **surcharges}


class TestRbac:
    def test_collaborateur_refuse(self, client: TestClient, creer_compte, entetes_de) -> None:
        creer_compte(email="collab.c@example.com", roles=["COLLABORATEUR"])
        reponse = client.get("/campagnes", headers=entetes_de("collab.c@example.com"))
        assert reponse.status_code == 403

    def test_manager_consulte_mais_n_ouvre_pas(
        self, client: TestClient, creer_compte, entetes_de, entetes_rh
    ) -> None:
        creer_compte(email="chef.c@example.com", roles=["MANAGER"])
        entetes = entetes_de("chef.c@example.com")
        identifiant = client.post("/campagnes", json=_campagne(2041), headers=entetes_rh).json()[
            "id"
        ]

        assert client.get("/campagnes", headers=entetes).status_code == 200
        assert client.post(f"/campagnes/{identifiant}/ouvrir", headers=entetes).status_code == 403


class TestCreation:
    def test_creation_en_brouillon(self, client: TestClient, entetes_rh) -> None:
        reponse = client.post("/campagnes", json=_campagne(2042), headers=entetes_rh)
        assert reponse.status_code == 201
        corps = reponse.json()
        assert corps["statut"] == "BROUILLON"
        assert corps["accepte_des_entretiens"] is False

    def test_dates_incoherentes(self, client: TestClient, entetes_rh) -> None:
        reponse = client.post(
            "/campagnes",
            json=_campagne(2043, date_ouverture="2043-12-31", date_limite="2043-01-01"),
            headers=entetes_rh,
        )
        assert reponse.status_code == 422

    def test_annee_incoherente_avec_l_ouverture(self, client: TestClient, entetes_rh) -> None:
        reponse = client.post(
            "/campagnes",
            json=_campagne(2044, date_ouverture="2045-01-01", date_limite="2045-12-31"),
            headers=entetes_rh,
        )
        assert reponse.status_code == 422
        assert "2044" in reponse.json()["message"]

    def test_doublon_annee_et_type(self, client: TestClient, entetes_rh) -> None:
        client.post("/campagnes", json=_campagne(2046), headers=entetes_rh)
        reponse = client.post("/campagnes", json=_campagne(2046), headers=entetes_rh)
        assert reponse.status_code == 409

    def test_deux_types_la_meme_annee_coexistent(self, client: TestClient, entetes_rh) -> None:
        client.post("/campagnes", json=_campagne(2047), headers=entetes_rh)
        reponse = client.post(
            "/campagnes",
            json=_campagne(2047, type_entretien="PROFESSIONNEL", libelle="Pro 2047"),
            headers=entetes_rh,
        )
        assert reponse.status_code == 201


class TestCycleDeVie:
    def test_ouverture(self, client: TestClient, entetes_rh, trame_publiee) -> None:
        annee = date.today().year + 1
        identifiant = client.post("/campagnes", json=_campagne(annee), headers=entetes_rh).json()[
            "id"
        ]

        reponse = client.post(f"/campagnes/{identifiant}/ouvrir", headers=entetes_rh)
        assert reponse.status_code == 200
        assert reponse.json()["statut"] == "OUVERTE"
        assert reponse.json()["accepte_des_entretiens"] is True
        assert reponse.json()["ouverte_le"] is not None

    def test_ouverture_sans_trame_publiee_refusee(self, client: TestClient, entetes_rh) -> None:
        annee = date.today().year + 1
        identifiant = client.post(
            "/campagnes",
            json=_campagne(annee, type_entretien="PROFESSIONNEL", libelle="Pro"),
            headers=entetes_rh,
        ).json()["id"]

        reponse = client.post(f"/campagnes/{identifiant}/ouvrir", headers=entetes_rh)
        assert reponse.status_code == 422
        assert "PROFESSIONNEL" in reponse.json()["message"]

    def test_ouverture_d_une_campagne_echue_refusee(
        self, client: TestClient, entetes_rh, trame_publiee
    ) -> None:
        passe = date.today() - timedelta(days=400)
        identifiant = client.post(
            "/campagnes",
            json={
                "libelle": "Passée",
                "annee": passe.year,
                "type_entretien": "ANNUEL",
                "date_ouverture": str(passe),
                "date_limite": str(passe + timedelta(days=30)),
            },
            headers=entetes_rh,
        ).json()["id"]

        reponse = client.post(f"/campagnes/{identifiant}/ouvrir", headers=entetes_rh)
        assert reponse.status_code == 422
        assert "passée" in reponse.json()["message"]

    def test_cloture_definitive(self, client: TestClient, entetes_rh, trame_publiee) -> None:
        annee = date.today().year + 2
        identifiant = client.post("/campagnes", json=_campagne(annee), headers=entetes_rh).json()[
            "id"
        ]
        client.post(f"/campagnes/{identifiant}/ouvrir", headers=entetes_rh)

        cloture = client.post(f"/campagnes/{identifiant}/cloturer", headers=entetes_rh)
        assert cloture.status_code == 200
        assert cloture.json()["statut"] == "CLOTUREE"
        assert cloture.json()["accepte_des_entretiens"] is False

        assert (
            client.post(f"/campagnes/{identifiant}/ouvrir", headers=entetes_rh).status_code == 409
        )

    def test_double_ouverture_refusee(self, client: TestClient, entetes_rh, trame_publiee) -> None:
        annee = date.today().year + 3
        identifiant = client.post("/campagnes", json=_campagne(annee), headers=entetes_rh).json()[
            "id"
        ]
        client.post(f"/campagnes/{identifiant}/ouvrir", headers=entetes_rh)
        assert (
            client.post(f"/campagnes/{identifiant}/ouvrir", headers=entetes_rh).status_code == 409
        )


class TestConsultation:
    def test_filtre_par_annee(self, client: TestClient, entetes_rh) -> None:
        client.post("/campagnes", json=_campagne(2050), headers=entetes_rh)
        corps = client.get("/campagnes?annee=2050", headers=entetes_rh).json()
        assert corps["total"] == 1
        assert corps["elements"][0]["annee"] == 2050

    def test_campagne_introuvable(self, client: TestClient, entetes_rh) -> None:
        assert (
            client.get(
                "/campagnes/01930000-0000-7000-8000-000000000000", headers=entetes_rh
            ).status_code
            == 404
        )
