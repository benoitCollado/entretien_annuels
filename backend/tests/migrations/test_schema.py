"""Application des migrations sur une base PostgreSQL jetable.

Quatre propriétés vérifiées :

1. les migrations s'appliquent depuis une base vierge ;
2. les rejouer ne casse rien — c'est le scénario du conteneur `migrate`
   redémarré ;
3. elles sont réellement réversibles, globalement et pas à pas ;
4. le schéma migré et les modèles SQLAlchemy ne divergent pas.
"""

from __future__ import annotations

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text

from tests.migrations.conftest import config_alembic, revisions_existantes

pytestmark = pytest.mark.migrations


# ---------------------------------------------------------------------------
# Introspection du schéma
# ---------------------------------------------------------------------------
REQUETE_COLONNES = """
SELECT table_name, column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, column_name
"""

REQUETE_CONTRAINTES = """
SELECT c.relname, con.conname, con.contype, con.condeferrable, con.condeferred,
       pg_get_constraintdef(con.oid)
FROM pg_constraint con
JOIN pg_class c ON c.oid = con.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
ORDER BY c.relname, con.conname
"""

REQUETE_INDEX = """
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname
"""


def empreinte_schema(url: str) -> dict[str, list[tuple]]:
    """Photographie déterministe du schéma, comparable d'une exécution à l'autre.

    `alembic_version` est exclue : son contenu varie légitimement selon la
    position dans l'historique.
    """
    moteur = create_engine(url)
    try:
        with moteur.connect() as connexion:
            return {
                "colonnes": [
                    tuple(ligne)
                    for ligne in connexion.execute(text(REQUETE_COLONNES))
                    if ligne[0] != "alembic_version"
                ],
                "contraintes": [
                    tuple(ligne)
                    for ligne in connexion.execute(text(REQUETE_CONTRAINTES))
                    if ligne[0] != "alembic_version"
                ],
                "index": [
                    tuple(ligne)
                    for ligne in connexion.execute(text(REQUETE_INDEX))
                    if ligne[0] != "alembic_version"
                ],
            }
    finally:
        moteur.dispose()


def tables_applicatives(url: str) -> set[str]:
    moteur = create_engine(url)
    try:
        with moteur.connect() as connexion:
            resultat = connexion.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
                )
            )
            return {ligne[0] for ligne in resultat if ligne[0] != "alembic_version"}
    finally:
        moteur.dispose()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_upgrade_depuis_base_vierge(url_base_vierge: str, exige_des_revisions: None) -> None:
    config = config_alembic(url_base_vierge)
    command.upgrade(config, "head")

    moteur = create_engine(url_base_vierge)
    try:
        with moteur.connect() as connexion:
            version = connexion.execute(text("SELECT version_num FROM alembic_version")).scalar()
    finally:
        moteur.dispose()

    assert version == revisions_existantes()[-1]
    assert tables_applicatives(url_base_vierge), "aucune table créée par les migrations"


def test_upgrade_est_idempotent(url_base_vierge: str, exige_des_revisions: None) -> None:
    """Rejouer `upgrade head` ne doit rien faire et ne rien casser.

    C'est exactement ce qui se produit quand le service `migrate` du compose
    redémarre : sans cette propriété, un simple `docker compose up` après une
    coupure deviendrait un incident.
    """
    config = config_alembic(url_base_vierge)
    command.upgrade(config, "head")
    empreinte_avant = empreinte_schema(url_base_vierge)

    command.upgrade(config, "head")

    assert empreinte_schema(url_base_vierge) == empreinte_avant


def test_reversibilite_globale(url_base_vierge: str, exige_des_revisions: None) -> None:
    """Montée, descente complète, remontée : le schéma doit être identique."""
    config = config_alembic(url_base_vierge)

    command.upgrade(config, "head")
    empreinte_initiale = empreinte_schema(url_base_vierge)

    command.downgrade(config, "base")
    restantes = tables_applicatives(url_base_vierge)
    assert not restantes, f"tables laissées derrière par le downgrade : {sorted(restantes)}"

    command.upgrade(config, "head")
    assert empreinte_schema(url_base_vierge) == empreinte_initiale


@pytest.mark.parametrize(
    "revision", revisions_existantes() or [pytest.param(None, marks=pytest.mark.skip)]
)
def test_reversibilite_pas_a_pas(url_base_vierge: str, revision: str) -> None:
    """Descendre puis remonter d'un seul cran, sur chaque révision.

    Sans ce test, un `downgrade()` bâclé sur une révision intermédiaire reste
    invisible : la révision suivante recrée souvent ce que la précédente avait
    mal défait, et l'aller-retour global passe malgré tout.
    """
    config = config_alembic(url_base_vierge)

    command.upgrade(config, revision)
    empreinte_attendue = empreinte_schema(url_base_vierge)

    command.downgrade(config, "-1")
    command.upgrade(config, revision)

    assert empreinte_schema(url_base_vierge) == empreinte_attendue, (
        f"la révision {revision} n'est pas réversible proprement"
    )


def test_aucune_derive_entre_modeles_et_migrations(url_base_vierge: str) -> None:
    """Les modèles SQLAlchemy décrivent-ils exactement le schéma migré ?

    C'est le test qui rattrape l'erreur la plus fréquente du quotidien :
    modifier un modèle sans générer la migration correspondante.

    Angles morts assumés (§10.4) : `compare_metadata` ne voit ni les
    contraintes CHECK, ni les renommages, ni les triggers, vues et extensions.
    Ils relèvent de tests écrits à la main et de la relecture de chaque
    migration générée.
    """
    try:
        from app.models import Base
    except (ImportError, AttributeError):
        pytest.skip("aucun modèle déclaré dans app/models : rien à comparer")

    metadonnees = Base.metadata
    if not metadonnees.tables:
        pytest.skip("métadonnées vides : aucun modèle importé dans app/models/__init__.py")

    command.upgrade(config_alembic(url_base_vierge), "head")

    moteur = create_engine(url_base_vierge)
    try:
        with moteur.connect() as connexion:
            contexte = MigrationContext.configure(
                connexion,
                opts={"compare_type": True, "compare_server_default": True},
            )
            differences = compare_metadata(contexte, metadonnees)
    finally:
        moteur.dispose()

    assert not differences, "dérive entre les modèles et le schéma migré :\n" + "\n".join(
        repr(difference) for difference in differences
    )
