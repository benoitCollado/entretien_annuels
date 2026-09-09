from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.core.exceptions import ConflitMetier
from app.services.regles import transitions_entretien as etats
from app.services.regles.signature import (
    deja_signe,
    double_signature_acquise,
    exiger_droit_de_signer,
    exiger_signature_unique,
    observation_autorisee,
    peut_signer,
)

T1 = datetime(2026, 3, 1, 10, 0, tzinfo=UTC)
T2 = datetime(2026, 3, 1, 11, 0, tzinfo=UTC)


class TestQuiPeutSigner:
    @pytest.mark.parametrize("role", [etats.COLLABORATEUR, etats.MANAGER])
    def test_les_deux_acteurs_signent(self, role: str) -> None:
        assert peut_signer(etats.ENTRETIEN_REALISE, role) is True

    def test_le_rh_ne_signe_pas(self) -> None:
        assert peut_signer(etats.ENTRETIEN_REALISE, etats.RH) is False

    def test_un_tiers_ne_signe_pas(self) -> None:
        assert peut_signer(etats.ENTRETIEN_REALISE, None) is False

    @pytest.mark.parametrize(
        "statut",
        [etats.PREPARATION, etats.SOUMIS_COLLABORATEUR, etats.REVUE_MANAGER, etats.SIGNE],
    )
    def test_uniquement_apres_l_entretien(self, statut: str) -> None:
        assert peut_signer(statut, etats.COLLABORATEUR) is False

    def test_le_refus_est_explicite(self) -> None:
        with pytest.raises(ConflitMetier, match="réalisé"):
            exiger_droit_de_signer(etats.REVUE_MANAGER, etats.MANAGER)
        with pytest.raises(ConflitMetier, match="collaborateur et le manager"):
            exiger_droit_de_signer(etats.ENTRETIEN_REALISE, etats.RH)


class TestDoubleSignature:
    def test_une_seule_signature_ne_suffit_pas(self) -> None:
        assert double_signature_acquise(T1, None) is False
        assert double_signature_acquise(None, T1) is False

    def test_les_deux_signatures_suffisent(self) -> None:
        assert double_signature_acquise(T1, T2) is True

    def test_l_ordre_est_indifferent(self) -> None:
        assert double_signature_acquise(T1, T2) is double_signature_acquise(T2, T1)

    def test_aucune_signature(self) -> None:
        assert double_signature_acquise(None, None) is False


class TestSignatureUnique:
    def test_resigner_est_refuse(self) -> None:
        with pytest.raises(ConflitMetier, match="déjà signé"):
            exiger_signature_unique(etats.COLLABORATEUR, T1, None)

    def test_le_manager_peut_signer_apres_le_collaborateur(self) -> None:
        exiger_signature_unique(etats.MANAGER, T1, None)

    def test_deja_signe_regarde_le_bon_horodatage(self) -> None:
        assert deja_signe(etats.COLLABORATEUR, T1, None) is True
        assert deja_signe(etats.MANAGER, T1, None) is False


class TestDroitDeReserve:
    def test_l_observation_appartient_au_collaborateur(self) -> None:
        assert observation_autorisee(etats.COLLABORATEUR) is True

    def test_le_manager_a_deja_la_synthese(self) -> None:
        assert observation_autorisee(etats.MANAGER) is False
