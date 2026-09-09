from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import Contexte
from tests.lecture_pdf import texte_du_pdf

pytestmark = pytest.mark.integration


@pytest.fixture
def realise(client: TestClient, contexte: Contexte, soumettre):
    soumettre(contexte)
    client.post(f"/entretiens/{contexte.entretien_id}/revue", headers=contexte.entetes_manager)
    client.post(
        f"/entretiens/{contexte.entretien_id}/synthese",
        json={"contenu": "Année satisfaisante, objectifs tenus."},
        headers=contexte.entetes_manager,
    )
    reponse = client.post(
        f"/entretiens/{contexte.entretien_id}/cloturer-echange",
        headers=contexte.entetes_manager,
    )
    assert reponse.status_code == 200, reponse.text
    return contexte


@pytest.fixture
def signe(client: TestClient, realise: Contexte):
    client.post(
        f"/entretiens/{realise.entretien_id}/signer",
        json={},
        headers=realise.entetes_collaborateur,
    )
    reponse = client.post(
        f"/entretiens/{realise.entretien_id}/signer", json={}, headers=realise.entetes_manager
    )
    assert reponse.status_code == 200, reponse.text
    return realise


class TestDoubleSignature:
    def test_une_seule_signature_ne_change_pas_le_statut(
        self, client: TestClient, realise: Contexte
    ) -> None:
        reponse = client.post(
            f"/entretiens/{realise.entretien_id}/signer",
            json={},
            headers=realise.entetes_collaborateur,
        )
        assert reponse.status_code == 200
        assert reponse.json()["statut"] == "ENTRETIEN_REALISE"
        assert reponse.json()["soumis_collaborateur_le"] is not None

    def test_la_seconde_signature_bascule_en_signe(
        self, client: TestClient, signe: Contexte
    ) -> None:
        fiche = client.get(
            f"/entretiens/{signe.entretien_id}", headers=signe.entetes_manager
        ).json()
        assert fiche["statut"] == "SIGNE"

    def test_l_ordre_des_signatures_est_indifferent(
        self, client: TestClient, realise: Contexte
    ) -> None:
        client.post(
            f"/entretiens/{realise.entretien_id}/signer",
            json={},
            headers=realise.entetes_manager,
        )
        reponse = client.post(
            f"/entretiens/{realise.entretien_id}/signer",
            json={},
            headers=realise.entetes_collaborateur,
        )
        assert reponse.json()["statut"] == "SIGNE"

    def test_resigner_est_refuse(self, client: TestClient, realise: Contexte) -> None:
        client.post(
            f"/entretiens/{realise.entretien_id}/signer",
            json={},
            headers=realise.entetes_collaborateur,
        )
        reponse = client.post(
            f"/entretiens/{realise.entretien_id}/signer",
            json={},
            headers=realise.entetes_collaborateur,
        )
        assert reponse.status_code == 409
        assert "déjà signé" in reponse.json()["message"]

    def test_un_tiers_ne_signe_pas(self, client: TestClient, realise: Contexte) -> None:
        reponse = client.post(
            f"/entretiens/{realise.entretien_id}/signer",
            json={},
            headers=realise.entetes_tiers,
        )
        assert reponse.status_code == 403

    def test_le_rh_ne_signe_pas_non_plus(self, client: TestClient, realise: Contexte) -> None:
        reponse = client.post(
            f"/entretiens/{realise.entretien_id}/signer", json={}, headers=realise.entetes_rh
        )
        assert reponse.status_code == 403

    def test_signature_impossible_avant_l_entretien(
        self, client: TestClient, contexte: Contexte, soumettre
    ) -> None:
        soumettre(contexte)
        reponse = client.post(
            f"/entretiens/{contexte.entretien_id}/signer",
            json={},
            headers=contexte.entetes_collaborateur,
        )
        assert reponse.status_code == 409


class TestDroitDeReserve:
    def test_le_collaborateur_peut_signer_avec_observation(
        self, client: TestClient, realise: Contexte
    ) -> None:
        reponse = client.post(
            f"/entretiens/{realise.entretien_id}/signer",
            json={"observation": "Je ne partage pas l'évaluation du point 2."},
            headers=realise.entetes_collaborateur,
        )
        assert reponse.status_code == 200
        assert "point 2" in reponse.json()["observation_collaborateur"]

        suite = client.post(
            f"/entretiens/{realise.entretien_id}/signer",
            json={},
            headers=realise.entetes_manager,
        )
        assert suite.json()["statut"] == "SIGNE"

    def test_le_manager_ne_formule_pas_d_observation(
        self, client: TestClient, realise: Contexte
    ) -> None:
        reponse = client.post(
            f"/entretiens/{realise.entretien_id}/signer",
            json={"observation": "Remarque du manager"},
            headers=realise.entetes_manager,
        )
        assert reponse.status_code == 422


