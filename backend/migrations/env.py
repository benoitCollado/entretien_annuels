from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

url = config.get_main_option("sqlalchemy.url") or os.environ.get("DATABASE_URL")
if not url:
    raise RuntimeError(
        "URL de base absente : renseigner DATABASE_URL, ou passer "
        "-x sqlalchemy.url=... à la commande alembic."
    )
config.set_main_option("sqlalchemy.url", url)


def _metadonnees_cible():
    try:
        from app.models import Base
    except (ImportError, AttributeError):
        return None
    return Base.metadata


target_metadata = _metadonnees_cible()

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
