"""Event queue registry for SSE streaming.

Implements FRD 5 Section 7.7.

Maintains an in-memory registry of asyncio.Queue instances keyed by report_id.
Each queue holds StreamEvent objects that are consumed by the SSE endpoint.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

# Maximum queue size to prevent memory exhaustion
MAX_QUEUE_SIZE = 1000

# Registry of event queues keyed by report_id
_event_queues: dict[str, asyncio.Queue] = {}


def get_event_queue(report_id: str) -> asyncio.Queue:
    """Get or create an event queue for a report's pipeline execution.
    
    If a queue doesn't exist for the report_id, creates a new bounded queue.
    
    Args:
        report_id: The report's unique identifier
        
    Returns:
        asyncio.Queue instance for the report
    """
    if report_id not in _event_queues:
        _event_queues[report_id] = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)
        logger.info("Created event queue for report: %s", report_id)
    return _event_queues[report_id]


def remove_event_queue(report_id: str) -> None:
    """Remove an event queue after pipeline completion.
    
    Should be called after the pipeline completes to free resources.
    
    Args:
        report_id: The report's unique identifier
    """
    if report_id in _event_queues:
        del _event_queues[report_id]
        logger.info("Removed event queue for report: %s", report_id)


def has_event_queue(report_id: str) -> bool:
    """Check if an event queue exists for a report.
    
    Args:
        report_id: The report's unique identifier
        
    Returns:
        True if a queue exists, False otherwise
    """
    return report_id in _event_queues


async def push_event(report_id: str, event) -> bool:
    """Push an event to a report's queue.
    
    If the queue is full, logs a warning and drops the oldest event.
    
    Args:
        report_id: The report's unique identifier
        event: The StreamEvent to push (or None as sentinel)
        
    Returns:
        True if event was pushed, False if queue doesn't exist
    """
    if report_id not in _event_queues:
        logger.warning("No event queue for report %s, dropping event", report_id)
        return False
    
    queue = _event_queues[report_id]
    
    try:
        queue.put_nowait(event)
        return True
    except asyncio.QueueFull:
        # Drop oldest event to make room
        try:
            queue.get_nowait()
            logger.warning(
                "Event queue full for report %s, dropped oldest event",
                report_id,
            )
            queue.put_nowait(event)
            return True
        except asyncio.QueueEmpty:
            pass
    
    return False
