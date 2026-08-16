"""Repository des utilisateurs contre PostgreSQL réel.

Ce qui est vérifié ici ne peut pas l'être en test unitaire : le comportement de
CITEXT, l'application des filtres en SQL et la remontée de la hiérarchie.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.repositories.utilisateur_repository import UtilisateurRepository

pytestmark = pytest.mark.integration


class TestRechercheParEmail:
    def test_insensible_a_la_casse(self, session: Session, creer_compte) -> None:
        """La colonne est en CITEXT : c'est PostgreSQL qui compare, sans
        `lower()` applicatif."""
        creer_compte(email="Alice.Martin@Example.COM")
        depot = UtilisateurRepository(session)

        assert depot.get_par_email("alice.martin@example.com") is not None
        assert depot.get_par_email("ALICE.MARTIN@EXAMPLE.COM") is not None

    def test_compte_archive_invisible(self, session: Session, creer_compte) -> None:
        compte = creer_compte(email="parti@example.com")
        depot = UtilisateurRepository(session)

        from datetime import UTC, datetime

        compte.archived_at = datetime.now(UTC)
        session.flush()

        assert depot.get_par_email("parti@example.com") is None

    def test_email_existe_inclut_les_archives(self, session: Session, creer_compte) -> None:
        """Réutiliser l'adresse d'un salarié parti violerait l'unicité en base :
        la vérification doit donc voir aussi les comptes archivés."""
        compte = creer_compte(email="parti2@example.com")
        from datetime import UTC, datetime

        compte.archived_at = datetime.now(UTC)
        session.flush()

        assert UtilisateurRepository(session).email_existe("parti2@example.com") is True


class TestGetActif:
    def test_compte_desactive_non_retourne(self, session: Session, creer_compte) -> None:
        compte = creer_compte(actif=False)
        assert UtilisateurRepository(session).get_actif(compte.id) is None

    def test_compte_actif_retourne(self, session: Session, creer_compte) -> None:
        compte = creer_compte()
        assert UtilisateurRepository(session).get_actif(compte.id) is not None


class TestPerimetreEnSql:
    def test_filtre_par_manager(self, session: Session, creer_compte) -> None:
        """Le filtre de portée est appliqué **dans la requête**, jamais après
        coup en Python (§6.3)."""
        manager = creer_compte(roles=["MANAGER"])
        creer_compte(manager_id=manager.id)
        creer_compte(manager_id=manager.id)
        creer_compte()  # hors équipe

        depot = UtilisateurRepository(session)
        assert depot.compter(manager_id=manager.id) == 2
        assert depot.compter() >= 4

    def test_pagination(self, session: Session, creer_compte) -> None:
        for _ in range(5):
            creer_compte()
        depot = UtilisateurRepository(session)

        page = depot.lister_filtre(limite=2, decalage=0)
        suivante = depot.lister_filtre(limite=2, decalage=2)

        assert len(page) == 2
        assert {u.id for u in page}.isdisjoint({u.id for u in suivante})

    def test_les_archives_sont_exclus(self, session: Session, creer_compte) -> None:
        compte = creer_compte()
        depot = UtilisateurRepository(session)
        avant = depot.compter()

        from datetime import UTC, datetime

        compte.archived_at = datetime.now(UTC)
        session.flush()

        assert depot.compter() == avant - 1


class TestChaineHierarchique:
    def test_remontee_complete(self, session: Session, creer_compte) -> None:
        direction = creer_compte()
        manager = creer_compte(manager_id=direction.id)
        salarie = creer_compte(manager_id=manager.id)

        chaine = UtilisateurRepository(session).chaine_hierarchique(salarie.id)
        assert chaine == [manager.id, direction.id]

    def test_sans_manager(self, session: Session, creer_compte) -> None:
        assert UtilisateurRepository(session).chaine_hierarchique(creer_compte().id) == []

    def test_la_remontee_est_bornee(self, session: Session, creer_compte) -> None:
        """Sur une base déjà corrompue par un cycle, une remontée non bornée ne
        se terminerait jamais."""
        a = creer_compte()
        b = creer_compte(manager_id=a.id)
        a.manager_id = b.id  # cycle forcé, la contrainte CHECK ne l'interdit pas
        session.flush()

        chaine = UtilisateurRepository(session).chaine_hierarchique(a.id, profondeur_max=5)
        assert len(chaine) <= 5
