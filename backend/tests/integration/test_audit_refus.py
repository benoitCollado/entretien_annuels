from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.models.audit import JournalAudit
from app.repositories.audit_repository import AuditRepository

pytestmark = pytest.mark.integration

MOTIF = "test — accès refusé hors transaction"


@pytest.fixture
def fabrique_reelle(monkeypatch: pytest.MonkeyPatch, moteur: Engine) -> Iterator[sessionmaker]:
    fabrique = sessionmaker(bind=moteur)
    monkeypatch.setattr("app.database.obtenir_fabrique_sessions", lambda: fabrique)
    yield fabrique

    with fabrique() as menage:
        menage.execute(delete(JournalAudit).where(JournalAudit.donnees["motif"].astext == MOTIF))
        menage.commit()


def lignes_tracees(fabrique: sessionmaker) -> list[JournalAudit]:
    with fabrique() as lecture:
        return list(
            lecture.scalars(
                select(JournalAudit).where(JournalAudit.donnees["motif"].astext == MOTIF)
            )
        )


def test_la_trace_survit_au_rollback_de_la_requete(fabrique_reelle: sessionmaker) -> None:
    session_de_requete: Session = fabrique_reelle()
    try:
        AuditRepository(session_de_requete).tracer_refus(
            utilisateur_id=None,
            entretien_id=None,
            statut_avant="PREPARATION",
            donnees={"motif": MOTIF},
            adresse_ip="203.0.113.7",
        )
        session_de_requete.rollback()
    finally:
        session_de_requete.close()

    tracees = lignes_tracees(fabrique_reelle)
    assert len(tracees) == 1, "La trace du refus a été annulée avec la requête."
    assert tracees[0].action == "ACCES_REFUSE"
    assert str(tracees[0].adresse_ip) == "203.0.113.7"


def test_la_trace_n_altere_pas_la_transaction_appelante(fabrique_reelle: sessionmaker) -> None:
    session_de_requete: Session = fabrique_reelle()
    try:
        session_de_requete.add(
            JournalAudit(action="CONSULTATION", donnees={"motif": "ne doit pas survivre"})
        )
        session_de_requete.flush()

        AuditRepository(session_de_requete).tracer_refus(
            utilisateur_id=None,
            entretien_id=None,
            donnees={"motif": MOTIF},
            adresse_ip=None,
        )
        session_de_requete.rollback()
    finally:
        session_de_requete.close()

    with fabrique_reelle() as lecture:
        survivantes = list(
            lecture.scalars(
                select(JournalAudit).where(
                    JournalAudit.donnees["motif"].astext == "ne doit pas survivre"
                )
            )
        )
    assert survivantes == [], "L'écriture métier aurait dû être annulée avec le refus."
    assert len(lignes_tracees(fabrique_reelle)) == 1


def test_une_adresse_non_ip_est_neutralisee(fabrique_reelle: sessionmaker) -> None:
    session_de_requete: Session = fabrique_reelle()
    try:
        AuditRepository(session_de_requete).tracer_refus(
            utilisateur_id=None,
            entretien_id=None,
            donnees={"motif": MOTIF},
            adresse_ip="pas-une-adresse",
        )
    finally:
        session_de_requete.close()

    tracees = lignes_tracees(fabrique_reelle)
    assert len(tracees) == 1
    assert tracees[0].adresse_ip is None
