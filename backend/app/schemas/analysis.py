"""Analysis request/response schemas.

Implements FRD 3 (Claims Agent).
"""

from datetime import datetime

from pydantic import BaseModel, Field


class StartAnalysisResponse(BaseModel):
    """Response after triggering analysis."""

    report_id: str
    status: str
    message: str


class AnalysisStatusResponse(BaseModel):
    """Response for analysis status polling."""

    report_id: str
    status: str
    claims_count: int
    claims_by_type: dict[str, int]
    claims_by_priority: dict[str, int]
    error_message: str | None = None
    updated_at: datetime


class IFRSParagraphMapping(BaseModel):
    """IFRS paragraph mapping with relevance explanation."""

    paragraph_id: str
    pillar: str
    relevance: str


class ClaimResponse(BaseModel):
    """Response for a single claim."""

    id: str
    claim_text: str
    claim_type: str
    source_page: int
    source_location: dict | None = None
    ifrs_paragraphs: list[IFRSParagraphMapping] = Field(default_factory=list)
    priority: str
    agent_reasoning: str | None = None
    created_at: datetime


class ClaimsListResponse(BaseModel):
    """Paginated response for claims list."""

    claims: list[ClaimResponse]
    total: int
    page: int
    size: int
