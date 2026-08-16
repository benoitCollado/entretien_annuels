"""Règles d'attribution des rôles — aucune base, aucun HTTP."""

from __future__ import annotations

import pytest
from uuid_utils.compat import uuid7

from app.core.exceptions import AccesRefuse, DonneesInvalides
from app.services.regles import rbac

EXISTANTS = ["ADMIN", "RH", "MANAGER", "COLLABORATEUR"]


class TestRolesConnus:
    def test_roles_existants_acceptes(self) -> None:
        rbac.exiger_roles_connus(["RH", "MANAGER"], EXISTANTS)

    def test_role_inconnu_refuse(self) -> None:
        with pytest.raises(DonneesInvalides, match="SUPERVISEUR"):
            rbac.exiger_roles_connus(["RH", "SUPERVISEUR"], EXISTANTS)

    def test_le_message_liste_tous_les_inconnus(self) -> None:
        with pytest.raises(DonneesInvalides) as erreur:
            rbac.exiger_roles_connus(["A", "B"], EXISTANTS)
        assert erreur.value.details[0]["valeurs_invalides"] == ["A", "B"]


class TestEscaladeDePrivileges:
    def test_admin_peut_conferer_admin(self) -> None:
        rbac.exiger_attribution_autorisee(["ADMIN"], ["ADMIN"])

    def test_rh_ne_peut_pas_conferer_admin(self) -> None:
        """Le RH possède `role:attribuer`. Sans cette règle, il pourrait
        s'octroyer les pleins pouvoirs : le RBAC seul ne l'empêche pas,
        puisqu'il raisonne sur l'action et non sur sa cible."""
        with pytest.raises(AccesRefuse, match="administrateur"):
            rbac.exiger_attribution_autorisee(["RH"], ["ADMIN"])

    def test_rh_peut_conferer_les_autres_roles(self) -> None:
        rbac.exiger_attribution_autorisee(["RH"], ["MANAGER", "COLLABORATEUR"])


class TestAutoModification:
    def test_modifier_son_propre_compte_est_refuse(self) -> None:
        identifiant = uuid7()
        with pytest.raises(AccesRefuse):
            rbac.exiger_pas_auto_modification(identifiant, identifiant)

    def test_modifier_un_autre_compte_est_autorise(self) -> None:
        rbac.exiger_pas_auto_modification(uuid7(), uuid7())