class TestImmutabilite:
    def test_plus_aucun_commentaire_apres_signature(
        self, client: TestClient, signe: Contexte
    ) -> None:
        reponse = client.post(
            f"/entretiens/{signe.entretien_id}/questions/"
            f"{signe.questions['COLLABORATEUR']}/commentaires",
            json={"contenu": "Ajout tardif"},
            headers=signe.entetes_manager,
        )
        assert reponse.status_code in (403, 409)

    def test_plus_aucun_objectif_apres_signature(self, client: TestClient, signe: Contexte) -> None:
        reponse = client.post(
            f"/entretiens/{signe.entretien_id}/objectifs",
            json={"libelle": "Objectif ajouté après coup"},
            headers=signe.entetes_manager,
        )
        assert reponse.status_code == 409


class TestClotureRh:
    def test_le_rh_cloture_un_entretien_signe(self, client: TestClient, signe: Contexte) -> None:
        reponse = client.post(
            f"/entretiens/{signe.entretien_id}/cloturer", headers=signe.entetes_rh
        )
        assert reponse.status_code == 200
        assert reponse.json()["statut"] == "CLOTURE"

    def test_la_cloture_ouvre_le_contenu_au_rh(self, client: TestClient, signe: Contexte) -> None:
        avant = client.get(
            f"/entretiens/{signe.entretien_id}/questionnaire", headers=signe.entetes_rh
        ).json()
        assert avant["reponses"] == []

        client.post(f"/entretiens/{signe.entretien_id}/cloturer", headers=signe.entetes_rh)

        apres = client.get(
            f"/entretiens/{signe.entretien_id}/questionnaire", headers=signe.entetes_rh
        ).json()
        assert len(apres["reponses"]) == 2

    def test_un_manager_ne_cloture_pas(self, client: TestClient, signe: Contexte) -> None:
        reponse = client.post(
            f"/entretiens/{signe.entretien_id}/cloturer", headers=signe.entetes_manager
        )
        assert reponse.status_code == 403

    def test_cloture_impossible_avant_signature(
        self, client: TestClient, realise: Contexte
    ) -> None:
        reponse = client.post(
            f"/entretiens/{realise.entretien_id}/cloturer", headers=realise.entetes_rh
        )
        assert reponse.status_code == 409


class TestObjectifs:
    def test_le_manager_fixe_un_objectif(self, client: TestClient, contexte: Contexte, soumettre):
        soumettre(contexte)
        client.post(f"/entretiens/{contexte.entretien_id}/revue", headers=contexte.entetes_manager)

        reponse = client.post(
            f"/entretiens/{contexte.entretien_id}/objectifs",
            json={
                "libelle": "Former deux alternants",
                "indicateur": "Nombre d'alternants encadrés",
                "echeance": "2027-12-31",
            },
            headers=contexte.entetes_manager,
        )
        assert reponse.status_code == 201
        assert reponse.json()["statut"] == "EN_COURS"
        assert reponse.json()["entretien_evaluation_id"] is None

    def test_le_collaborateur_ne_fixe_pas_ses_objectifs(
        self, client: TestClient, contexte: Contexte, soumettre
    ) -> None:
        soumettre(contexte)
        client.post(f"/entretiens/{contexte.entretien_id}/revue", headers=contexte.entetes_manager)
        reponse = client.post(
            f"/entretiens/{contexte.entretien_id}/objectifs",
            json={"libelle": "Auto-attribué"},
            headers=contexte.entetes_collaborateur,
        )
        assert reponse.status_code == 403

    def test_pas_d_objectif_avant_la_revue(self, client: TestClient, contexte: Contexte) -> None:
        reponse = client.post(
            f"/entretiens/{contexte.entretien_id}/objectifs",
            json={"libelle": "Trop tôt"},
            headers=contexte.entetes_manager,
        )
        assert reponse.status_code == 409

    def test_un_objectif_ne_s_evalue_pas_dans_son_propre_entretien(
        self, client: TestClient, contexte: Contexte, soumettre
    ) -> None:
        soumettre(contexte)
        client.post(f"/entretiens/{contexte.entretien_id}/revue", headers=contexte.entetes_manager)
        objectif = client.post(
            f"/entretiens/{contexte.entretien_id}/objectifs",
            json={"libelle": "Objectif de l'année"},
            headers=contexte.entetes_manager,
        ).json()

        reponse = client.post(
            f"/objectifs/{objectif['id']}/evaluation",
            json={"entretien_id": contexte.entretien_id, "statut": "ATTEINT"},
            headers=contexte.entetes_manager,
        )
        assert reponse.status_code == 409
        assert "fixé" in reponse.json()["message"]

    def test_les_objectifs_de_l_entretien_sont_listes(
        self, client: TestClient, contexte: Contexte, soumettre
    ) -> None:
        soumettre(contexte)
        client.post(f"/entretiens/{contexte.entretien_id}/revue", headers=contexte.entetes_manager)
        client.post(
            f"/entretiens/{contexte.entretien_id}/objectifs",
            json={"libelle": "Objectif A"},
            headers=contexte.entetes_manager,
        )

        vue = client.get(
            f"/entretiens/{contexte.entretien_id}/objectifs",
            headers=contexte.entetes_collaborateur,
        ).json()
        assert len(vue["fixes"]) == 1
        assert vue["a_evaluer"] == []

    def test_le_collaborateur_voit_les_objectifs(
        self, client: TestClient, contexte: Contexte, soumettre
    ) -> None:
        soumettre(contexte)
        client.post(f"/entretiens/{contexte.entretien_id}/revue", headers=contexte.entetes_manager)
        reponse = client.get(
            f"/entretiens/{contexte.entretien_id}/objectifs",
            headers=contexte.entetes_collaborateur,
        )
        assert reponse.status_code == 200

    def test_un_tiers_ne_voit_pas_les_objectifs(
        self, client: TestClient, contexte: Contexte
    ) -> None:
        reponse = client.get(
            f"/entretiens/{contexte.entretien_id}/objectifs", headers=contexte.entetes_tiers
        )
        assert reponse.status_code == 403


