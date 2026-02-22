"""Pipeline runner for executing the full Sibyl LangGraph pipeline.

Implements FRD 5 Section 9.2.

Orchestrates the complete analysis pipeline from claims extraction through
verdict generation, with SSE streaming and PostgreSQL checkpointing.
"""

import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.event_registry import get_event_queue, remove_event_queue
from app.agents.graph import get_checkpointer, get_compiled_graph, EXTRACT_CLAIMS
from app.agents.state import SibylState, StreamEvent, Claim as StateClaim
from app.core.config import settings
from app.models.report import Report
from app.models.claim import Claim
from app.core.database import generate_uuid7

logger = logging.getLogger(__name__)


async def _persist_claims(
    report_id: str, 
    state_claims: list[StateClaim], 
    db: AsyncSession
) -> int:
    """Persist extracted claims to the database.
    
    Args:
        report_id: The report's unique identifier
        state_claims: List of claims from the pipeline state
        db: Database session
        
    Returns:
        Number of claims persisted
    """
    persisted_count = 0
    
    for sc in state_claims:
        # Build IFRS paragraphs with metadata
        ifrs_paragraphs = []
        for pid in (sc.ifrs_paragraphs or []):
            ifrs_paragraphs.append({
                "paragraph_id": pid,
                "pillar": "unknown",  # Will be enriched later
                "relevance": "Preliminary mapping",
            })
        
        claim = Claim(
            id=generate_uuid7(),
            report_id=UUID(report_id),
            claim_text=sc.text,
            claim_type=sc.claim_type,
            source_page=sc.page_number,
            source_location=sc.source_location or {},
            ifrs_paragraphs=ifrs_paragraphs,
            priority=sc.priority,
            agent_reasoning=sc.agent_reasoning,
        )
        db.add(claim)
        persisted_count += 1
    
    await db.commit()
    logger.warning("Persisted %d claims for report %s", persisted_count, report_id)
    return persisted_count


async def _persist_findings(
    report_id: str, 
    findings: list, 
    db: AsyncSession
) -> int:
    """Persist agent findings to the database.
    
    Args:
        report_id: The report's unique identifier
        findings: List of AgentFinding from the pipeline state
        db: Database session
        
    Returns:
        Number of findings persisted
    """
    from app.models.finding import Finding
    from app.models.claim import Claim as ClaimModel
    
    persisted_count = 0
    
    for f in findings:
        # Check if finding already exists (by finding_id)
        finding_id = getattr(f, 'finding_id', None) or f.get('finding_id') if isinstance(f, dict) else None
        if not finding_id:
            continue
            
        # Get finding attributes (handle both object and dict)
        if hasattr(f, 'agent_name'):
            agent_name = f.agent_name
            claim_id_str = f.claim_id
            evidence_type = f.evidence_type
            summary = f.summary
            details = f.details
            supports_claim = f.supports_claim
            confidence = f.confidence
            iteration = f.iteration
        else:
            agent_name = f.get('agent_name', 'unknown')
            claim_id_str = f.get('claim_id')
            evidence_type = f.get('evidence_type', 'unknown')
            summary = f.get('summary', '')
            details = f.get('details', {})
            supports_claim = f.get('supports_claim')
            confidence = f.get('confidence')
            iteration = f.get('iteration', 1)
        
        # Resolve claim UUID from claim_id string
        claim_uuid = None
        if claim_id_str:
            stmt = select(ClaimModel.id).where(
                ClaimModel.report_id == UUID(report_id),
                ClaimModel.claim_id == claim_id_str
            )
            result = await db.execute(stmt)
            claim_row = result.first()
            if claim_row:
                claim_uuid = claim_row[0]
        
        finding = Finding(
            id=generate_uuid7(),
            report_id=UUID(report_id),
            claim_id=claim_uuid,
            agent_name=agent_name,
            evidence_type=evidence_type,
            summary=summary,
            details=details,
            supports_claim=supports_claim,
            confidence=confidence,
            iteration=iteration,
        )
        db.add(finding)
        persisted_count += 1
    
    if persisted_count > 0:
        await db.commit()
        logger.warning("Persisted %d findings for report %s", persisted_count, report_id)
    
    return persisted_count


