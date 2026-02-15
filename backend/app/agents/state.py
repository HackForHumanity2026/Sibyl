"""LangGraph shared state schema for the Sibyl pipeline.

This module defines the state schema for LangGraph using TypedDict with
Annotated types. List fields that receive concurrent updates from multiple
parallel nodes (e.g., specialist agents writing to 'findings' simultaneously)
use `operator.add` as the reducer function to merge the updates.

See: https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers
"""

import operator
from typing import Annotated, TypedDict

from pydantic import BaseModel


# =============================================================================
# Pydantic models for individual data types
# =============================================================================


class DocumentChunk(BaseModel):
    """A chunk of parsed document content."""

    chunk_id: str
    text: str
    page_number: int | None = None
    section_header: str | None = None
    metadata: dict = {}


class Claim(BaseModel):
    """A verifiable sustainability claim extracted from the report."""

    claim_id: str
    text: str
    page_number: int
    claim_type: str  # geographic | quantitative | legal_governance | strategic | environmental
    ifrs_paragraphs: list[str] = []
    priority: str = "medium"  # high | medium | low
    source_location: dict | None = None
    agent_reasoning: str | None = None


class RoutingAssignment(BaseModel):
    """Maps a claim to one or more specialist agents."""

    claim_id: str
    assigned_agents: list[str]  # agent names
    reasoning: str | None = None


class AgentStatus(BaseModel):
    """Current status of a specialist agent."""

    agent_name: str
    status: str = "idle"  # idle | working | completed | error
    claims_assigned: int = 0
    claims_completed: int = 0
    error_message: str | None = None


class AgentFinding(BaseModel):
    """Evidence gathered by a specialist agent."""

    finding_id: str
    agent_name: str
    claim_id: str
    evidence_type: str
    summary: str
    details: dict = {}
    supports_claim: bool | None = None
    confidence: str | None = None  # high | medium | low
    iteration: int = 1


class InfoRequest(BaseModel):
    """Cross-domain information request from one agent."""

    request_id: str
    requesting_agent: str
    description: str
    context: dict = {}
    status: str = "pending"  # pending | routed | responded


class InfoResponse(BaseModel):
    """Response to a cross-domain information request."""

    request_id: str
    responding_agent: str
    response: str
    details: dict = {}


class ClaimVerdict(BaseModel):
    """Judge Agent's final verdict on a claim."""

    claim_id: str
    verdict: str  # verified | unverified | contradicted | insufficient_evidence
    reasoning: str
    ifrs_mapping: list[dict]  # [{paragraph: "S2.14(a)(iv)", status: "compliant"}]
    evidence_summary: dict = {}
    iteration_count: int = 1


class ReinvestigationRequest(BaseModel):
    """Judge Agent's request for deeper investigation."""

    claim_id: str
    target_agents: list[str]
    evidence_gap: str
    refined_queries: list[str] = []
    required_evidence: str | None = None


class StreamEvent(BaseModel):
    """Event emitted to the frontend via SSE."""

    event_type: str
    # agent_started | agent_thinking | agent_completed | claim_routed |
    # evidence_found | verdict_issued | reinvestigation | pipeline_completed | error
    agent_name: str | None = None
    data: dict = {}
    timestamp: str  # ISO 8601


# =============================================================================
# Custom reducers for complex merge operations
# =============================================================================


def merge_agent_status(
    current: dict[str, AgentStatus], updates: dict[str, AgentStatus]
) -> dict[str, AgentStatus]:
    """Merge agent status dictionaries, preferring newer updates."""
    if not current:
        return updates
    if not updates:
        return current
    merged = dict(current)
    merged.update(updates)
    return merged


# =============================================================================
# LangGraph State Schema (TypedDict with Annotated reducers)
# =============================================================================


class SibylState(TypedDict, total=False):
    """Shared state for the entire LangGraph pipeline.

    Uses TypedDict with Annotated types for LangGraph compatibility.
    List fields use `operator.add` as reducer to merge concurrent updates
    from parallel specialist agent nodes.

    Fields marked with `Annotated[..., operator.add]` will concatenate
    list values when multiple nodes write to them in the same step.
    """

    # --- Input (set once, not updated concurrently) ---
    report_id: str
    document_content: str
    document_chunks: list[DocumentChunk]

    # --- Claims Agent output (set once by claims agent) ---
    claims: Annotated[list[Claim], operator.add]

    # --- Orchestrator tracking ---
    # routing_plan: set by orchestrator, may be updated on re-investigation
    routing_plan: Annotated[list[RoutingAssignment], operator.add]
    # agent_status: dictionary merging from multiple agents
    agent_status: Annotated[dict[str, AgentStatus], merge_agent_status]

    # --- Specialist agent findings (CONCURRENT WRITES from parallel agents) ---
    findings: Annotated[list[AgentFinding], operator.add]

    # --- Inter-agent communication ---
    info_requests: Annotated[list[InfoRequest], operator.add]
    info_responses: Annotated[list[InfoResponse], operator.add]

    # --- Judge Agent ---
    verdicts: Annotated[list[ClaimVerdict], operator.add]
    reinvestigation_requests: Annotated[list[ReinvestigationRequest], operator.add]
    iteration_count: int
    max_iterations: int

    # --- Disclosure gaps (Legal Agent) ---
    disclosure_gaps: Annotated[list[dict], operator.add]

    # --- Streaming (CONCURRENT WRITES from parallel agents) ---
    events: Annotated[list[StreamEvent], operator.add]
