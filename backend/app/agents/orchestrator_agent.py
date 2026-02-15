"""Orchestrator Agent - routes claims to specialist agents and manages pipeline.

Implements FRD 5 Sections 2-5.

Model: Claude Sonnet 4.5 (strong reasoning for routing decisions)

The Orchestrator is the supervisory node that:
- Creates routing plans assigning claims to specialist agents
- Manages agent status and execution priorities
- Routes InfoRequests between agents
- Handles re-investigation requests from the Judge
"""

import json
import logging
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.agents.state import (
    AgentStatus,
    RoutingAssignment,
    SibylState,
    StreamEvent,
)
from app.core.database import generate_uuid7
from app.services.openrouter_client import Models, openrouter_client

logger = logging.getLogger(__name__)


# =============================================================================
# Response schemas for structured output
# =============================================================================


class RoutingDecision(BaseModel):
    """Routing decision for a single claim."""
    
    claim_id: str
    assigned_agents: list[str]
    reasoning: str
    priority_order: list[str] = Field(
        default_factory=list,
        description="Agents in order of investigation priority",
    )


class RoutingPlanResult(BaseModel):
    """Complete routing plan from the Orchestrator."""
    
    assignments: list[RoutingDecision]
    routing_summary: str = ""
    agent_workload: dict[str, int] = Field(default_factory=dict)


class ReinvestigationContext(BaseModel):
    """Context from the Judge for a re-investigation pass."""
    
    claim_id: str
    evidence_gap: str
    refined_queries: list[str] = Field(default_factory=list)
    required_evidence: str | None = None
    cycle_number: int = 1


# =============================================================================
# Routing prompts (from FRD 5 Appendix A)
# =============================================================================

ORCHESTRATOR_SYSTEM_PROMPT = """You are the Orchestrator Agent in Sibyl, an AI system that verifies sustainability reports against IFRS S1/S2 disclosure standards. Your task is to create a routing plan that assigns extracted claims to the appropriate specialist investigation agents.

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

Return a JSON object with:
- assignments: Array of routing decisions, one per claim
- routing_summary: Brief summary of the routing strategy
- agent_workload: Dictionary mapping agent names to number of assigned claims"""


ORCHESTRATOR_USER_PROMPT = """Create a routing plan for the following {claim_count} extracted claims. Each claim includes its ID, text, type, priority, and preliminary IFRS mappings.

Claims:
{claims_json}

Return a routing plan as a JSON object. For each claim, include:
- claim_id: The claim's unique identifier
- assigned_agents: List of agent names to route to
- reasoning: Brief explanation of why these agents were selected
- priority_order: Agents ordered by investigation priority"""


# =============================================================================
# Default routing matrix (fallback)
# =============================================================================

DEFAULT_ROUTING: dict[str, list[str]] = {
    "geographic": ["geography", "legal"],
    "quantitative": ["data_metrics", "legal"],
    "legal_governance": ["legal"],
    "strategic": ["legal", "academic", "news_media"],
    "environmental": ["academic", "geography", "data_metrics"],
}

VALID_AGENTS = {"geography", "legal", "news_media", "academic", "data_metrics"}


# =============================================================================
# Helper functions
# =============================================================================


def _apply_default_routing(claims: list) -> list[RoutingAssignment]:
    """Apply rule-based default routing when LLM routing fails.
    
    Uses the default routing matrix from FRD 5 Section 3.2.
    
    Args:
        claims: List of Claim objects from the state
        
    Returns:
        List of RoutingAssignment objects
    """
    assignments = []
    
    for claim in claims:
        agents = DEFAULT_ROUTING.get(claim.claim_type, ["legal"])
        
        # Add extra agents based on content analysis
        claim_lower = claim.text.lower()
        
        # Geographic keywords
        if any(kw in claim_lower for kw in [
            "facility", "site", "location", "region", "country", "area",
            "forest", "land", "water", "biodiversity", "deforestation",
        ]):
            if "geography" not in agents:
                agents = list(agents) + ["geography"]
        
        # Quantitative keywords
        if any(kw in claim_lower for kw in [
            "%", "percent", "million", "billion", "tonnes", "tons", "mtco2",
            "scope 1", "scope 2", "scope 3", "reduction", "increase",
        ]):
            if "data_metrics" not in agents:
                agents = list(agents) + ["data_metrics"]
        
        # News-worthy keywords
        if any(kw in claim_lower for kw in [
            "commitment", "pledge", "announced", "invest", "target", "goal",
            "net zero", "net-zero", "carbon neutral",
        ]):
            if "news_media" not in agents:
                agents = list(agents) + ["news_media"]
        
        # Academic/research keywords
        if any(kw in claim_lower for kw in [
            "sbti", "science based", "methodology", "certified", "verified",
            "standard", "framework", "protocol", "ghg protocol",
        ]):
            if "academic" not in agents:
                agents = list(agents) + ["academic"]
        
        assignments.append(
            RoutingAssignment(
                claim_id=claim.claim_id,
                assigned_agents=agents,
                reasoning=f"Default routing for {claim.claim_type} claim",
            )
        )
    
    return assignments


