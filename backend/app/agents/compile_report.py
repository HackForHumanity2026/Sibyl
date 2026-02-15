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

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import SibylState, StreamEvent
from app.core.database import generate_uuid7, get_db_session
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
    events = []
    
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
                "message": f"Compiling report with {len(state.verdicts)} verdicts "
                f"and {len(state.findings)} findings..."
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
    verdict_counts = {}
    for v in state.verdicts:
        verdict_counts[v.verdict] = verdict_counts.get(v.verdict, 0) + 1
    
    agent_findings = {}
    for f in state.findings:
        agent_findings[f.agent_name] = agent_findings.get(f.agent_name, 0) + 1
    
    # Emit pipeline_completed event
    events.append(
        StreamEvent(
            event_type="pipeline_completed",
            agent_name=None,
            data={
                "total_claims": len(state.claims),
                "total_findings": len(state.findings),
                "total_verdicts": len(state.verdicts),
                "iterations": state.iteration_count,
                "verdict_breakdown": verdict_counts,
                "findings_by_agent": agent_findings,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    
    return {
        "events": state.events + events,
    }


async def _persist_results(state: SibylState, db: AsyncSession) -> None:
    """Persist findings and verdicts to the database.
    
    Args:
        state: Final pipeline state
        db: Database session
    """
    report_id = UUID(state.report_id)
    
    # Persist findings
    for finding in state.findings:
        # Skip if this is a stub finding without real evidence
        if finding.details.get("stub"):
            continue
        
        db_finding = Finding(
            id=generate_uuid7(),
            report_id=report_id,
            claim_id=UUID(finding.claim_id) if finding.claim_id else None,
            agent_name=finding.agent_name,
            evidence_type=finding.evidence_type,
            summary=finding.summary,
            details=finding.details,
            supports_claim=finding.supports_claim,
            confidence=finding.confidence,
            iteration=finding.iteration,
        )
        db.add(db_finding)
    
    # Persist verdicts
    for verdict in state.verdicts:
        db_verdict = Verdict(
            id=generate_uuid7(),
            report_id=report_id,
            claim_id=UUID(verdict.claim_id),
            verdict=verdict.verdict,
            reasoning=verdict.reasoning,
            ifrs_mapping=verdict.ifrs_mapping,
            evidence_summary=verdict.evidence_summary,
            iteration_count=verdict.iteration_count,
        )
        db.add(db_verdict)
    
    # Update report status to completed
    stmt = (
        update(Report)
        .where(Report.id == report_id)
        .values(status="completed")
    )
    await db.execute(stmt)
    
    await db.commit()
    
    logger.info(
        "Persisted %d findings and %d verdicts for report %s",
        len([f for f in state.findings if not f.details.get("stub")]),
        len(state.verdicts),
        state.report_id,
    )
