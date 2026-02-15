"""LangGraph callback handler for SSE streaming.

Implements FRD 5 Section 7.2.

Captures StreamEvents from LangGraph node execution and forwards them
to connected SSE clients via asyncio.Queue.
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.agents.state import StreamEvent

logger = logging.getLogger(__name__)

# Mapping from LangGraph node names to agent names
NODE_TO_AGENT: dict[str, str] = {
    "extract_claims": "claims",
    "orchestrate": "orchestrator",
    "investigate_geography": "geography",
    "investigate_legal": "legal",
    "investigate_news": "news_media",
    "investigate_academic": "academic",
    "investigate_data": "data_metrics",
    "judge_evidence": "judge",
    "compile_report": "compiler",
}


class SSECallbackHandler:
    """Captures StreamEvents from LangGraph node execution and
    forwards them to connected SSE clients.
    
    Events are placed into an asyncio.Queue that the SSE endpoint
    reads from.
    """
    
    def __init__(self, event_queue: asyncio.Queue):
        """Initialize the callback handler.
        
        Args:
            event_queue: Queue to push events to for SSE streaming
        """
        self.event_queue = event_queue
        self._last_event_count: dict[str, int] = {}
    
    async def on_node_start(self, node_name: str, state) -> None:
        """Called when a node begins execution.
        
        Records the current event count for comparison after node completes.
        
        Args:
            node_name: Name of the LangGraph node
            state: Current SibylState (TypedDict)
        """
        # Track event count before node execution
        # Support both dict access (TypedDict) and attribute access (legacy)
        events = state.get("events", []) if isinstance(state, dict) else getattr(state, "events", [])
        event_count = len(events)
        self._last_event_count[node_name] = event_count
        logger.debug("Node %s started, event count: %d", node_name, event_count)
    
    async def on_node_end(self, node_name: str, state) -> None:
        """Called when a node completes execution.
        
        Extracts any new StreamEvents added to state.events since the
        last check and pushes them to the event queue.
        
        Args:
            node_name: Name of the LangGraph node
            state: Current SibylState after node execution
        """
        # Support both dict access (TypedDict) and attribute access (legacy)
        events = state.get("events", []) if isinstance(state, dict) else getattr(state, "events", None)
        if events is None:
            return
        
        # Get new events since node started
        last_count = self._last_event_count.get(node_name, 0)
        new_events = events[last_count:]
        
        # Push new events to the queue
        for event in new_events:
            try:
                self.event_queue.put_nowait(event)
                logger.debug(
                    "Pushed event from node %s: %s",
                    node_name,
                    event.event_type,
                )
            except asyncio.QueueFull:
                # Drop oldest event to make room
                try:
                    self.event_queue.get_nowait()
                    self.event_queue.put_nowait(event)
                    logger.warning(
                        "Queue full, dropped oldest event to push: %s",
                        event.event_type,
                    )
                except asyncio.QueueEmpty:
                    pass
        
        logger.debug(
            "Node %s completed, pushed %d events",
            node_name,
            len(new_events),
        )
    
    async def on_error(self, node_name: str, error: Exception) -> None:
        """Called when a node encounters an error.
        
        Creates and pushes an error StreamEvent.
        
        Args:
            node_name: Name of the LangGraph node that errored
            error: The exception that was raised
        """
        agent_name = NODE_TO_AGENT.get(node_name, node_name)
        
        event = StreamEvent(
            event_type="error",
            agent_name=agent_name,
            data={"message": str(error), "node": node_name},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
        try:
            self.event_queue.put_nowait(event)
            logger.warning(
                "Pushed error event for node %s: %s",
                node_name,
                str(error)[:100],
            )
        except asyncio.QueueFull:
            logger.error(
                "Failed to push error event (queue full) for node %s",
                node_name,
            )


def extract_new_events(state, last_count: int) -> list[StreamEvent]:
    """Extract new events from state since the last count.
    
    Helper function for manual event extraction.
    
    Args:
        state: SibylState with events list
        last_count: Number of events previously processed
        
    Returns:
        List of new StreamEvent objects
    """
    # Support both dict access (TypedDict) and attribute access (legacy)
    events = state.get("events", []) if isinstance(state, dict) else getattr(state, "events", [])
    if not events:
        return []
    return list(events[last_count:])
