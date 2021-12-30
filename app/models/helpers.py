# Helpers for Postgres Database and SqlAlchemy
import asyncio
import contextlib

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app import settings


def pg_create_engine():
    """
    Shortcut for creating a SA engine for the specified database from `settings`.

    Returns:

    """
    from sqlalchemy import create_engine
    conn_str = f"postgresql+psycopg2://" \
               f"{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@" \
               f"{settings.POSTGRES_HOST}/{settings.POSTGRES_DATABASE}"
    return create_engine(conn_str)


async def pg_create_async_engine(echo=False) -> AsyncEngine:
    conn_str = f"postgresql+asyncpg://" \
               f"{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@" \
               f"{settings.POSTGRES_HOST}/{settings.POSTGRES_DATABASE}"
    return create_async_engine(
        conn_str, echo=echo,
    )


_default_engine = None


def pg_get_session(engine=None, expire_on_commit=False):
    """
    Examples:

        async with pg_get_session() as session:
            # work with your session here
            stmt = select(A).options(selectinload(A.bs))
            result = await session.execute(stmt...)

    Args:
        engine:
        expire_on_commit:

    Returns:

    """
    global _default_engine
    if not _default_engine:
        _default_engine = asyncio.run(pg_create_async_engine())
    if not engine:
        engine = _default_engine
    return sessionmaker(
        engine,
        expire_on_commit=expire_on_commit,
        class_=AsyncSession
    )
