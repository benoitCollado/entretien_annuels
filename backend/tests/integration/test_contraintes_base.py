"""Les contraintes de la base mordent-elles réellement ?

Complément indispensable au test de dérive : `compare_metadata` ne détecte pas
les contraintes CHECK. Seul un test comportemental prouve qu'elles sont
présentes **et** actives.
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.utilisateur import Utilisateur

pytestmark = pytest.mark.integration


def test_email_unique(session: Session, creer_compte) -> None:
    creer_compte(email="doublon@example.com")
    with pytest.raises(IntegrityError):
        creer_compte(email="doublon@example.com")
        session.flush()


def test_email_unique_insensible_a_la_casse(session: Session, creer_compte) -> None:
    """Conséquence directe du type CITEXT : deux graphies de la même adresse
    sont le même compte."""
    creer_compte(email="Casse@example.com")
    with pytest.raises(IntegrityError):
        creer_compte(email="casse@EXAMPLE.com")
        session.flush()


def test_utilisateur_ne_peut_pas_etre_son_propre_manager(session: Session, creer_compte) -> None:
    """Contrainte CHECK `ck_utilisateur_pas_son_manager`.

    Le doublon avec la règle applicative est volontaire : la base garantit
    l'invariant même si une écriture contourne l'application.
    """
    compte = creer_compte()
    compte.manager_id = compte.id
    with pytest.raises(IntegrityError):
        session.flush()


def test_manager_archive_met_le_rattachement_a_null(session: Session, creer_compte) -> None:
    """`ON DELETE SET NULL` et non CASCADE : supprimer un manager ne doit jamais
    faire disparaître son équipe."""
    manager = creer_compte(roles=["MANAGER"])
    salarie = creer_compte(manager_id=manager.id)
    identifiant = salarie.id

    session.delete(manager)
    session.flush()
    session.expire_all()

    assert session.get(Utilisateur, identifiant) is not None
    assert session.get(Utilisateur, identifiant).manager_id is None


def test_version_jeton_par_defaut(session: Session, creer_compte) -> None:
    compte = creer_compte()
    session.refresh(compte)
    assert compte.version_jeton == 1
    assert compte.actif is True
    assert compte.archived_at is None
