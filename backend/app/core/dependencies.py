"""Shared FastAPI dependencies."""

from typing import TYPE_CHECKING, Annotated

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