class TestExportPdf:
    def test_export_refuse_avant_signature(self, client: TestClient, realise: Contexte) -> None:
        reponse = client.get(
            f"/entretiens/{realise.entretien_id}/export", headers=realise.entetes_collaborateur
        )
        assert reponse.status_code == 409

    def test_le_collaborateur_exporte_son_compte_rendu(
        self, client: TestClient, signe: Contexte
    ) -> None:
        reponse = client.get(
            f"/entretiens/{signe.entretien_id}/export", headers=signe.entetes_collaborateur
        )
        assert reponse.status_code == 200
        assert reponse.headers["content-type"] == "application/pdf"
        assert reponse.content.startswith(b"%PDF-")
        assert "attachment" in reponse.headers["content-disposition"]

    def test_le_manager_exporte_aussi(self, client: TestClient, signe: Contexte) -> None:
        reponse = client.get(
            f"/entretiens/{signe.entretien_id}/export", headers=signe.entetes_manager
        )
        assert reponse.status_code == 200

    def test_un_tiers_ne_peut_pas_exporter(self, client: TestClient, signe: Contexte) -> None:
        reponse = client.get(
            f"/entretiens/{signe.entretien_id}/export", headers=signe.entetes_tiers
        )
        assert reponse.status_code == 403

    def test_l_export_du_rh_avant_cloture_ne_contient_pas_le_contenu(
        self, client: TestClient, signe: Contexte
    ) -> None:
        avant = client.get(f"/entretiens/{signe.entretien_id}/export", headers=signe.entetes_rh)
        assert avant.status_code == 200
        texte_rh = texte_du_pdf(avant.content)
        assert "Projet livré" not in texte_rh
        assert "pas accessibles" in texte_rh

        complet = client.get(
            f"/entretiens/{signe.entretien_id}/export", headers=signe.entetes_collaborateur
        )
        assert "Projet livré" in texte_du_pdf(complet.content)

        client.post(f"/entretiens/{signe.entretien_id}/cloturer", headers=signe.entetes_rh)
        apres = client.get(f"/entretiens/{signe.entretien_id}/export", headers=signe.entetes_rh)
        assert "Projet livré" in texte_du_pdf(apres.content)

    def test_le_pdf_porte_les_signatures_horodatees(
        self, client: TestClient, signe: Contexte
    ) -> None:
        reponse = client.get(
            f"/entretiens/{signe.entretien_id}/export", headers=signe.entetes_collaborateur
        )
        texte = texte_du_pdf(reponse.content)
        assert "Signatures" in texte
        assert "non signé" not in texte


class TestHistorique:
    def test_le_collaborateur_consulte_son_parcours(
        self, client: TestClient, contexte: Contexte
    ) -> None:
        reponse = client.get(
            f"/collaborateurs/{contexte.id_collaborateur}/objectifs",
            headers=contexte.entetes_collaborateur,
        )
        assert reponse.status_code == 200

    def test_le_manager_consulte_celui_de_son_equipe(
        self, client: TestClient, contexte: Contexte
    ) -> None:
        reponse = client.get(
            f"/collaborateurs/{contexte.id_collaborateur}/objectifs",
            headers=contexte.entetes_manager,
        )
        assert reponse.status_code == 200

    def test_un_tiers_est_refuse(self, client: TestClient, contexte: Contexte) -> None:
        reponse = client.get(
            f"/collaborateurs/{contexte.id_collaborateur}/objectifs",
            headers=contexte.entetes_tiers,
        )
        assert reponse.status_code == 403
