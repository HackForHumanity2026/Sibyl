"""Analysis endpoints for claims extraction and pipeline control.

Implements FRD 3 (Claims Agent).
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
from app.models.report import Report
from app.schemas.analysis import (
    AnalysisStatusResponse,
    ClaimResponse,
    ClaimsListResponse,
    IFRSParagraphMapping,
    StartAnalysisResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Redis queue key for claims extraction
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


@router.post("/{report_id}/start", response_model=StartAnalysisResponse)
async def start_analysis(
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> StartAnalysisResponse:
    """Start claims extraction analysis for a report.

    The report must be in 'parsed' status. This endpoint:
    1. Sets the report status to 'analyzing'
    2. Enqueues a claims extraction task in Redis
    3. Returns immediately while extraction happens in the background
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

    # Set status to analyzing
    report.status = "analyzing"
    report.error_message = None  # Clear any previous error
    await db.commit()

    # Enqueue the claims extraction task
    redis_client = await get_redis()
    try:
        await redis_client.lpush(EXTRACT_CLAIMS_QUEUE, report_id)
        logger.info("Enqueued claims extraction task for report: %s", report_id)
    finally:
        await redis_client.aclose()

    return StartAnalysisResponse(
        report_id=report_id,
        status="analyzing",
        message="Claims extraction started.",
    )


@router.get("/{report_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> AnalysisStatusResponse:
    """Get the current analysis status for a report.

    Returns claim counts by type and priority once extraction begins.
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

    return AnalysisStatusResponse(
        report_id=report_id,
        status=report.status,
        claims_count=total_claims,
        claims_by_type=claims_by_type,
        claims_by_priority=claims_by_priority,
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
