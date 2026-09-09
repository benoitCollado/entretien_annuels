from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.models.campagne import Campagne
from app.models.entretien import Entretien
from app.models.enums import StatutObjectif
from app.models.objectif import Objectif
from app.repositories.objectif_repository import ObjectifRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def deux_annees(session: Session, creer_compte):
    manager = creer_compte(email="mgr.obj@example.com", roles=["MANAGER"])
    collaborateur = creer_compte(email="col.obj@example.com", manager_id=manager.id)

    entretiens = []
    for annee in (2030, 2031):
        campagne = Campagne(
            libelle=f"Campagne {annee}",
            annee=annee,
            type_entretien="ANNUEL",
            date_ouverture=date(annee, 1, 1),
            date_limite=date(annee, 12, 31),
            statut="OUVERTE",
        )
        session.add(campagne)
        session.flush()

        entretien = Entretien(
            campagne_id=campagne.id,
            collaborateur_id=collaborateur.id,
            manager_id=manager.id,
            type_entretien="ANNUEL",
            statut="REVUE_MANAGER",
        )
        session.add(entretien)
        session.flush()
        entretiens.append(entretien)

    return collaborateur, entretiens[0], entretiens[1]


def fixer(session: Session, entretien: Entretien, collaborateur, libelle: str) -> Objectif:
    objectif = Objectif(
        entretien_origine_id=entretien.id,
        collaborateur_id=collaborateur.id,
        libelle=libelle,
        statut=StatutObjectif.EN_COURS,
    )
    session.add(objectif)
    session.flush()
    return objectif


def test_un_objectif_de_n_1_est_rappele_en_n(session: Session, deux_annees) -> None:
    collaborateur, annee_n1, annee_n = deux_annees
    fixer(session, annee_n1, collaborateur, "Former deux alternants")

    a_evaluer = ObjectifRepository(session).lister_a_evaluer(collaborateur.id, annee_n.id)

    assert [o.libelle for o in a_evaluer] == ["Former deux alternants"]


def test_un_objectif_fixe_dans_l_entretien_courant_ne_se_rappelle_pas(
    session: Session, deux_annees
) -> None:
    collaborateur, _, annee_n = deux_annees
    fixer(session, annee_n, collaborateur, "Objectif de cette année")

    assert ObjectifRepository(session).lister_a_evaluer(collaborateur.id, annee_n.id) == []


def test_un_objectif_deja_evalue_ne_revient_pas(session: Session, deux_annees) -> None:
    collaborateur, annee_n1, annee_n = deux_annees
    objectif = fixer(session, annee_n1, collaborateur, "Déjà évalué")

    objectif.statut = StatutObjectif.ATTEINT
    objectif.entretien_evaluation_id = annee_n.id
    objectif.niveau_atteinte = 100
    session.flush()

    assert ObjectifRepository(session).lister_a_evaluer(collaborateur.id, annee_n.id) == []


def test_les_objectifs_d_un_autre_collaborateur_ne_remontent_pas(
    session: Session, deux_annees, creer_compte
) -> None:
    collaborateur, annee_n1, annee_n = deux_annees
    autre = creer_compte(email="autre.obj@example.com")

    objectif = Objectif(
        entretien_origine_id=annee_n1.id,
        collaborateur_id=autre.id,
        libelle="Objectif d'un autre",
        statut=StatutObjectif.EN_COURS,
    )
    session.add(objectif)
    session.flush()

    a_evaluer = ObjectifRepository(session).lister_a_evaluer(collaborateur.id, annee_n.id)
    assert [o.libelle for o in a_evaluer] == []


def test_le_report_est_calcule_et_non_copie(session: Session, deux_annees) -> None:
    collaborateur, annee_n1, annee_n = deux_annees
    objectifs = ObjectifRepository(session)

    assert objectifs.lister_a_evaluer(collaborateur.id, annee_n.id) == []

    fixer(session, annee_n1, collaborateur, "Ajouté après coup")

    assert len(objectifs.lister_a_evaluer(collaborateur.id, annee_n.id)) == 1


def test_l_historique_couvre_toutes_les_annees(session: Session, deux_annees) -> None:
    collaborateur, annee_n1, annee_n = deux_annees
    fixer(session, annee_n1, collaborateur, "Objectif 2030")
    fixer(session, annee_n, collaborateur, "Objectif 2031")

    historique = ObjectifRepository(session).lister_du_collaborateur(collaborateur.id)
    assert {o.libelle for o in historique} == {"Objectif 2030", "Objectif 2031"}
