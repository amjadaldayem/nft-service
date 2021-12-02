# Helpers for Postgres Database and SqlAlchemy
import contextlib

from sqlalchemy.orm import sessionmaker
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


_default_engine = None


def sql_db_get_session(engine=None, expire_on_commit=False):
    global _default_engine
    if not _default_engine:
        _default_engine = sql_db_create_engine()
    if not engine:
        engine = _default_engine
    return sessionmaker(engine, expire_on_commit=expire_on_commit)()


@contextlib.contextmanager
def sql_db_session(engine=None, expire_on_commit=False):
    sess = sql_db_get_session(engine, expire_on_commit)
    try:
        yield sess
        sess.commit()
    except:  # noqa
        raise
    finally:
        sess.close()
