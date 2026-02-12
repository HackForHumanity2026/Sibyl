# Feature Requirements Document: FRD 5 -- Orchestrator Agent & LangGraph Pipeline (v1.0)

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.3](../PRD.md) |
| **FRD Order** | [FRD Order](../FRD-order.md) |
| **PRD Sections** | 4.3 (Orchestrator Agent), 5.3 (LangGraph State Machine Design), 5.4 (Inter-Agent Communication) |
| **Type** | Feature |
| **Depends On** | FRD 0 (Setup Document), FRD 3 (Claims Agent) |
| **Delivers** | LangGraph StateGraph definition and compilation, Orchestrator routing logic, SSE streaming infrastructure, inter-agent communication protocol, re-investigation handling, conditional edges, LangGraph PostgreSQL checkpointing, Analysis Page right panel with agent reasoning stream |
| **Created** | 2026-02-09 |

---

## Summary

FRD 5 delivers the Orchestrator Agent and the compiled LangGraph pipeline -- the central nervous system of Sibyl's multi-agent architecture. The Orchestrator Agent (`app/agents/orchestrator_agent.py`) replaces the FRD 0 stub with a functional LangGraph node that receives categorized claims from the Claims Agent (FRD 3), constructs a routing plan assigning each claim to one or more specialist agents based on claim type and content, manages execution state (priorities, failure handling, timeouts, agent status tracking), processes inter-agent communication (`InfoRequest`/`InfoResponse` through shared state), and handles re-investigation requests from the Judge Agent by re-routing refined queries back to specialist agents. FRD 5 also compiles the full LangGraph `StateGraph` (`app/agents/graph.py`), replacing the FRD 0 stub with a functional graph definition including all nodes, edges, conditional fan-out from the Orchestrator to specialist agents, and the conditional cyclic edge from the Judge back to the Orchestrator. Specialist agent nodes remain as stubs that accept routed claims and return placeholder findings -- their implementations are delivered in FRDs 6-10. The SSE streaming infrastructure is built end-to-end: a LangGraph callback handler emits `StreamEvent` objects during node execution, a FastAPI SSE endpoint (`app/api/routes/stream.py`) streams these events to the frontend, and the Analysis Page right panel displays a real-time agent reasoning stream with agent tabs. LangGraph PostgreSQL checkpointing is configured for fault tolerance and pipeline replay. The Orchestrator uses Claude Sonnet 4.5 for routing decisions. After FRD 5, claims flow into the Orchestrator, routing plans are created, SSE events stream to the frontend, and the reasoning panel displays real-time agent activity -- with specialist agents existing as stubs ready for implementation in subsequent FRDs.

---

## Given Context (Preconditions)

The following are assumed to be in place from prior FRDs:

| Prerequisite | Source FRD | Deliverable |
|---|---|---|
| Docker Compose with PostgreSQL 17 + pgvector, Redis, backend, frontend | FRD 0 | `docker-compose.yml` |
| `SibylState` Pydantic schema with all supporting types (`Claim`, `RoutingAssignment`, `AgentStatus`, `AgentFinding`, `InfoRequest`, `InfoResponse`, `ClaimVerdict`, `ReinvestigationRequest`, `StreamEvent`) | FRD 0 | `app/agents/state.py` |
| Graph stub with placeholder node names (`parse_document`, `extract_claims`, `orchestrate`, `investigate_geography`, `investigate_legal`, `investigate_news`, `investigate_academic`, `investigate_data`, `judge_evidence`, `compile_report`) | FRD 0 | `app/agents/graph.py` |
| Orchestrator Agent stub (`orchestrate` function signature) | FRD 0 | `app/agents/orchestrator_agent.py` |
| All specialist agent stubs (`investigate_geography`, `investigate_legal`, `investigate_news`, `investigate_academic`, `investigate_data`) and Judge Agent stub (`judge_evidence`) | FRD 0 | `app/agents/*.py` |
| OpenRouter client wrapper with retry logic and `Models.CLAUDE_SONNET` constant | FRD 0 | `app/services/openrouter_client.py` |
| Stream route stub (`app/api/routes/stream.py`) | FRD 0 | Empty `APIRouter` |
| Analysis route with endpoints: `POST /api/v1/analysis/{reportId}/start`, `GET /api/v1/analysis/{reportId}/status`, `GET /api/v1/analysis/{reportId}/claims` | FRD 3 | `app/api/routes/analysis.py` |
| Analysis schema (`app/schemas/analysis.py`) with `StartAnalysisResponse`, `AnalysisStatusResponse`, `ClaimResponse`, `ClaimsListResponse` | FRD 3 | `app/schemas/analysis.py` |
| `Report` SQLAlchemy model with status values: `uploaded`, `parsing`, `parsed`, `analyzing`, `completed`, `error` | FRD 0 | `app/models/report.py` |
| `Claim`, `Finding`, `Verdict` SQLAlchemy models | FRD 0 | `app/models/claim.py`, `finding.py`, `verdict.py` |
| `extract_claims` functional node (Claims Agent) | FRD 3 | `app/agents/claims_agent.py` |
| `run_claims_extraction` standalone wrapper | FRD 3 | `app/agents/claims_agent.py` |
| Background task worker with Redis `BRPOP` pattern and multi-queue support | FRD 2, FRD 3 | `app/services/task_worker.py` |
| Frontend `AnalysisPage` with three-panel layout | FRD 4 | `src/pages/AnalysisPage.tsx` |
| Frontend `AnalysisLayout` with resizable panels (left: PDF viewer, center: placeholder, right: claims list) | FRD 4 | `src/components/Analysis/AnalysisLayout.tsx` |
| `useAnalysis` hook for analysis state management | FRD 3 | `src/hooks/useAnalysis.ts` |
| `AgentName`, `AgentStatus`, `AgentFinding` TypeScript types | FRD 0 | `src/types/agent.ts` |
| `useSSE` hook stub | FRD 0 | `src/hooks/index.ts` |
| SSE client stub (`src/services/sse.ts`) | FRD 0 | Empty file |

### Terms

| Term | Definition |
|---|---|
| Orchestrator | The supervisory LangGraph node that routes claims to specialist agents, manages execution, and coordinates inter-agent communication |
| Routing plan | A mapping of each claim to one or more specialist agents, created by the Orchestrator based on claim type and content |
| Fan-out | A LangGraph pattern where a single node dispatches work to multiple downstream nodes in parallel |
| Conditional edge | A LangGraph edge whose target is determined at runtime by a routing function |
| Cyclic edge | An edge that routes back to a previously executed node, creating a loop (Judge → Orchestrator) |
| SSE | Server-Sent Events -- a unidirectional server-to-client streaming protocol used to push real-time agent reasoning to the frontend |
| StreamEvent | A Pydantic model representing a single event emitted during pipeline execution, streamed to the frontend via SSE |
| Callback handler | A LangGraph mechanism that intercepts node execution events and emits StreamEvents |
| Checkpointing | LangGraph's persistence mechanism that saves pipeline state after each node execution for fault tolerance and replay |
| InfoRequest | A cross-domain information request posted by a specialist agent to the shared state, routed by the Orchestrator |
| InfoResponse | A response to an InfoRequest, posted by the target specialist agent |
| ReinvestigationRequest | A request from the Judge Agent to re-investigate a claim with refined queries and specific evidence gaps |

---

## Executive Summary (Gherkin-Style)

```gherkin
Feature: Orchestrator Agent & LangGraph Pipeline

  Background:
    Given  FRD 0, FRD 1, FRD 2, FRD 3, and FRD 4 are complete
    And    all services are running (backend, frontend, PostgreSQL, Redis)
    And    a sustainability report has been uploaded, parsed, and claims extracted
    And    claims are stored in the database with types, priorities, and IFRS mappings

  Scenario: Compile and run the LangGraph pipeline
    Given  the LangGraph StateGraph is defined with all nodes and edges
    When   the pipeline is invoked with a report_id
    Then   it loads the report and its extracted claims
    And    the pipeline executes nodes in order: extract_claims → orchestrate → specialists → judge_evidence → compile_report
    And    the conditional cyclic edge from Judge to Orchestrator is functional

  Scenario: Orchestrator routes claims to specialist agents
    Given  the Orchestrator receives a state with extracted claims
    When   it processes the claims
    Then   it creates a routing plan mapping each claim to one or more specialist agents
    And    geographic claims are routed to the Geography Agent
    And    quantitative claims are routed to the Data/Metrics Agent
    And    legal/governance claims are routed to the Legal Agent
    And    strategic claims are routed to multiple agents (Legal + Academic/Research)
    And    environmental claims are routed based on content analysis
    And    cross-domain claims are routed to multiple specialists
    And    the routing plan includes reasoning for each assignment

  Scenario: Specialist agent stubs accept routed claims
    Given  the Orchestrator has created a routing plan
    When   specialist agent nodes execute
    Then   each stub receives its assigned claims from the routing plan
    And    each stub returns placeholder findings
    And    the pipeline continues to the Judge node

  Scenario: SSE streaming delivers real-time events
    Given  the pipeline is executing
    When   a node emits StreamEvent objects
    Then   the LangGraph callback handler captures the events
    And    the FastAPI SSE endpoint streams the events to the frontend
    And    the frontend receives events within 500ms of emission
    And    events include: agent_started, agent_thinking, agent_completed, claim_routed, evidence_found, error

  Scenario: Frontend displays agent reasoning stream
    Given  the pipeline is running and SSE events are streaming
    When   the user views the Analysis Page
    Then   the right panel shows an agent reasoning stream
    And    agent tabs allow switching between agents to see their reasoning history
    And    the currently active agent's tab shows a pulsing indicator
    And    reasoning text appears in real time as agents work

  Scenario: Inter-agent communication protocol
    Given  a specialist agent posts an InfoRequest to the shared state
    When   the Orchestrator detects the pending request
    Then   it routes the request to the appropriate specialist agent(s)
    And    the target agent processes the request and posts an InfoResponse
    And    the requesting agent can access the response on its next execution
    And    all communication is visible in the SSE stream

  Scenario: Judge re-investigation cycle
    Given  the Judge Agent determines evidence is insufficient
    When   it posts ReinvestigationRequests to the shared state
    Then   the conditional edge routes back to the Orchestrator
    And    the Orchestrator re-routes refined queries to the specified agents
    And    the specialists re-investigate with the Judge's guidance
    And    the cycle continues until evidence is sufficient or max iterations is reached

  Scenario: LangGraph checkpointing persists state
    Given  the pipeline is executing
    When   a node completes
    Then   the state is checkpointed to PostgreSQL
    And    if the pipeline crashes, it can resume from the last checkpoint

  Scenario: Pipeline status transitions
    Given  the user starts analysis on a report
    When   the pipeline executes
    Then   the report status transitions: "analyzing" → "completed"
    And    intermediate status updates are available via the status endpoint
    And    on failure, the status transitions to "error" with a descriptive message

  Scenario: Handle pipeline execution errors
    Given  the pipeline is executing
    When   a specialist agent encounters an error
    Then   the Orchestrator marks that agent's status as "error"
    And    the pipeline continues with remaining agents
    And    an error StreamEvent is emitted
    And    the Judge evaluates whatever evidence is available
```

