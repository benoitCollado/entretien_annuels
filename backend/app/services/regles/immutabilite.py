from __future__ import annotations

from app.core.exceptions import ConflitMetier
from app.services.regles.transitions_entretien import SIGNE, au_moins


def est_gele(statut: str) -> bool:
    return au_moins(statut, SIGNE)


def exiger_non_gele(statut: str, quoi: str = "Cet élément") -> None:
    if est_gele(statut):
        raise ConflitMetier(
            f"{quoi} ne peut plus être modifié : l'entretien est signé.",
            details=[{"statut": statut}],
        )
