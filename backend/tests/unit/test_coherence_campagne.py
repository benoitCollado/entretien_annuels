from __future__ import annotations

from datetime import date

import pytest

from app.core.exceptions import ConflitMetier, DonneesInvalides
from app.services.regles import coherence_campagne as regle

OUVERTURE = date(2026, 1, 1)
LIMITE = date(2026, 12, 31)


class TestDates:
    def test_dates_coherentes(self) -> None:
        regle.exiger_dates_coherentes(OUVERTURE, LIMITE)

    def test_limite_anterieure_refusee(self) -> None:
        with pytest.raises(DonneesInvalides, match="postérieure"):
            regle.exiger_dates_coherentes(LIMITE, OUVERTURE)

    def test_dates_identiques_refusees(self) -> None:
        with pytest.raises(DonneesInvalides):
            regle.exiger_dates_coherentes(OUVERTURE, OUVERTURE)

    def test_annee_coherente(self) -> None:
        regle.exiger_annee_coherente(2026, OUVERTURE)

    def test_annee_incoherente_refusee(self) -> None:
        with pytest.raises(DonneesInvalides, match="2026"):
            regle.exiger_annee_coherente(2026, date(2028, 3, 1))


class TestTransitions:
    def test_brouillon_vers_ouverte(self) -> None:
        regle.exiger_transition(regle.BROUILLON, regle.OUVERTE)

    def test_ouverte_vers_cloturee(self) -> None:
        regle.exiger_transition(regle.OUVERTE, regle.CLOTUREE)

    def test_brouillon_peut_etre_abandonne(self) -> None:
        regle.exiger_transition(regle.BROUILLON, regle.CLOTUREE)

    def test_cloturee_ne_se_rouvre_pas(self) -> None:
        with pytest.raises(ConflitMetier, match="interdite"):
            regle.exiger_transition(regle.CLOTUREE, regle.OUVERTE)

    def test_double_ouverture_refusee(self) -> None:
        with pytest.raises(ConflitMetier):
            regle.exiger_transition(regle.OUVERTE, regle.OUVERTE)


class TestEtat:
    def test_seule_une_campagne_ouverte_accepte_des_entretiens(self) -> None:
        assert regle.accepte_des_entretiens(regle.OUVERTE) is True
        assert regle.accepte_des_entretiens(regle.BROUILLON) is False
        assert regle.accepte_des_entretiens(regle.CLOTUREE) is False

    def test_echeance(self) -> None:
        assert regle.est_echue(LIMITE, date(2027, 1, 1)) is True
        assert regle.est_echue(LIMITE, LIMITE) is False
        assert regle.est_echue(LIMITE, date(2026, 6, 1)) is False


class TestCompatibiliteDesTypes:
    def test_types_identiques(self) -> None:
        regle.exiger_types_compatibles("ANNUEL", "ANNUEL")

    def test_types_differents_refuses(self) -> None:
        with pytest.raises(DonneesInvalides, match="PROFESSIONNEL"):
            regle.exiger_types_compatibles("ANNUEL", "PROFESSIONNEL")
