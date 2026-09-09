from __future__ import annotations

import pytest

from app.core.exceptions import ConflitMetier
from app.services.regles import transitions_entretien as etats


class TestCheminNominal:
    @pytest.mark.parametrize(
        ("depuis", "vers", "acteur"),
        [
            (etats.BROUILLON, etats.PLANIFIE, etats.MANAGER),
            (etats.BROUILLON, etats.PLANIFIE, etats.RH),
            (etats.PLANIFIE, etats.PREPARATION, etats.COLLABORATEUR),
            (etats.PREPARATION, etats.SOUMIS_COLLABORATEUR, etats.COLLABORATEUR),
            (etats.SOUMIS_COLLABORATEUR, etats.REVUE_MANAGER, etats.MANAGER),
            (etats.REVUE_MANAGER, etats.ENTRETIEN_REALISE, etats.MANAGER),
            (etats.ENTRETIEN_REALISE, etats.SIGNE, etats.COLLABORATEUR),
            (etats.ENTRETIEN_REALISE, etats.SIGNE, etats.MANAGER),
            (etats.SIGNE, etats.CLOTURE, etats.RH),
        ],
    )
    def test_transitions_autorisees(self, depuis: str, vers: str, acteur: str) -> None:
        etats.exiger_transition(depuis, vers, acteur)


class TestActeurs:
    def test_seul_le_collaborateur_soumet(self) -> None:
        with pytest.raises(ConflitMetier):
            etats.exiger_transition(etats.PREPARATION, etats.SOUMIS_COLLABORATEUR, etats.MANAGER)

    def test_le_collaborateur_n_ouvre_pas_la_revue(self) -> None:
        with pytest.raises(ConflitMetier):
            etats.exiger_transition(
                etats.SOUMIS_COLLABORATEUR, etats.REVUE_MANAGER, etats.COLLABORATEUR
            )

    def test_seul_le_rh_cloture(self) -> None:
        with pytest.raises(ConflitMetier):
            etats.exiger_transition(etats.SIGNE, etats.CLOTURE, etats.MANAGER)


class TestRetoursInterdits:
    def test_pas_de_retour_en_arriere(self) -> None:
        with pytest.raises(ConflitMetier):
            etats.exiger_transition(
                etats.SOUMIS_COLLABORATEUR, etats.PREPARATION, etats.COLLABORATEUR
            )

    def test_pas_de_saut_d_etape(self) -> None:
        with pytest.raises(ConflitMetier):
            etats.exiger_transition(etats.PREPARATION, etats.SIGNE, etats.MANAGER)

    @pytest.mark.parametrize("statut", [etats.CLOTURE, etats.ANNULE])
    def test_les_statuts_terminaux_le_sont(self, statut: str) -> None:
        assert etats.est_terminal(statut) is True
        with pytest.raises(ConflitMetier):
            etats.exiger_transition(statut, etats.PREPARATION, etats.RH)


class TestAnnulation:
    @pytest.mark.parametrize(
        "statut",
        [
            etats.BROUILLON,
            etats.PLANIFIE,
            etats.PREPARATION,
            etats.SOUMIS_COLLABORATEUR,
            etats.REVUE_MANAGER,
        ],
    )
    def test_le_rh_annule_depuis_tout_statut_non_terminal(self, statut: str) -> None:
        etats.exiger_transition(statut, etats.ANNULE, etats.RH)

    def test_le_manager_n_annule_pas(self) -> None:
        with pytest.raises(ConflitMetier):
            etats.exiger_transition(etats.PREPARATION, etats.ANNULE, etats.MANAGER)

    def test_on_n_annule_pas_un_entretien_clos(self) -> None:
        with pytest.raises(ConflitMetier):
            etats.exiger_transition(etats.CLOTURE, etats.ANNULE, etats.RH)


class TestProgression:
    def test_au_moins(self) -> None:
        assert etats.au_moins(etats.REVUE_MANAGER, etats.SOUMIS_COLLABORATEUR) is True
        assert etats.au_moins(etats.PREPARATION, etats.SOUMIS_COLLABORATEUR) is False
        assert etats.au_moins(etats.SOUMIS_COLLABORATEUR, etats.SOUMIS_COLLABORATEUR) is True

    def test_annule_ne_depasse_aucun_seuil(self) -> None:
        assert etats.au_moins(etats.ANNULE, etats.BROUILLON) is False
        assert etats.au_moins(etats.ANNULE, etats.SOUMIS_COLLABORATEUR) is False


class TestTransitionsPossibles:
    def test_pour_l_interface(self) -> None:
        assert etats.transitions_possibles(etats.PREPARATION, etats.COLLABORATEUR) == [
            etats.SOUMIS_COLLABORATEUR
        ]
        assert etats.transitions_possibles(etats.PREPARATION, etats.MANAGER) == []

    def test_le_rh_peut_toujours_annuler(self) -> None:
        assert etats.ANNULE in etats.transitions_possibles(etats.PREPARATION, etats.RH)

    def test_rien_depuis_un_statut_terminal(self) -> None:
        assert etats.transitions_possibles(etats.CLOTURE, etats.RH) == []
