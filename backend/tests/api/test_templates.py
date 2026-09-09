from __future__ import annotations

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
                    "obligatoire": True,
                },
                {
                    "libelle": "Satisfaction",
                    "type_question": "echelle",
                    "cible": "PARTAGEE",
                    "configuration": {"minimum": 1, "maximum": 5},
                },
            ],
        },
        {
            "titre": "Perspectives",
            "questions": [
                {
                    "libelle": "Formation souhaitée ?",
                    "type_question": "oui_non",
                    "cible": "COLLABORATEUR",
                }
            ],
        },
    ]
}


@pytest.fixture
def entetes_rh(creer_compte, entetes_de) -> dict[str, str]:
    creer_compte(email="rh.trames@example.com", roles=["RH"])
    return entetes_de("rh.trames@example.com")


def _creer_trame(client: TestClient, entetes: dict[str, str], nom: str = "Trame test") -> str:
    reponse = client.post(
        "/templates", json={"nom": nom, "type_entretien": "ANNUEL"}, headers=entetes
    )
    assert reponse.status_code == 201, reponse.text
    return reponse.json()["id"]


class TestRbac:
    def test_collaborateur_ne_voit_pas_les_trames(
        self, client: TestClient, creer_compte, entetes_de
    ) -> None:
        creer_compte(email="collab.t@example.com", roles=["COLLABORATEUR"])
        reponse = client.get("/templates", headers=entetes_de("collab.t@example.com"))
        assert reponse.status_code == 403
        assert "template:lire" in reponse.json()["message"]

    def test_manager_consulte_mais_ne_cree_pas(
        self, client: TestClient, creer_compte, entetes_de
    ) -> None:
        creer_compte(email="chef.t@example.com", roles=["MANAGER"])
        entetes = entetes_de("chef.t@example.com")

        assert client.get("/templates", headers=entetes).status_code == 200
        reponse = client.post(
            "/templates", json={"nom": "X", "type_entretien": "ANNUEL"}, headers=entetes
        )
        assert reponse.status_code == 403

    def test_sans_jeton(self, client: TestClient) -> None:
        assert client.get("/templates").status_code == 401


class TestCreation:
    def test_creation_en_brouillon(self, client: TestClient, entetes_rh) -> None:
        reponse = client.post(
            "/templates",
            json={"nom": "Annuel 2026", "type_entretien": "ANNUEL", "description": "Trame"},
            headers=entetes_rh,
        )
        assert reponse.status_code == 201
        corps = reponse.json()
        assert corps["version"] == 1
        assert corps["statut"] == "BROUILLON"
        assert corps["est_modifiable"] is True
        assert corps["nombre_questions"] == 0

    def test_nom_deja_pris(self, client: TestClient, entetes_rh) -> None:
        _creer_trame(client, entetes_rh, "Unique")
        reponse = client.post(
            "/templates", json={"nom": "Unique", "type_entretien": "ANNUEL"}, headers=entetes_rh
        )
        assert reponse.status_code == 409
        assert "nouvelle version" in reponse.json()["message"]

    def test_type_entretien_invalide(self, client: TestClient, entetes_rh) -> None:
        reponse = client.post(
            "/templates", json={"nom": "X", "type_entretien": "INVENTE"}, headers=entetes_rh
        )
        assert reponse.status_code == 422


