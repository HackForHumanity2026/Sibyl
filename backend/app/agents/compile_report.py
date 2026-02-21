"""Compile Report - persists results and finalizes the analysis pipeline.

Implements FRD 13 (stub implementation in FRD 5).

This is the terminal node in the pipeline that:
1. Persists findings and verdicts to the database
2. Sets the report status to "completed"
3. Emits the pipeline_completed event
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import SibylState, StreamEvent
from app.core.database import generate_uuid7, get_db_session
from app.models.claim import Claim as DBClaim
from app.models.finding import Finding
from app.models.report import Report
from app.models.verdict import Verdict

logger = logging.getLogger(__name__)


async def compile_report(state: SibylState) -> dict:
    """Compile Report stub: Persist results and finalize the pipeline.
    
    This stub implementation:
    1. Reads all verdicts, findings, and disclosure gaps from state
    2. Persists verdicts and findings to the database
    3. Sets the report status to "completed"
    4. Emits the pipeline_completed event
    
    Full implementation in FRD 13 will include:
    - Full Source of Truth report generation
    - PDF report compilation
    - Disclosure gap analysis summary
    - Confidence scoring aggregation
    
    Args:
        state: Final pipeline state with all verdicts and findings
        
    Returns:
        Empty partial state update (terminal node)
    """
    events: list[StreamEvent] = []
    
    # Get state values using dict access
    verdicts = state.get("verdicts", [])
    findings = state.get("findings", [])
    claims = state.get("claims", [])
    iteration_count = state.get("iteration_count", 0)
    
    # Emit start event
    events.append(
        StreamEvent(
            event_type="agent_started",
            agent_name="compiler",
            data={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    
    # Emit thinking event
    events.append(
        StreamEvent(
            event_type="agent_thinking",
            agent_name="compiler",
            data={
                "message": f"Compiling report with {len(verdicts)} verdicts "
                f"and {len(findings)} findings..."
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    
    # Persist to database
    try:
        async for db in get_db_session():
            await _persist_results(state, db)
            break
    except Exception as e:
        logger.exception("Failed to persist results: %s", e)
        events.append(
            StreamEvent(
                event_type="error",
                agent_name="compiler",
                data={"message": f"Failed to persist results: {e}"},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )
    
    # Compute summary statistics
    verdict_counts: dict[str, int] = {}
    for v in verdicts:
        verdict_counts[v.verdict] = verdict_counts.get(v.verdict, 0) + 1
    
    agent_findings: dict[str, int] = {}
    for f in findings:
        agent_findings[f.agent_name] = agent_findings.get(f.agent_name, 0) + 1
    
    # Emit pipeline_completed event
    events.append(
        StreamEvent(
            event_type="pipeline_completed",
            agent_name=None,
            data={
                "total_claims": len(claims),
                "total_findings": len(findings),
                "total_verdicts": len(verdicts),
                "iterations": iteration_count,
                "verdict_breakdown": verdict_counts,
                "findings_by_agent": agent_findings,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    
    # Return only NEW events - the reducer will merge them
    return {
        "events": events,
    }


async def _persist_results(state: SibylState, db: AsyncSession) -> None:
    """Persist claims, findings, and verdicts to the database.
    
    Args:
        state: Final pipeline state
        db: Database session
    """
    report_id_str = state.get("report_id", "")
    report_id = UUID(report_id_str)
    claims = state.get("claims", [])
    findings = state.get("findings", [])
    verdicts = state.get("verdicts", [])
    
    # Persist claims first (other entities reference them)
    claim_id_mapping: dict[str, UUID] = {}  # Maps state claim_id -> DB UUID
    for claim in claims:
        db_claim_id = generate_uuid7()
        claim_id_mapping[claim.claim_id] = db_claim_id
        
        db_claim = DBClaim(
            id=db_claim_id,
            report_id=report_id,
            claim_text=claim.text,
            claim_type=claim.claim_type,
            source_page=claim.page_number,
            source_location=claim.source_location,
            ifrs_paragraphs=[{"paragraph_id": p} for p in claim.ifrs_paragraphs],
            priority=claim.priority,
            agent_reasoning=claim.agent_reasoning,
        )
        db.add(db_claim)
    
    # Persist findings (using mapped claim IDs)
    for finding in findings:
        # Skip if this is a stub finding without real evidence
        if finding.details.get("stub"):
            continue
        
        # Map state claim_id to the persisted DB claim UUID
        db_claim_id = claim_id_mapping.get(finding.claim_id) if finding.claim_id else None
        
        db_finding = Finding(
            id=generate_uuid7(),
            report_id=report_id,
            claim_id=db_claim_id,
            agent_name=finding.agent_name,
            evidence_type=finding.evidence_type,
            summary=finding.summary,
            details=finding.details,
            supports_claim=finding.supports_claim,
            confidence=finding.confidence,
            iteration=finding.iteration,
        )
        db.add(db_finding)
    
    # Persist verdicts (using mapped claim IDs) with upsert to handle re-judging
    for verdict in verdicts:
        # Map state claim_id to the persisted DB claim UUID
        db_claim_id = claim_id_mapping.get(verdict.claim_id)
        if not db_claim_id:
            logger.warning(
                "Verdict references unknown claim_id: %s", verdict.claim_id
            )
            continue
        
        # Use upsert to update existing verdicts on re-judging
        verdict_data = {
            "id": generate_uuid7(),
            "report_id": report_id,
            "claim_id": db_claim_id,
            "verdict": verdict.verdict,
            "reasoning": verdict.reasoning,
            "ifrs_mapping": verdict.ifrs_mapping,
            "evidence_summary": verdict.evidence_summary,
            "iteration_count": verdict.iteration_count,
        }
        stmt = pg_insert(Verdict).values(**verdict_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["claim_id"],
            set_={
                "verdict": stmt.excluded.verdict,
                "reasoning": stmt.excluded.reasoning,
                "ifrs_mapping": stmt.excluded.ifrs_mapping,
                "evidence_summary": stmt.excluded.evidence_summary,
                "iteration_count": stmt.excluded.iteration_count,
            }
        )
        await db.execute(stmt)
    
    # Update report status to completed
    stmt = (
        update(Report)
        .where(Report.id == report_id)
        .values(status="completed")
    )
    await db.execute(stmt)
    
    await db.commit()
    
    logger.info(
        "Persisted %d claims, %d findings, and %d verdicts for report %s",
        len(claims),
        len([f for f in findings if not f.details.get("stub")]),
        len(verdicts),
        report_id_str,
    )
