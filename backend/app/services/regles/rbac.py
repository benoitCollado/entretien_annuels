from __future__ import annotations

from collections.abc import Iterable

from app.core.exceptions import AccesRefuse, DonneesInvalides

ROLE_ADMIN = "ADMIN"


def exiger_roles_connus(codes_demandes: Iterable[str], codes_existants: Iterable[str]) -> None:
    inconnus = sorted(set(codes_demandes) - set(codes_existants))
    if inconnus:
        raise DonneesInvalides(
            "Rôle inconnu : " + ", ".join(inconnus),
            details=[{"champ": "roles", "valeurs_invalides": inconnus}],
        )


def exiger_attribution_autorisee(
    codes_roles_auteur: Iterable[str],
    codes_roles_demandes: Iterable[str],
) -> None:
    if ROLE_ADMIN in set(codes_roles_demandes) and ROLE_ADMIN not in set(codes_roles_auteur):
        raise AccesRefuse("Seul un administrateur peut attribuer le rôle ADMIN.")


def exiger_pas_auto_modification(identifiant_auteur: object, identifiant_cible: object) -> None:
    if identifiant_auteur == identifiant_cible:
        raise AccesRefuse("Vous ne pouvez pas modifier votre propre compte par cette voie.")