class TestStructure:
    def test_definition_de_la_structure(self, client: TestClient, entetes_rh) -> None:
        identifiant = _creer_trame(client, entetes_rh)
        reponse = client.put(
            f"/templates/{identifiant}/structure", json=STRUCTURE, headers=entetes_rh
        )

        assert reponse.status_code == 200
        corps = reponse.json()
        assert corps["nombre_sections"] == 2
        assert corps["nombre_questions"] == 3
        assert [s["ordre"] for s in corps["sections"]] == [0, 1]
        assert [q["ordre"] for q in corps["sections"][0]["questions"]] == [0, 1]

    def test_l_ordre_recu_fait_l_ordre(self, client: TestClient, entetes_rh) -> None:
        identifiant = _creer_trame(client, entetes_rh)
        client.put(f"/templates/{identifiant}/structure", json=STRUCTURE, headers=entetes_rh)

        inverse = {"sections": list(reversed(STRUCTURE["sections"]))}
        corps = client.put(
            f"/templates/{identifiant}/structure", json=inverse, headers=entetes_rh
        ).json()

        assert [s["titre"] for s in corps["sections"]] == ["Perspectives", "Bilan"]
        assert [s["ordre"] for s in corps["sections"]] == [0, 1]

    def test_remplacement_idempotent(self, client: TestClient, entetes_rh) -> None:
        identifiant = _creer_trame(client, entetes_rh)
        premier = client.put(
            f"/templates/{identifiant}/structure", json=STRUCTURE, headers=entetes_rh
        ).json()
        second = client.put(
            f"/templates/{identifiant}/structure", json=STRUCTURE, headers=entetes_rh
        ).json()
        assert premier["nombre_questions"] == second["nombre_questions"] == 3

    def test_choix_multiple_sans_options_refuse(self, client: TestClient, entetes_rh) -> None:
        identifiant = _creer_trame(client, entetes_rh)
        mauvaise = {
            "sections": [
                {
                    "titre": "S",
                    "questions": [
                        {
                            "libelle": "Q",
                            "type_question": "choix_multiple",
                            "cible": "COLLABORATEUR",
                        }
                    ],
                }
            ]
        }
        reponse = client.put(
            f"/templates/{identifiant}/structure", json=mauvaise, headers=entetes_rh
        )
        assert reponse.status_code == 422
        assert "options" in reponse.text

    def test_echelle_aux_bornes_inversees_refusee(self, client: TestClient, entetes_rh) -> None:
        identifiant = _creer_trame(client, entetes_rh)
        mauvaise = {
            "sections": [
                {
                    "titre": "S",
                    "questions": [
                        {
                            "libelle": "Q",
                            "type_question": "echelle",
                            "cible": "PARTAGEE",
                            "configuration": {"minimum": 5, "maximum": 1},
                        }
                    ],
                }
            ]
        }
        assert (
            client.put(
                f"/templates/{identifiant}/structure", json=mauvaise, headers=entetes_rh
            ).status_code
            == 422
        )

    def test_section_sans_question_refusee(self, client: TestClient, entetes_rh) -> None:
        identifiant = _creer_trame(client, entetes_rh)
        assert (
            client.put(
                f"/templates/{identifiant}/structure",
                json={"sections": [{"titre": "Vide", "questions": []}]},
                headers=entetes_rh,
            ).status_code
            == 422
        )

    def test_titres_de_sections_distincts(self, client: TestClient, entetes_rh) -> None:
        identifiant = _creer_trame(client, entetes_rh)
        doublon = {"sections": [STRUCTURE["sections"][0], STRUCTURE["sections"][0]]}
        assert (
            client.put(
                f"/templates/{identifiant}/structure", json=doublon, headers=entetes_rh
            ).status_code
            == 422
        )


class TestPublication:
    def test_publication(self, client: TestClient, entetes_rh) -> None:
        identifiant = _creer_trame(client, entetes_rh)
        client.put(f"/templates/{identifiant}/structure", json=STRUCTURE, headers=entetes_rh)

        reponse = client.post(f"/templates/{identifiant}/publier", headers=entetes_rh)
        assert reponse.status_code == 200
        assert reponse.json()["statut"] == "PUBLIEE"
        assert reponse.json()["publie_le"] is not None
        assert reponse.json()["est_modifiable"] is False

    def test_publier_une_trame_vide_est_refuse(self, client: TestClient, entetes_rh) -> None:
        identifiant = _creer_trame(client, entetes_rh)
        reponse = client.post(f"/templates/{identifiant}/publier", headers=entetes_rh)
        assert reponse.status_code == 422
        assert "au moins une section" in reponse.json()["message"]

    def test_une_trame_publiee_est_immuable(self, client: TestClient, entetes_rh) -> None:
        identifiant = _creer_trame(client, entetes_rh)
        client.put(f"/templates/{identifiant}/structure", json=STRUCTURE, headers=entetes_rh)
        client.post(f"/templates/{identifiant}/publier", headers=entetes_rh)

        modification = client.patch(
            f"/templates/{identifiant}", json={"description": "après coup"}, headers=entetes_rh
        )
        structure = client.put(
            f"/templates/{identifiant}/structure", json=STRUCTURE, headers=entetes_rh
        )

        assert modification.status_code == 409
        assert structure.status_code == 409

    def test_republier_est_refuse(self, client: TestClient, entetes_rh) -> None:
        identifiant = _creer_trame(client, entetes_rh)
        client.put(f"/templates/{identifiant}/structure", json=STRUCTURE, headers=entetes_rh)
        client.post(f"/templates/{identifiant}/publier", headers=entetes_rh)
        assert (
            client.post(f"/templates/{identifiant}/publier", headers=entetes_rh).status_code == 409
        )


