"""Cohérence de la lignée Alembic — sans base de données.

Ces tests s'exécutent en quelques millisecondes et tournent dans le job
unitaire de la CI. Ils attrapent l'accident le plus fréquent et le plus
pénible à réparer : deux têtes divergentes après la fusion de deux branches
git ayant chacune ajouté une migration.
"""

from __future__ import annotations

import ast
import re

import pytest

from tests.migrations.conftest import (
    config_alembic,
    fichiers_de_migration,
    repertoire_scripts,
)

MOTIF_NOM_FICHIER = re.compile(r"^\d{8}_[0-9a-f]+_[a-z0-9_]+\.py$")


def test_configuration_alembic_est_lisible() -> None:
    """Actif dès maintenant : garantit qu'alembic.ini et env.py sont cohérents."""
    config = config_alembic("postgresql+psycopg://ignore/ignore")
    assert config.get_main_option("script_location")


def test_au_plus_une_tete() -> None:
    """Une seule tête, toujours.

    Volontairement formulé « au plus une » plutôt que « exactement une » : le
    test est ainsi actif dès le premier jour, avant même la première
    migration, et échoue dès qu'une divergence apparaît.
    """
    tetes = repertoire_scripts().get_heads()
    assert len(tetes) <= 1, (
        f"{len(tetes)} têtes Alembic : {tetes}. Deux branches ont ajouté une "
        "migration en parallèle — les fusionner avec `alembic merge`."
    )


def test_chaine_sans_trou(exige_des_revisions: None) -> None:
    """Chaque révision pointe une parente qui existe, et une seule racine."""
    scripts = repertoire_scripts()
    revisions = list(scripts.walk_revisions())
    connues = {rev.revision for rev in revisions}

    racines = [rev for rev in revisions if rev.down_revision is None]
    assert len(racines) == 1, f"{len(racines)} révisions racines, une seule attendue"

    for revision in revisions:
        if revision.down_revision is None:
            continue
        parentes = (
            revision.down_revision
            if isinstance(revision.down_revision, tuple)
            else (revision.down_revision,)
        )
        for parente in parentes:
            assert parente in connues, (
                f"la révision {revision.revision} référence une parente inconnue : {parente}"
            )


def test_chaque_migration_a_un_downgrade_effectif(exige_des_revisions: None) -> None:
    """Un `downgrade()` réduit à `pass` rend la migration irréversible.

    On analyse l'arbre syntaxique plutôt que le texte : un commentaire ou une
    docstring ne doit pas faire passer le test pour une implémentation.
    """
    fautifs: list[str] = []

    for fichier in fichiers_de_migration():
        arbre = ast.parse(fichier.read_text(encoding="utf-8"))
        for noeud in ast.walk(arbre):
            if not (isinstance(noeud, ast.FunctionDef) and noeud.name == "downgrade"):
                continue
            corps = [
                instruction
                for instruction in noeud.body
                if not isinstance(instruction, ast.Pass)
                and not (
                    isinstance(instruction, ast.Expr)
                    and isinstance(instruction.value, ast.Constant)
                )
            ]
            if not corps:
                fautifs.append(fichier.name)

    assert not fautifs, (
        "downgrade() vide dans : " + ", ".join(fautifs) + ".\n"
        "Si l'irréversibilité est assumée (perte de données), le documenter "
        "explicitement dans la migration et adapter ce test plutôt que de le "
        "contourner."
    )


@pytest.mark.parametrize(
    "fichier", fichiers_de_migration() or [pytest.param(None, marks=pytest.mark.skip)]
)
def test_nommage_des_fichiers(fichier) -> None:
    """`AAAAMMJJ_<revision>_<slug>.py`, imposé par `file_template`.

    L'ordre lexicographique du dossier correspond alors à l'ordre
    chronologique, ce qui rend l'historique lisible d'un coup d'œil.
    """
    assert MOTIF_NOM_FICHIER.match(fichier.name), (
        f"{fichier.name} ne suit pas le gabarit AAAAMMJJ_<revision>_<slug>.py"
    )
