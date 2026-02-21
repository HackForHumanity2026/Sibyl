"""Source of Truth report compiler.

Implements FRD 13 (Source of Truth Report).

Compiles the final compliance report from:
- Extracted claims with IFRS mappings
- Specialist agent findings
- Judge verdicts
- Disclosure gap analysis

Organized by IFRS S1 pillars:
- Governance (S1.26-27, S2.5-7)
- Strategy (S1.28-35, S2.8-23)
- Risk Management (S1.38-42, S2.24-26)
- Metrics and Targets (S1.43-53, S2.27-37)
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.claim import Claim
from app.models.finding import Finding
from app.models.report import Report
from app.models.verdict import Verdict
from app.schemas.report import (
    ClaimResponse,
    ClaimWithVerdictResponse,
    DisclosureGapResponse,
    EvidenceChainEntry,
    IFRSMappingResponse,
    PillarSectionResponse,
    PillarSummaryResponse,
    ReportSummaryResponse,
    SourceOfTruthReportResponse,
    VerdictBreakdown,
    VerdictResponse,
)

logger = logging.getLogger(__name__)

# Pillar display names
PILLAR_DISPLAY_NAMES = {
    "governance": "Governance",
    "strategy": "Strategy",
    "risk_management": "Risk Management",
    "metrics_targets": "Metrics & Targets",
}

# IFRS paragraph to pillar mapping (loaded from registry)
_PARAGRAPH_REGISTRY: dict | None = None


def _load_paragraph_registry() -> dict:
    """Load the IFRS paragraph registry."""
    global _PARAGRAPH_REGISTRY
    if _PARAGRAPH_REGISTRY is not None:
        return _PARAGRAPH_REGISTRY
    
    registry_path = Path(__file__).parent.parent.parent / "data" / "ifrs" / "paragraph_registry.json"
    if registry_path.exists():
        with open(registry_path, "r") as f:
            data = json.load(f)
            # Build paragraph_id -> pillar mapping
            _PARAGRAPH_REGISTRY = {}
            for p in data.get("paragraphs", []):
                _PARAGRAPH_REGISTRY[p["paragraph_id"]] = {
                    "pillar": p["pillar"],
                    "requirement_text": p.get("requirement_text", ""),
                    "materiality_note": p.get("materiality_note", ""),
                    "sub_requirements": p.get("sub_requirements", []),
                    "s1_counterpart": p.get("s1_counterpart"),
                }
    else:
        _PARAGRAPH_REGISTRY = {}
        logger.warning("IFRS paragraph registry not found at %s", registry_path)
    
    return _PARAGRAPH_REGISTRY


def get_pillar_for_paragraph(paragraph_id: str) -> str:
    """Get the IFRS pillar for a paragraph ID."""
    registry = _load_paragraph_registry()
    
    # Direct lookup
    if paragraph_id in registry:
        return registry[paragraph_id]["pillar"]
    
    # Try without sub-requirement suffix (e.g., S2.14(a)(iv) -> S2.14)
    base_id = paragraph_id.split("(")[0] if "(" in paragraph_id else paragraph_id
    if base_id in registry:
        return registry[base_id]["pillar"]
    
    # Default mapping based on paragraph number ranges
    if paragraph_id.startswith("S1.") or paragraph_id.startswith("S2."):
        num_part = paragraph_id[3:].split("(")[0]
        try:
            num = int(num_part)
            if paragraph_id.startswith("S1."):
                if 26 <= num <= 27:
                    return "governance"
                elif 28 <= num <= 37:
                    return "strategy"
                elif 38 <= num <= 42:
                    return "risk_management"
                elif 43 <= num <= 53:
                    return "metrics_targets"
            else:  # S2
                if 5 <= num <= 7:
                    return "governance"
                elif 8 <= num <= 23:
                    return "strategy"
                elif 24 <= num <= 26:
                    return "risk_management"
                elif 27 <= num <= 37:
                    return "metrics_targets"
        except ValueError:
            pass
    
    return "governance"  # Default fallback


class ReportCompiler:
    """Service for compiling Source of Truth reports from database."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the compiler with a database session."""
        self.db = db
    
    async def compile_report(self, report_id: str) -> SourceOfTruthReportResponse:
        """Compile the full Source of Truth report.
        
        Args:
            report_id: The report UUID string.
            
        Returns:
            Compiled report with all pillars, claims, verdicts, and gaps.
        """
        report_uuid = UUID(report_id)
        
        # Load report
        report = await self.db.get(Report, report_uuid)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # Load claims with findings and verdicts
        claims_stmt = (
            select(Claim)
            .where(Claim.report_id == report_uuid)
            .options(
                selectinload(Claim.findings),
                selectinload(Claim.verdict),
            )
        )
        claims_result = await self.db.execute(claims_stmt)
        claims = list(claims_result.scalars().all())
        
        # Load disclosure gap findings
        gaps_stmt = (
            select(Finding)
            .where(Finding.report_id == report_uuid)
            .where(Finding.evidence_type == "disclosure_gap")
        )
        gaps_result = await self.db.execute(gaps_stmt)
        gap_findings = list(gaps_result.scalars().all())
        
        # Organize by pillar
        pillar_claims = self._organize_claims_by_pillar(claims)
        pillar_gaps = self._organize_gaps_by_pillar(gap_findings)
        
        # Build pillar sections
        pillars: dict[str, PillarSectionResponse] = {}
        for pillar in ["governance", "strategy", "risk_management", "metrics_targets"]:
            claims_list = pillar_claims.get(pillar, [])
            gaps_list = pillar_gaps.get(pillar, [])
            
            pillars[pillar] = PillarSectionResponse(
                pillar=pillar,  # type: ignore
                pillar_display_name=PILLAR_DISPLAY_NAMES[pillar],
                claims=claims_list,
                gaps=gaps_list,
                summary=self._compute_pillar_summary(claims_list, gaps_list),
            )
        
        # Compute overall summary
        summary = self._compute_report_summary(report_id, claims, gap_findings)
        
        compiled_at = datetime.now(timezone.utc)
        
        return SourceOfTruthReportResponse(
            report_id=report_id,
            filename=report.filename,
            status=report.status,
            summary=summary,
            pillars=pillars,
            compiled_at=compiled_at,
        )
    
    def _organize_claims_by_pillar(
        self, claims: list[Claim]
    ) -> dict[str, list[ClaimWithVerdictResponse]]:
        """Organize claims by IFRS pillar."""
        pillar_claims: dict[str, list[ClaimWithVerdictResponse]] = {
            "governance": [],
            "strategy": [],
            "risk_management": [],
            "metrics_targets": [],
        }
        
        for claim in claims:
            claim_response = self._build_claim_response(claim)
            
            # Determine pillar(s) from IFRS paragraphs
            pillars_found = set()
            if claim.ifrs_paragraphs:
                for mapping in claim.ifrs_paragraphs:
                    if isinstance(mapping, dict):
                        # Check if pillar is already in mapping
                        if "pillar" in mapping:
                            pillars_found.add(mapping["pillar"])
                        # Otherwise look up from paragraph_id
                        elif "paragraph_id" in mapping:
                            pillar = get_pillar_for_paragraph(mapping["paragraph_id"])
                            pillars_found.add(pillar)
            
            # If no pillars found, use claim type heuristics
            if not pillars_found:
                if claim.claim_type == "legal_governance":
                    pillars_found.add("governance")
                elif claim.claim_type == "strategic":
                    pillars_found.add("strategy")
                elif claim.claim_type == "quantitative":
                    pillars_found.add("metrics_targets")
                else:
                    pillars_found.add("strategy")  # Default
            
            # Add to each relevant pillar
            for pillar in pillars_found:
                if pillar in pillar_claims:
                    pillar_claims[pillar].append(claim_response)
        
        return pillar_claims
    
    def _organize_gaps_by_pillar(
        self, gap_findings: list[Finding]
    ) -> dict[str, list[DisclosureGapResponse]]:
        """Organize disclosure gaps by IFRS pillar."""
        pillar_gaps: dict[str, list[DisclosureGapResponse]] = {
            "governance": [],
            "strategy": [],
            "risk_management": [],
            "metrics_targets": [],
        }
        
        registry = _load_paragraph_registry()
        
        for finding in gap_findings:
            details = finding.details or {}
            paragraph_id = details.get("paragraph_id", "")
            
            # Get pillar
            pillar = get_pillar_for_paragraph(paragraph_id)
            
            # Get requirement info from registry
            para_info = registry.get(paragraph_id, {})
            
            gap_response = DisclosureGapResponse(
                gap_id=str(finding.id),
                paragraph_id=paragraph_id,
                pillar=pillar,  # type: ignore
                gap_type=details.get("gap_type", "fully_unaddressed"),
                requirement_text=para_info.get("requirement_text", details.get("requirement_text", "")),
                missing_requirements=details.get("missing_requirements", []),
                materiality_context=para_info.get("materiality_note", details.get("materiality_context", "")),
                severity=details.get("severity", "medium"),
                s1_counterpart=para_info.get("s1_counterpart"),
            )
            
            if pillar in pillar_gaps:
                pillar_gaps[pillar].append(gap_response)
        
        return pillar_gaps
    
    def _build_claim_response(self, claim: Claim) -> ClaimWithVerdictResponse:
        """Build a ClaimWithVerdictResponse from a Claim model."""
        # Build IFRS mappings
        ifrs_mappings = []
        if claim.ifrs_paragraphs:
            for mapping in claim.ifrs_paragraphs:
                if isinstance(mapping, dict):
                    ifrs_mappings.append(IFRSMappingResponse(
                        paragraph_id=mapping.get("paragraph_id", ""),
                        pillar=mapping.get("pillar", get_pillar_for_paragraph(mapping.get("paragraph_id", ""))),
                        relevance=mapping.get("relevance"),
                    ))
        
        claim_response = ClaimResponse(
            claim_id=str(claim.id),
            claim_text=claim.claim_text,
            claim_type=claim.claim_type,  # type: ignore
            source_page=claim.source_page,
            source_location=claim.source_location,
            ifrs_paragraphs=ifrs_mappings,
            priority=claim.priority,  # type: ignore
            agent_reasoning=claim.agent_reasoning,
            created_at=claim.created_at,
        )
        
        # Build verdict response
        verdict_response = None
        if claim.verdict:
            verdict_response = VerdictResponse(
                verdict_id=str(claim.verdict.id),
                verdict=claim.verdict.verdict,  # type: ignore
                reasoning=claim.verdict.reasoning,
                ifrs_mapping=claim.verdict.ifrs_mapping or [],
                evidence_summary=claim.verdict.evidence_summary,
                iteration_count=claim.verdict.iteration_count,
                created_at=claim.verdict.created_at,
            )
        
        # Build evidence chain from findings
        evidence_chain = []
        if claim.findings:
            sorted_findings = sorted(
                claim.findings,
                key=lambda f: (f.iteration, f.created_at)
            )
            for finding in sorted_findings:
                evidence_chain.append(EvidenceChainEntry(
                    finding_id=str(finding.id),
                    agent_name=finding.agent_name,  # type: ignore
                    evidence_type=finding.evidence_type,
                    summary=finding.summary,
                    supports_claim=finding.supports_claim,
                    confidence=finding.confidence,  # type: ignore
                    reasoning=finding.details.get("reasoning") if finding.details else None,
                    iteration=finding.iteration,
                    created_at=finding.created_at,
                ))
        
        return ClaimWithVerdictResponse(
            claim=claim_response,
            verdict=verdict_response,
            evidence_chain=evidence_chain,
        )
    
    def _compute_pillar_summary(
        self,
        claims: list[ClaimWithVerdictResponse],
        gaps: list[DisclosureGapResponse],
    ) -> PillarSummaryResponse:
        """Compute summary statistics for a single pillar."""
        verified = sum(1 for c in claims if c.verdict and c.verdict.verdict == "verified")
        unverified = sum(1 for c in claims if c.verdict and c.verdict.verdict == "unverified")
        contradicted = sum(1 for c in claims if c.verdict and c.verdict.verdict == "contradicted")
        insufficient = sum(1 for c in claims if c.verdict and c.verdict.verdict == "insufficient_evidence")
        
        return PillarSummaryResponse(
            total_claims=len(claims),
            verified_claims=verified,
            unverified_claims=unverified,
            contradicted_claims=contradicted,
            insufficient_evidence_claims=insufficient,
            disclosure_gaps=len(gaps),
        )
    
    def _compute_report_summary(
        self,
        report_id: str,
        claims: list[Claim],
        gap_findings: list[Finding],
    ) -> ReportSummaryResponse:
        """Compute overall report summary statistics."""
        # Count verdicts by type
        verdicts_count = {"verified": 0, "unverified": 0, "contradicted": 0, "insufficient_evidence": 0}
        max_iteration = 1
        
        for claim in claims:
            if claim.verdict:
                verdict = claim.verdict.verdict
                if verdict in verdicts_count:
                    verdicts_count[verdict] += 1
                max_iteration = max(max_iteration, claim.verdict.iteration_count)
        
        # Count gaps by status
        gaps_by_status = {"fully_unaddressed": 0, "partially_addressed": 0}
        for gap in gap_findings:
            gap_type = gap.details.get("gap_type", "fully_unaddressed") if gap.details else "fully_unaddressed"
            if gap_type in gaps_by_status:
                gaps_by_status[gap_type] += 1
        
        # Compute coverage by pillar (verified / total)
        pillar_claims = self._organize_claims_by_pillar(claims)
        coverage_by_pillar = {}
        for pillar, p_claims in pillar_claims.items():
            total = len(p_claims)
            verified = sum(1 for c in p_claims if c.verdict and c.verdict.verdict == "verified")
            coverage_by_pillar[pillar] = (verified / total * 100) if total > 0 else 0.0
        
        return ReportSummaryResponse(
            report_id=report_id,
            total_claims=len(claims),
            verdicts_by_type=VerdictBreakdown(**verdicts_count),
            coverage_by_pillar=coverage_by_pillar,
            gaps_by_status=gaps_by_status,
            pipeline_iterations=max_iteration,
            compiled_at=datetime.now(timezone.utc),
        )
    
    async def get_claims_filtered(
        self,
        report_id: str,
        pillar: str | None = None,
        verdict: str | None = None,
        claim_type: str | None = None,
        agent: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[ClaimWithVerdictResponse], int]:
        """Get claims with optional filters.
        
        Returns:
            Tuple of (filtered claims list, total count).
        """
        report_uuid = UUID(report_id)
        
        # Load all claims with relationships
        stmt = (
            select(Claim)
            .where(Claim.report_id == report_uuid)
            .options(
                selectinload(Claim.findings),
                selectinload(Claim.verdict),
            )
        )
        result = await self.db.execute(stmt)
        all_claims = list(result.scalars().all())
        
        # Build responses and filter
        filtered = []
        for claim in all_claims:
            claim_response = self._build_claim_response(claim)
            
            # Apply pillar filter
            if pillar:
                claim_pillars = set()
                for mapping in claim_response.claim.ifrs_paragraphs:
                    claim_pillars.add(mapping.pillar)
                if pillar not in claim_pillars:
                    continue
            
            # Apply verdict filter
            if verdict:
                if not claim_response.verdict or claim_response.verdict.verdict != verdict:
                    continue
            
            # Apply claim type filter
            if claim_type:
                if claim_response.claim.claim_type != claim_type:
                    continue
            
            # Apply agent filter
            if agent:
                agent_found = any(e.agent_name == agent for e in claim_response.evidence_chain)
                if not agent_found:
                    continue
            
            filtered.append(claim_response)
        
        total = len(filtered)
        
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated = filtered[start:end]
        
        return paginated, total
    
    async def get_gaps_filtered(
        self,
        report_id: str,
        pillar: str | None = None,
        gap_status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[DisclosureGapResponse], int]:
        """Get disclosure gaps with optional filters.
        
        Returns:
            Tuple of (filtered gaps list, total count).
        """
        report_uuid = UUID(report_id)
        
        # Load gap findings
        stmt = (
            select(Finding)
            .where(Finding.report_id == report_uuid)
            .where(Finding.evidence_type == "disclosure_gap")
        )
        result = await self.db.execute(stmt)
        gap_findings = list(result.scalars().all())
        
        # Organize by pillar
        pillar_gaps = self._organize_gaps_by_pillar(gap_findings)
        
        # Flatten and filter
        all_gaps = []
        for p, gaps in pillar_gaps.items():
            if pillar and p != pillar:
                continue
            for gap in gaps:
                if gap_status and gap.gap_type != gap_status:
                    continue
                all_gaps.append(gap)
        
        total = len(all_gaps)
        
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated = all_gaps[start:end]
        
        return paginated, total
