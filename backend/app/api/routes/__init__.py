"""API routes aggregator."""

from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.upload import router as upload_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.stream import router as stream_router
from app.api.routes.report import router as report_router
from app.api.routes.reports import router as reports_router
from app.api.routes.chat import router as chat_router
from app.api.routes.rag import router as rag_router
from app.api.routes.satellite import router as satellite_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
api_router.include_router(stream_router, prefix="/stream", tags=["stream"])
api_router.include_router(report_router, prefix="/report", tags=["report"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(rag_router, prefix="/rag", tags=["RAG Pipeline"])
api_router.include_router(satellite_router, prefix="/satellite", tags=["satellite"])
