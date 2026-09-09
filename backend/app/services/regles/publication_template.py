from __future__ import annotations

from collections.abc import Iterable, Sequence

from app.core.exceptions import ConflitMetier, DonneesInvalides

BROUILLON = "BROUILLON"
PUBLIEE = "PUBLIEE"
ARCHIVEE = "ARCHIVEE"

TRANSITIONS: dict[str, frozenset[str]] = {
    BROUILLON: frozenset({PUBLIEE}),
    PUBLIEE: frozenset({ARCHIVEE}),
    ARCHIVEE: frozenset(),
}


def est_modifiable(statut: str) -> bool:
    return statut == BROUILLON


def exiger_modifiable(statut: str) -> None:
    if not est_modifiable(statut):
        raise ConflitMetier(
            "Une trame publiée ne se modifie plus. Créez une nouvelle version "
            "pour la faire évoluer."
        )


def exiger_transition(depuis: str, vers: str) -> None:
    if vers not in TRANSITIONS.get(depuis, frozenset()):
        raise ConflitMetier(f"Transition interdite : {depuis} → {vers}.")


def est_instanciable(statut: str) -> bool:
    return statut == PUBLIEE


def exiger_structure_publiable(
    nombres_de_questions_par_section: Sequence[int],
) -> None:
    if not nombres_de_questions_par_section:
        raise DonneesInvalides("Une trame doit comporter au moins une section.")

    sections_vides = [
        position
        for position, nombre in enumerate(nombres_de_questions_par_section, start=1)
        if nombre == 0
    ]
    if sections_vides:
        raise DonneesInvalides(
            "Chaque section doit comporter au moins une question.",
            details=[{"sections_vides": sections_vides}],
        )


def exiger_ordres_valides(ordres: Iterable[int], contexte: str) -> None:
    positions = list(ordres)
    attendues = list(range(len(positions)))

    if sorted(positions) != attendues:
        raise DonneesInvalides(
            f"Les positions de {contexte} doivent être une suite continue à partir de 0.",
            details=[{"recu": positions, "attendu": attendues}],
        )


def version_suivante(version_actuelle: int) -> int:
    return version_actuelle + 1
