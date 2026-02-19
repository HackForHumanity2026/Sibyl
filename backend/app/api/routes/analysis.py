"""Analysis endpoints for claims extraction and pipeline control.

Implements FRD 3 (Claims Agent) and FRD 5 (Orchestrator Agent).
"""

import logging
from uuid import UUID

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.models.claim import Claim
from app.models.finding import Finding
from app.models.report import Report
from app.models.verdict import Verdict
from app.schemas.analysis import (
    AnalysisStatusResponse,
    ClaimResponse,
    ClaimsListResponse,
    ClaimWithFindingsResponse,
    FindingResponse,
    FindingsListResponse,
    IFRSParagraphMapping,
    StartAnalysisResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Redis queue keys
# FRD 5: New pipeline queue replaces extract_claims for full pipeline
RUN_PIPELINE_QUEUE = "sibyl:tasks:run_pipeline"
# Legacy queue for backwards compatibility (standalone claims extraction)
EXTRACT_CLAIMS_QUEUE = "sibyl:tasks:extract_claims"


async def get_redis() -> redis.Redis:
    """Get async Redis client."""
    return redis.from_url(settings.REDIS_URL)


def _claim_to_response(claim: Claim) -> ClaimResponse:
    """Convert a Claim model to ClaimResponse schema."""
    # Parse ifrs_paragraphs from JSONB
    ifrs_mappings = []
    if claim.ifrs_paragraphs:
        for mapping in claim.ifrs_paragraphs:
            if isinstance(mapping, dict):
                ifrs_mappings.append(
                    IFRSParagraphMapping(
                        paragraph_id=mapping.get("paragraph_id", ""),
                        pillar=mapping.get("pillar", ""),
                        relevance=mapping.get("relevance", ""),
                    )
                )

    return ClaimResponse(
        id=str(claim.id),
        claim_text=claim.claim_text,
        claim_type=claim.claim_type,
        source_page=claim.source_page,
        source_location=claim.source_location,
        ifrs_paragraphs=ifrs_mappings,
        priority=claim.priority,
        agent_reasoning=claim.agent_reasoning,
        created_at=claim.created_at,
    )


def _derive_pipeline_stage(
    status: str,
    claims_count: int,
    findings_count: int,
    verdicts_count: int,
) -> str | None:
    """Derive the pipeline stage from counts and status.
    
    Args:
        status: Report status
        claims_count: Number of claims
        findings_count: Number of findings
        verdicts_count: Number of verdicts
        
    Returns:
        Pipeline stage string or None if not applicable
    """
    if status == "completed":
        return "completed"
    if status == "error":
        return "error"
    if status != "analyzing":
        return None
    
    # Derive from entity counts
    if verdicts_count > 0:
        return "compiling"
    if findings_count > 0:
        return "judging"
    if claims_count > 0:
        return "investigating"
    
    return "extracting_claims"


@router.post("/{report_id}/start", response_model=StartAnalysisResponse)
async def start_analysis(
    report_id: str,
    skip_claims_extraction: bool = Query(
        False,
        description="Skip claims extraction and start from routing (if claims exist)",
    ),
    db: AsyncSession = Depends(get_db),
) -> StartAnalysisResponse:
    """Start the full analysis pipeline for a report.
    
    FRD 5: This now enqueues to the full pipeline queue instead of
    just claims extraction. The pipeline includes:
    - Claims extraction (unless skip_claims_extraction=true)
    - Orchestrator routing
    - Specialist agent investigation (stubs)
    - Judge evaluation (stub)
    - Report compilation
    
    The report must be in 'parsed' status. This endpoint:
    1. Sets the report status to 'analyzing'
    2. Enqueues a pipeline task in Redis
    3. Returns immediately while the pipeline runs in the background
    """
    # Fetch the report
    try:
        report_uuid = UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID format.")

    stmt = select(Report).where(Report.id == report_uuid)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")

    # Check current status
    if report.status == "analyzing":
        raise HTTPException(
            status_code=409, detail="Analysis is already in progress for this report."
        )

    if report.status == "completed":
        raise HTTPException(
            status_code=409,
            detail="Analysis has already been completed for this report.",
        )

    if report.status != "parsed":
        raise HTTPException(
            status_code=400,
            detail=f"Report must be in 'parsed' status to start analysis. "
            f"Current status: '{report.status}'.",
        )

    # If skipping claims extraction, verify claims exist
    if skip_claims_extraction:
        claims_count_stmt = select(func.count()).where(Claim.report_id == report_uuid)
        claims_result = await db.execute(claims_count_stmt)
        claims_count = claims_result.scalar() or 0
        
        if claims_count == 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot skip claims extraction: no claims exist for this report.",
            )

    # Set status to analyzing
    report.status = "analyzing"
    report.error_message = None  # Clear any previous error
    await db.commit()

    # Enqueue the full pipeline task (FRD 5)
    redis_client = await get_redis()
    try:
        # Include skip flag in the task payload
        task_payload = report_id
        if skip_claims_extraction:
            task_payload = f"{report_id}:skip_claims"
        
        await redis_client.lpush(RUN_PIPELINE_QUEUE, task_payload)
        logger.info("Enqueued pipeline task for report: %s", report_id)
    finally:
        await redis_client.aclose()

    return StartAnalysisResponse(
        report_id=report_id,
        status="analyzing",
        message="Analysis pipeline started.",
    )


