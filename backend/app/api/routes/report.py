"""Report endpoints for Source of Truth retrieval.

Implements FRD 13 (Source of Truth Report).
"""

import logging
from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.report import Report
from app.schemas.report import (
    ClaimsListPaginatedResponse,
    GapsListPaginatedResponse,
    ReportSummaryResponse,
    SourceOfTruthReportResponse,
)
from app.services.report_compiler import ReportCompiler

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=list[dict])
async def list_reports(
    db: AsyncSession = Depends(get_db),
):
    """List all reports in the system.
    
    Returns basic metadata for each report including ID, filename, status, and creation date.
    """
    result = await db.execute(
        select(Report).order_by(Report.created_at.desc())
    )
    reports = result.scalars().all()
    
    return [
        {
            "report_id": str(report.id),
            "filename": report.filename,
            "status": report.status,
            "file_size_bytes": report.file_size_bytes,
            "page_count": report.page_count,
            "created_at": report.created_at.isoformat(),
            "updated_at": report.updated_at.isoformat(),
        }
        for report in reports
    ]


@router.get("/{report_id}", response_model=SourceOfTruthReportResponse)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> SourceOfTruthReportResponse:
    """Get full compiled Source of Truth report.
    
    Returns the complete report organized by IFRS pillars with all claims,
    verdicts, evidence chains, and disclosure gaps.
    """
    try:
        report_uuid = UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID format")
    
    # Check report exists
    report = await db.get(Report, report_uuid)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Report is not ready. Status: {report.status}"
        )
    
    compiler = ReportCompiler(db)
    try:
        return await compiler.compile_report(report_id)
    except Exception as e:
        logger.exception("Failed to compile report: %s", e)
        raise HTTPException(status_code=500, detail="Failed to compile report")


@router.get("/{report_id}/claims", response_model=ClaimsListPaginatedResponse)
async def get_report_claims(
    report_id: str,
    pillar: str | None = Query(None, description="Filter by IFRS pillar"),
    verdict: str | None = Query(None, description="Filter by verdict status"),
    claim_type: str | None = Query(None, description="Filter by claim type"),
    agent: str | None = Query(None, description="Filter by investigating agent"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> ClaimsListPaginatedResponse:
    """Get claims with optional filtering and pagination.
    
    Filters:
    - pillar: governance, strategy, risk_management, metrics_targets
    - verdict: verified, unverified, contradicted, insufficient_evidence
    - claim_type: geographic, quantitative, legal_governance, strategic, environmental
    - agent: geography, legal, news_media, academic, data_metrics, judge
    """
    try:
        report_uuid = UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID format")
    
    # Check report exists
    report = await db.get(Report, report_uuid)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    compiler = ReportCompiler(db)
    claims, total = await compiler.get_claims_filtered(
        report_id=report_id,
        pillar=pillar,
        verdict=verdict,
        claim_type=claim_type,
        agent=agent,
        page=page,
        page_size=page_size,
    )
    
    total_pages = ceil(total / page_size) if total > 0 else 1
    
    return ClaimsListPaginatedResponse(
        claims=claims,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{report_id}/gaps", response_model=GapsListPaginatedResponse)
async def get_report_gaps(
    report_id: str,
    pillar: str | None = Query(None, description="Filter by IFRS pillar"),
    gap_status: str | None = Query(None, description="Filter by gap status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> GapsListPaginatedResponse:
    """Get disclosure gaps with optional filtering and pagination.
    
    Filters:
    - pillar: governance, strategy, risk_management, metrics_targets
    - gap_status: fully_unaddressed, partially_addressed
    """
    try:
        report_uuid = UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID format")
    
    # Check report exists
    report = await db.get(Report, report_uuid)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    compiler = ReportCompiler(db)
    gaps, total = await compiler.get_gaps_filtered(
        report_id=report_id,
        pillar=pillar,
        gap_status=gap_status,
        page=page,
        page_size=page_size,
    )
    
    total_pages = ceil(total / page_size) if total > 0 else 1
    
    return GapsListPaginatedResponse(
        gaps=gaps,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{report_id}/summary", response_model=ReportSummaryResponse)
async def get_report_summary(
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> ReportSummaryResponse:
    """Get report summary statistics only.
    
    Lighter endpoint when you only need stats, not full claim data.
    """
    try:
        report_uuid = UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID format")
    
    # Check report exists
    report = await db.get(Report, report_uuid)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    compiler = ReportCompiler(db)
    full_report = await compiler.compile_report(report_id)
    
    return full_report.summary

