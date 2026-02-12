"""Pydantic schemas for RAG API endpoints.

Implements FRD 1 (RAG Pipeline) Section 7 - Backend Endpoints.
"""

from typing import Literal

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Request Schemas
# -----------------------------------------------------------------------------


class IngestRequest(BaseModel):
    """Request body for POST /api/v1/rag/ingest."""

    corpus: Literal["all", "ifrs", "sasb"] = Field(
        default="all",
        description="Which corpus to ingest: 'all' (IFRS + SASB), 'ifrs' (S1 + S2), or 'sasb'",
    )


class SearchRequest(BaseModel):
    """Request body for POST /api/v1/rag/search."""

    query: str = Field(
        ...,
        description="The search query text",
        min_length=1,
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return",
    )
    mode: Literal["semantic", "keyword", "hybrid"] = Field(
        default="hybrid",
        description="Search mode: semantic (vector), keyword (full-text), or hybrid (both with RRF)",
    )
    source_types: list[str] | None = Field(
        default=None,
        description="Filter by corpus type(s): ifrs_s1, ifrs_s2, sasb, report. None = all",
    )
    report_id: str | None = Field(
        default=None,
        description="Filter to a specific report's chunks (UUID)",
    )
    rrf_k: int = Field(
        default=60,
        ge=1,
        le=1000,
        description="RRF constant for hybrid mode (higher = smoother ranking)",
    )


# -----------------------------------------------------------------------------
# Response Schemas
# -----------------------------------------------------------------------------


class RAGResultResponse(BaseModel):
    """Single search result in the response."""

    chunk_id: str = Field(description="UUID of the embedding row")
    chunk_text: str = Field(description="Full chunk text including context header")
    metadata: dict = Field(description="Chunk metadata (corpus-specific)")
    source_type: str = Field(description="Corpus type: ifrs_s1, ifrs_s2, sasb, or report")
    report_id: str | None = Field(description="Report UUID for report chunks, null otherwise")
    score: float = Field(description="Retrieval score (similarity, rank, or RRF)")
    search_method: str = Field(description="Search method: semantic, keyword, or hybrid")


class SearchResponse(BaseModel):
    """Response body for POST /api/v1/rag/search."""

    results: list[RAGResultResponse] = Field(description="Ranked search results")
    total_results: int = Field(description="Number of results returned")
    search_mode: str = Field(description="Search mode used")


class IngestResponse(BaseModel):
    """Response body for POST /api/v1/rag/ingest."""

    status: Literal["completed", "already_ingested"] = Field(
        description="Ingestion status"
    )
    ifrs_s1_chunks: int = Field(default=0, description="Number of IFRS S1 chunks")
    ifrs_s2_chunks: int = Field(default=0, description="Number of IFRS S2 chunks")
    sasb_chunks: int = Field(default=0, description="Number of SASB chunks")
    total_chunks: int = Field(default=0, description="Total chunks ingested")
    duration_seconds: float | None = Field(
        default=None, description="Ingestion duration in seconds"
    )
    message: str | None = Field(
        default=None, description="Additional message (e.g., for already_ingested)"
    )


class CorpusStatsResponse(BaseModel):
    """Response body for GET /api/v1/rag/stats."""

    ifrs_s1: int = Field(default=0, description="Number of IFRS S1 embeddings")
    ifrs_s2: int = Field(default=0, description="Number of IFRS S2 embeddings")
    sasb: int = Field(default=0, description="Number of SASB embeddings")
    report: int = Field(default=0, description="Number of report embeddings")
    total: int = Field(default=0, description="Total embeddings")


class DeleteCorpusResponse(BaseModel):
    """Response body for DELETE /api/v1/rag/corpus/{source_type}."""

    status: Literal["deleted"] = Field(description="Operation status")
    source_type: str = Field(description="Source type that was deleted")
    deleted_count: int = Field(description="Number of embeddings deleted")


class AlreadyIngestedResponse(BaseModel):
    """Response body for 409 Conflict when corpus already exists."""

    status: Literal["already_ingested"] = Field(description="Status indicator")
    message: str = Field(description="Explanation message")
    existing_counts: dict[str, int] = Field(
        description="Existing embedding counts by source type"
    )
