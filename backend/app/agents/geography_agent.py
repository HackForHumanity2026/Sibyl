"""Geography Agent - verifies geographic claims via satellite imagery.

Implements FRD 10 (stub implementation in FRD 5).

Model: Gemini 2.5 Pro (best multimodal/vision capabilities)
Data Source: Microsoft Planetary Computer (Sentinel-2 imagery)
"""

from datetime import datetime, timezone

from app.agents.state import (
    AgentFinding,
    AgentStatus,
    SibylState,
    StreamEvent,
)
from app.core.database import generate_uuid7


async def investigate_geography(state: SibylState) -> dict:
    """Specialist Agent stub: Geography Agent.
    
    Accepts routed claims and returns placeholder findings.
    Full implementation in FRD 10.
    
    Capabilities (when implemented):
    - Vegetation change detection (NDVI analysis)
    - Land cover classification
    - Temporal comparison (before/after imagery)
    - Environmental impact indicators
    
    Args:
        state: Current pipeline state with assigned geographic claims
        
    Returns:
        Partial state update with geographic findings
    """
    agent_name = "geography"
    events = []
    
    # Emit start event
    events.append(
        StreamEvent(
            event_type="agent_started",
            agent_name=agent_name,
            data={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    
    # Find claims assigned to this agent
    assigned_claims = [
        a for a in state.routing_plan
        if agent_name in a.assigned_agents
    ]
    
    # Update agent status
    agent_status = dict(state.agent_status)
    agent_status[agent_name] = AgentStatus(
        agent_name=agent_name,
        status="working",
        claims_assigned=len(assigned_claims),
        claims_completed=0,
    )
    
    # Emit thinking event
    events.append(
        StreamEvent(
            event_type="agent_thinking",
            agent_name=agent_name,
            data={
                "message": f"Processing {len(assigned_claims)} assigned claims... "
                "(stub -- full satellite imagery analysis in FRD 10)"
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    
    # Generate placeholder findings
    findings = list(state.findings)
    for assignment in assigned_claims:
        finding = AgentFinding(
            finding_id=str(generate_uuid7()),
            agent_name=agent_name,
            claim_id=assignment.claim_id,
            evidence_type="placeholder",
            summary=f"Placeholder finding from {agent_name} agent (stub). "
            "Full satellite imagery investigation in FRD 10.",
            details={"stub": True, "agent": agent_name},
            supports_claim=None,
            confidence=None,
            iteration=state.iteration_count + 1,
        )
        findings.append(finding)
        
        # Emit evidence found event
        events.append(
            StreamEvent(
                event_type="evidence_found",
                agent_name=agent_name,
                data={
                    "claim_id": assignment.claim_id,
                    "evidence_type": "placeholder",
                    "summary": finding.summary,
                    "supports_claim": None,
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )
    
    # Update agent status to completed
    agent_status[agent_name] = AgentStatus(
        agent_name=agent_name,
        status="completed",
        claims_assigned=len(assigned_claims),
        claims_completed=len(assigned_claims),
    )
    
    # Emit completion event
    events.append(
        StreamEvent(
            event_type="agent_completed",
            agent_name=agent_name,
            data={
                "claims_processed": len(assigned_claims),
                "findings_count": len(assigned_claims),
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    
    return {
        "findings": findings,
        "agent_status": agent_status,
        "events": state.events + events,
    }