async def _route_with_llm(claims: list) -> list[RoutingAssignment] | None:
    """Route claims using Claude Sonnet 4.5.
    
    Args:
        claims: List of Claim objects from the state
        
    Returns:
        List of RoutingAssignment objects, or None if LLM fails
    """
    # Build claims JSON for the prompt
    claims_data = []
    for claim in claims:
        claims_data.append({
            "claim_id": claim.claim_id,
            "text": claim.text[:500],  # Truncate long claims
            "type": claim.claim_type,
            "priority": claim.priority,
            "ifrs_paragraphs": claim.ifrs_paragraphs[:5],  # Limit for prompt
        })
    
    user_prompt = ORCHESTRATOR_USER_PROMPT.format(
        claim_count=len(claims),
        claims_json=json.dumps(claims_data, indent=2),
    )
    
    try:
        response = await openrouter_client.chat_completion(
            model=Models.CLAUDE_SONNET,
            messages=[
                {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=8192,
        )
        
        # Parse the response
        # Try to extract JSON from the response
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            import re
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                result = json.loads(json_match.group())
            else:
                logger.warning("Could not parse LLM routing response")
                return None
        
        # Parse into RoutingPlanResult
        plan = RoutingPlanResult(**result)
        
        # Convert to RoutingAssignment objects
        assignments = []
        for decision in plan.assignments:
            # Filter out invalid agent names
            valid_agents = [a for a in decision.assigned_agents if a in VALID_AGENTS]
            if not valid_agents:
                valid_agents = ["legal"]  # Fallback
            
            assignments.append(
                RoutingAssignment(
                    claim_id=decision.claim_id,
                    assigned_agents=valid_agents,
                    reasoning=decision.reasoning,
                )
            )
        
        logger.info("LLM routing successful: %d assignments", len(assignments))
        return assignments
        
    except Exception as e:
        logger.warning("LLM routing failed: %s", e)
        return None


def _route_info_requests(state: SibylState) -> list:
    """Route pending InfoRequests to appropriate agents.
    
    Args:
        state: Current pipeline state
        
    Returns:
        Updated info_requests list
    """
    info_requests = list(state.info_requests)
    
    for request in info_requests:
        if request.status != "pending":
            continue
        
        # Determine target agent based on content
        description_lower = request.description.lower()
        
        target_agents = []
        
        # Content-based routing
        if any(kw in description_lower for kw in [
            "location", "satellite", "imagery", "land", "facility", "site",
            "coordinates", "geographic",
        ]):
            target_agents.append("geography")
        
        if any(kw in description_lower for kw in [
            "ifrs", "s1", "s2", "compliance", "paragraph", "regulation",
            "governance", "disclosure",
        ]):
            target_agents.append("legal")
        
        if any(kw in description_lower for kw in [
            "news", "media", "press", "public", "reporting", "controversy",
            "journalist",
        ]):
            target_agents.append("news_media")
        
        if any(kw in description_lower for kw in [
            "research", "academic", "benchmark", "sbti", "methodology",
            "peer-reviewed", "standard",
        ]):
            target_agents.append("academic")
        
        if any(kw in description_lower for kw in [
            "numbers", "calculation", "emissions", "data", "scope", "metrics",
            "consistency", "figures",
        ]):
            target_agents.append("data_metrics")
        
        # Default to legal if no match
        if not target_agents:
            target_agents = ["legal"]
        
        # Update request status
        request.status = "routed"
        # Store target in context
        request.context["target_agents"] = target_agents
    
    return info_requests


# =============================================================================
# Main orchestrate function
# =============================================================================


async def orchestrate(state: SibylState) -> dict:
    """Orchestrator Agent: Route claims to specialist agents and manage pipeline.
    
    Modes:
    - Initial routing (iteration_count == 0): Create routing plan from claims
    - Re-investigation (iteration_count > 0): Process Judge's requests
    
    Args:
        state: Current pipeline state with claims and agent status
        
    Returns:
        Partial state update with routing plan, agent status, and events
    """
    events: list[StreamEvent] = []
    
    # Emit start event
    events.append(
        StreamEvent(
            event_type="agent_started",
            agent_name="orchestrator",
            data={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    
    # Determine operating mode
    is_initial_routing = (
        state.iteration_count == 0 and len(state.routing_plan) == 0
    )
    is_reinvestigation = (
        state.iteration_count > 0 or len(state.reinvestigation_requests) > 0
    )
    
    routing_plan: list[RoutingAssignment] = []
    iteration_count = state.iteration_count
    agent_status = dict(state.agent_status)
    
    if is_initial_routing:
        # =====================================================================
        # Initial routing mode
        # =====================================================================
        
        events.append(
            StreamEvent(
                event_type="agent_thinking",
                agent_name="orchestrator",
                data={
                    "message": f"Analyzing {len(state.claims)} claims for routing..."
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )
        
        # Try LLM routing first
        llm_assignments = await _route_with_llm(state.claims)
        
        if llm_assignments:
            routing_plan = llm_assignments
            events.append(
                StreamEvent(
                    event_type="agent_thinking",
                    agent_name="orchestrator",
                    data={"message": "Created routing plan using LLM analysis"},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )
        else:
            # Fallback to rule-based routing
            routing_plan = _apply_default_routing(state.claims)
            events.append(
                StreamEvent(
                    event_type="agent_thinking",
                    agent_name="orchestrator",
                    data={"message": "Using default routing rules (LLM unavailable)"},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )
        
        # Emit claim_routed events
        for assignment in routing_plan:
            events.append(
                StreamEvent(
                    event_type="claim_routed",
                    agent_name="orchestrator",
                    data={
                        "claim_id": assignment.claim_id,
                        "assigned_agents": assignment.assigned_agents,
                        "reasoning": assignment.reasoning,
                    },
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )
        
        # Initialize agent status for all agents in the routing plan
        for agent_name in VALID_AGENTS:
            claims_count = sum(
                1 for a in routing_plan if agent_name in a.assigned_agents
            )
            agent_status[agent_name] = AgentStatus(
                agent_name=agent_name,
                status="idle" if claims_count > 0 else "idle",
                claims_assigned=claims_count,
                claims_completed=0,
            )
        
    elif is_reinvestigation:
        # =====================================================================
        # Re-investigation mode
        # =====================================================================
        
        iteration_count += 1
        
        events.append(
            StreamEvent(
                event_type="agent_thinking",
                agent_name="orchestrator",
                data={
                    "message": f"Processing re-investigation requests (cycle {iteration_count})"
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )
        
        # Process reinvestigation requests
        for request in state.reinvestigation_requests:
            # Create targeted routing assignment
            assignment = RoutingAssignment(
                claim_id=request.claim_id,
                assigned_agents=request.target_agents,
                reasoning=f"Re-investigation: {request.evidence_gap}",
            )
            routing_plan.append(assignment)
            
            # Emit reinvestigation event
            events.append(
                StreamEvent(
                    event_type="reinvestigation",
                    agent_name="orchestrator",
                    data={
                        "claim_id": request.claim_id,
                        "target_agents": request.target_agents,
                        "cycle": iteration_count,
                        "evidence_gap": request.evidence_gap,
                    },
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )
            
            # Update agent status for re-activated agents
            for agent_name in request.target_agents:
                if agent_name in agent_status:
                    agent_status[agent_name] = AgentStatus(
                        agent_name=agent_name,
                        status="idle",
                        claims_assigned=agent_status[agent_name].claims_assigned + 1,
                        claims_completed=agent_status[agent_name].claims_completed,
                    )
    
    # =========================================================================
    # Process InfoRequests (on every invocation)
    # =========================================================================
    
    updated_info_requests = _route_info_requests(state)
    
    # Emit events for newly routed InfoRequests
    for request in updated_info_requests:
        if (
            request.status == "routed" and
            "target_agents" in request.context and
            request.context.get("_event_emitted") is not True
        ):
            events.append(
                StreamEvent(
                    event_type="info_request_routed",
                    agent_name="orchestrator",
                    data={
                        "requesting_agent": request.requesting_agent,
                        "target_agents": request.context["target_agents"],
                        "description": request.description[:200],
                    },
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )
            request.context["_event_emitted"] = True
    
    # =========================================================================
    # Compute routing summary
    # =========================================================================
    
    agent_workload = {}
    for agent_name in VALID_AGENTS:
        count = sum(1 for a in routing_plan if agent_name in a.assigned_agents)
        if count > 0:
            agent_workload[agent_name] = count
    
    # Emit completion event
    events.append(
        StreamEvent(
            event_type="agent_completed",
            agent_name="orchestrator",
            data={
                "routing_plan_size": len(routing_plan),
                "agent_workload": agent_workload,
                "iteration": iteration_count,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    
    return {
        "routing_plan": routing_plan,
        "agent_status": agent_status,
        "info_requests": updated_info_requests,
        "iteration_count": iteration_count,
        "reinvestigation_requests": [],  # Clear processed requests
        "events": state.events + events,
    }
