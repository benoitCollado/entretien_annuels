from __future__ import annotations

import pytest
from uuid_utils.compat import uuid7

from app.core.exceptions import DonneesInvalides
from app.services.regles import portee_hierarchique as portee

ALICE, JULIEN, SOPHIE = uuid7(), uuid7(), uuid7()


class TestRattachement:
    def test_etre_son_propre_manager_est_refuse(self) -> None:
        with pytest.raises(DonneesInvalides, match="son propre manager"):
            portee.exiger_rattachement_valide(ALICE, ALICE)

    def test_absence_de_manager_est_valide(self) -> None:
        portee.exiger_rattachement_valide(ALICE, None)

    def test_rattachement_simple_est_valide(self) -> None:
        portee.exiger_rattachement_valide(SOPHIE, JULIEN, ancetres_du_manager=[ALICE])

    def test_cycle_indirect_est_refuse(self) -> None:
        with pytest.raises(DonneesInvalides, match="cycle"):
            portee.exiger_rattachement_valide(ALICE, JULIEN, ancetres_du_manager=[ALICE])

    def test_cycle_profond_est_refuse(self) -> None:
        with pytest.raises(DonneesInvalides, match="cycle"):
            portee.exiger_rattachement_valide(ALICE, SOPHIE, ancetres_du_manager=[JULIEN, ALICE])


class TestPerimetreDeLecture:
    @pytest.mark.parametrize("role", ["ADMIN", "RH"])
    def test_portee_globale_sans_restriction(self, role: str) -> None:
        assert portee.perimetre_de_lecture([role], ALICE) is None

    def test_manager_restreint_a_son_equipe(self) -> None:
        assert portee.perimetre_de_lecture(["MANAGER"], JULIEN) == JULIEN

    def test_collaborateur_restreint_a_lui_meme(self) -> None:
        assert portee.perimetre_de_lecture(["COLLABORATEUR"], SOPHIE) == SOPHIE

    def test_cumul_de_roles_prend_le_plus_large(self) -> None:
        assert portee.perimetre_de_lecture(["MANAGER", "RH"], JULIEN) is None


class TestGestionDesComptes:
    @pytest.mark.parametrize(
        ("roles", "attendu"),
        [
            (["ADMIN"], True),
            (["RH"], True),
            (["MANAGER"], False),
            (["COLLABORATEUR"], False),
            (["MANAGER", "COLLABORATEUR"], False),
        ],
    )
    def test_qui_peut_gerer_les_comptes(self, roles: list[str], attendu: bool) -> None:
        assert portee.peut_gerer(roles) is attendu
