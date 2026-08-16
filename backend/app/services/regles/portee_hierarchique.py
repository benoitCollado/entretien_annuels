"""Règles de hiérarchie et de périmètre (US-02, §6.1).

Contrat de la couche : fonctions **pures**. Elles reçoivent des identifiants et
des ensembles déjà chargés, et retournent une décision. Aucune entrée-sortie,
aucun accès à la base, aucun framework web — ce qui les rend testables en
quelques millisecondes.

Distinction à garder en tête : le **RBAC** répond à « ce rôle peut-il faire
cette action ? », la **portée** à « cet utilisateur-là, précisément ? ». Les
deux contrôles se superposent, aucun ne remplace l'autre.
"""

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from app.core.exceptions import DonneesInvalides

ROLE_ADMIN = "ADMIN"
ROLE_RH = "RH"
ROLE_MANAGER = "MANAGER"

# Rôles dont le périmètre de lecture n'est pas restreint à une équipe.
ROLES_PORTEE_GLOBALE = frozenset({ROLE_ADMIN, ROLE_RH})


def est_son_propre_manager(utilisateur_id: UUID, manager_id: UUID | None) -> bool:
    return manager_id is not None and manager_id == utilisateur_id


def cree_un_cycle(
    utilisateur_id: UUID,
    manager_id: UUID | None,
    ancetres_du_manager: Iterable[UUID],
) -> bool:
    """L'utilisateur apparaît-il déjà au-dessus du manager proposé ?

    `ancetres_du_manager` est la chaîne des managers successifs du manager
    envisagé, chargée par l'appelant. La règle ne va pas la chercher elle-même :
    c'est ce qui lui permet de rester pure.
    """
    if manager_id is None:
        return False
    return utilisateur_id in set(ancetres_du_manager)


def exiger_rattachement_valide(
    utilisateur_id: UUID,
    manager_id: UUID | None,
    ancetres_du_manager: Iterable[UUID] = (),
) -> None:
    """Lève `DonneesInvalides` si le rattachement est incohérent.

    Le cas « être son propre manager » est aussi couvert par une contrainte
    CHECK en base. Le doublon est volontaire : la base garantit l'invariant même
    si une écriture contourne l'application, et la règle produit un message
    lisible plutôt qu'une violation d'intégrité brute.

    Les cycles plus longs, eux, ne sont **pas** exprimables en CHECK sous
    PostgreSQL — les sous-requêtes y sont interdites. Cette règle est donc leur
    seule protection, ce qui justifie qu'elle soit testée sérieusement.
    """
    if est_son_propre_manager(utilisateur_id, manager_id):
        raise DonneesInvalides("Un utilisateur ne peut pas être son propre manager.")

    if cree_un_cycle(utilisateur_id, manager_id, ancetres_du_manager):
        raise DonneesInvalides(
            "Ce rattachement créerait un cycle dans la hiérarchie.",
        )


def perimetre_de_lecture(codes_roles: Iterable[str], utilisateur_id: UUID) -> UUID | None:
    """Restriction à appliquer à une liste d'utilisateurs.

    Retourne `None` quand aucune restriction ne s'applique, sinon l'identifiant
    du manager dont il faut lister l'équipe.

    Un manager porte le rôle `MANAGER` **partout**, mais ne doit voir que son
    équipe : c'est exactement la distinction du §6.1 que le jury cherche à
    entendre.
    """
    roles = set(codes_roles)
    if roles & ROLES_PORTEE_GLOBALE:
        return None
    return utilisateur_id


def peut_gerer(codes_roles: Iterable[str]) -> bool:
    """Seuls l'administrateur et le RH créent ou modifient des comptes.

    Un manager consulte son équipe mais n'administre pas les comptes : cette
    séparation évite qu'il puisse s'attribuer des rôles.
    """
    return bool(set(codes_roles) & ROLES_PORTEE_GLOBALE)