class TestVersionnement:
    def _publier(self, client: TestClient, entetes: dict[str, str], nom: str) -> str:
        identifiant = _creer_trame(client, entetes, nom)
        client.put(f"/templates/{identifiant}/structure", json=STRUCTURE, headers=entetes)
        client.post(f"/templates/{identifiant}/publier", headers=entetes)
        return identifiant

    def test_nouvelle_version_copie_l_arborescence(self, client: TestClient, entetes_rh) -> None:
        origine = self._publier(client, entetes_rh, "Versionnee")

        reponse = client.post(f"/templates/{origine}/nouvelle-version", headers=entetes_rh)
        assert reponse.status_code == 201
        copie = reponse.json()

        assert copie["version"] == 2
        assert copie["statut"] == "BROUILLON"
        assert copie["template_parent_id"] == origine
        assert copie["nombre_questions"] == 3
        assert copie["id"] != origine

    def test_les_questions_copiees_sont_des_objets_distincts(
        self, client: TestClient, entetes_rh
    ) -> None:
        origine = self._publier(client, entetes_rh, "Distincte")
        copie_id = client.post(f"/templates/{origine}/nouvelle-version", headers=entetes_rh).json()[
            "id"
        ]

        client.put(
            f"/templates/{copie_id}/structure",
            json={"sections": [STRUCTURE["sections"][0]]},
            headers=entetes_rh,
        )

        originale = client.get(f"/templates/{origine}", headers=entetes_rh).json()
        assert originale["nombre_sections"] == 2
        assert originale["nombre_questions"] == 3

    def test_deux_versions_depuis_la_v1_ne_collisionnent_pas(
        self, client: TestClient, entetes_rh
    ) -> None:
        origine = self._publier(client, entetes_rh, "Multiple")

        premiere = client.post(f"/templates/{origine}/nouvelle-version", headers=entetes_rh)
        seconde = client.post(f"/templates/{origine}/nouvelle-version", headers=entetes_rh)

        assert premiere.json()["version"] == 2
        assert seconde.json()["version"] == 3

    def test_versionner_un_brouillon_est_refuse(self, client: TestClient, entetes_rh) -> None:
        identifiant = _creer_trame(client, entetes_rh, "Brouillon")
        reponse = client.post(f"/templates/{identifiant}/nouvelle-version", headers=entetes_rh)
        assert reponse.status_code == 409
        assert "brouillon" in reponse.json()["message"].lower()


class TestConsultation:
    def test_referentiel_des_types(self, client: TestClient, entetes_rh) -> None:
        corps = client.get("/templates/referentiel", headers=entetes_rh).json()
        assert "texte_libre" in corps["types_question"]
        assert corps["cibles"] == ["COLLABORATEUR", "MANAGER", "PARTAGEE"]

    def test_filtre_par_statut(self, client: TestClient, entetes_rh) -> None:
        identifiant = _creer_trame(client, entetes_rh, "Filtree")
        client.put(f"/templates/{identifiant}/structure", json=STRUCTURE, headers=entetes_rh)
        client.post(f"/templates/{identifiant}/publier", headers=entetes_rh)
        _creer_trame(client, entetes_rh, "EnBrouillon")

        publiees = client.get("/templates?statut=PUBLIEE", headers=entetes_rh).json()
        assert all(t["statut"] == "PUBLIEE" for t in publiees["elements"])
        assert publiees["total"] >= 1

    def test_trame_introuvable(self, client: TestClient, entetes_rh) -> None:
        reponse = client.get("/templates/01930000-0000-7000-8000-000000000000", headers=entetes_rh)
        assert reponse.status_code == 404
