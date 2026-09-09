from __future__ import annotations

import pytest

from app.core.exceptions import ConflitMetier, DonneesInvalides
from app.services.regles import publication_template as regle


class TestImmutabilite:
    def test_un_brouillon_est_modifiable(self) -> None:
        assert regle.est_modifiable(regle.BROUILLON) is True
        regle.exiger_modifiable(regle.BROUILLON)

    @pytest.mark.parametrize("statut", [regle.PUBLIEE, regle.ARCHIVEE])
    def test_une_trame_publiee_est_immuable(self, statut: str) -> None:
        with pytest.raises(ConflitMetier, match="nouvelle version"):
            regle.exiger_modifiable(statut)


class TestTransitions:
    def test_brouillon_vers_publiee(self) -> None:
        regle.exiger_transition(regle.BROUILLON, regle.PUBLIEE)

    def test_publiee_vers_archivee(self) -> None:
        regle.exiger_transition(regle.PUBLIEE, regle.ARCHIVEE)

    def test_publiee_ne_redevient_pas_brouillon(self) -> None:
        with pytest.raises(ConflitMetier):
            regle.exiger_transition(regle.PUBLIEE, regle.BROUILLON)

    def test_archivee_est_terminal(self) -> None:
        with pytest.raises(ConflitMetier):
            regle.exiger_transition(regle.ARCHIVEE, regle.PUBLIEE)

    def test_republier_est_refuse(self) -> None:
        with pytest.raises(ConflitMetier):
            regle.exiger_transition(regle.PUBLIEE, regle.PUBLIEE)


class TestInstanciabilite:
    def test_seule_une_trame_publiee_est_instanciable(self) -> None:
        assert regle.est_instanciable(regle.PUBLIEE) is True
        assert regle.est_instanciable(regle.BROUILLON) is False
        assert regle.est_instanciable(regle.ARCHIVEE) is False


class TestStructurePubliable:
    def test_structure_valide(self) -> None:
        regle.exiger_structure_publiable([3, 2, 5])

    def test_trame_sans_section_refusee(self) -> None:
        with pytest.raises(DonneesInvalides, match="au moins une section"):
            regle.exiger_structure_publiable([])

    def test_section_vide_refusee(self) -> None:
        with pytest.raises(DonneesInvalides, match="au moins une question"):
            regle.exiger_structure_publiable([3, 0, 5])

    def test_le_message_designe_les_sections_fautives(self) -> None:
        with pytest.raises(DonneesInvalides) as erreur:
            regle.exiger_structure_publiable([0, 2, 0])
        assert erreur.value.details[0]["sections_vides"] == [1, 3]


class TestOrdres:
    def test_suite_continue_acceptee(self) -> None:
        regle.exiger_ordres_valides([0, 1, 2], "sections")

    def test_ordre_de_reception_indifferent(self) -> None:
        regle.exiger_ordres_valides([2, 0, 1], "sections")

    def test_trou_refuse(self) -> None:
        with pytest.raises(DonneesInvalides, match="suite continue"):
            regle.exiger_ordres_valides([0, 1, 3], "sections")

    def test_doublon_refuse(self) -> None:
        with pytest.raises(DonneesInvalides):
            regle.exiger_ordres_valides([0, 1, 1], "questions")

    def test_ne_commence_pas_a_zero(self) -> None:
        with pytest.raises(DonneesInvalides):
            regle.exiger_ordres_valides([1, 2, 3], "sections")


class TestVersion:
    def test_incrementation(self) -> None:
        assert regle.version_suivante(1) == 2
        assert regle.version_suivante(7) == 8
