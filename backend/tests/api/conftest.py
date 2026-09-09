from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pytest
from fastapi.testclient import TestClient

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
                {
                    "libelle": "Point manager",
                    "type_question": "texte_libre",
                    "cible": "MANAGER",
                    "obligatoire": True,
                },
            ],
        }
    ]
}


@dataclass(slots=True)
class Contexte:
    entretien_id: str
    campagne_id: str
    template_id: str
    section_id: str
    questions: dict[str, str]
    entetes_rh: dict[str, str]
    entetes_manager: dict[str, str]
    entetes_collaborateur: dict[str, str]
    entetes_tiers: dict[str, str]
    id_collaborateur: str
    id_manager: str


@pytest.fixture
def contexte(client: TestClient, creer_compte, entetes_de) -> Contexte:
    creer_compte(email="rh.c@example.com", roles=["RH", "ADMIN"])
    manager = creer_compte(email="mgr.c@example.com", roles=["MANAGER"])
    collaborateur = creer_compte(email="col.c@example.com", manager_id=manager.id)
    creer_compte(email="tiers.c@example.com", roles=["MANAGER"])

    e_rh = entetes_de("rh.c@example.com")
    e_mgr = entetes_de("mgr.c@example.com")
    e_col = entetes_de("col.c@example.com")
    e_tiers = entetes_de("tiers.c@example.com")

    template_id = client.post(
        "/templates", json={"nom": "Trame C", "type_entretien": "ANNUEL"}, headers=e_rh
    ).json()["id"]
    client.put(f"/templates/{template_id}/structure", json=STRUCTURE, headers=e_rh)
    client.post(f"/templates/{template_id}/publier", headers=e_rh)

    annee = date.today().year + 10
    campagne_id = client.post(
        "/campagnes",
        json={
            "libelle": f"Campagne {annee}",
            "annee": annee,
            "type_entretien": "ANNUEL",
            "date_ouverture": f"{annee}-01-01",
            "date_limite": f"{annee}-12-31",
        },
        headers=e_rh,
    ).json()["id"]
    client.post(f"/campagnes/{campagne_id}/ouvrir", headers=e_rh)

    entretien = client.post(
        "/entretiens",
        json={
            "campagne_id": campagne_id,
            "collaborateur_id": str(collaborateur.id),
            "template_id": template_id,
        },
        headers=e_mgr,
    )
    assert entretien.status_code == 201, entretien.text
    entretien_id = entretien.json()["id"]

    vue = client.get(f"/entretiens/{entretien_id}/questionnaire", headers=e_col).json()
    section = vue["sections"][0]

    return Contexte(
        entretien_id=entretien_id,
        campagne_id=campagne_id,
        template_id=template_id,
        section_id=section["id"],
        questions={q["cible"]: q["id"] for q in section["questions"]},
        entetes_rh=e_rh,
        entetes_manager=e_mgr,
        entetes_collaborateur=e_col,
        entetes_tiers=e_tiers,
        id_collaborateur=str(collaborateur.id),
        id_manager=str(manager.id),
    )


@pytest.fixture
def repondre(client: TestClient):

    def _repondre(ctx: Contexte) -> None:
        reponse = client.put(
            f"/entretiens/{ctx.entretien_id}/reponses",
            json={
                "reponses": [
                    {
                        "question_id": ctx.questions["COLLABORATEUR"],
                        "valeur": {"contenu": "Projet livré dans les délais"},
                    },
                    {"question_id": ctx.questions["PARTAGEE"], "valeur": {"note": 4}},
                ]
            },
            headers=ctx.entetes_collaborateur,
        )
        assert reponse.status_code == 200, reponse.text

    return _repondre


@pytest.fixture
def soumettre(client: TestClient, repondre):

    def _soumettre(ctx: Contexte) -> None:
        repondre(ctx)
        reponse = client.post(
            f"/entretiens/{ctx.entretien_id}/soumettre", headers=ctx.entetes_collaborateur
        )
        assert reponse.status_code == 200, reponse.text

    return _soumettre
