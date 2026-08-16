"""Environnement Alembic.

Deux propriétés recherchées :

1. **L'URL vient de l'environnement**, pas de `alembic.ini`. Les tests peuvent
   donc pointer une base jetable en surchargeant simplement l'option
   `sqlalchemy.url` de l'objet `Config` qu'ils construisent.
2. **Le fichier fonctionne sans modèle.** Tant qu'aucun modèle n'est déclaré,
   `target_metadata` vaut `None` : les commandes Alembic restent utilisables et
   le test de dérive se met en attente au lieu d'échouer.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Priorité à ce que le test (ou la ligne de commande) a explicitement fourni.
url = config.get_main_option("sqlalchemy.url") or os.environ.get("DATABASE_URL")
if not url:
    raise RuntimeError(
        "URL de base absente : renseigner DATABASE_URL, ou passer "
        "-x sqlalchemy.url=... à la commande alembic."
    )
config.set_main_option("sqlalchemy.url", url)


def _metadonnees_cible():
    """Métadonnées SQLAlchemy, ou `None` tant qu'aucun modèle n'existe.

    ⚠️ Chaque nouveau module de modèle doit être importé dans
    `app/models/__init__.py`. L'oublier rendrait le test de dérive
    faussement vert : une table absente des métadonnées ne peut produire
    aucune différence.
    """
    try:
        from app.models import Base
    except (ImportError, AttributeError):
        return None
    return Base.metadata


target_metadata = _metadonnees_cible()

# `compare_type` et `compare_server_default` rendent la détection de dérive
# nettement plus fine. Rappel des angles morts d'Alembic (§10.4) : les
# contraintes CHECK, les renommages, les triggers et les vues ne sont PAS
# détectés — d'où les tests de contraintes écrits à la main.
OPTIONS_COMPARAISON = {
    "compare_type": True,
    "compare_server_default": True,
}


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **OPTIONS_COMPARAISON,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            **OPTIONS_COMPARAISON,
        )
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
