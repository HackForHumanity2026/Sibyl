"""LangGraph shared state schema for the Sibyl pipeline."""

from pydantic import BaseModel


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


class SibylState(BaseModel):
    """Shared state for the entire LangGraph pipeline."""

    # --- Input ---
    report_id: str
    document_content: str = ""
    document_chunks: list[DocumentChunk] = []

    # --- Claims Agent output ---
    claims: list[Claim] = []

    # --- Orchestrator tracking ---
    routing_plan: list[RoutingAssignment] = []
    agent_status: dict[str, AgentStatus] = {}

    # --- Specialist agent findings ---
    findings: list[AgentFinding] = []

    # --- Inter-agent communication ---
    info_requests: list[InfoRequest] = []
    info_responses: list[InfoResponse] = []

    # --- Judge Agent ---
    verdicts: list[ClaimVerdict] = []
    reinvestigation_requests: list[ReinvestigationRequest] = []
    iteration_count: int = 0
    max_iterations: int = 3

    # --- Disclosure gaps (Legal Agent) ---
    disclosure_gaps: list[dict] = []

    # --- Streaming ---
    events: list[StreamEvent] = []
