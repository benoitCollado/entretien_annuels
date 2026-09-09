from __future__ import annotations

from datetime import date

from app.core.exceptions import ConflitMetier, DonneesInvalides

BROUILLON = "BROUILLON"
OUVERTE = "OUVERTE"
CLOTUREE = "CLOTUREE"

TRANSITIONS: dict[str, frozenset[str]] = {
    BROUILLON: frozenset({OUVERTE, CLOTUREE}),
    OUVERTE: frozenset({CLOTUREE}),
    CLOTUREE: frozenset(),
}


def exiger_dates_coherentes(date_ouverture: date, date_limite: date) -> None:
    if date_limite <= date_ouverture:
        raise DonneesInvalides(
            "La date limite doit être postérieure à la date d'ouverture.",
            details=[{"date_ouverture": str(date_ouverture), "date_limite": str(date_limite)}],
        )


def exiger_annee_coherente(annee: int, date_ouverture: date) -> None:
    if annee != date_ouverture.year:
        raise DonneesInvalides(
            f"L'année {annee} ne correspond pas à la date d'ouverture ({date_ouverture.year}).",
        )


def exiger_transition(depuis: str, vers: str) -> None:
    if vers not in TRANSITIONS.get(depuis, frozenset()):
        raise ConflitMetier(f"Transition interdite : {depuis} → {vers}.")


def accepte_des_entretiens(statut: str) -> bool:
    return statut == OUVERTE


def est_echue(date_limite: date, aujourdhui: date) -> bool:
    return aujourdhui > date_limite


def exiger_types_compatibles(type_campagne: str, type_template: str) -> None:
    if type_campagne != type_template:
        raise DonneesInvalides(
            f"Une campagne de type {type_campagne} ne peut pas utiliser une "
            f"trame de type {type_template}.",
        )
