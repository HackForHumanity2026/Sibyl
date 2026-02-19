"""FastAPI application entry point."""

import asyncio
import logging
import subprocess
import sys
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.core.database import async_session_maker, engine
from app.services.task_worker import TaskWorker

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Run Alembic migrations via subprocess to avoid event loop conflicts."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info("Database migrations completed successfully")
        if result.stdout:
            logger.debug("Alembic stdout: %s", result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to run migrations: %s", e.stderr)
        # Don't raise - allow app to start even if migrations fail
        # This allows the health check to report degraded status
    except Exception as e:
        logger.error("Failed to run migrations: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Sibyl API...")
    run_migrations()

    # Create Redis client for task worker
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=False)

    # Create and start the task worker
    worker = TaskWorker(redis_client, async_session_maker)
    worker_task = asyncio.create_task(worker.start())
    logger.info("Task worker started")

    yield

    # Shutdown
    logger.info("Shutting down Sibyl API...")

    # Stop the task worker
    await worker.stop()
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    logger.info("Task worker stopped")

    # Close Redis connection
    await redis_client.aclose()

    # Dispose database engine
    await engine.dispose()


app = FastAPI(
    title="Sibyl API",
    version="0.1.0",
    description="Multi-agent AI system for sustainability report verification and IFRS S1/S2 compliance analysis.",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")
