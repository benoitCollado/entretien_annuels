"""Règles d'attribution des rôles (US-02).

Fonctions pures : elles raisonnent sur des ensembles de codes, sans rien
connaître de la persistance ni du transport.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.core.exceptions import AccesRefuse, DonneesInvalides

ROLE_ADMIN = "ADMIN"


def exiger_roles_connus(codes_demandes: Iterable[str], codes_existants: Iterable[str]) -> None:
    """Tous les rôles demandés doivent exister au référentiel."""
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
    """Seul un administrateur peut conférer le rôle `ADMIN`.

    Sans cette règle, un RH — qui possède déjà `role:attribuer` — pourrait
    s'octroyer les pleins pouvoirs. C'est une escalade de privilèges que le RBAC
    seul n'empêche pas, puisqu'il raisonne sur l'action et non sur sa cible.
    """
    if ROLE_ADMIN in set(codes_roles_demandes) and ROLE_ADMIN not in set(codes_roles_auteur):
        raise AccesRefuse("Seul un administrateur peut attribuer le rôle ADMIN.")


def exiger_pas_auto_modification(identifiant_auteur: object, identifiant_cible: object) -> None:
    """Interdit de modifier ses propres rôles ou d'archiver son propre compte.

    Protège des deux sens : se retirer un rôle par mégarde et se retrouver sans
    accès, ou s'en ajouter un.
    """
    if identifiant_auteur == identifiant_cible:
        raise AccesRefuse("Vous ne pouvez pas modifier votre propre compte par cette voie.")
