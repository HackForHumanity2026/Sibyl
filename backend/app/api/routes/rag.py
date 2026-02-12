"""RAG Pipeline API routes.

Implements FRD 1 (RAG Pipeline) Section 7 - Backend Endpoints.

Provides:
- POST /ingest -- trigger corpus ingestion
- GET /stats -- return embedding counts
- POST /search -- search the RAG knowledge base
- DELETE /corpus/{source_type} -- delete a corpus for re-ingestion
"""

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import DbSession
from app.schemas.rag import (
    AlreadyIngestedResponse,
    CorpusStatsResponse,
    DeleteCorpusResponse,
    IngestRequest,
    IngestResponse,
    RAGResultResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter()


# -----------------------------------------------------------------------------
# Dependency
# -----------------------------------------------------------------------------


async def get_rag_service(db: DbSession) -> RAGService:
    """Dependency that provides a RAGService instance."""
    embedding_service = EmbeddingService()
    return RAGService(db, embedding_service)


RAGServiceDep = Annotated[RAGService, Depends(get_rag_service)]


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------


@router.post(
    "/ingest",
    response_model=IngestResponse,
    responses={
        200: {"description": "Ingestion completed successfully"},
        409: {
            "description": "Corpus already ingested",
            "model": AlreadyIngestedResponse,
        },
    },
    summary="Ingest static corpus data",
    description="Trigger ingestion of IFRS and/or SASB corpus data. "
    "Returns 409 if the corpus already exists.",
)
async def ingest_corpus(
    request: IngestRequest,
    rag_service: RAGServiceDep,
) -> IngestResponse:
    """Ingest IFRS and/or SASB corpus data."""
    logger.info("Ingestion request: corpus=%s", request.corpus)

    total_chunks = 0
    ifrs_s1_chunks = 0
    ifrs_s2_chunks = 0
    sasb_chunks = 0
    duration = 0.0
    already_ingested = False

    if request.corpus in ("all", "ifrs"):
        stats = await rag_service.ingest_ifrs_corpus()
        ifrs_s1_chunks = stats.get("ifrs_s1_chunks", 0)
        ifrs_s2_chunks = stats.get("ifrs_s2_chunks", 0)
        duration += stats.get("duration_seconds", 0)
        if stats.get("already_ingested"):
            already_ingested = True

    if request.corpus in ("all", "sasb"):
        stats = await rag_service.ingest_sasb_corpus()
        sasb_chunks = stats.get("sasb_chunks", 0)
        duration += stats.get("duration_seconds", 0)
        if stats.get("already_ingested"):
            already_ingested = True

    total_chunks = ifrs_s1_chunks + ifrs_s2_chunks + sasb_chunks

    if already_ingested and total_chunks > 0:
        # Return 409 if any corpus was already ingested
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "status": "already_ingested",
                "message": "Corpus already exists. Delete it first to re-ingest.",
                "existing_counts": {
                    "ifrs_s1": ifrs_s1_chunks,
                    "ifrs_s2": ifrs_s2_chunks,
                    "sasb": sasb_chunks,
                },
            },
        )

    return IngestResponse(
        status="completed",
        ifrs_s1_chunks=ifrs_s1_chunks,
        ifrs_s2_chunks=ifrs_s2_chunks,
        sasb_chunks=sasb_chunks,
        total_chunks=total_chunks,
        duration_seconds=round(duration, 2),
    )


@router.get(
    "/stats",
    response_model=CorpusStatsResponse,
    summary="Get corpus statistics",
    description="Return counts of embeddings by source type.",
)
async def get_corpus_stats(
    rag_service: RAGServiceDep,
) -> CorpusStatsResponse:
    """Get embedding counts by source type."""
    stats = await rag_service.corpus_stats()

    return CorpusStatsResponse(
        ifrs_s1=stats.get("ifrs_s1", 0),
        ifrs_s2=stats.get("ifrs_s2", 0),
        sasb=stats.get("sasb", 0),
        report=stats.get("report", 0),
        total=stats.get("total", 0),
    )


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Search the RAG knowledge base",
    description="Perform semantic, keyword, or hybrid search against the RAG knowledge base. "
    "This endpoint is for development/debug purposes. Agents use the rag_lookup tool.",
)
async def search(
    request: SearchRequest,
    rag_service: RAGServiceDep,
) -> SearchResponse:
    """Search the RAG knowledge base."""
    logger.debug(
        "Search request: query=%s, mode=%s, top_k=%d",
        request.query[:50],
        request.mode,
        request.top_k,
    )

    results = await rag_service.search(
        query=request.query,
        top_k=request.top_k,
        mode=request.mode,
        source_types=request.source_types,
        report_id=request.report_id,
        rrf_k=request.rrf_k,
    )

    return SearchResponse(
        results=[
            RAGResultResponse(
                chunk_id=r.chunk_id,
                chunk_text=r.chunk_text,
                metadata=r.metadata,
                source_type=r.source_type,
                report_id=r.report_id,
                score=r.score,
                search_method=r.search_method,
            )
            for r in results
        ],
        total_results=len(results),
        search_mode=request.mode,
    )


@router.delete(
    "/corpus/{source_type}",
    response_model=DeleteCorpusResponse,
    summary="Delete corpus data",
    description="Delete all embeddings for a specific source type. "
    "Use this to re-ingest corpus data.",
)
async def delete_corpus(
    source_type: Literal["ifrs_s1", "ifrs_s2", "sasb", "report"],
    rag_service: RAGServiceDep,
) -> DeleteCorpusResponse:
    """Delete all embeddings for a source type."""
    logger.info("Delete corpus request: source_type=%s", source_type)

    count = await rag_service.delete_corpus(source_type)

    return DeleteCorpusResponse(
        status="deleted",
        source_type=source_type,
        deleted_count=count,
    )
