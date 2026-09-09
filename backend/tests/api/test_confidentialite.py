from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import Contexte

pytestmark = pytest.mark.integration


class TestScenarioDemonstration:
    def test_1_le_collaborateur_saisit_son_brouillon(
        self, client: TestClient, contexte: Contexte, repondre
    ) -> None:
        repondre(contexte)
        fiche = client.get(
            f"/entretiens/{contexte.entretien_id}", headers=contexte.entetes_collaborateur
        ).json()
        assert fiche["statut"] == "PREPARATION"

    def test_2_le_manager_ne_voit_aucune_reponse(
        self, client: TestClient, contexte: Contexte, repondre
    ) -> None:
        repondre(contexte)
        vue = client.get(
            f"/entretiens/{contexte.entretien_id}/questionnaire",
            headers=contexte.entetes_manager,
        )

        assert vue.status_code == 200
        assert vue.json()["reponses"] == []
        assert vue.json()["contenu_masque"] is True
        assert len(vue.json()["sections"][0]["questions"]) == 3

    def test_3_le_collaborateur_soumet(
        self, client: TestClient, contexte: Contexte, soumettre
    ) -> None:
        soumettre(contexte)
        fiche = client.get(
            f"/entretiens/{contexte.entretien_id}", headers=contexte.entetes_collaborateur
        ).json()
        assert fiche["statut"] == "SOUMIS_COLLABORATEUR"
        assert fiche["soumis_collaborateur_le"] is not None

    def test_4_le_manager_voit_alors_les_reponses(
        self, client: TestClient, contexte: Contexte, soumettre
    ) -> None:
        soumettre(contexte)
        vue = client.get(
            f"/entretiens/{contexte.entretien_id}/questionnaire",
            headers=contexte.entetes_manager,
        ).json()

        assert len(vue["reponses"]) == 2
        assert any("Projet livré" in str(r["valeur"]) for r in vue["reponses"])

    def test_5_le_rh_voit_l_avancement_mais_aucun_contenu(
        self, client: TestClient, contexte: Contexte, soumettre
    ) -> None:
        soumettre(contexte)

        tableau = client.get(
            f"/tableau-bord/campagnes/{contexte.campagne_id}", headers=contexte.entetes_rh
        ).json()
        assert tableau["total"] == 1
        assert {x["statut"] for x in tableau["par_statut"]} == {"SOUMIS_COLLABORATEUR"}
        assert "reponses" not in tableau

        contenu = client.get(
            f"/entretiens/{contexte.entretien_id}/questionnaire", headers=contexte.entetes_rh
        ).json()
        assert contenu["reponses"] == []


class TestPortee:
    def test_un_tiers_est_refuse(self, client: TestClient, contexte: Contexte) -> None:
        reponse = client.get(
            f"/entretiens/{contexte.entretien_id}/questionnaire",
            headers=contexte.entetes_tiers,
        )
        assert reponse.status_code == 403

    def test_le_refus_ne_laisse_aucune_ecriture_derriere_lui(
        self, client: TestClient, contexte: Contexte
    ) -> None:
        client.get(
            f"/entretiens/{contexte.entretien_id}/questionnaire",
            headers=contexte.entetes_tiers,
        )
        apres = client.get(f"/entretiens/{contexte.entretien_id}", headers=contexte.entetes_manager)
        assert apres.status_code == 200
        assert apres.json()["statut"] == "PLANIFIE"

    def test_un_tiers_ne_voit_pas_l_entretien_en_liste(
        self, client: TestClient, contexte: Contexte
    ) -> None:
        liste = client.get("/entretiens", headers=contexte.entetes_tiers).json()
        assert contexte.entretien_id not in {e["id"] for e in liste["elements"]}

    def test_le_collaborateur_voit_le_sien(self, client: TestClient, contexte: Contexte) -> None:
        liste = client.get("/entretiens", headers=contexte.entetes_collaborateur).json()
        assert contexte.entretien_id in {e["id"] for e in liste["elements"]}


class TestEcriture:
    def test_le_manager_ne_peut_pas_repondre_a_la_place(
        self, client: TestClient, contexte: Contexte
    ) -> None:
        reponse = client.put(
            f"/entretiens/{contexte.entretien_id}/reponses",
            json={
                "reponses": [
                    {"question_id": contexte.questions["COLLABORATEUR"], "valeur": {"contenu": "x"}}
                ]
            },
            headers=contexte.entetes_manager,
        )
        assert reponse.status_code == 403

    def test_la_soumission_est_irreversible(
        self, client: TestClient, contexte: Contexte, soumettre
    ) -> None:
        soumettre(contexte)
        reponse = client.put(
            f"/entretiens/{contexte.entretien_id}/reponses",
            json={
                "reponses": [
                    {
                        "question_id": contexte.questions["COLLABORATEUR"],
                        "valeur": {"contenu": "modifié après coup"},
                    }
                ]
            },
            headers=contexte.entetes_collaborateur,
        )
        assert reponse.status_code == 403

    def test_soumission_refusee_si_obligatoire_manquante(
        self, client: TestClient, contexte: Contexte
    ) -> None:
        client.put(
            f"/entretiens/{contexte.entretien_id}/reponses",
            json={
                "reponses": [{"question_id": contexte.questions["PARTAGEE"], "valeur": {"note": 3}}]
            },
            headers=contexte.entetes_collaborateur,
        )
        reponse = client.post(
            f"/entretiens/{contexte.entretien_id}/soumettre",
            headers=contexte.entetes_collaborateur,
        )
        assert reponse.status_code == 422
        assert "obligatoires" in reponse.json()["message"]
        assert reponse.json()["details"][0]["libelle"] == "Vos réussites ?"

    def test_la_question_manager_n_est_pas_exigee_du_collaborateur(
        self, client: TestClient, contexte: Contexte, repondre
    ) -> None:
        repondre(contexte)
        assert (
            client.post(
                f"/entretiens/{contexte.entretien_id}/soumettre",
                headers=contexte.entetes_collaborateur,
            ).status_code
            == 200
        )

    def test_valeur_incoherente_avec_le_type(self, client: TestClient, contexte: Contexte) -> None:
        reponse = client.put(
            f"/entretiens/{contexte.entretien_id}/reponses",
            json={
                "reponses": [{"question_id": contexte.questions["PARTAGEE"], "valeur": {"note": 9}}]
            },
            headers=contexte.entetes_collaborateur,
        )
        assert reponse.status_code == 422

    def test_question_d_un_autre_entretien_refusee(
        self, client: TestClient, contexte: Contexte
    ) -> None:
        reponse = client.put(
            f"/entretiens/{contexte.entretien_id}/reponses",
            json={
                "reponses": [
                    {
                        "question_id": "01930000-0000-7000-8000-000000000000",
                        "valeur": {"contenu": "x"},
                    }
                ]
            },
            headers=contexte.entetes_collaborateur,
        )
        assert reponse.status_code == 422