---

## Table of Contents

1. [LangGraph StateGraph Definition](#1-langgraph-stategraph-definition)
2. [Orchestrator Agent Implementation](#2-orchestrator-agent-implementation)
3. [Routing Logic](#3-routing-logic)
4. [Inter-Agent Communication Protocol](#4-inter-agent-communication-protocol)
5. [Re-Investigation Handling](#5-re-investigation-handling)
6. [Specialist Agent Stubs](#6-specialist-agent-stubs)
7. [SSE Streaming Infrastructure](#7-sse-streaming-infrastructure)
8. [LangGraph PostgreSQL Checkpointing](#8-langgraph-postgresql-checkpointing)
9. [Pipeline Execution and Task Integration](#9-pipeline-execution-and-task-integration)
10. [Backend Endpoints](#10-backend-endpoints)
11. [Frontend Agent Reasoning Panel](#11-frontend-agent-reasoning-panel)
12. [Analysis Status Updates](#12-analysis-status-updates)
13. [Error Handling](#13-error-handling)
14. [Exit Criteria](#14-exit-criteria)
15. [Appendix A: Orchestrator Routing Prompt](#appendix-a-orchestrator-routing-prompt)
16. [Appendix B: Graph Topology Diagram](#appendix-b-graph-topology-diagram)
17. [Appendix C: SSE Event Schema Reference](#appendix-c-sse-event-schema-reference)
18. [Appendix D: Pipeline Execution Sequence Diagram](#appendix-d-pipeline-execution-sequence-diagram)
19. [Design Decisions Log](#design-decisions-log)

---

## 1. LangGraph StateGraph Definition

### 1.1 Overview

The graph definition (`app/agents/graph.py`) replaces the FRD 0 stub with a compiled, executable LangGraph `StateGraph` that implements the full multi-agent pipeline described in PRD Section 5.3. The graph uses `SibylState` as its state schema and defines all nodes, edges, and conditional routing functions.

### 1.2 Graph Construction

The system shall define the graph as follows:

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

def build_graph() -> StateGraph:
    """Build the Sibyl multi-agent pipeline graph."""
    graph = StateGraph(SibylState)

    # Add nodes
    graph.add_node("extract_claims", extract_claims)
    graph.add_node("orchestrate", orchestrate)
    graph.add_node("investigate_geography", investigate_geography)
    graph.add_node("investigate_legal", investigate_legal)
    graph.add_node("investigate_news", investigate_news)
    graph.add_node("investigate_academic", investigate_academic)
    graph.add_node("investigate_data", investigate_data)
    graph.add_node("judge_evidence", judge_evidence)
    graph.add_node("compile_report", compile_report)

    # Entry edge
    graph.add_edge(START, "extract_claims")
    graph.add_edge("extract_claims", "orchestrate")

    # Orchestrator fans out to specialists via conditional edges
    graph.add_conditional_edges(
        "orchestrate",
        route_to_specialists,
        {
            "investigate_geography": "investigate_geography",
            "investigate_legal": "investigate_legal",
            "investigate_news": "investigate_news",
            "investigate_academic": "investigate_academic",
            "investigate_data": "investigate_data",
            "judge_evidence": "judge_evidence",  # Skip specialists if re-investigation with no new assignments
        }
    )

    # All specialist nodes converge to judge_evidence
    graph.add_edge("investigate_geography", "judge_evidence")
    graph.add_edge("investigate_legal", "judge_evidence")
    graph.add_edge("investigate_news", "judge_evidence")
    graph.add_edge("investigate_academic", "judge_evidence")
    graph.add_edge("investigate_data", "judge_evidence")

    # Judge conditionally cycles back or proceeds to compile
    graph.add_conditional_edges(
        "judge_evidence",
        should_continue_or_compile,
        {
            "orchestrate": "orchestrate",
            "compile_report": "compile_report",
        }
    )

    # Terminal edge
    graph.add_edge("compile_report", END)

    return graph
```

### 1.3 Conditional Routing Function: `route_to_specialists`

The `route_to_specialists` function examines the `SibylState` routing plan and returns the list of specialist agent nodes that have claims assigned to them:

```python
def route_to_specialists(state: SibylState) -> list[str]:
    """Determine which specialist agents to invoke based on the routing plan.

    Returns a list of node names for agents with assigned claims.
    If no agents have assignments (e.g., re-investigation with only
    InfoRequests), routes directly to judge_evidence.
    """
    active_agents = set()
    for assignment in state.routing_plan:
        for agent in assignment.assigned_agents:
            node_name = AGENT_TO_NODE[agent]
            active_agents.add(node_name)

    if not active_agents:
        return ["judge_evidence"]

    return list(active_agents)
```

LangGraph's `Send` API is used for the fan-out pattern, enabling parallel execution of specialist agents that have claims assigned.

### 1.4 Conditional Edge Function: `should_continue_or_compile`

The `should_continue_or_compile` function implements the cyclic validation loop described in PRD Section 4.9:

```python
def should_continue_or_compile(state: SibylState) -> str:
    """Determine whether to cycle back for re-investigation or compile the report.

    Returns "orchestrate" if:
      - There are pending reinvestigation_requests AND
      - iteration_count < max_iterations

    Returns "compile_report" otherwise.
    """
    has_reinvestigation = len(state.reinvestigation_requests) > 0
    within_limit = state.iteration_count < state.max_iterations

    if has_reinvestigation and within_limit:
        return "orchestrate"
    return "compile_report"
```

### 1.5 Agent-to-Node Name Mapping

The system shall define a constant mapping between agent names (used in the state) and LangGraph node names:

```python
AGENT_TO_NODE: dict[str, str] = {
    "geography": "investigate_geography",
    "legal": "investigate_legal",
    "news_media": "investigate_news",
    "academic": "investigate_academic",
    "data_metrics": "investigate_data",
}

NODE_TO_AGENT: dict[str, str] = {v: k for k, v in AGENT_TO_NODE.items()}
```

### 1.6 Graph Compilation

The system shall provide a function to compile the graph with a checkpointer:

```python
async def get_compiled_graph(checkpointer: AsyncPostgresSaver | None = None):
    """Compile the graph with optional PostgreSQL checkpointing."""
    graph = build_graph()
    return graph.compile(checkpointer=checkpointer)
```

### 1.7 Compile Report Stub

The `compile_report` node is a stub in FRD 5 (fully implemented in FRD 13). The stub shall:

1. Read all verdicts, findings, and disclosure gaps from the state.
2. Persist verdicts and findings to the database (inserting into the `findings` and `verdicts` tables).
3. Set the report status to `"completed"`.
4. Emit a `StreamEvent` with `event_type = "pipeline_completed"`.
5. Return an empty partial state update.

---

## 2. Orchestrator Agent Implementation

### 2.1 Overview

The Orchestrator Agent (`app/agents/orchestrator_agent.py`) replaces the FRD 0 stub with a functional LangGraph node. It is the supervisory node that manages the downstream investigation flow as described in PRD Section 4.3.

### 2.2 Node Function

```python
async def orchestrate(state: SibylState) -> dict:
    """Orchestrator Agent: Route claims to specialist agents and manage pipeline.

    Reads: state.claims, state.routing_plan, state.agent_status,
           state.info_requests, state.reinvestigation_requests,
           state.iteration_count, state.findings
    Writes: state.routing_plan, state.agent_status, state.info_requests,
            state.events

    Responsibilities:
    1. On first invocation: Create a routing plan from extracted claims.
    2. On re-investigation: Update routing plan with Judge's refined queries.
    3. On each invocation: Process pending InfoRequests and route them.

    Returns:
        Partial state update with routing plan, agent status, and events.
    """
```

### 2.3 Orchestrator Modes

The Orchestrator operates in different modes depending on the pipeline state:

| Mode | Condition | Behavior |
|---|---|---|
| **Initial routing** | `iteration_count == 0` and `routing_plan` is empty | Create a full routing plan from all extracted claims |
| **Re-investigation** | `iteration_count > 0` and `reinvestigation_requests` is non-empty | Create targeted routing assignments from the Judge's re-investigation requests |
| **InfoRequest routing** | `info_requests` contains items with `status == "pending"` | Route pending information requests to appropriate specialist agents |

### 2.4 Model Configuration

| Parameter | Value | Rationale |
|---|---|---|
| Model | `anthropic/claude-sonnet-4-5` (`Models.CLAUDE_SONNET`) | Strong reasoning for complex routing decisions and coordination logic (PRD Section 4.3) |
| Temperature | `0.1` | Low temperature for deterministic, consistent routing decisions |
| Max output tokens | `8192` | Sufficient for routing plans covering up to 200 claims |
| Response format | JSON schema (structured output) | Ensures parseable routing plan output |

### 2.5 Processing Steps

The `orchestrate` node shall execute the following steps:

1. **Emit start event:** Append a `StreamEvent` with `event_type = "agent_started"`, `agent_name = "orchestrator"`.

2. **Determine mode:** Check `iteration_count` and `reinvestigation_requests` to determine the operating mode.

3. **Initial routing (mode: initial):**
   a. Construct the routing prompt with claim summaries, type distributions, and the agent capability matrix (see Appendix A).
   b. Call Claude Sonnet 4.5 via OpenRouter requesting structured JSON output.
   c. Parse the response into `RoutingAssignment` objects.
   d. Emit `StreamEvent` objects with `event_type = "claim_routed"` for each routing assignment.
   e. Initialize `AgentStatus` objects for all specialist agents that received assignments.

4. **Re-investigation routing (mode: re-investigation):**
   a. Increment `iteration_count`.
   b. Read `reinvestigation_requests` from the state.
   c. For each request, create a `RoutingAssignment` targeting the specified agents with the refined queries.
   d. Update `AgentStatus` objects for re-activated agents.
   e. Emit `StreamEvent` with `event_type = "reinvestigation"` including cycle number and targeted agents.
   f. Clear processed `reinvestigation_requests`.

5. **InfoRequest routing (on every invocation):**
   a. Scan `info_requests` for items with `status == "pending"`.
   b. For each pending request, determine the target agent(s) based on request content (using LLM-assisted analysis or rule-based heuristics).
   c. Update the `InfoRequest.status` to `"routed"` and set the routing metadata.
   d. Emit `StreamEvent` with `event_type = "agent_thinking"` describing the cross-domain routing.

6. **Emit completion event:** Append a `StreamEvent` with `event_type = "agent_completed"`, `agent_name = "orchestrator"`, including routing plan summary.

7. **Return partial state:** Return the updated `routing_plan`, `agent_status`, `info_requests`, `iteration_count`, and new `events`.

### 2.6 Agent Status Management

The Orchestrator maintains an `agent_status` dictionary tracking each specialist agent's state:

```python
# Initial status for all agents in the routing plan
agent_status = {
    "geography": AgentStatus(agent_name="geography", status="idle"),
    "legal": AgentStatus(agent_name="legal", status="idle"),
    "news_media": AgentStatus(agent_name="news_media", status="idle"),
    "academic": AgentStatus(agent_name="academic", status="idle"),
    "data_metrics": AgentStatus(agent_name="data_metrics", status="idle"),
}
```

Status transitions:

| Transition | Trigger |
|---|---|
| `idle` → `working` | Agent node begins execution (set by the agent node itself) |
| `working` → `completed` | Agent node finishes successfully (set by the agent node) |
| `working` → `error` | Agent node encounters an error (set by the agent node) |
| `completed` → `working` | Agent re-activated for re-investigation (set by the Orchestrator) |

### 2.7 Execution Timeout Management

The system shall implement timeout handling for specialist agents:

1. Define a per-agent timeout: `AGENT_TIMEOUT_SECONDS = 120` (2 minutes per agent per claim batch).
2. The graph compilation includes a `timeout` parameter on each specialist node (if supported by LangGraph v1.0).
3. If LangGraph does not support per-node timeouts natively, implement timeout tracking in the Orchestrator: record the start time of each agent invocation and check elapsed time on re-entry. If an agent has exceeded the timeout, mark its status as `"error"` with a timeout message, and the pipeline continues with available findings.

---

## 3. Routing Logic

### 3.1 Routing Strategy

The Orchestrator routes claims based on a combination of claim type (primary signal) and claim content (secondary signal). A single claim may be routed to multiple agents when it spans domains.

### 3.2 Default Routing Matrix

The following matrix defines the default claim-type-to-agent routing:

| Claim Type | Primary Agent(s) | Secondary Agent(s) | Routing Rationale |
|---|---|---|---|
| `geographic` | Geography | Legal | Geographic claims need satellite verification; Legal Agent checks IFRS S2.13 business model effects |
| `quantitative` | Data/Metrics | Legal | Quantitative claims need mathematical validation; Legal Agent checks S2.27-37 compliance |
| `legal_governance` | Legal | -- | Governance claims are primarily a Legal/IFRS compliance matter |
| `strategic` | Legal, Academic/Research | News/Media | Strategic claims need IFRS mapping (Legal) and benchmark validation (Academic); News for corroboration |
| `environmental` | Academic/Research | Geography, Data/Metrics | Environmental claims need research validation; may need satellite or quantitative checks |

### 3.3 Content-Based Routing Refinements

Beyond the default matrix, the Orchestrator uses LLM reasoning to refine routing:

1. **Cross-domain claims:** A geographic claim mentioning specific emission figures (e.g., "Our Borneo facility reduced emissions by 30%") is routed to both Geography and Data/Metrics.
2. **News-worthy claims:** Claims about controversial topics, large financial commitments, or public commitments are additionally routed to News/Media for public corroboration.
3. **SBTi and target claims:** Claims referencing Science Based Targets initiative, net-zero commitments, or specific reduction pathways are additionally routed to Academic/Research.
4. **Facility-specific claims:** Any claim mentioning a specific geographic location, facility, or site is additionally routed to Geography.

### 3.4 Routing Assignment Output Format

The Orchestrator produces `RoutingAssignment` objects (defined in FRD 0's `state.py`):

```python
class RoutingAssignment(BaseModel):
    claim_id: str
    assigned_agents: list[str]   # Agent names (e.g., ["geography", "data_metrics"])
    reasoning: str | None = None  # Why these agents were chosen
```

### 3.5 LLM Routing Response Schema

The system shall request structured output from Claude Sonnet 4.5:

```python
class RoutingDecision(BaseModel):
    """Routing decision for a single claim."""
    claim_id: str
    assigned_agents: list[str]
    reasoning: str
    priority_order: list[str]  # Agents in order of investigation priority

class RoutingPlanResult(BaseModel):
    """Complete routing plan from the Orchestrator."""
    assignments: list[RoutingDecision]
    routing_summary: str  # Brief summary of the routing strategy
    agent_workload: dict[str, int]  # Agent name → number of assigned claims
```

### 3.6 Claim Batching for Agents

To manage specialist agent invocations efficiently, the Orchestrator groups claims per agent:

1. After generating the routing plan, group all claims assigned to each agent.
2. Each specialist agent node receives its full batch of assigned claims at once (not one claim at a time).
3. This enables agents to process related claims together, identify patterns, and reduce redundant tool calls (e.g., a single satellite imagery query for multiple geographic claims in the same area).

---

## 4. Inter-Agent Communication Protocol

### 4.1 Overview

The inter-agent communication protocol implements PRD Section 5.4. Specialist agents never communicate directly -- all cross-domain requests flow through the shared state, mediated by the Orchestrator.

### 4.2 InfoRequest Flow

```
1. Agent A posts InfoRequest to state.info_requests (status = "pending")
2. Agent A completes its current execution
3. Orchestrator runs (next cycle or re-invocation)
4. Orchestrator detects pending InfoRequest
5. Orchestrator determines target agent(s) based on request content
6. Orchestrator sets InfoRequest.status = "routed"
7. Target Agent B runs, detects routed InfoRequest addressed to it
8. Agent B processes the request and posts InfoResponse to state.info_responses
9. Agent A accesses the InfoResponse on its next execution (if re-invoked)
```

### 4.3 InfoRequest Routing Logic

The Orchestrator routes InfoRequests using a combination of:

1. **Content analysis:** Parse the request description for domain keywords (e.g., "satellite", "emissions data", "regulatory filing").
2. **Agent capability matching:** Match the request content against agent capabilities:

| Keywords / Content Patterns | Target Agent |
|---|---|
| Location, coordinates, satellite, imagery, land use, facility site | Geography |
| IFRS, S1, S2, compliance, paragraph, regulation, governance | Legal |
| News, media, public reporting, press, controversy, journalist | News/Media |
| Research, academic, benchmark, SBTi, methodology, peer-reviewed | Academic/Research |
| Numbers, calculation, emissions data, Scope, metrics, consistency | Data/Metrics |

3. **Fallback:** If content analysis is ambiguous, use a lightweight LLM call to classify the request.

### 4.4 InfoRequest Visibility

All InfoRequests and InfoResponses are emitted as `StreamEvent` objects:

| Event Type | Data | When |
|---|---|---|
| `info_request_posted` | `{requesting_agent, description}` | Agent posts a request |
| `info_request_routed` | `{requesting_agent, target_agents, description}` | Orchestrator routes the request |
| `info_response_posted` | `{requesting_agent, responding_agent, summary}` | Target agent responds |

These events are displayed in the detective dashboard (FRD 12) as inter-agent communication edges flowing through the Orchestrator node.

### 4.5 InfoRequest in Stubs

For FRD 5, specialist agent stubs do not generate InfoRequests. The protocol is fully implemented in the Orchestrator and ready to be consumed once specialist agents are implemented in FRDs 6-10. The Orchestrator's InfoRequest routing logic is testable via manually injected InfoRequest objects in the state.

---

## 5. Re-Investigation Handling

### 5.1 Overview

Re-investigation implements the cyclic validation loop from PRD Section 4.9. When the Judge Agent determines that evidence is insufficient, contradictory, or incomplete, it posts `ReinvestigationRequest` objects to the shared state. The conditional edge routes back to the Orchestrator, which re-routes refined queries to the specified specialist agents.

### 5.2 ReinvestigationRequest Processing

When the Orchestrator runs in re-investigation mode:

1. **Read requests:** Load all `ReinvestigationRequest` objects from the state.
2. **Create targeted assignments:** For each request:
   - Map `target_agents` to node names.
   - Create a `RoutingAssignment` with the specified agents.
   - Attach the `evidence_gap`, `refined_queries`, and `required_evidence` as metadata on the assignment.
3. **Augment routing context:** The specialist agent stubs (and future implementations) receive the re-investigation context, enabling them to focus their investigation on the specific gaps identified by the Judge.
4. **Increment cycle count:** Set `iteration_count += 1`.
5. **Clear processed requests:** Remove processed `ReinvestigationRequest` objects from the state.

### 5.3 Iteration Control

The system enforces the maximum iteration limit defined in `SibylState.max_iterations` (default: 3, configurable via `settings.MAX_JUDGE_ITERATIONS`):

1. The `should_continue_or_compile` conditional edge checks `iteration_count < max_iterations`.
2. If the limit is reached and there are still unresolved claims, the Judge issues final verdicts of `"insufficient_evidence"` for those claims.
3. The iteration count is included in `StreamEvent` data for the frontend to display the current cycle number.

### 5.4 Re-Investigation State Schema Extension

The system shall add a `reinvestigation_context` field to support passing Judge guidance to specialist agents:

```python
class ReinvestigationContext(BaseModel):
    """Context from the Judge for a re-investigation pass."""
    claim_id: str
    evidence_gap: str
    refined_queries: list[str]
    required_evidence: str | None = None
    cycle_number: int
```

This is stored as supplementary metadata on the `RoutingAssignment` and accessible to specialist agents during re-investigation.

---

## 6. Specialist Agent Stubs

### 6.1 Overview

FRD 5 replaces the FRD 0 agent stubs with functional stubs that integrate with the compiled graph. Each stub accepts routed claims from the Orchestrator, emits appropriate `StreamEvent` objects, and returns placeholder findings. This enables end-to-end pipeline execution and SSE streaming testing before the specialist agents are fully implemented (FRDs 6-10).

### 6.2 Stub Template

All specialist agent stubs shall follow this template:

```python
async def investigate_{agent}(state: SibylState) -> dict:
    """Specialist Agent stub: {Agent Name}.

    Accepts routed claims and returns placeholder findings.
    Full implementation in FRD {N}.
    """
    agent_name = "{agent}"
    events = []

    # Emit start event
    events.append(StreamEvent(
        event_type="agent_started",
        agent_name=agent_name,
        data={},
        timestamp=datetime.utcnow().isoformat()
    ))

    # Find claims assigned to this agent
    assigned_claims = [
        a for a in state.routing_plan
        if agent_name in a.assigned_agents
    ]

    # Update agent status
    agent_status = state.agent_status.copy()
    agent_status[agent_name] = AgentStatus(
        agent_name=agent_name,
        status="working",
        claims_assigned=len(assigned_claims),
        claims_completed=0,
    )

    # Emit thinking event
    events.append(StreamEvent(
        event_type="agent_thinking",
        agent_name=agent_name,
        data={"message": f"Processing {len(assigned_claims)} assigned claims... (stub -- full implementation in FRD {N})"},
        timestamp=datetime.utcnow().isoformat()
    ))

    # Generate placeholder findings
    findings = []
    for assignment in assigned_claims:
        finding = AgentFinding(
            finding_id=str(generate_uuid7()),
            agent_name=agent_name,
            claim_id=assignment.claim_id,
            evidence_type="placeholder",
            summary=f"Placeholder finding from {agent_name} agent (stub). Full investigation in FRD {N}.",
            details={"stub": True},
            supports_claim=None,
            confidence=None,
            iteration=state.iteration_count + 1,
        )
        findings.append(finding)

    # Update agent status to completed
    agent_status[agent_name] = AgentStatus(
        agent_name=agent_name,
        status="completed",
        claims_assigned=len(assigned_claims),
        claims_completed=len(assigned_claims),
    )

    # Emit completion event
    events.append(StreamEvent(
        event_type="agent_completed",
        agent_name=agent_name,
        data={"claims_processed": len(assigned_claims), "findings_count": len(findings)},
        timestamp=datetime.utcnow().isoformat()
    ))

    return {
        "findings": state.findings + findings,
        "agent_status": agent_status,
        "events": state.events + events,
    }
```

### 6.3 Stub-Specific Details

| Agent | Node Name | Stub FRD | Full FRD |
|---|---|---|---|
| Geography | `investigate_geography` | FRD 5 | FRD 10 |
| Legal | `investigate_legal` | FRD 5 | FRD 6 |
| News/Media | `investigate_news` | FRD 5 | FRD 8 |
| Academic/Research | `investigate_academic` | FRD 5 | FRD 9 |
| Data/Metrics | `investigate_data` | FRD 5 | FRD 7 |

### 6.4 Judge Agent Stub

The Judge Agent stub (`judge_evidence`) is a special stub that implements the verdict/re-investigation decision logic. For FRD 5:

1. Receive all findings from specialist agents.
2. For each claim, produce a placeholder verdict of `"unverified"` with reasoning: "Stub verdict -- specialist agents not yet implemented. Full evaluation in FRD 11."
3. Do NOT generate reinvestigation requests (to avoid infinite loops with stub agents).
4. Set `iteration_count += 1` in the returned state.
5. Emit `StreamEvent` objects for each placeholder verdict.
6. The stub returns verdicts that flow to `compile_report` via the conditional edge (since no reinvestigation requests are generated, `should_continue_or_compile` returns `"compile_report"`).

---

## 7. SSE Streaming Infrastructure

### 7.1 Overview

The SSE streaming infrastructure delivers real-time pipeline events from the LangGraph backend to the React frontend. It consists of three components: a LangGraph callback handler that captures events during node execution, a FastAPI SSE endpoint that streams events to connected clients, and a frontend SSE client that processes and displays the events.

### 7.2 LangGraph Callback Handler

The system shall implement a custom callback handler that intercepts LangGraph node execution events:

```python
# app/agents/callbacks.py

class SSECallbackHandler:
    """Captures StreamEvents from LangGraph node execution and
    forwards them to connected SSE clients.

    Events are placed into an asyncio.Queue that the SSE endpoint
    reads from.
    """

    def __init__(self, event_queue: asyncio.Queue):
        self.event_queue = event_queue

    async def on_node_start(self, node_name: str, state: SibylState):
        """Called when a node begins execution."""
        # Events emitted by the node itself via state.events are the primary
        # mechanism. This handler captures them after each node completes.

    async def on_node_end(self, node_name: str, state: SibylState):
        """Called when a node completes execution.

        Extracts any new StreamEvents added to state.events since the
        last check and pushes them to the event queue.
        """
        new_events = self._extract_new_events(state)
        for event in new_events:
            await self.event_queue.put(event)

    async def on_error(self, node_name: str, error: Exception):
        """Called when a node encounters an error."""
        event = StreamEvent(
            event_type="error",
            agent_name=NODE_TO_AGENT.get(node_name, node_name),
            data={"message": str(error), "node": node_name},
            timestamp=datetime.utcnow().isoformat()
        )
        await self.event_queue.put(event)
```

### 7.3 Event Queue Architecture

The system uses an `asyncio.Queue` to decouple event production (LangGraph execution) from event consumption (SSE endpoint):

1. Each pipeline execution creates a new `asyncio.Queue`.
2. The callback handler pushes events to the queue as nodes execute.
3. The SSE endpoint reads from the queue and yields events to connected clients.
4. A sentinel value (`None`) is pushed to the queue when the pipeline completes or errors, signaling the SSE endpoint to close the connection.

### 7.4 FastAPI SSE Endpoint

The stream route (`app/api/routes/stream.py`) replaces the FRD 0 stub:

```
GET /api/v1/stream/{reportId}

Headers:
  Content-Type: text/event-stream
  Cache-Control: no-cache
  Connection: keep-alive

Response: SSE stream

Event format:
  event: {event_type}
  data: {JSON payload}
  id: {sequential event ID}

Example events:
  event: agent_started
  data: {"agent_name": "orchestrator", "timestamp": "2026-02-09T15:30:00Z"}
  id: 1

  event: agent_thinking
  data: {"agent_name": "orchestrator", "message": "Analyzing 87 claims for routing...", "timestamp": "2026-02-09T15:30:01Z"}
  id: 2

  event: claim_routed
  data: {"claim_id": "uuid-...", "assigned_agents": ["geography", "data_metrics"], "reasoning": "...", "timestamp": "2026-02-09T15:30:02Z"}
  id: 3

  event: pipeline_completed
  data: {"total_claims": 87, "total_findings": 42, "total_verdicts": 87, "timestamp": "2026-02-09T15:35:00Z"}
  id: 156
```

### 7.5 SSE Endpoint Implementation

```python
# app/api/routes/stream.py

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/stream", tags=["Streaming"])

@router.get("/{report_id}")
async def stream_analysis(report_id: str, db: AsyncSession = Depends(get_db)):
    """Stream real-time analysis events via Server-Sent Events.

    The client connects to this endpoint and receives events as the
    LangGraph pipeline executes. The connection remains open until
    the pipeline completes or errors.
    """
    # Verify the report exists and is in "analyzing" state
    report = await get_report_or_404(report_id, db)

    # Get or create the event queue for this report
    event_queue = get_event_queue(report_id)

    async def event_generator():
        event_id = 0
        try:
            while True:
                event = await asyncio.wait_for(
                    event_queue.get(), timeout=30.0
                )
                if event is None:  # Sentinel: pipeline complete
                    break

                event_id += 1
                yield format_sse_event(event, event_id)
        except asyncio.TimeoutError:
            # Send keepalive comment to prevent connection timeout
            yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
```

### 7.6 SSE Event Formatting

```python
def format_sse_event(event: StreamEvent, event_id: int) -> str:
    """Format a StreamEvent as an SSE message."""
    data = event.model_dump_json()
    lines = [
        f"event: {event.event_type}",
        f"data: {data}",
        f"id: {event_id}",
        "",
        "",  # Double newline terminates the event
    ]
    return "\n".join(lines)
```

### 7.7 Event Queue Registry

The system shall maintain a registry of active event queues, keyed by report ID:

```python
# app/agents/event_registry.py

_event_queues: dict[str, asyncio.Queue] = {}

def get_event_queue(report_id: str) -> asyncio.Queue:
    """Get or create an event queue for a report's pipeline execution."""
    if report_id not in _event_queues:
        _event_queues[report_id] = asyncio.Queue()
    return _event_queues[report_id]

def remove_event_queue(report_id: str):
    """Remove an event queue after pipeline completion."""
    _event_queues.pop(report_id, None)
```

### 7.8 Keepalive and Reconnection

1. The SSE endpoint sends a keepalive comment (`: keepalive\n\n`) every 30 seconds if no events are emitted. This prevents proxy/load balancer timeouts.
2. Each event includes a sequential `id` field. If the client reconnects (via the `Last-Event-ID` header), the endpoint can resume from the last received event. For MVP, reconnection replays all events from the queue (events are not persisted). The LangGraph checkpointer provides state recovery for the pipeline itself.

---

## 8. LangGraph PostgreSQL Checkpointing

### 8.1 Overview

LangGraph checkpointing persists the pipeline state to PostgreSQL after each node execution, enabling fault tolerance (resume after crash), debugging (inspect state at any point), and replay (step through a completed analysis).

### 8.2 Checkpointer Configuration

The system shall configure the `AsyncPostgresSaver` checkpointer:

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async def get_checkpointer() -> AsyncPostgresSaver:
    """Create a PostgreSQL-backed checkpointer for LangGraph."""
    checkpointer = AsyncPostgresSaver.from_conn_string(
        settings.DATABASE_URL
    )
    await checkpointer.setup()  # Creates checkpoint tables if not exist
    return checkpointer
```

### 8.3 Checkpoint Tables

LangGraph's `AsyncPostgresSaver` automatically creates its own tables in PostgreSQL for storing checkpoint data. These tables are managed by LangGraph and do not require Alembic migrations. The `setup()` call creates them idempotently on first use.

### 8.4 Thread ID Convention

Each pipeline execution is identified by a unique thread ID. The system shall use the `report_id` as the thread ID:

```python
config = {
    "configurable": {
        "thread_id": report_id,
    }
}
result = await compiled_graph.ainvoke(initial_state, config=config)
```

This enables:
- Multiple concurrent pipeline executions (different reports, different thread IDs).
- Querying checkpoint state by report ID for debugging.
- Pipeline resumption using the report ID as the resume key.

### 8.5 Pipeline Resumption

If the pipeline crashes (backend restart, OOM, etc.):

1. On backend restart, check for reports with `status = "analyzing"`.
2. For each, check whether a checkpoint exists for that `report_id` thread.
3. If a checkpoint exists, resume the pipeline from the last checkpoint using `compiled_graph.ainvoke(None, config=config)` (passing `None` as input to resume from checkpoint).
4. If no checkpoint exists, re-run the pipeline from scratch.

Pipeline resumption is not automatic in FRD 5 -- it requires manual triggering via the retry mechanism. Automatic resumption is a post-MVP enhancement.

### 8.6 Dependencies

The system shall add `langgraph-checkpoint-postgres` to `requirements.txt`:

```
langgraph-checkpoint-postgres
```

---

## 9. Pipeline Execution and Task Integration

### 9.1 Overview

FRD 5 transitions the analysis flow from FRD 3's standalone `run_claims_extraction` wrapper to a full LangGraph pipeline execution. The background task worker is updated to invoke the compiled graph instead of calling the Claims Agent directly.

### 9.2 Pipeline Runner

The system shall implement a pipeline runner that manages graph execution:

```python
# app/agents/pipeline.py

async def run_pipeline(report_id: str, db: AsyncSession):
    """Execute the full Sibyl analysis pipeline for a report.

    1. Load the report and its parsed content from the database.
    2. Create the initial SibylState.
    3. Set up the event queue and callback handler.
    4. Compile the graph with checkpointing.
    5. Invoke the graph.
    6. Handle completion or error.
    """
    # Load report
    report = await load_report(report_id, db)

    # Create initial state
    initial_state = SibylState(
        report_id=report_id,
        document_content=report.parsed_content,
        document_chunks=[],  # Populated by extract_claims if needed
        max_iterations=settings.MAX_JUDGE_ITERATIONS,
    )

    # Set up SSE streaming
    event_queue = get_event_queue(report_id)
    callback_handler = SSECallbackHandler(event_queue)

    # Compile graph with checkpointer
    checkpointer = await get_checkpointer()
    compiled_graph = await get_compiled_graph(checkpointer=checkpointer)

    # Execute
    config = {
        "configurable": {"thread_id": report_id},
        "callbacks": [callback_handler],
    }

    try:
        result = await compiled_graph.ainvoke(initial_state, config=config)
        # Pipeline completed successfully
        await event_queue.put(None)  # Sentinel
    except Exception as e:
        # Pipeline failed
        error_event = StreamEvent(
            event_type="error",
            agent_name=None,
            data={"message": str(e)},
            timestamp=datetime.utcnow().isoformat()
        )
        await event_queue.put(error_event)
        await event_queue.put(None)  # Sentinel
        raise
    finally:
        remove_event_queue(report_id)
```

### 9.3 Task Worker Updates

The background task worker (`app/services/task_worker.py`) shall be updated:

1. **New queue key:** `sibyl:tasks:run_pipeline` replaces `sibyl:tasks:extract_claims`.
2. **Pipeline execution:** When a pipeline task is dequeued, call `run_pipeline(report_id, db)` instead of `run_claims_extraction`.
3. **Status management:** The pipeline runner (not the task worker) manages status transitions. The worker sets `status = "analyzing"` before invoking the runner and `status = "error"` if the runner raises an exception.
4. **Backward compatibility:** The `sibyl:tasks:extract_claims` queue is deprecated. The `POST /api/v1/analysis/{reportId}/start` endpoint now enqueues to `sibyl:tasks:run_pipeline`.

### 9.4 Claims Agent Integration

The `extract_claims` node is the first node in the pipeline. In FRD 3, it was invoked standalone. In FRD 5, it runs as part of the full graph. The node function itself does not change -- it reads `document_content` from the state and writes `claims` to the state, exactly as before. The key differences:

1. Claims are no longer persisted by the Claims Agent directly. Instead, claims are stored in the state and persisted by the `compile_report` node at the end of the pipeline (or during intermediate checkpoints).
2. The standalone `run_claims_extraction` wrapper remains available for testing but is no longer used by the task worker.

**Note:** For FRD 5, the Claims Agent's claim persistence behavior from FRD 3 is preserved (it writes to the database during execution) to ensure claims are immediately available for the frontend claims list and PDF highlights. The `compile_report` node handles persistence of findings and verdicts.

---

## 10. Backend Endpoints

### 10.1 Start Analysis Endpoint Updates

The `POST /api/v1/analysis/{reportId}/start` endpoint (FRD 3) is updated:

1. Enqueue to `sibyl:tasks:run_pipeline` instead of `sibyl:tasks:extract_claims`.
2. Accept an optional `skip_claims_extraction: bool = false` query parameter. If `true` and claims already exist for the report, the pipeline starts from the `orchestrate` node (useful for re-running routing/investigation without re-extracting claims).
3. The status transition remains `parsed` → `analyzing`.

### 10.2 Analysis Status Endpoint Updates

The `GET /api/v1/analysis/{reportId}/status` endpoint (FRD 3) is extended:

```
GET /api/v1/analysis/{reportId}/status

Response 200:
{
  "report_id": "uuid-...",
  "status": "analyzing",
  "claims_count": 87,
  "claims_by_type": { ... },
  "claims_by_priority": { ... },
  "pipeline_stage": "investigating",
  "active_agents": ["legal", "data_metrics"],
  "iteration_count": 1,
  "findings_count": 42,
  "verdicts_count": 0,
  "error_message": null,
  "updated_at": "2026-02-09T15:32:00Z"
}
```

New fields:

| Field | Type | Description |
|---|---|---|
| `pipeline_stage` | `string` | Current pipeline stage: `"extracting_claims"`, `"routing"`, `"investigating"`, `"judging"`, `"compiling"`, `"completed"` |
| `active_agents` | `list[string]` | Agent names currently executing |
| `iteration_count` | `int` | Current investigation cycle (0 = first pass) |
| `findings_count` | `int` | Total findings produced so far |
| `verdicts_count` | `int` | Total verdicts issued so far |

### 10.3 SSE Stream Endpoint

The `GET /api/v1/stream/{reportId}` endpoint is new in FRD 5 (see Section 7.4-7.5 for full specification).

### 10.4 Pipeline Events Endpoint (Replay)

```
GET /api/v1/analysis/{reportId}/events

Query Parameters:
  - after_id: int (optional) -- return events after this event ID

Response 200:
{
  "events": [
    {
      "event_id": 1,
      "event_type": "agent_started",
      "agent_name": "claims",
      "data": {},
      "timestamp": "2026-02-09T15:30:00Z"
    },
    ...
  ],
  "total": 156,
  "pipeline_complete": true
}
```

This endpoint allows the frontend to fetch historical events for a completed pipeline (for replay/review) or catch up on missed events after a reconnection. Events are stored in the pipeline state (via checkpointing) and can be retrieved after pipeline completion.

### 10.5 Route Registration

The stream router shall be registered in the root API router alongside existing routers. The analysis router retains its existing registration and gains the new fields on the status endpoint.

---

## 11. Frontend Agent Reasoning Panel

### 11.1 Overview

The Analysis Page's right panel (FRD 4: "Claims & Reasoning") is enhanced with a real-time agent reasoning stream. The panel transitions from displaying only the claims list (FRD 3/4) to a tabbed interface showing both agent reasoning (live) and the claims list.

### 11.2 Panel Structure

The right panel shall contain two top-level tabs:

| Tab | Label | Content |
|---|---|---|
| **Reasoning** | "Agent Activity" | Real-time SSE-driven reasoning stream with per-agent sub-tabs |
| **Claims** | "Claims ({count})" | The existing claims list from FRD 3, unchanged |

The "Agent Activity" tab is selected by default when the pipeline is running. The "Claims" tab is selected by default when the pipeline is complete.

### 11.3 Agent Reasoning Stream Component

```typescript
// src/components/Analysis/AgentReasoningPanel.tsx

interface AgentReasoningPanelProps {
  reportId: string;
  isAnalyzing: boolean;
}
```

The `AgentReasoningPanel` component shall:

1. **Connect to SSE:** Establish an `EventSource` connection to `GET /api/v1/stream/{reportId}` when `isAnalyzing` is true.
2. **Process events:** Parse incoming SSE events and route them to the appropriate agent tab.
3. **Display reasoning:** Render agent thoughts as a scrollable, time-ordered list of messages.
4. **Auto-scroll:** Automatically scroll to the latest message as new events arrive (with a "scroll to bottom" button if the user has scrolled up).

### 11.4 Agent Tabs

Below the top-level tab bar, the Agent Activity view contains sub-tabs -- one per agent:

| Tab Label | Agent Name | Color (from FRD 0 design system) |
|---|---|---|
| "Claims" | `claims` | Slate blue |
| "Orchestrator" | `orchestrator` | White/silver |
| "Geography" | `geography` | Forest green |
| "Legal" | `legal` | Deep purple |
| "News/Media" | `news_media` | Amber/gold |
| "Academic" | `academic` | Teal |
| "Data/Metrics" | `data_metrics` | Coral/orange |
| "Judge" | `judge` | Crimson red |

**Tab behavior:**

1. Tabs appear dynamically as agents are activated (initially only "Claims" and "Orchestrator" are visible; specialist tabs appear when the Orchestrator routes claims to them).
2. The active agent's tab shows a pulsing dot indicator (using the agent's color).
3. A completed agent's tab shows a checkmark icon.
4. An errored agent's tab shows a warning icon.
5. Clicking a tab shows that agent's reasoning history.
6. An "All" tab (first position) shows a unified timeline of all agents' events, interleaved chronologically.

### 11.5 Reasoning Message Component

```typescript
// src/components/Analysis/ReasoningMessage.tsx

interface ReasoningMessageProps {
  event: StreamEvent;
}
```

Each reasoning message displays:

1. **Timestamp:** Relative time ("2s ago", "1m ago") or absolute time, shown in muted text.
2. **Agent badge:** Small colored dot and agent name.
3. **Message text:** The reasoning content from the `StreamEvent.data.message` field.
4. **Event-specific content:**
   - `agent_started`: "Started processing..."
   - `agent_thinking`: The thinking message text
   - `claim_routed`: "Routed claim to {agents}: {reasoning}"
   - `evidence_found`: "Found evidence: {summary}"
   - `verdict_issued`: "Verdict for claim: {verdict}" with color-coded badge
   - `reinvestigation`: "Requesting re-investigation (cycle {N}): {gap}"
   - `agent_completed`: "Completed. {claims_processed} claims, {findings_count} findings."
   - `error`: Error message in red text
   - `pipeline_completed`: "Analysis complete. {totals}"

### 11.6 SSE Hook (`src/hooks/useSSE.ts`)

The system shall implement the `useSSE` hook:

```typescript
// src/hooks/useSSE.ts

interface UseSSEReturn {
  events: StreamEvent[];
  eventsByAgent: Record<string, StreamEvent[]>;
  isConnected: boolean;
  error: string | null;
  activeAgents: string[];
  completedAgents: string[];
  erroredAgents: string[];
}

function useSSE(reportId: string, enabled: boolean): UseSSEReturn;
```

**Implementation requirements:**

1. Create an `EventSource` connection to `${API_BASE_URL}/stream/${reportId}` when `enabled` is true.
2. Parse incoming events and store them in state, grouped by agent name.
3. Track connection status (connected, disconnected, error).
4. Handle reconnection: `EventSource` automatically reconnects on connection loss. Use the `Last-Event-ID` header for event resumption.
5. Close the connection when `enabled` becomes false or the component unmounts.
6. Provide `activeAgents`, `completedAgents`, and `erroredAgents` computed from the event stream.

### 11.7 SSE Client Service (`src/services/sse.ts`)

The system shall implement the SSE client service:

```typescript
// src/services/sse.ts

interface StreamEvent {
  event_type: string;
  agent_name: string | null;
  data: Record<string, unknown>;
  timestamp: string;
}

function createSSEConnection(
  reportId: string,
  onEvent: (event: StreamEvent) => void,
  onError: (error: Event) => void,
  onOpen: () => void,
): EventSource;
```

### 11.8 Analysis Page Integration

The `AnalysisPage` shall be updated:

1. Connect the `useSSE` hook when the report status is `"analyzing"`.
2. Pass SSE events to the `AgentReasoningPanel` in the right panel.
3. The right panel switches from the current single claims list to a tabbed view:
   - During analysis: "Agent Activity" tab (default) + "Claims" tab
   - After completion: "Claims" tab (default) + "Agent Activity" tab (for review)
4. The center panel placeholder ("Detective Dashboard -- coming in FRD 12") remains unchanged. The SSE events will drive the dashboard in FRD 12.

---

## 12. Analysis Status Updates

### 12.1 Pipeline Stage Tracking

The system shall track the current pipeline stage and make it available via the status endpoint. Pipeline stage is derived from the most recent `StreamEvent`:

| Event | Pipeline Stage |
|---|---|
| `agent_started` with `agent_name = "claims"` | `extracting_claims` |
| `agent_started` with `agent_name = "orchestrator"` | `routing` |
| `agent_started` with any specialist agent | `investigating` |
| `agent_started` with `agent_name = "judge"` | `judging` |
| `pipeline_completed` | `completed` |
| `error` (terminal) | `error` |

### 12.2 Status Endpoint Behavior Change

In FRD 3, the status endpoint returned `claims_count` and `claims_by_type` by querying the database. In FRD 5, the endpoint is extended:

1. Continue returning claim data from the database (unchanged).
2. Add `pipeline_stage`, `active_agents`, `iteration_count`, `findings_count`, and `verdicts_count` by querying the database (counts from the `findings` and `verdicts` tables) and the pipeline state.
3. The `pipeline_stage` can be derived from the latest event in the checkpoint or from the report's related entities (if claims exist but no findings → `"routing"` or `"investigating"`).

### 12.3 Report Status Values

FRD 5 uses the existing report status values defined in FRD 0:

| Status | Meaning in FRD 5 |
|---|---|
| `parsed` | Report parsed, ready for full pipeline |
| `analyzing` | Full pipeline is running (claims → routing → investigation → judging) |
| `completed` | Full pipeline complete, all verdicts issued, report compiled |
| `error` | Pipeline failed at some stage |

The `analyzing` status now covers the entire pipeline (not just claims extraction as in FRD 3). FRD 3's behavior of setting `completed` after claims extraction is superseded -- the report remains `analyzing` until the full pipeline completes.

---

## 13. Error Handling

### 13.1 Pipeline-Level Errors

| Error | Trigger | Handling |
|---|---|---|
| Graph compilation failure | Invalid graph topology, missing nodes | Log the error; set report status to `"error"` with message "Pipeline configuration error" |
| Checkpointer connection failure | PostgreSQL unreachable for checkpointing | Fall back to in-memory execution without checkpointing; log a warning |
| Pipeline timeout | Entire pipeline exceeds 10 minutes | Kill the pipeline execution; set report status to `"error"` with timeout message |

### 13.2 Orchestrator Errors

| Error | Trigger | Handling |
|---|---|---|
| LLM routing failure | Claude Sonnet 4.5 returns non-JSON or fails after retries | Use fallback rule-based routing (default routing matrix from Section 3.2); log the error |
| Empty routing plan | LLM returns no routing assignments | Apply default routing for all claims based on claim type; log a warning |
| Invalid agent names in routing | LLM returns agent names not in the agent registry | Filter out invalid agents; route only to valid agents; log invalid entries |

### 13.3 Specialist Agent Errors

| Error | Trigger | Handling |
|---|---|---|
| Agent node exception | Any unhandled exception in a specialist agent | Catch at the node level; set agent status to `"error"`; emit error `StreamEvent`; return empty findings for that agent; the pipeline continues with other agents |
| Agent timeout | Specialist agent exceeds 120 seconds | Mark agent status as `"error"` with timeout message; pipeline continues |

### 13.4 SSE Streaming Errors

| Error | Trigger | Handling |
|---|---|---|
| Client disconnect | Frontend navigates away or loses connection | The SSE generator detects `CancelledError`; the pipeline continues executing (not tied to the SSE connection) |
| No active pipeline for report | Client connects to SSE for a report that is not analyzing | Return historical events if available (from checkpoint); close with a completion event if the pipeline is already done |
| Event queue overflow | Events are produced faster than consumed | Set a max queue size of 1000 events; drop oldest events on overflow; log a warning |

### 13.5 Graceful Agent Degradation

As specified in PRD Section 8: if any individual specialist agent fails, the pipeline continues with the remaining agents. The Judge evaluates whatever evidence is available and notes the missing agent in its assessment. The system shall:

1. Wrap each specialist node call in try/except within the graph execution.
2. On failure, emit an error `StreamEvent` and set the agent's status to `"error"`.
3. The Judge receives the `agent_status` dictionary and knows which agents completed vs. errored.
4. The Source of Truth report (FRD 13) includes a note on claims where an investigating agent failed.

---

## 14. Exit Criteria

FRD 5 is complete when ALL of the following are satisfied:

| # | Criterion | Verification |
|---|---|---|
| 1 | LangGraph StateGraph compiles without errors | Call `get_compiled_graph()` and verify it returns a compiled graph object |
| 2 | Full pipeline executes end-to-end | Start analysis on a report with extracted claims; verify the pipeline runs through all nodes: extract_claims → orchestrate → specialist stubs → judge stub → compile_report |
| 3 | Orchestrator creates a routing plan | After pipeline execution, inspect the state; verify `routing_plan` contains assignments mapping claims to agents |
| 4 | Routing follows the default matrix | Verify geographic claims are routed to Geography, quantitative to Data/Metrics, etc. |
| 5 | Cross-domain claims are routed to multiple agents | Verify claims spanning domains are assigned to multiple specialist agents |
| 6 | Specialist stubs execute and return placeholder findings | Verify each activated stub runs, emits events, and returns findings with `stub: true` |
| 7 | Judge stub produces placeholder verdicts | Verify the Judge stub returns `"unverified"` verdicts for all claims |
| 8 | Conditional edge from Judge works | With stub agents (no reinvestigation requests), verify the edge routes to `compile_report` |
| 9 | SSE endpoint streams events | Connect to `GET /api/v1/stream/{reportId}` during analysis; verify events arrive in real time |
| 10 | SSE events include all expected types | Verify the stream contains: `agent_started`, `agent_thinking`, `claim_routed`, `agent_completed`, `pipeline_completed` |
| 11 | Frontend receives and displays SSE events | Navigate to the Analysis Page during analysis; verify the right panel shows real-time reasoning text |
| 12 | Agent tabs work | Verify agent sub-tabs appear as agents activate; clicking a tab shows that agent's reasoning |
| 13 | Active agent indicator works | Verify the currently executing agent's tab shows a pulsing indicator |
| 14 | Completed agents show checkmarks | After an agent finishes, verify its tab shows a checkmark |
| 15 | Report status transitions correctly | Verify the report status goes from `"analyzing"` to `"completed"` after pipeline execution |
| 16 | Pipeline stage is reported in status endpoint | Call `GET /api/v1/analysis/{reportId}/status` during execution; verify `pipeline_stage` reflects the current stage |
| 17 | LangGraph checkpointing is configured | Verify checkpoint tables exist in PostgreSQL after pipeline execution |
| 18 | Checkpointed state is queryable | After pipeline completion, verify the checkpoint for the report's thread ID contains the full final state |
| 19 | Agent error does not crash the pipeline | Inject an error in one specialist stub; verify the pipeline continues with other agents and completes |
| 20 | SSE keepalive prevents timeout | Leave an SSE connection open for >30 seconds during a slow pipeline; verify keepalive comments are sent |
| 21 | Pipeline executes in reasonable time | Verify the full pipeline (with stubs) completes in under 2 minutes for a report with 100 claims |
| 22 | Existing FRD 3/4 functionality preserved | Verify claims list, PDF viewer, and highlights still work after the pipeline infrastructure changes |

---

## Appendix A: Orchestrator Routing Prompt

### A.1 System Prompt

```
You are the Orchestrator Agent in Sibyl, an AI system that verifies sustainability reports against IFRS S1/S2 disclosure standards. Your task is to create a routing plan that assigns extracted claims to the appropriate specialist investigation agents.

## Available Specialist Agents

1. **Geography Agent** (agent name: "geography")
   Capabilities: Satellite imagery analysis (Microsoft Planetary Computer), NDVI vegetation change detection, land cover classification, temporal comparison, geocoding
   Handles: Facility locations, land use assertions, deforestation/reforestation claims, water usage in specific regions, geographic concentration of climate risks, physical risk exposure at specific sites

2. **Legal Agent** (agent name: "legal")
   Capabilities: IFRS S1/S2 compliance mapping (RAG retrieval), SASB standards matching, regulatory analysis, disclosure gap detection
   Handles: Governance structures (S1.26-27, S2.5-7), risk management (S1.38-42, S2.24-26), strategy/transition plans (S2.14), metrics compliance (S2.27-37), general compliance assertions

3. **News/Media Agent** (agent name: "news_media")
   Capabilities: Web search, source credibility tiering (Tier 1-4), contradiction detection, historical coverage analysis
   Handles: Public corroboration/contradiction of claims, company-specific news, industry incidents, whistleblower reports, executive statements

4. **Academic/Research Agent** (agent name: "academic")
   Capabilities: Academic paper search, benchmark comparison, methodology validation, SBTi framework assessment
   Handles: Emissions methodology validation, renewable energy certification, carbon offset legitimacy, science-based target alignment, industry benchmark comparison

5. **Data/Metrics Agent** (agent name: "data_metrics")
   Capabilities: Mathematical consistency checks, unit validation, benchmark plausibility, target achievability analysis, historical consistency
   Handles: Scope 1/2/3 emissions figures, percentage calculations, year-over-year comparisons, financial impacts, reduction targets, internal carbon pricing

## Routing Rules

1. Route each claim to at least one specialist agent.
2. Route claims to multiple agents when the claim spans domains (e.g., a geographic emissions claim goes to both Geography and Data/Metrics).
3. All claims with specific IFRS paragraph mappings should include the Legal Agent.
4. Claims mentioning specific locations, facilities, or geographic areas should include the Geography Agent.
5. Claims with numerical figures, percentages, or quantitative targets should include the Data/Metrics Agent.
6. Claims about high-profile commitments, controversies, or public statements should include the News/Media Agent.
7. Claims referencing methodologies, standards, certifications, or academic frameworks should include the Academic/Research Agent.
8. Prioritize agents by relevance: primary agents investigate the core assertion; secondary agents provide corroborating evidence.

## Output Format

For each claim, provide:
- claim_id: The claim's unique identifier
- assigned_agents: List of agent names to route to
- reasoning: Brief explanation of why these agents were selected
- priority_order: Agents ordered by investigation priority
```

### A.2 User Prompt

```
Create a routing plan for the following {claim_count} extracted claims. Each claim includes its text, type, priority, and preliminary IFRS mappings.

Claims:
{claims_json}

Return a routing plan as a JSON object matching the specified schema. Include a brief routing_summary and the agent_workload distribution.
```

---

## Appendix B: Graph Topology Diagram

```
                    ┌──────────┐
                    │  START    │
                    └────┬─────┘
                         │
                         ▼
                ┌────────────────┐
                │ extract_claims │
                │ (Claims Agent) │
                └───────┬────────┘
                        │
                        ▼
                ┌───────────────┐◄──────────────────────────────┐
                │  orchestrate  │                                │
                │(Orchestrator) │                                │
                └───────┬───────┘                                │
                        │                                        │
            ┌───────────┼───────────┐                            │
            │     conditional       │                            │
            │      fan-out          │                            │
            ▼           ▼           ▼                            │
   ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
   │geography │  │  legal   │  │news_media│                     │
   │  agent   │  │  agent   │  │  agent   │   (parallel)        │
   └────┬─────┘  └────┬─────┘  └────┬─────┘                     │
        │              │              │                          │
   ┌──────────┐  ┌──────────┐                                    │
   │academic  │  │data_metr.│                                    │
   │  agent   │  │  agent   │   (parallel)                       │
   └────┬─────┘  └────┬─────┘                                    │
        │              │                                         │
        └──────┬───────┘                                         │
               │ (all specialists converge)                      │
               ▼                                                 │
        ┌──────────────┐                                         │
        │judge_evidence│                                         │
        │(Judge Agent) │                                         │
        └──────┬───────┘                                         │
               │                                                 │
               ├── reinvestigation_requests AND                  │
               │   iteration_count < max_iterations ─────────────┘
               │          (cyclic edge)
               │
               ├── otherwise
               ▼
        ┌──────────────┐
        │compile_report│
        └──────┬───────┘
               │
               ▼
          ┌─────────┐
          │   END   │
          └─────────┘
```

---

## Appendix C: SSE Event Schema Reference

### C.1 Complete Event Types

| Event Type | Agent Name | Data Fields | Description |
|---|---|---|---|
| `agent_started` | Any agent | `{}` | Agent node begins execution |
| `agent_thinking` | Any agent | `{message: string}` | Agent reasoning/progress update |
| `agent_completed` | Any agent | `{claims_processed?: int, findings_count?: int}` | Agent node finishes successfully |
| `claim_routed` | `orchestrator` | `{claim_id: string, assigned_agents: string[], reasoning: string}` | Orchestrator routes a claim |
| `evidence_found` | Specialist agent | `{claim_id: string, evidence_type: string, summary: string, supports_claim: bool?}` | Agent finds evidence for a claim |
| `verdict_issued` | `judge` | `{claim_id: string, verdict: string, reasoning: string}` | Judge issues a verdict |
| `reinvestigation` | `judge` | `{claim_ids: string[], target_agents: string[], cycle: int, evidence_gaps: string[]}` | Judge requests re-investigation |
| `info_request_posted` | Specialist agent | `{requesting_agent: string, description: string}` | Agent posts cross-domain request |
| `info_request_routed` | `orchestrator` | `{requesting_agent: string, target_agents: string[], description: string}` | Orchestrator routes info request |
| `info_response_posted` | Specialist agent | `{responding_agent: string, requesting_agent: string, summary: string}` | Agent responds to info request |
| `pipeline_completed` | `null` | `{total_claims: int, total_findings: int, total_verdicts: int, iterations: int}` | Full pipeline complete |
| `error` | Any agent or `null` | `{message: string, node?: string}` | Error during execution |

### C.2 Event Ordering

Events are ordered chronologically by `timestamp`. Within a single node execution, events are ordered by emission order. The `id` field on each SSE message provides a sequential counter for reconnection support.

---

## Appendix D: Pipeline Execution Sequence Diagram

```
Frontend           Backend              TaskWorker          Graph               ClaimsAgent    Orchestrator    Specialists    Judge         CompileReport
 │                    │                     │                  │                    │               │              │              │               │
 │ POST /analysis/    │                     │                  │                    │               │              │              │               │
 │ {id}/start         │                     │                  │                    │               │              │              │               │
 │───────────────────►│                     │                  │                    │               │              │              │               │
 │                    │  Enqueue pipeline   │                  │                    │               │              │              │               │
 │                    │─────────────────────►                  │                    │               │              │              │               │
 │  200 {analyzing}   │                     │                  │                    │               │              │              │               │
 │◄───────────────────│                     │                  │                    │               │              │              │               │
 │                    │                     │                  │                    │               │              │              │               │
 │ GET /stream/{id}   │                     │  BRPOP           │                    │               │              │              │               │
 │───────────────────►│                     │  run_pipeline()  │                    │               │              │              │               │
 │                    │                     │─────────────────►│                    │               │              │              │               │
 │  SSE connection    │                     │                  │  extract_claims    │               │              │              │               │
 │  opened            │                     │                  │───────────────────►│               │              │              │               │
 │                    │                     │                  │                    │  LLM call     │              │              │               │
 │ event: agent_      │                     │                  │                    │  (Gemini)     │              │              │               │
 │ started (claims)   │                     │                  │                    │               │              │              │               │
 │◄───────────────────│                     │                  │                    │               │              │              │               │
 │                    │                     │                  │◄───────────────────│               │              │              │               │
 │ event: agent_      │                     │                  │  state.claims = [] │               │              │              │               │
 │ completed (claims) │                     │                  │                    │               │              │              │               │
 │◄───────────────────│                     │                  │                    │               │              │              │               │
 │                    │                     │                  │  orchestrate       │               │              │              │               │
 │                    │                     │                  │──────────────────────────────────►│              │              │               │
 │ event: agent_      │                     │                  │                    │               │  LLM call   │              │               │
 │ started (orch.)    │                     │                  │                    │               │  (Sonnet)   │              │               │
 │◄───────────────────│                     │                  │                    │               │              │              │               │
 │ event: claim_      │                     │                  │                    │               │              │              │               │
 │ routed (×N)        │                     │                  │                    │               │              │              │               │
 │◄───────────────────│                     │                  │◄──────────────────────────────────│              │              │               │
 │                    │                     │                  │  state.routing_plan│               │              │              │               │
 │                    │                     │                  │                    │               │              │              │               │
 │                    │                     │                  │  fan-out           │               │              │              │               │
 │                    │                     │                  │──────────────────────────────────────────────────►│              │               │
 │ event: agent_      │                     │                  │                    │               │  (parallel)  │              │               │
 │ started (spec.)    │                     │                  │                    │               │  stubs       │              │               │
 │◄───────────────────│                     │                  │                    │               │              │              │               │
 │ event: agent_      │                     │                  │◄──────────────────────────────────────────────────│              │               │
 │ completed (spec.)  │                     │                  │  state.findings    │               │              │              │               │
 │◄───────────────────│                     │                  │                    │               │              │              │               │
 │                    │                     │                  │  judge_evidence    │               │              │              │               │
 │                    │                     │                  │──────────────────────────────────────────────────────────────────►│               │
 │ event: verdict_    │                     │                  │                    │               │              │              │               │
 │ issued (×N)        │                     │                  │                    │               │              │  stub        │               │
 │◄───────────────────│                     │                  │◄──────────────────────────────────────────────────────────────────│               │
 │                    │                     │                  │  should_continue   │               │              │              │               │
 │                    │                     │                  │  → compile_report  │               │              │              │               │
 │                    │                     │                  │──────────────────────────────────────────────────────────────────────────────────►│
 │                    │                     │                  │                    │               │              │              │  Persist       │
 │ event: pipeline_   │                     │                  │                    │               │              │              │  verdicts +    │
 │ completed          │                     │                  │                    │               │              │              │  findings      │
 │◄───────────────────│                     │                  │◄──────────────────────────────────────────────────────────────────────────────────│
 │                    │                     │                  │                    │               │              │              │               │
 │                    │                     │◄─────────────────│                    │               │              │              │               │
 │                    │                     │  Set "completed" │                    │               │              │              │               │
 │  SSE connection    │                     │                  │                    │               │              │              │               │
 │  closed            │                     │                  │                    │               │              │              │               │
```

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| LangGraph `Send` API for fan-out over sequential specialist invocation | The PRD specifies "specialist agents run in parallel where possible" (Section 5.3). LangGraph's `Send` API enables parallel execution of multiple specialist nodes in a single step, reducing total pipeline latency. |
| `asyncio.Queue` for SSE event delivery over polling the state | A queue provides immediate, push-based event delivery from the pipeline to the SSE endpoint. Polling the checkpoint state would introduce latency (poll interval) and unnecessary database reads. The queue is lightweight and disposable. |
| In-process event queue over Redis Pub/Sub for SSE | For MVP with a single backend process, an in-process `asyncio.Queue` is simpler and faster than Redis Pub/Sub. Redis Pub/Sub would be needed for horizontal scaling (multiple backend instances), which is deferred. |
| Claude Sonnet 4.5 for routing over rule-based routing | The PRD specifies Claude Sonnet 4.5 for the Orchestrator (Section 4.3). LLM-based routing enables nuanced, content-aware decisions (e.g., detecting a geographic claim that also needs quantitative validation) that a static routing table cannot handle. Rule-based routing is available as a fallback if the LLM fails. |
| Report ID as LangGraph thread ID | Creates a 1:1 mapping between reports and pipeline executions. Simplifies checkpoint retrieval, event routing, and pipeline resumption. Multiple analyses of the same report would require a new thread ID (report_id + timestamp), but this is out of scope for MVP (one analysis per report). |
| Specialist stubs return placeholder findings over returning empty state | Placeholder findings enable end-to-end testing of the entire pipeline, including Judge evaluation and compile_report. Empty returns would cause the Judge to have no evidence to evaluate, making the pipeline less testable. |
| Judge stub does NOT generate reinvestigation requests | Generating reinvestigation requests with stub specialists would create an infinite loop of stubs calling stubs. The Judge stub issues `"unverified"` verdicts directly, testing the `compile_report` path. The cyclic edge is verified separately by manually injecting reinvestigation requests. |
| Claims Agent persists to database directly (preserved from FRD 3) | Claims need to be immediately available for the frontend claims list and PDF viewer highlights while the pipeline continues running. Deferring persistence to `compile_report` would create a gap where the frontend has no claims to display during investigation. Findings and verdicts, which are produced later, are persisted by `compile_report`. |
| `compile_report` as a stub in FRD 5 | The full report compilation logic depends on all specialist agents being implemented (FRDs 6-10) and the Judge producing real verdicts (FRD 11). FRD 5's stub handles persistence and status transition, which is sufficient for pipeline testing. Full implementation in FRD 13. |
| SSE keepalive every 30 seconds over no keepalive | Many reverse proxies (nginx, CloudFlare, AWS ALB) close idle connections after 60-120 seconds. Sending a comment line every 30 seconds prevents premature disconnection without generating real events. |
| Pipeline task queue key `sibyl:tasks:run_pipeline` over reusing `extract_claims` key | The full pipeline is a semantically different task from standalone claims extraction. A new queue key avoids confusion and allows the old key to remain for backward compatibility (standalone claims extraction for testing). |
| `langgraph-checkpoint-postgres` over custom checkpoint implementation | LangGraph provides a battle-tested PostgreSQL checkpointer that handles serialization, schema management, and resume logic. Building a custom checkpointer would duplicate this effort with less reliability. |
| Agent tabs appear dynamically over showing all tabs from the start | Showing 8+ agent tabs before any agents are active creates visual noise. Dynamic tab appearance makes the UI responsive to the pipeline state and reveals agents only when they become relevant. |
| "All" tab as a unified timeline over agent-only views | Users may want to see the full investigative flow chronologically (which agent worked when, how evidence flowed between agents). The "All" tab provides this without requiring users to manually switch between agent tabs. |
| Max 1000 events in the queue over unbounded queue | Prevents memory exhaustion if the SSE consumer is slower than the producer (e.g., during network issues). 1000 events is sufficient for a full pipeline execution (typically 100-200 events). Dropped events are logged but do not break the pipeline. |
| Timeout of 120 seconds per agent over no timeout | Prevents a stuck agent (e.g., due to an LLM API hang) from blocking the entire pipeline indefinitely. 120 seconds is generous enough for complex investigations while preventing indefinite waits. The pipeline continues with available evidence if an agent times out. |
