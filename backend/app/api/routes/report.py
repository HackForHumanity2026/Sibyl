"""Report endpoints for Source of Truth retrieval.

Implements FRD 13 (Source of Truth Report).
"""

import logging
from datetime import datetime, timezone
from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import generate_uuid7
from app.core.dependencies import get_db
from app.models.claim import Claim
from app.models.finding import Finding
from app.models.report import Report
from app.models.verdict import Verdict
from app.schemas.report import (
    ClaimsListPaginatedResponse,
    GapsListPaginatedResponse,
    MockSeedResponse,
    ReportSummaryResponse,
    SourceOfTruthReportResponse,
)
from app.services.report_compiler import ReportCompiler

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Mock Data Endpoints (Dev Only)
# ============================================================================

@router.post("/mock", response_model=dict)
async def create_mock_report(
    db: AsyncSession = Depends(get_db),
):
    """Create a mock report record without uploading a PDF.

    For development/testing only - creates a report you can seed with mock data.
    """
    report_id = generate_uuid7()

    report = Report(
        id=report_id,
        filename="mock_sustainability_report_2024.pdf",
        file_size_bytes=1024000,
        page_count=87,
        status="completed",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(report)
    await db.commit()

    return {
        "report_id": str(report_id),
        "message": f"Mock report created. Call POST /api/v1/report/{report_id}/seed-mock to populate.",
    }


async def _create_mock_data(
    db: AsyncSession, report_uuid: UUID
) -> tuple[int, int, int, int]:
    """Create all mock claims, findings, verdicts, and gaps. Returns counts."""

    # ------------------------------------------------------------------
    # Mock Claims
    # ------------------------------------------------------------------
    mock_claims_data = [
        # Governance
        {
            "claim_text": "The Board's Sustainability Committee has primary oversight for climate matters and meets quarterly to review progress against climate targets.",
            "claim_type": "legal_governance",
            "source_page": 12,
            "ifrs_paragraphs": [
                {"paragraph_id": "S2.6", "pillar": "governance", "relevance": "Board oversight of climate-related risks and opportunities"},
            ],
            "priority": "high",
            "verdict": "verified",
            "verdict_reasoning": "Board committee structure and meeting cadence corroborated by governance filings and legal agent analysis. IFRS S2.6 requires explicit board-level climate oversight.",
            "agents": [
                ("legal", "ifrs_compliance", True, "high", "Claim meets IFRS S2.6 requirements for board-level climate oversight. Committee charter reviewed and verified."),
                ("news_media", "news_corroboration", True, "medium", "Multiple ESG news outlets report on company's active sustainability governance. No contradictory reports found."),
            ],
        },
        {
            "claim_text": "Management has designated a Chief Sustainability Officer (CSO) with direct reporting line to the CEO, responsible for day-to-day climate risk management.",
            "claim_type": "legal_governance",
            "source_page": 14,
            "ifrs_paragraphs": [
                {"paragraph_id": "S2.7", "pillar": "governance", "relevance": "Management role in climate-related risk"},
            ],
            "priority": "medium",
            "verdict": "verified",
            "verdict_reasoning": "CSO appointment confirmed via company filings and public announcements. Reporting structure verified.",
            "agents": [
                ("legal", "ifrs_compliance", True, "high", "Management-level climate governance role satisfies IFRS S2.7 disclosure requirements."),
            ],
        },
        # Strategy
        {
            "claim_text": "Our transition plan targets net-zero by 2050 with a 42% absolute reduction in Scope 1 and 2 emissions by 2030 from a 2019 baseline.",
            "claim_type": "strategic",
            "source_page": 45,
            "ifrs_paragraphs": [
                {"paragraph_id": "S2.14", "pillar": "strategy", "relevance": "Transition plan disclosure"},
                {"paragraph_id": "S2.14", "pillar": "strategy", "relevance": "Quantified emission reduction targets"},
            ],
            "priority": "high",
            "verdict": "verified",
            "verdict_reasoning": "Emission targets consistent with IEA net-zero pathway. Academic research confirms 42% reduction aligns with 1.5°C scenario. Data metrics analysis confirms mathematical consistency.",
            "agents": [
                ("legal", "ifrs_compliance", True, "high", "Net-zero transition plan meets IFRS S2.14 disclosure requirements including timeline and interim targets."),
                ("academic", "methodology_validation", True, "high", "42% reduction target aligns with peer-reviewed science-based targets for this sector. Methodology validated against SBTi framework."),
                ("data_metrics", "mathematical_consistency", True, "high", "Baseline emissions verified. 42% reduction trajectory mathematically consistent with stated 2030 target."),
            ],
        },
        {
            "claim_text": "The company has identified physical climate risks affecting 23 manufacturing facilities across Southeast Asia, representing 34% of total production capacity.",
            "claim_type": "geographic",
            "source_page": 52,
            "ifrs_paragraphs": [
                {"paragraph_id": "S2.10", "pillar": "strategy", "relevance": "Physical climate risk assessment"},
            ],
            "priority": "high",
            "verdict": "insufficient_evidence",
            "verdict_reasoning": "Facility locations could not be independently verified. Satellite analysis inconclusive for 8 of 23 sites. Physical risk assessment methodology not disclosed.",
            "agents": [
                ("geography", "satellite_analysis", None, "low", "Satellite imagery analysis completed for 15 of 23 facilities. Remaining 8 sites could not be located with provided coordinates. Flood risk maps partially corroborate claims for confirmed sites."),
                ("legal", "ifrs_compliance", None, "medium", "IFRS S2.10 requires disclosure of how physical risks are identified and assessed. Methodology section is insufficiently detailed."),
            ],
        },
        # Risk Management
        {
            "claim_text": "Annual climate risk assessment conducted using the TCFD framework, integrated with enterprise risk management processes reviewed by the Board.",
            "claim_type": "legal_governance",
            "source_page": 38,
            "ifrs_paragraphs": [
                {"paragraph_id": "S2.25", "pillar": "risk_management", "relevance": "Risk identification and assessment process"},
            ],
            "priority": "medium",
            "verdict": "verified",
            "verdict_reasoning": "TCFD-aligned risk process corroborated by third-party assurance statement. Board review confirmed in governance disclosures.",
            "agents": [
                ("legal", "ifrs_compliance", True, "high", "TCFD-aligned process satisfies IFRS S2.25 requirements for systematic risk identification and assessment."),
            ],
        },
        {
            "claim_text": "Climate scenario analysis performed using 1.5°C, 2°C, and 3°C+ warming scenarios across a 30-year time horizon to assess strategic resilience.",
            "claim_type": "strategic",
            "source_page": 41,
            "ifrs_paragraphs": [
                {"paragraph_id": "S2.22", "pillar": "risk_management", "relevance": "Climate scenario analysis"},
            ],
            "priority": "high",
            "verdict": "verified",
            "verdict_reasoning": "Scenario analysis methodology aligns with IPCC AR6 pathways. Academic validation confirms appropriate scenario selection.",
            "agents": [
                ("academic", "methodology_validation", True, "high", "Scenario parameters consistent with IPCC AR6 SSP1-1.9, SSP2-4.5, and SSP5-8.5 pathways. 30-year horizon appropriate for long-lived assets."),
                ("legal", "ifrs_compliance", True, "high", "Scenario analysis satisfies IFRS S2.22 requirements including multiple scenarios and long-term time horizons."),
            ],
        },
        # Metrics & Targets
        {
            "claim_text": "Scope 1 emissions: 450,000 tCO2e. Scope 2 (market-based): 1,200,000 tCO2e. Scope 3 (categories 1-15): 12,400,000 tCO2e. Total: 14,050,000 tCO2e.",
            "claim_type": "quantitative",
            "source_page": 68,
            "ifrs_paragraphs": [
                {"paragraph_id": "S2.29", "pillar": "metrics_targets", "relevance": "GHG emissions disclosure"},
            ],
            "priority": "high",
            "verdict": "verified",
            "verdict_reasoning": "Emissions figures independently verified against GHG Protocol methodology. Scope 3 categories fully enumerated. Third-party assurance provided.",
            "agents": [
                ("data_metrics", "mathematical_consistency", True, "high", "Scope 1+2+3 figures sum correctly. Year-over-year change consistent with stated operational changes (-8% Scope 1, -12% Scope 2 vs prior year)."),
                ("legal", "ifrs_compliance", True, "high", "Full Scope 1, 2, and 3 disclosure meets IFRS S2.29 requirements. GHG Protocol methodology confirmed."),
                ("academic", "methodology_validation", True, "medium", "Emissions accounting methodology consistent with GHG Protocol Corporate Standard. Scope 3 category coverage comprehensive."),
            ],
        },
        {
            "claim_text": "Renewable energy constitutes 67% of total electricity consumption as of FY2024, up from 41% in FY2022.",
            "claim_type": "quantitative",
            "source_page": 71,
            "ifrs_paragraphs": [
                {"paragraph_id": "S2.29", "pillar": "metrics_targets", "relevance": "Energy metrics and transition progress"},
            ],
            "priority": "medium",
            "verdict": "contradicted",
            "verdict_reasoning": "Renewable energy percentage contradicted by utility data and news reporting. Independent analysis suggests actual renewable consumption closer to 52%. Certificate purchases appear to be double-counted.",
            "agents": [
                ("data_metrics", "mathematical_consistency", False, "high", "Renewable energy certificates (RECs) appear double-counted with direct renewable purchases. Corrected calculation yields approximately 52% renewable electricity."),
                ("news_media", "news_corroboration", False, "medium", "Industry publication reported in Q3 2024 that company overstated renewable credentials. Article cites internal audit findings."),
                ("legal", "ifrs_compliance", False, "high", "If renewable figure is overstated, this may constitute a material misstatement under IFRS S2.29 and related disclosure requirements."),
            ],
        },
    ]

    claims_created = 0
    findings_created = 0
    verdicts_created = 0

    for claim_data in mock_claims_data:
        claim_id = generate_uuid7()
        claim = Claim(
            id=claim_id,
            report_id=report_uuid,
            claim_text=claim_data["claim_text"],
            claim_type=claim_data["claim_type"],
            source_page=claim_data["source_page"],
            ifrs_paragraphs=claim_data["ifrs_paragraphs"],
            priority=claim_data["priority"],
            agent_reasoning=f"Claims agent extracted this {claim_data['claim_type']} claim from page {claim_data['source_page']}.",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(claim)
        claims_created += 1

        # Create findings for each agent
        for iteration, (agent_name, evidence_type, supports, confidence, summary) in enumerate(claim_data["agents"], start=1):
            finding = Finding(
                id=generate_uuid7(),
                report_id=report_uuid,
                claim_id=claim_id,
                agent_name=agent_name,
                evidence_type=evidence_type,
                summary=summary,
                supports_claim=supports,
                confidence=confidence,
                iteration=iteration,
                details={"mock": True},
                created_at=datetime.now(timezone.utc),
            )
            db.add(finding)
            findings_created += 1

        # Create verdict
        verdict = Verdict(
            id=generate_uuid7(),
            report_id=report_uuid,
            claim_id=claim_id,
            verdict=claim_data["verdict"],
            reasoning=claim_data["verdict_reasoning"],
            ifrs_mapping=claim_data["ifrs_paragraphs"],
            evidence_summary={"agents_used": [a[0] for a in claim_data["agents"]], "mock": True},
            iteration_count=len(claim_data["agents"]),
            created_at=datetime.now(timezone.utc),
        )
        db.add(verdict)
        verdicts_created += 1

    # ------------------------------------------------------------------
    # Mock Disclosure Gaps (stored as Finding records with evidence_type="disclosure_gap")
    # ------------------------------------------------------------------
    mock_gaps_data = [
        {
            "paragraph_id": "S1.27",
            "pillar": "governance",
            "gap_type": "fully_unaddressed",
            "requirement_text": "How the body determines the appropriate skills and competencies needed to oversee climate-related risks and opportunities.",
            "missing_requirements": ["Skills matrix for board climate competency", "Training programs for directors"],
            "materiality_context": "Board competency in climate matters is critical for effective oversight. Without demonstrated expertise, governance quality cannot be assessed.",
            "severity": "high",
        },
        {
            "paragraph_id": "S2.14",
            "pillar": "strategy",
            "gap_type": "partially_addressed",
            "requirement_text": "Progress of plans disclosed in prior reporting periods, including quantitative milestones achieved.",
            "missing_requirements": ["Prior period milestone comparison", "Explanation of deviations from plan"],
            "materiality_context": "Without progress reporting against prior commitments, stakeholders cannot assess management credibility or accountability.",
            "severity": "medium",
        },
        {
            "paragraph_id": "S2.26",
            "pillar": "risk_management",
            "gap_type": "fully_unaddressed",
            "requirement_text": "How the entity monitors climate-related risks and opportunities on an ongoing basis, including frequency of monitoring.",
            "missing_requirements": ["Monitoring frequency and cadence", "KPIs used for ongoing risk tracking", "Escalation protocols"],
            "materiality_context": "Ongoing monitoring is essential to demonstrate that risk management is active, not merely periodic.",
            "severity": "medium",
        },
        {
            "paragraph_id": "S2.33",
            "pillar": "metrics_targets",
            "gap_type": "partially_addressed",
            "requirement_text": "Financed emissions and facilitated emissions where the entity is involved in financing activities.",
            "missing_requirements": ["Category 15 Scope 3 financed emissions detail", "PCAF methodology disclosure"],
            "materiality_context": "For entities with significant financial operations, financed emissions can dwarf operational emissions.",
            "severity": "high",
        },
    ]

    gaps_created = 0
    for gap_data in mock_gaps_data:
        gap_finding = Finding(
            id=generate_uuid7(),
            report_id=report_uuid,
            claim_id=None,
            agent_name="judge",
            evidence_type="disclosure_gap",
            summary=f"Disclosure gap identified for {gap_data['paragraph_id']}: {gap_data['requirement_text'][:100]}",
            supports_claim=None,
            confidence="high",
            iteration=1,
            details={
                "paragraph_id": gap_data["paragraph_id"],
                "pillar": gap_data["pillar"],
                "gap_type": gap_data["gap_type"],
                "requirement_text": gap_data["requirement_text"],
                "missing_requirements": gap_data["missing_requirements"],
                "materiality_context": gap_data["materiality_context"],
                "severity": gap_data["severity"],
                "mock": True,
            },
            created_at=datetime.now(timezone.utc),
        )
        db.add(gap_finding)
        gaps_created += 1

    await db.flush()
    return claims_created, findings_created, verdicts_created, gaps_created


@router.post("/{report_id}/seed-mock", response_model=MockSeedResponse)
async def seed_mock_data(
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> MockSeedResponse:
    """Seed mock data for testing the Source of Truth report.

    For development/testing only - populates a report with realistic mock claims,
    findings, verdicts, and disclosure gaps across all four IFRS pillars.
    """
    try:
        report_uuid = UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID format")

    report = await db.get(Report, report_uuid)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check if data already exists
    existing_claims = await db.execute(
        select(Claim).where(Claim.report_id == report_uuid).limit(1)
    )
    if existing_claims.scalar():
        raise HTTPException(status_code=400, detail="Report already has data. Delete it first.")

    claims_created, findings_created, verdicts_created, gaps_created = await _create_mock_data(
        db, report_uuid
    )

    report.status = "completed"
    await db.commit()

    return MockSeedResponse(
        report_id=report_id,
        claims_created=claims_created,
        findings_created=findings_created,
        verdicts_created=verdicts_created,
        gaps_created=gaps_created,
        message=f"Mock data seeded successfully: {claims_created} claims, {findings_created} findings, {verdicts_created} verdicts, {gaps_created} disclosure gaps.",
    )


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

