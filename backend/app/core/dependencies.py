"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, settings
from app.core.database import get_db, DbSession

# Re-export database dependency
__all__ = ["get_db", "DbSession", "get_settings", "SettingsDep"]


def get_settings() -> Settings:
    """Dependency that returns the application settings singleton."""
    return settings


SettingsDep = Annotated[Settings, Depends(get_settings)]