async def load_report(report_id: str, db: AsyncSession) -> Report:
    """Load a report from the database.
    
    Args:
        report_id: The report's unique identifier
        db: Database session
        
    Returns:
        Report model instance
        
    Raises:
        ValueError: If report not found or has no parsed content
    """
    stmt = select(Report).where(Report.id == UUID(report_id))
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    
    if report is None:
        raise ValueError(f"Report not found: {report_id}")
    
    if report.parsed_content is None:
        raise ValueError(f"Report has no parsed content: {report_id}")
    
    return report


async def run_pipeline(report_id: str, db: AsyncSession) -> None:
    """Execute the full Sibyl analysis pipeline for a report.
    
    Steps:
    1. Load the report and its parsed content from the database.
    2. Create the initial SibylState.
    3. Set up the event queue and callback handler.
    4. Compile the graph with PostgreSQL checkpointing.
    5. Invoke the graph.
    6. Handle completion or error.
    
    Args:
        report_id: The report's unique identifier
        db: Database session
    """
    logger.info("Starting pipeline for report: %s", report_id)
    
    # Load report
    report = await load_report(report_id, db)
    
    # Create initial state (SibylState is a TypedDict)
    initial_state: SibylState = {
        "report_id": report_id,
        "document_content": report.parsed_content,
        "document_chunks": [],
        "max_iterations": getattr(settings, 'MAX_JUDGE_ITERATIONS', 3),
        "iteration_count": 0,
        "claims": [],
        "routing_plan": [],
        "agent_status": {},
        "findings": [],
        "info_requests": [],
        "info_responses": [],
        "verdicts": [],
        "reinvestigation_requests": [],
        "disclosure_gaps": [],
        "events": [],
    }
    
    # Set up SSE streaming
    event_queue = get_event_queue(report_id)
    
    # Compile graph with checkpointer
    try:
        checkpointer = await get_checkpointer()
    except Exception as e:
        logger.warning(
            "Failed to create checkpointer, running without checkpointing: %s",
            e,
        )
        checkpointer = None
    
    compiled_graph = get_compiled_graph(checkpointer=checkpointer)
    
    # Configure execution
    config = {
        "configurable": {"thread_id": report_id},
    }
    
    try:
        # Execute the pipeline with real-time streaming
        # stream_mode=["updates", "custom"] enables:
        # - "updates": State updates after each node completes
        # - "custom": Real-time events from get_stream_writer() calls within nodes
        logger.warning("Invoking pipeline graph for report: %s", report_id)
        logger.warning("Initial state keys: %s", list(initial_state.keys()))
        
        node_count = 0
        
        async for stream_mode, chunk in compiled_graph.astream(
            initial_state,
            config=config,
            stream_mode=["updates", "custom"],
        ):
            if stream_mode == "custom":
                # Real-time events from get_stream_writer() - sent immediately during node execution
                if isinstance(chunk, StreamEvent):
                    try:
                        await event_queue.put(chunk)
                        logger.debug("Pushed custom event: %s from %s", chunk.event_type, chunk.agent_name)
                    except asyncio.QueueFull:
                        logger.warning("Event queue full, dropping custom event")
                elif isinstance(chunk, dict):
                    # Handle dict-formatted events (convert to StreamEvent)
                    try:
                        event_obj = StreamEvent(**chunk)
                        await event_queue.put(event_obj)
                        logger.debug("Pushed custom dict event: %s", event_obj.event_type)
                    except Exception as e:
                        logger.warning("Invalid custom event dict: %s", e)
            
            elif stream_mode == "updates":
                # State updates - node completed, extract info for persistence
                for node_name, node_output in chunk.items():
                    node_count += 1
                    logger.warning("Node completed: %s (output type: %s)", node_name, type(node_output).__name__)
                    
                    # Log output contents for debugging
                    if isinstance(node_output, dict):
                        logger.debug("Node %s output keys: %s", node_name, list(node_output.keys()))
                    
                    # Persist claims immediately after extraction
                    if node_name == EXTRACT_CLAIMS:
                        if isinstance(node_output, dict) and 'claims' in node_output:
                            extracted_claims = node_output.get('claims', [])
                            if extracted_claims:
                                logger.warning("Persisting %d claims immediately", len(extracted_claims))
                                await _persist_claims(report_id, extracted_claims, db)
                    
                    # Persist findings immediately after each specialist agent completes
                    if node_name.startswith('investigate_'):
                        if isinstance(node_output, dict) and 'findings' in node_output:
                            new_findings = node_output.get('findings', [])
                            if new_findings:
                                logger.warning("Persisting %d findings from %s", len(new_findings), node_name)
                                await _persist_findings(report_id, new_findings, db)
        
        logger.warning("Pipeline completed for report %s (%d nodes)", report_id, node_count)
        
        # Push sentinel to close SSE connection
        await event_queue.put(None)
        
    except Exception as e:
        logger.exception("Pipeline failed for report %s: %s", report_id, e)
        
        # Emit error event
        error_event = StreamEvent(
            event_type="error",
            agent_name=None,
            data={"message": str(e)},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        try:
            await event_queue.put(error_event)
        except asyncio.QueueFull:
            pass
        
        # Push sentinel
        await event_queue.put(None)
        
        raise
        
    finally:
        # Clean up the event queue
        remove_event_queue(report_id)


async def run_pipeline_skip_claims(
    report_id: str,
    db: AsyncSession,
) -> None:
    """Execute the pipeline starting from orchestration (skip claims extraction).
    
    Used when claims have already been extracted and we want to re-run
    the investigation/routing phase.
    
    Args:
        report_id: The report's unique identifier
        db: Database session
    """
    from app.models.claim import Claim as ClaimModel
    from app.agents.state import Claim
    
    logger.info("Starting pipeline (skip claims) for report: %s", report_id)
    
    # Load report
    report = await load_report(report_id, db)
    
    # Load existing claims
    stmt = select(ClaimModel).where(ClaimModel.report_id == UUID(report_id))
    result = await db.execute(stmt)
    db_claims = result.scalars().all()
    
    if not db_claims:
        raise ValueError(f"No claims found for report: {report_id}")
    
    # Convert to state claims
    state_claims = []
    for c in db_claims:
        state_claims.append(
            Claim(
                claim_id=str(c.id),
                text=c.claim_text,
                page_number=c.source_page,
                claim_type=c.claim_type,
                ifrs_paragraphs=[p.get("paragraph_id", "") for p in (c.ifrs_paragraphs or [])],
                priority=c.priority or "medium",
                source_location=c.source_location,
                agent_reasoning=c.agent_reasoning,
            )
        )
    
    # Create initial state with existing claims (SibylState is a TypedDict)
    initial_state: SibylState = {
        "report_id": report_id,
        "document_content": report.parsed_content,
        "document_chunks": [],
        "claims": state_claims,
        "max_iterations": getattr(settings, 'MAX_JUDGE_ITERATIONS', 3),
        "iteration_count": 0,
        "routing_plan": [],
        "agent_status": {},
        "findings": [],
        "info_requests": [],
        "info_responses": [],
        "verdicts": [],
        "reinvestigation_requests": [],
        "disclosure_gaps": [],
        "events": [],
    }
    
    # Set up SSE streaming
    event_queue = get_event_queue(report_id)
    
    # Compile graph with checkpointer
    try:
        checkpointer = await get_checkpointer()
    except Exception as e:
        logger.warning("Checkpointer unavailable: %s", e)
        checkpointer = None
    
    compiled_graph = get_compiled_graph(checkpointer=checkpointer)
    
    config = {
        "configurable": {"thread_id": f"{report_id}-rerun"},
    }
    
    try:
        # Execute starting from orchestrator with real-time streaming
        # Note: Claims are pre-populated in initial_state, extract_claims will skip
        
        async for stream_mode, chunk in compiled_graph.astream(
            initial_state,
            config=config,
            stream_mode=["updates", "custom"],
        ):
            if stream_mode == "custom":
                # Real-time events from get_stream_writer()
                if isinstance(chunk, StreamEvent):
                    try:
                        await event_queue.put(chunk)
                    except asyncio.QueueFull:
                        pass
                elif isinstance(chunk, dict):
                    try:
                        event_obj = StreamEvent(**chunk)
                        await event_queue.put(event_obj)
                    except Exception:
                        pass
            
            elif stream_mode == "updates":
                # State updates - node completed
                for node_name, node_output in chunk.items():
                    logger.debug("Node completed (skip-claims): %s", node_name)
        
        await event_queue.put(None)
        
    except Exception as e:
        logger.exception("Pipeline (skip claims) failed: %s", e)
        error_event = StreamEvent(
            event_type="error",
            agent_name=None,
            data={"message": str(e)},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await event_queue.put(error_event)
        await event_queue.put(None)
        raise
        
    finally:
        remove_event_queue(report_id)
