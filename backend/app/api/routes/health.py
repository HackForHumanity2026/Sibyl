"""Health check endpoint."""

import redis.asyncio as redis
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Health check endpoint that verifies database and Redis connectivity.

    Returns:
        JSON with status, database, redis, and version fields
    """
    status = "healthy"
    db_status = "connected"
    redis_status = "connected"

    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"
        status = "degraded"

    # Check Redis connectivity
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.aclose()
    except Exception:
        redis_status = "disconnected"
        status = "degraded"

    return {
        "status": status,
        "database": db_status,
        "redis": redis_status,
        "version": "0.1.0",
    }
