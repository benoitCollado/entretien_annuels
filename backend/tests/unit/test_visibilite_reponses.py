from __future__ import annotations

import pytest
from uuid_utils.compat import uuid7

from app.services.regles import transitions_entretien as etats
from app.services.regles.visibilite_reponses import (
    auteurs_lisibles,
    peut_commenter,
    peut_ecrire_ses_reponses,
    peut_lire_les_reponses,
)

COLLAB, MANAGER, RH, ETRANGER = uuid7(), uuid7(), uuid7(), uuid7()

AVANT_SOUMISSION = [etats.BROUILLON, etats.PLANIFIE, etats.PREPARATION]
APRES_SOUMISSION = [
    etats.SOUMIS_COLLABORATEUR,
    etats.REVUE_MANAGER,
    etats.ENTRETIEN_REALISE,
    etats.SIGNE,
    etats.CLOTURE,
]


def lisibles(statut: str, lecteur, rh: bool = False):
    return auteurs_lisibles(statut, lecteur, COLLAB, MANAGER, rh)


class TestManagerAvantSoumission:
    @pytest.mark.parametrize("statut", AVANT_SOUMISSION)
    def test_le_manager_ne_voit_pas_les_reponses_du_collaborateur(self, statut: str) -> None:
        assert COLLAB not in lisibles(statut, MANAGER)

    @pytest.mark.parametrize("statut", AVANT_SOUMISSION)
    def test_le_manager_voit_quand_meme_les_siennes(self, statut: str) -> None:
        assert lisibles(statut, MANAGER) == [MANAGER]


class TestManagerApresSoumission:
    @pytest.mark.parametrize("statut", APRES_SOUMISSION)
    def test_le_manager_voit_les_reponses_du_collaborateur(self, statut: str) -> None:
        assert COLLAB in lisibles(statut, MANAGER)

    def test_bascule_exactement_a_la_soumission(self) -> None:
        assert COLLAB not in lisibles(etats.PREPARATION, MANAGER)
        assert COLLAB in lisibles(etats.SOUMIS_COLLABORATEUR, MANAGER)


class TestCollaborateur:
    @pytest.mark.parametrize("statut", [*AVANT_SOUMISSION, *APRES_SOUMISSION])
    def test_voit_toujours_ses_propres_reponses(self, statut: str) -> None:
        assert COLLAB in lisibles(statut, COLLAB)

    @pytest.mark.parametrize("statut", [etats.PREPARATION, etats.SOUMIS_COLLABORATEUR])
    def test_ne_voit_pas_celles_du_manager_avant_la_revue(self, statut: str) -> None:
        assert MANAGER not in lisibles(statut, COLLAB)

    @pytest.mark.parametrize("statut", [etats.REVUE_MANAGER, etats.ENTRETIEN_REALISE])
    def test_voit_celles_du_manager_a_partir_de_la_revue(self, statut: str) -> None:
        assert MANAGER in lisibles(statut, COLLAB)


class TestRh:
    @pytest.mark.parametrize("statut", [*AVANT_SOUMISSION, etats.REVUE_MANAGER, etats.SIGNE])
    def test_ne_voit_rien_avant_la_cloture(self, statut: str) -> None:
        assert lisibles(statut, RH, rh=True) == []

    def test_voit_tout_apres_cloture(self) -> None:
        assert lisibles(etats.CLOTURE, RH, rh=True) is None

    def test_un_rh_qui_est_aussi_le_manager_garde_ses_droits(self) -> None:
        assert COLLAB in auteurs_lisibles(
            etats.SOUMIS_COLLABORATEUR, MANAGER, COLLAB, MANAGER, True
        )


class TestEtranger:
    @pytest.mark.parametrize("statut", [*AVANT_SOUMISSION, *APRES_SOUMISSION])
    def test_un_tiers_ne_voit_rien(self, statut: str) -> None:
        assert lisibles(statut, ETRANGER) == []

    @pytest.mark.parametrize("statut", [*AVANT_SOUMISSION, *APRES_SOUMISSION])
    def test_un_tiers_se_voit_refuser_l_acces(self, statut: str) -> None:
        assert (
            peut_lire_les_reponses(statut, ETRANGER, COLLAB, MANAGER, lecteur_est_rh=False) is False
        )


class TestDistinctionAucunFiltreEtAucunAcces:
    def test_none_signifie_aucune_restriction(self) -> None:
        assert lisibles(etats.CLOTURE, RH, rh=True) is None

    def test_liste_vide_signifie_aucun_acces(self) -> None:
        assert lisibles(etats.PREPARATION, RH, rh=True) == []

    def test_le_manager_avant_soumission_a_bien_acces_a_la_structure(self) -> None:
        assert peut_lire_les_reponses(
            etats.PREPARATION, MANAGER, COLLAB, MANAGER, lecteur_est_rh=False
        )


class TestEcriture:
    @pytest.mark.parametrize("statut", [etats.PLANIFIE, etats.PREPARATION])
    def test_le_collaborateur_saisit_avant_soumission(self, statut: str) -> None:
        assert peut_ecrire_ses_reponses(statut, COLLAB, COLLAB) is True

    @pytest.mark.parametrize("statut", APRES_SOUMISSION)
    def test_la_soumission_est_irreversible(self, statut: str) -> None:
        assert peut_ecrire_ses_reponses(statut, COLLAB, COLLAB) is False

    def test_le_manager_n_ecrit_pas_les_reponses_du_collaborateur(self) -> None:
        assert peut_ecrire_ses_reponses(etats.PREPARATION, MANAGER, COLLAB) is False


class TestCommentaires:
    @pytest.mark.parametrize("statut", AVANT_SOUMISSION)
    def test_pas_de_commentaire_avant_soumission(self, statut: str) -> None:
        assert peut_commenter(statut, MANAGER, MANAGER) is False

    @pytest.mark.parametrize(
        "statut", [etats.SOUMIS_COLLABORATEUR, etats.REVUE_MANAGER, etats.ENTRETIEN_REALISE]
    )
    def test_commentaire_possible_entre_soumission_et_gel(self, statut: str) -> None:
        assert peut_commenter(statut, MANAGER, MANAGER) is True

    @pytest.mark.parametrize("statut", [etats.SIGNE, etats.CLOTURE])
    def test_plus_de_commentaire_apres_signature(self, statut: str) -> None:
        assert peut_commenter(statut, MANAGER, MANAGER) is False

    def test_le_collaborateur_ne_commente_pas(self) -> None:
        assert peut_commenter(etats.REVUE_MANAGER, COLLAB, MANAGER) is False


class TestEntretienAnnule:
    def test_un_entretien_annule_ne_depasse_aucun_seuil(self) -> None:
        assert COLLAB not in lisibles(etats.ANNULE, MANAGER)
