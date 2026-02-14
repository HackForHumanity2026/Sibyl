"""Shared FastAPI dependencies."""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Annotated

import redis.asyncio as redis
from fastapi import Depends

from app.core.config import Settings, settings
from app.core.database import get_db, DbSession

if TYPE_CHECKING:
    from app.services.rag_service import RAGService

# Re-export database dependency
__all__ = [
    "get_db",
    "DbSession",
    "get_settings",
    "SettingsDep",
    "get_rag_service",
    "RAGServiceDep",
    "get_redis",
    "RedisDep",
]


def get_settings() -> Settings:
    """Dependency that returns the application settings singleton."""
    return settings


SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_rag_service(db: DbSession) -> "RAGService":
    """Dependency that provides a RAGService instance.

    Creates a fresh EmbeddingService and RAGService for each request.
    """
    from app.services.embedding_service import EmbeddingService
    from app.services.rag_service import RAGService

    embedding_service = EmbeddingService()
    return RAGService(db, embedding_service)


RAGServiceDep = Annotated["RAGService", Depends(get_rag_service)]


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """Dependency that provides an async Redis client.

    Creates a connection for each request and closes it afterward.
    """
    client = redis.from_url(settings.REDIS_URL, decode_responses=False)
    try:
        yield client
    finally:
        await client.aclose()


RedisDep = Annotated[redis.Redis, Depends(get_redis)]
