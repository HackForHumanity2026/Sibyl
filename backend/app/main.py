"""FastAPI application entry point."""

import logging
import subprocess
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.core.database import engine

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
    yield
    # Shutdown
    logger.info("Shutting down Sibyl API...")
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
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")
