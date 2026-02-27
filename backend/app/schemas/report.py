"""Report response schemas.

Implements FRD 13 (Source of Truth Report).
"""

from datetime import datetime
from pydantic import BaseModel
from typing import Literal


# ============================================================================
# Evidence Chain Types
# ============================================================================

class EvidenceChainEntry(BaseModel):
    """Single entry in the evidence chain."""
    
    finding_id: str
    agent_name: Literal[
        "claims", "orchestrator", "geography", "legal",
        "news_media", "academic", "data_metrics", "judge"
    ]
    evidence_type: str
    summary: str
    supports_claim: bool | None
    confidence: Literal["high", "medium", "low"] | None
    reasoning: str | None = None
    iteration: int
    created_at: datetime


# ============================================================================
# IFRS Mapping Types
# ============================================================================

class IFRSMappingResponse(BaseModel):
    """IFRS paragraph mapping in response."""
    
    paragraph_id: str
    pillar: str
    relevance: str | None = None


# ============================================================================
# Claim Response Types
# ============================================================================

class ClaimResponse(BaseModel):
    """Claim data in response."""
    
    claim_id: str
    claim_text: str
    claim_type: Literal[
        "geographic", "quantitative", "legal_governance",
        "strategic", "environmental", "risk_management"
    ]
    source_page: int
    source_location: dict | None = None
    ifrs_paragraphs: list[IFRSMappingResponse]
    priority: Literal["high", "medium", "low"]
    agent_reasoning: str | None = None
    created_at: datetime


class VerdictResponse(BaseModel):
    """Verdict data in response."""
    
    verdict_id: str
    verdict: Literal["verified", "unverified", "contradicted", "insufficient_evidence"]
    reasoning: str
    ifrs_mapping: list[dict]
    evidence_summary: dict | None = None
    iteration_count: int
    created_at: datetime


class ClaimWithVerdictResponse(BaseModel):
    """Claim paired with its verdict and findings."""
    
    claim: ClaimResponse
    verdict: VerdictResponse | None
    evidence_chain: list[EvidenceChainEntry]


# ============================================================================
# Disclosure Gap Types
# ============================================================================

class DisclosureGapResponse(BaseModel):
    """Disclosure gap finding."""
    
    gap_id: str
    paragraph_id: str
    pillar: Literal["governance", "strategy", "risk_management", "metrics_targets"]
    gap_type: Literal["fully_unaddressed", "partially_addressed"]
    requirement_text: str
    missing_requirements: list[str]
    materiality_context: str
    severity: Literal["high", "medium", "low"]
    s1_counterpart: str | None = None


# ============================================================================
# Pillar Section Types
# ============================================================================

class PillarSummaryResponse(BaseModel):
    """Summary statistics for a single pillar."""
    
    total_claims: int
    verified_claims: int
    unverified_claims: int
    contradicted_claims: int
    insufficient_evidence_claims: int
    disclosure_gaps: int


class PillarSectionResponse(BaseModel):
    """A single IFRS pillar section with claims and gaps."""
    
    pillar: Literal["governance", "strategy", "risk_management", "metrics_targets"]
    pillar_display_name: str
    claims: list[ClaimWithVerdictResponse]
    gaps: list[DisclosureGapResponse]
    summary: PillarSummaryResponse


# ============================================================================
# Report Summary Types
# ============================================================================

class VerdictBreakdown(BaseModel):
    """Breakdown of verdicts by type."""
    
    verified: int
    unverified: int
    contradicted: int
    insufficient_evidence: int


class ReportSummaryResponse(BaseModel):
    """Summary statistics for the entire report."""
    
    report_id: str
    total_claims: int
    verdicts_by_type: VerdictBreakdown
    coverage_by_pillar: dict[str, float]  # pillar -> coverage percentage
    gaps_by_status: dict[str, int]  # "fully_unaddressed" | "partially_addressed" -> count
    pipeline_iterations: int
    compiled_at: datetime


# ============================================================================
# Full Report Response
# ============================================================================

class SourceOfTruthReportResponse(BaseModel):
    """Full Source of Truth report with all pillars."""
    
    report_id: str
    filename: str
    status: str
    summary: ReportSummaryResponse
    pillars: dict[str, PillarSectionResponse]
    compiled_at: datetime


# ============================================================================
# Claims List Response (with pagination)
# ============================================================================

class ClaimsListPaginatedResponse(BaseModel):
    """Paginated claims response."""
    
    claims: list[ClaimWithVerdictResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Gaps List Response (with pagination)
# ============================================================================

class GapsListPaginatedResponse(BaseModel):
    """Paginated gaps response."""
    
    gaps: list[DisclosureGapResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
