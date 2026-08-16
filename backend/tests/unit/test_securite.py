"""Hachage et jetons — aucune base, aucun HTTP."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from uuid_utils.compat import uuid7

from app.config import Parametres
from app.core import securite
from app.core.exceptions import NonAuthentifie

MOT_DE_PASSE = "MotDePasseDeTest2026!"


class TestHachage:
    def test_le_hash_ne_contient_pas_le_mot_de_passe(self) -> None:
        empreinte = securite.hacher_mot_de_passe(MOT_DE_PASSE)
        assert MOT_DE_PASSE not in empreinte

    def test_profil_argon2id(self) -> None:
        """OWASP recommande argon2id plutôt que argon2i ou argon2d (§4.4)."""
        assert securite.hacher_mot_de_passe(MOT_DE_PASSE).startswith("$argon2id$")

    def test_deux_hachages_different(self) -> None:
        """Le sel est aléatoire : deux empreintes du même mot de passe diffèrent,
        ce qui interdit les tables précalculées."""
        assert securite.hacher_mot_de_passe(MOT_DE_PASSE) != securite.hacher_mot_de_passe(
            MOT_DE_PASSE
        )

    def test_verification_reussie(self) -> None:
        empreinte = securite.hacher_mot_de_passe(MOT_DE_PASSE)
        assert securite.verifier_mot_de_passe(MOT_DE_PASSE, empreinte) is True

    def test_verification_echouee(self) -> None:
        empreinte = securite.hacher_mot_de_passe(MOT_DE_PASSE)
        assert securite.verifier_mot_de_passe("autre-chose", empreinte) is False

    def test_empreinte_corrompue_ne_leve_pas(self) -> None:
        """L'appelant n'a pas à distinguer « mauvais mot de passe » de
        « empreinte illisible » : les deux se soldent par un refus."""
        assert securite.verifier_mot_de_passe(MOT_DE_PASSE, "pas-une-empreinte") is False

    def test_empreinte_factice_utilisable(self) -> None:
        """Sert à égaliser le temps de réponse quand l'adresse est inconnue."""
        assert securite.verifier_mot_de_passe("n-importe-quoi", securite.EMPREINTE_FACTICE) is False


class TestJetons:
    def test_aller_retour(self, parametres: Parametres) -> None:
        identifiant = uuid7()
        jeton, duree = securite.creer_jeton(identifiant, version_jeton=3)

        assert duree == parametres.duree_jeton_minutes * 60
        assert securite.decoder_jeton(jeton) == (identifiant, 3)

    def test_jeton_altere_refuse(self) -> None:
        jeton, _ = securite.creer_jeton(uuid7(), 1)
        with pytest.raises(NonAuthentifie, match="invalide"):
            securite.decoder_jeton(jeton[:-3] + "abc")

    def test_jeton_signe_avec_une_autre_cle_refuse(self, parametres: Parametres) -> None:
        etranger = jwt.encode(
            {"sub": str(uuid7()), "ver": 1, "exp": 9999999999},
            "une-autre-cle-de-plus-de-32-caracteres",
            algorithm="HS256",
        )
        with pytest.raises(NonAuthentifie):
            securite.decoder_jeton(etranger)

    def test_jeton_expire_refuse(self, parametres: Parametres) -> None:
        passe = datetime.now(UTC) - timedelta(hours=2)
        expire = jwt.encode(
            {"sub": str(uuid7()), "ver": 1, "exp": int(passe.timestamp())},
            parametres.secret_key,
            algorithm="HS256",
        )
        with pytest.raises(NonAuthentifie, match="expirée"):
            securite.decoder_jeton(expire)

    def test_jeton_sans_version_refuse(self, parametres: Parametres) -> None:
        """La version de jeton est le mécanisme de révocation (§7.3) : un jeton
        qui n'en porte pas ne peut pas être validé."""
        sans_version = jwt.encode(
            {"sub": str(uuid7()), "exp": 9999999999},
            parametres.secret_key,
            algorithm="HS256",
        )
        with pytest.raises(NonAuthentifie):
            securite.decoder_jeton(sans_version)

    def test_la_version_est_bien_transportee(self) -> None:
        _, _ = securite.creer_jeton(uuid7(), 1)
        identifiant = uuid7()
        jeton, _ = securite.creer_jeton(identifiant, version_jeton=42)
        assert securite.decoder_jeton(jeton)[1] == 42
