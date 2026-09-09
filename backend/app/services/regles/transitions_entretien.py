from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions import ConflitMetier

BROUILLON = "BROUILLON"
PLANIFIE = "PLANIFIE"
PREPARATION = "PREPARATION"
SOUMIS_COLLABORATEUR = "SOUMIS_COLLABORATEUR"
REVUE_MANAGER = "REVUE_MANAGER"
ENTRETIEN_REALISE = "ENTRETIEN_REALISE"
SIGNE = "SIGNE"
CLOTURE = "CLOTURE"
ANNULE = "ANNULE"

COLLABORATEUR = "COLLABORATEUR"
MANAGER = "MANAGER"
RH = "RH"


@dataclass(frozen=True, slots=True)
class Transition:
    depuis: str
    vers: str
    acteurs: frozenset[str]


TRANSITIONS: tuple[Transition, ...] = (
    Transition(BROUILLON, PLANIFIE, frozenset({MANAGER, RH})),
    Transition(PLANIFIE, PREPARATION, frozenset({COLLABORATEUR})),
    Transition(PREPARATION, SOUMIS_COLLABORATEUR, frozenset({COLLABORATEUR})),
    Transition(SOUMIS_COLLABORATEUR, REVUE_MANAGER, frozenset({MANAGER})),
    Transition(REVUE_MANAGER, ENTRETIEN_REALISE, frozenset({MANAGER})),
    Transition(ENTRETIEN_REALISE, SIGNE, frozenset({COLLABORATEUR, MANAGER})),
    Transition(SIGNE, CLOTURE, frozenset({RH})),
)

STATUTS_TERMINAUX = frozenset({CLOTURE, ANNULE})

ORDRE_STATUTS: dict[str, int] = {
    BROUILLON: 0,
    PLANIFIE: 1,
    PREPARATION: 2,
    SOUMIS_COLLABORATEUR: 3,
    REVUE_MANAGER: 4,
    ENTRETIEN_REALISE: 5,
    SIGNE: 6,
    CLOTURE: 7,
    ANNULE: -1,
}


def transition_autorisee(depuis: str, vers: str, acteur: str) -> bool:
    if vers == ANNULE:
        return acteur == RH and depuis not in STATUTS_TERMINAUX
    return any(
        transition.depuis == depuis and transition.vers == vers and acteur in transition.acteurs
        for transition in TRANSITIONS
    )


def exiger_transition(depuis: str, vers: str, acteur: str) -> None:
    if not transition_autorisee(depuis, vers, acteur):
        raise ConflitMetier(
            f"Transition {depuis} → {vers} interdite pour {acteur}.",
            details=[{"depuis": depuis, "vers": vers, "acteur": acteur}],
        )


def est_terminal(statut: str) -> bool:
    return statut in STATUTS_TERMINAUX


def au_moins(statut: str, seuil: str) -> bool:
    if statut == ANNULE:
        return False
    return ORDRE_STATUTS[statut] >= ORDRE_STATUTS[seuil]


def transitions_possibles(depuis: str, acteur: str) -> list[str]:
    possibles = [
        transition.vers
        for transition in TRANSITIONS
        if transition.depuis == depuis and acteur in transition.acteurs
    ]
    if acteur == RH and depuis not in STATUTS_TERMINAUX:
        possibles.append(ANNULE)
    return possibles
