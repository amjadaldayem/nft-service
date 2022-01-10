import asyncio
from logging.config import fileConfig

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
from sqlalchemy import engine_from_config, pool

from app import settings
from app.models.manager import SQLDBManager
from app.models.models import Base

config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata


def parse_db_alias(section_name) -> str:
    """

    Args:
        section_name:

    Returns:
        The actual db name.
    """
    section = config.get_section(config.config_ini_section)
    if not section:
        raise ValueError(f"Section {section_name} not found.")
    db_alias = section_name.rsplit('-', 1)[-1]
    if db_alias not in settings.DATABASES:
        raise ValueError(f"Database alias {db_alias} not found.")
    db = settings.DATABASES[db_alias]['name']
    return db


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    # Overrides DB name from command line (-x) -xdb=nft
    db = context.get_x_argument(as_dictionary=True).get('db')
    manager = SQLDBManager.create(db)
    connectable = manager.engine
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Extract the db name from the section name
    # e.g. database-nft -> nft
    db = parse_db_alias(config.config_ini_section)
    manager = SQLDBManager.create(db)
    connectable = manager.engine

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
