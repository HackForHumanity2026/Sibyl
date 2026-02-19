"""Analysis request/response schemas.

Implements FRD 3 (Claims Agent) and FRD 5 (Orchestrator Agent).
"""

from datetime import datetime

from pydantic import BaseModel, Field


class StartAnalysisResponse(BaseModel):
    """Response after triggering analysis."""

    report_id: str
    status: str
    message: str


class AnalysisStatusResponse(BaseModel):
    """Response for analysis status polling.
    
    Extended in FRD 5 with pipeline-specific fields.
    """

    report_id: str
    status: str
    claims_count: int
    claims_by_type: dict[str, int]
    claims_by_priority: dict[str, int]
    
    # FRD 5 additions
    pipeline_stage: str | None = None  # extracting_claims, routing, investigating, judging, compiling, completed
    active_agents: list[str] = Field(default_factory=list)  # Currently executing agents
    iteration_count: int = 0  # Current investigation cycle
    findings_count: int = 0  # Total findings produced so far
    verdicts_count: int = 0  # Total verdicts issued so far
    
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


# =============================================================================
# FRD 5 Additions: Events endpoint
# =============================================================================


class StreamEventResponse(BaseModel):
    """A single event from the pipeline execution."""
    
    event_id: int
    event_type: str
    agent_name: str | None = None
    data: dict = Field(default_factory=dict)
    timestamp: str


class EventsListResponse(BaseModel):
    """Response for pipeline events replay."""
    
    events: list[StreamEventResponse]
    total: int
    pipeline_complete: bool


# =============================================================================
# Findings Endpoints (Agent Investigation Results)
# =============================================================================


class FindingResponse(BaseModel):
    """Response for a single finding (agent investigation result)."""

    id: str
    claim_id: str | None = None
    agent_name: str
    evidence_type: str
    summary: str
    details: dict | None = None
    supports_claim: bool | None = None
    confidence: str | None = None
    iteration: int
    created_at: datetime


class FindingsListResponse(BaseModel):
    """Paginated response for findings list."""

    findings: list[FindingResponse]
    total: int
    page: int
    size: int


class ClaimWithFindingsResponse(BaseModel):
    """Response for a claim with its associated findings."""

    claim: ClaimResponse
    findings: list[FindingResponse] = Field(default_factory=list)
