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

from app.agents.callbacks import SSECallbackHandler
from app.agents.event_registry import get_event_queue, remove_event_queue
from app.agents.graph import get_checkpointer, get_compiled_graph
from app.agents.state import SibylState, StreamEvent
from app.core.config import settings
from app.models.report import Report

logger = logging.getLogger(__name__)


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
    
    # Create initial state
    initial_state = SibylState(
        report_id=report_id,
        document_content=report.parsed_content,
        document_chunks=[],
        max_iterations=getattr(settings, 'MAX_JUDGE_ITERATIONS', 3),
    )
    
    # Set up SSE streaming
    event_queue = get_event_queue(report_id)
    callback_handler = SSECallbackHandler(event_queue)
    
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
        # Execute the pipeline
        logger.info("Invoking pipeline graph for report: %s", report_id)
        
        # Run the graph
        last_event_count = 0
        
        async for event in compiled_graph.astream(initial_state, config=config):
            # Extract the state from the event
            # LangGraph astream yields dict with node outputs
            for node_name, node_output in event.items():
                # Call callbacks manually since we're using astream
                await callback_handler.on_node_start(node_name, initial_state)
                
                # Get the state from the node output
                if hasattr(node_output, 'events'):
                    state_events = node_output.events
                elif isinstance(node_output, dict) and 'events' in node_output:
                    state_events = node_output.get('events', [])
                else:
                    state_events = []
                
                # Push new events to the queue
                for event_obj in state_events[last_event_count:]:
                    try:
                        await event_queue.put(event_obj)
                    except asyncio.QueueFull:
                        logger.warning("Event queue full, dropping event")
                
                if state_events:
                    last_event_count = len(state_events)
                
                logger.debug("Node %s completed", node_name)
        
        logger.info("Pipeline completed successfully for report: %s", report_id)
        
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
    
    # Create initial state with existing claims
    initial_state = SibylState(
        report_id=report_id,
        document_content=report.parsed_content,
        document_chunks=[],
        claims=state_claims,
        max_iterations=getattr(settings, 'MAX_JUDGE_ITERATIONS', 3),
    )
    
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
        # Execute starting from orchestrator
        # Note: This requires customizing the graph entry point, 
        # which is done by setting claims in initial state
        # The extract_claims node will see claims already exist and skip
        
        last_event_count = 0
        
        async for event in compiled_graph.astream(initial_state, config=config):
            for node_name, node_output in event.items():
                if isinstance(node_output, dict) and 'events' in node_output:
                    state_events = node_output.get('events', [])
                    for event_obj in state_events[last_event_count:]:
                        try:
                            await event_queue.put(event_obj)
                        except asyncio.QueueFull:
                            pass
                    if state_events:
                        last_event_count = len(state_events)
        
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
