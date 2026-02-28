"""Database configuration and session management."""

import logging
from collections.abc import AsyncGenerator
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy import String, Text, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session
from uuid_utils import uuid7

from app.core.config import settings
from app.core.sanitize import sanitize_for_pg, sanitize_string

logger = logging.getLogger(__name__)


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


# =============================================================================
# PostgreSQL Sanitization Event Listener
# =============================================================================

# Column types that need sanitization for PostgreSQL compatibility
_SANITIZABLE_TYPES = (String, Text)


def _sanitize_model_instance(instance: Any) -> None:
    """Sanitize all string and JSONB columns on a model instance.
    
    This ensures no null bytes or unpaired surrogates reach PostgreSQL.
    """
    mapper = instance.__class__.__mapper__
    
    for column in mapper.columns:
        # Get the column type
        col_type = column.type
        
        # Check if this column needs sanitization
        if isinstance(col_type, _SANITIZABLE_TYPES):
            # Get current value
            value = getattr(instance, column.key, None)
            if value is not None and isinstance(value, str):
                sanitized = sanitize_string(value)
                if sanitized != value:
                    setattr(instance, column.key, sanitized)
                    logger.debug(
                        "Sanitized %s.%s (removed invalid chars)",
                        instance.__class__.__name__,
                        column.key,
                    )
        
        elif isinstance(col_type, JSONB):
            # Recursively sanitize JSONB values
            value = getattr(instance, column.key, None)
            if value is not None:
                sanitized = sanitize_for_pg(value)
                if sanitized != value:
                    setattr(instance, column.key, sanitized)
                    logger.debug(
                        "Sanitized %s.%s (JSONB, removed invalid chars)",
                        instance.__class__.__name__,
                        column.key,
                    )


@event.listens_for(Session, "before_flush")
def _sanitize_before_flush(
    session: Session,
    flush_context: Any,
    instances: Any,
) -> None:
    """SQLAlchemy event listener that sanitizes all new/dirty objects before flush.
    
    This is the nuclear option that catches ALL data going to the database,
    regardless of which code path wrote it. It ensures that null bytes and
    other PostgreSQL-incompatible characters never reach the database.
    """
    # Sanitize new objects
    for instance in session.new:
        if hasattr(instance, "__mapper__"):
            _sanitize_model_instance(instance)
    
    # Sanitize dirty (modified) objects
    for instance in session.dirty:
        if hasattr(instance, "__mapper__"):
            _sanitize_model_instance(instance)