@router.get("/{report_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> AnalysisStatusResponse:
    """Get the current analysis status for a report.
    
    FRD 5 additions:
    - pipeline_stage: Current stage of the pipeline
    - active_agents: List of agents currently executing
    - iteration_count: Current re-investigation cycle
    - findings_count: Total findings produced
    - verdicts_count: Total verdicts issued
    """
    # Fetch the report
    try:
        report_uuid = UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID format.")

    stmt = select(Report).where(Report.id == report_uuid)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")

    # Count claims by type
    type_counts_stmt = (
        select(Claim.claim_type, func.count(Claim.id))
        .where(Claim.report_id == report_uuid)
        .group_by(Claim.claim_type)
    )
    type_counts_result = await db.execute(type_counts_stmt)
    claims_by_type = dict(type_counts_result.all())

    # Count claims by priority
    priority_counts_stmt = (
        select(Claim.priority, func.count(Claim.id))
        .where(Claim.report_id == report_uuid)
        .group_by(Claim.priority)
    )
    priority_counts_result = await db.execute(priority_counts_stmt)
    claims_by_priority = dict(priority_counts_result.all())

    # Total claims count
    total_claims = sum(claims_by_type.values())
    
    # FRD 5: Count findings
    findings_count_stmt = (
        select(func.count())
        .where(Finding.report_id == report_uuid)
    )
    findings_result = await db.execute(findings_count_stmt)
    findings_count = findings_result.scalar() or 0
    
    # FRD 5: Count verdicts
    verdicts_count_stmt = (
        select(func.count())
        .where(Verdict.report_id == report_uuid)
    )
    verdicts_result = await db.execute(verdicts_count_stmt)
    verdicts_count = verdicts_result.scalar() or 0
    
    # Derive pipeline stage
    pipeline_stage = _derive_pipeline_stage(
        report.status,
        total_claims,
        findings_count,
        verdicts_count,
    )
    
    # For active_agents and iteration_count, we would need to query the
    # LangGraph checkpoint or maintain this in the Report model.
    # For now, return empty/default values as these are best obtained via SSE.
    active_agents: list[str] = []
    iteration_count = 0

    return AnalysisStatusResponse(
        report_id=report_id,
        status=report.status,
        claims_count=total_claims,
        claims_by_type=claims_by_type,
        claims_by_priority=claims_by_priority,
        pipeline_stage=pipeline_stage,
        active_agents=active_agents,
        iteration_count=iteration_count,
        findings_count=findings_count,
        verdicts_count=verdicts_count,
        error_message=report.error_message,
        updated_at=report.updated_at,
    )


@router.get("/{report_id}/claims", response_model=ClaimsListResponse)
async def get_claims(
    report_id: str,
    claim_type: str | None = Query(None, alias="type", description="Filter by claim type"),
    priority: str | None = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
) -> ClaimsListResponse:
    """Get paginated list of claims for a report.

    Claims are ordered by source page (ascending) then priority (high first).
    """
    # Validate report exists
    try:
        report_uuid = UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID format.")

    stmt = select(Report.id).where(Report.id == report_uuid)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Report not found.")

    # Build query for claims
    query = select(Claim).where(Claim.report_id == report_uuid)

    # Apply filters
    if claim_type is not None:
        query = query.where(Claim.claim_type == claim_type)
    if priority is not None:
        query = query.where(Claim.priority == priority)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply ordering: page ASC, then priority (high > medium > low)
    # Use CASE to order priority correctly
    from sqlalchemy import case

    priority_order = case(
        (Claim.priority == "high", 1),
        (Claim.priority == "medium", 2),
        (Claim.priority == "low", 3),
        else_=4,
    )
    query = query.order_by(Claim.source_page.asc(), priority_order)

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    # Execute query
    result = await db.execute(query)
    claims = result.scalars().all()

    # Convert to response
    claim_responses = [_claim_to_response(claim) for claim in claims]

    return ClaimsListResponse(
        claims=claim_responses,
        total=total,
        page=page,
        size=size,
    )


@router.get("/{report_id}/claims/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    report_id: str,
    claim_id: str,
    db: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    """Get a single claim by ID."""
    # Validate UUIDs
    try:
        report_uuid = UUID(report_id)
        claim_uuid = UUID(claim_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format.")

    # Fetch the claim
    stmt = select(Claim).where(
        Claim.id == claim_uuid,
        Claim.report_id == report_uuid,
    )
    result = await db.execute(stmt)
    claim = result.scalar_one_or_none()

    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found.")

    return _claim_to_response(claim)


# =============================================================================
# Findings Endpoints (Agent Investigation Results)
# =============================================================================


def _finding_to_response(finding: Finding) -> FindingResponse:
    """Convert a Finding model to FindingResponse schema."""
    return FindingResponse(
        id=str(finding.id),
        claim_id=str(finding.claim_id) if finding.claim_id else None,
        agent_name=finding.agent_name,
        evidence_type=finding.evidence_type,
        summary=finding.summary,
        details=finding.details,
        supports_claim=finding.supports_claim,
        confidence=finding.confidence,
        iteration=finding.iteration,
        created_at=finding.created_at,
    )


@router.get("/{report_id}/findings", response_model=FindingsListResponse)
async def get_findings(
    report_id: str,
    agent_name: str | None = Query(None, description="Filter by agent name"),
    claim_id: str | None = Query(None, description="Filter by claim ID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
) -> FindingsListResponse:
    """Get paginated list of findings (agent investigation results) for a report.
    
    Findings represent evidence gathered by specialist agents (legal, news, academic, etc.)
    during their investigation of claims.
    """
    # Validate report exists
    try:
        report_uuid = UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID format.")

    stmt = select(Report.id).where(Report.id == report_uuid)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Report not found.")

    # Build query for findings
    query = select(Finding).where(Finding.report_id == report_uuid)

    # Apply filters
    if agent_name is not None:
        query = query.where(Finding.agent_name == agent_name)
    if claim_id is not None:
        try:
            claim_uuid = UUID(claim_id)
            query = query.where(Finding.claim_id == claim_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid claim ID format.")

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Order by creation date (most recent first)
    query = query.order_by(Finding.created_at.desc())

    # Apply pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    # Execute query
    result = await db.execute(query)
    findings = result.scalars().all()

    # Convert to response
    finding_responses = [_finding_to_response(finding) for finding in findings]

    return FindingsListResponse(
        findings=finding_responses,
        total=total,
        page=page,
        size=size,
    )


@router.get("/{report_id}/claims/{claim_id}/findings", response_model=ClaimWithFindingsResponse)
async def get_claim_with_findings(
    report_id: str,
    claim_id: str,
    db: AsyncSession = Depends(get_db),
) -> ClaimWithFindingsResponse:
    """Get a claim with all its associated findings.
    
    This endpoint combines the claim details with all evidence gathered by specialist agents.
    """
    # Validate UUIDs
    try:
        report_uuid = UUID(report_id)
        claim_uuid = UUID(claim_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format.")

    # Fetch the claim
    claim_stmt = select(Claim).where(
        Claim.id == claim_uuid,
        Claim.report_id == report_uuid,
    )
    claim_result = await db.execute(claim_stmt)
    claim = claim_result.scalar_one_or_none()

    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found.")

    # Fetch findings for this claim
    findings_stmt = select(Finding).where(
        Finding.claim_id == claim_uuid
    ).order_by(Finding.created_at.asc())
    findings_result = await db.execute(findings_stmt)
    findings = findings_result.scalars().all()

    return ClaimWithFindingsResponse(
        claim=_claim_to_response(claim),
        findings=[_finding_to_response(f) for f in findings],
    )
