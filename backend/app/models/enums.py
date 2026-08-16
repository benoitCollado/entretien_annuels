"""Énumérations du domaine.

Déclarées en Python et persistées en `VARCHAR + CHECK`, jamais en type ENUM
PostgreSQL natif : un enum natif est pénible à faire évoluer en migration
Alembic, alors qu'un CHECK se remplace par un DROP puis un ADD (§4.2).
"""

from __future__ import annotations

from enum import StrEnum


class CodeRole(StrEnum):
    """Rôles RBAC du référentiel (US-02)."""

    COLLABORATEUR = "COLLABORATEUR"
    MANAGER = "MANAGER"
    RH = "RH"
    ADMIN = "ADMIN"


class CodePermission(StrEnum):
    """Permissions atomiques, au format `ressource:action`.

    Le RBAC répond à « ce rôle peut-il faire cette action ? ». Il ne dit rien du
    périmètre — « cet utilisateur-là, précisément ? » relève du contrôle de
    portée, porté par `services/regles/portee_hierarchique.py` (§6.1).
    """

    UTILISATEUR_LIRE = "utilisateur:lire"
    UTILISATEUR_CREER = "utilisateur:creer"
    UTILISATEUR_MODIFIER = "utilisateur:modifier"
    UTILISATEUR_ARCHIVER = "utilisateur:archiver"
    ROLE_LIRE = "role:lire"
    ROLE_ATTRIBUER = "role:attribuer"


# Attribution des permissions aux rôles. Source unique : la migration de
# données 0002 et le seed s'appuient dessus, ce qui interdit toute divergence
# entre le code et le référentiel en base.
PERMISSIONS_PAR_ROLE: dict[CodeRole, tuple[CodePermission, ...]] = {
    CodeRole.ADMIN: tuple(CodePermission),
    CodeRole.RH: (
        CodePermission.UTILISATEUR_LIRE,
        CodePermission.UTILISATEUR_CREER,
        CodePermission.UTILISATEUR_MODIFIER,
        CodePermission.ROLE_LIRE,
    ),
    CodeRole.MANAGER: (
        CodePermission.UTILISATEUR_LIRE,
        CodePermission.ROLE_LIRE,
    ),
    CodeRole.COLLABORATEUR: (),
}

LIBELLES_ROLE: dict[CodeRole, str] = {
    CodeRole.COLLABORATEUR: "Collaborateur",
    CodeRole.MANAGER: "Manager",
    CodeRole.RH: "Responsable RH",
    CodeRole.ADMIN: "Administrateur",
}

LIBELLES_PERMISSION: dict[CodePermission, str] = {
    CodePermission.UTILISATEUR_LIRE: "Consulter les utilisateurs",
    CodePermission.UTILISATEUR_CREER: "Créer un utilisateur",
    CodePermission.UTILISATEUR_MODIFIER: "Modifier un utilisateur",
    CodePermission.UTILISATEUR_ARCHIVER: "Archiver un utilisateur",
    CodePermission.ROLE_LIRE: "Consulter les rôles",
    CodePermission.ROLE_ATTRIBUER: "Attribuer un rôle",
}
