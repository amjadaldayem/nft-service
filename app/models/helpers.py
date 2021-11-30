# Helpers for Postgres Database and SqlAlchemy
from app import settings


def sql_db_create_engine():
    """
    Shortcut for creating a SA engine for the specified database from `settings`.

    Returns:

    """
    from sqlalchemy import create_engine
    conn_str = f"postgresql+psycopg2://" \
               f"{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@" \
               f"{settings.POSTGRES_HOST}/{settings.POSTGRES_DATABASE}"
    return create_engine(conn_str)
