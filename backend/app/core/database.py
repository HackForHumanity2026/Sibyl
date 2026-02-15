"""Database configuration and session management."""

from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from uuid_utils import uuid7

from app.core.config import settings


def generate_uuid7() -> UUID:
    """Generate a UUID v7 and return as stdlib uuid.UUID for psycopg3 compatibility."""
    return UUID(str(uuid7()))

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that yields an async database session.

    Handles commit on success and rollback on exception.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async generator that yields a database session.
    
    For use outside of FastAPI dependency injection (e.g., in LangGraph nodes).
    Does NOT auto-commit; caller is responsible for commit/rollback.
    """
    async with async_session_maker() as session:
        yield session


# Type alias for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
