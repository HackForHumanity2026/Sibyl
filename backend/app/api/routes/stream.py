"""SSE streaming endpoints for real-time pipeline updates.

Implements FRD 5 Section 7.

Provides Server-Sent Events (SSE) endpoints that stream real-time
agent reasoning events to the frontend during pipeline execution.
"""

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.event_registry import get_event_queue, has_event_queue
from app.agents.state import StreamEvent
from app.core.dependencies import get_db
from app.models.report import Report

logger = logging.getLogger(__name__)

router = APIRouter()


def format_sse_event(event: StreamEvent, event_id: int) -> str:
    """Format a StreamEvent as an SSE message.
    
    Args:
        event: The StreamEvent to format
        event_id: Sequential event ID for reconnection support
        
    Returns:
        SSE-formatted string with event type, data, and ID
    """
    data = event.model_dump_json()
    lines = [
        f"event: {event.event_type}",
        f"data: {data}",
        f"id: {event_id}",
        "",
        "",  # Double newline terminates the event
    ]
    return "\n".join(lines)


async def get_report_or_404(report_id: str, db: AsyncSession) -> Report:
    """Get a report by ID or raise 404.
    
    Args:
        report_id: The report's unique identifier
        db: Database session
        
    Returns:
        Report model instance
        
    Raises:
        HTTPException: If report not found or invalid ID
    """
    try:
        report_uuid = UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report ID format.")
    
    stmt = select(Report).where(Report.id == report_uuid)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    
    return report


@router.get("/{report_id}")
async def stream_analysis(
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream real-time analysis events via Server-Sent Events.
    
    The client connects to this endpoint and receives events as the
    LangGraph pipeline executes. The connection remains open until
    the pipeline completes or errors.
    
    Event types:
    - agent_started: An agent node begins execution
    - agent_thinking: Agent reasoning/progress update
    - agent_completed: Agent node finishes successfully
    - claim_routed: Orchestrator routes a claim to agents
    - evidence_found: Agent finds evidence for a claim
    - verdict_issued: Judge issues a verdict
    - reinvestigation: Judge requests re-investigation
    - pipeline_completed: Full pipeline complete
    - error: Error during execution
    
    Args:
        report_id: The report's unique identifier
        db: Database session
        
    Returns:
        StreamingResponse with SSE content type
    """
    # Verify the report exists
    report = await get_report_or_404(report_id, db)
    
    # If the report is completed and no queue exists, return historical events
    # (Future: could load from checkpoint)
    if report.status == "completed" and not has_event_queue(report_id):
        async def completed_generator():
            # Send a completion event for already-completed reports
            event = StreamEvent(
                event_type="pipeline_completed",
                agent_name=None,
                data={"message": "Analysis already completed."},
                timestamp=report.updated_at.isoformat() if report.updated_at else "",
            )
            yield format_sse_event(event, 1)
        
        return StreamingResponse(
            completed_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    
    # If the report is in error state with no queue, return error event
    if report.status == "error" and not has_event_queue(report_id):
        async def error_generator():
            event = StreamEvent(
                event_type="error",
                agent_name=None,
                data={"message": report.error_message or "Analysis failed."},
                timestamp=report.updated_at.isoformat() if report.updated_at else "",
            )
            yield format_sse_event(event, 1)
        
        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    
    # Get or create the event queue for this report
    event_queue = get_event_queue(report_id)
    
    async def event_generator():
        """Generate SSE events from the queue."""
        event_id = 0
        
        try:
            while True:
                try:
                    # Wait for an event with timeout for keepalive
                    event = await asyncio.wait_for(
                        event_queue.get(),
                        timeout=30.0,
                    )
                    
                    if event is None:
                        # Sentinel: pipeline complete
                        logger.debug("Received sentinel, closing SSE stream")
                        break
                    
                    event_id += 1
                    yield format_sse_event(event, event_id)
                    
                except asyncio.TimeoutError:
                    # Send keepalive comment to prevent connection timeout
                    yield ": keepalive\n\n"
                    
        except asyncio.CancelledError:
            logger.debug("SSE connection cancelled for report: %s", report_id)
        except Exception as e:
            logger.exception("Error in SSE event generator: %s", e)
            # Try to send an error event
            error_event = StreamEvent(
                event_type="error",
                agent_name=None,
                data={"message": str(e)},
                timestamp="",
            )
            event_id += 1
            yield format_sse_event(error_event, event_id)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
