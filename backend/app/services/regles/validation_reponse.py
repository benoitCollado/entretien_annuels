from __future__ import annotations

from typing import Any

from app.core.exceptions import DonneesInvalides

TEXTE_LIBRE = "texte_libre"
TEXTE_COURT = "texte_court"
ECHELLE = "echelle"
CHOIX_UNIQUE = "choix_unique"
CHOIX_MULTIPLE = "choix_multiple"
OUI_NON = "oui_non"
DATE = "date"
NOTE_5 = "note_5"

CLE_ATTENDUE: dict[str, str] = {
    TEXTE_LIBRE: "contenu",
    TEXTE_COURT: "contenu",
    ECHELLE: "note",
    NOTE_5: "note",
    CHOIX_UNIQUE: "option",
    CHOIX_MULTIPLE: "options",
    OUI_NON: "valeur",
    DATE: "date",
}


def _refuser(message: str, type_question: str) -> None:
    raise DonneesInvalides(message, details=[{"type_question": type_question}])


def valider(
    type_question: str, valeur: dict[str, Any] | None, configuration: dict[str, Any]
) -> None:
    if valeur is None:
        return

    if not isinstance(valeur, dict):
        _refuser("La valeur d'une réponse doit être un objet.", type_question)

    cle = CLE_ATTENDUE.get(type_question)
    if cle is None:
        _refuser(f"Type de question inconnu : {type_question}.", type_question)

    if cle not in valeur:
        _refuser(f"La clé « {cle} » est attendue pour ce type de question.", type_question)

    contenu = valeur[cle]

    if type_question in (TEXTE_LIBRE, TEXTE_COURT, DATE):
        if not isinstance(contenu, str):
            _refuser(f"« {cle} » doit être une chaîne.", type_question)

    elif type_question == OUI_NON:
        if not isinstance(contenu, bool):
            _refuser("« valeur » doit être un booléen.", type_question)

    elif type_question in (ECHELLE, NOTE_5):
        if not isinstance(contenu, int) or isinstance(contenu, bool):
            _refuser("« note » doit être un entier.", type_question)
        minimum = configuration.get("minimum", 1) if type_question == ECHELLE else 1
        maximum = configuration.get("maximum", 5) if type_question == ECHELLE else 5
        if not minimum <= contenu <= maximum:
            _refuser(f"« note » doit être comprise entre {minimum} et {maximum}.", type_question)

    elif type_question == CHOIX_UNIQUE:
        options = configuration.get("options", [])
        if contenu not in options:
            _refuser("L'option choisie ne fait pas partie des options proposées.", type_question)

    elif type_question == CHOIX_MULTIPLE:
        if not isinstance(contenu, list):
            _refuser("« options » doit être une liste.", type_question)
        options = configuration.get("options", [])
        inconnues = [choix for choix in contenu if choix not in options]
        if inconnues:
            _refuser(f"Options inconnues : {', '.join(map(str, inconnues))}.", type_question)
        if len(set(map(str, contenu))) != len(contenu):
            _refuser("Une option est sélectionnée deux fois.", type_question)


def est_repondue(valeur: dict[str, Any] | None, type_question: str) -> bool:
    if valeur is None:
        return False

    cle = CLE_ATTENDUE.get(type_question)
    if cle is None or cle not in valeur:
        return False

    contenu = valeur[cle]
    if isinstance(contenu, str):
        return bool(contenu.strip())
    if isinstance(contenu, list):
        return len(contenu) > 0
    return contenu is not None
