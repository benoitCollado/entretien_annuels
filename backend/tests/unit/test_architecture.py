from __future__ import annotations

import ast
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[2] / "app"

INTERDITS: dict[str, tuple[str, ...]] = {
    "routers": ("from sqlalchemy", "import sqlalchemy", "from app.repositories", "from app.models"),
    "services/regles": ("from sqlalchemy", "from fastapi", "Session"),
    "services/processus": ("from fastapi", "select(", "session.commit"),
    "repositories": ("from fastapi", "from app.services"),
    "services/rendu": ("from sqlalchemy", "from fastapi", "Session", "from app.repositories"),
}


def _fichiers(couche: str) -> list[Path]:
    dossier = RACINE / couche
    if not dossier.is_dir():
        return []
    return sorted(dossier.rglob("*.py"))


@pytest.mark.parametrize(("couche", "motifs"), sorted(INTERDITS.items()))
def test_couche_ne_depasse_pas_ses_responsabilites(couche: str, motifs: tuple[str, ...]) -> None:
    fautes = [
        f"{fichier.relative_to(RACINE)} : « {motif} »"
        for fichier in _fichiers(couche)
        for motif in motifs
        if motif in fichier.read_text(encoding="utf-8")
    ]
    assert not fautes, (
        f"Violations de couche dans {couche}/ :\n  " + "\n  ".join(fautes) + "\n\n"
        "Adapter la conception plutôt que la liste des motifs : un router qui a "
        "besoin de SQLAlchemy signale un traitement mal placé."
    )


def test_les_couches_verifiees_existent() -> None:
    for couche in INTERDITS:
        assert _fichiers(couche), f"aucun fichier analysé dans {couche}/"


def test_endpoints_declares_en_synchrone() -> None:
    fautifs = [
        f"{fichier.name}:{noeud.name}"
        for fichier in _fichiers("routers")
        for noeud in ast.walk(ast.parse(fichier.read_text(encoding="utf-8")))
        if isinstance(noeud, ast.AsyncFunctionDef)
    ]
    assert not fautifs, f"Fonctions asynchrones trouvées : {', '.join(fautifs)}"
