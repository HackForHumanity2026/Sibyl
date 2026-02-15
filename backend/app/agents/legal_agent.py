"""Legal Agent - validates compliance and governance claims against IFRS/SASB.

Implements FRD 6 (stub implementation in FRD 5).

Model: Claude Sonnet 4.5 (excellent legal and compliance reasoning)
Knowledge Base: IFRS S1/S2, SASB standards
"""

from datetime import datetime, timezone

from app.agents.state import (
    AgentFinding,
    AgentStatus,
    SibylState,
    StreamEvent,
)
from app.core.database import generate_uuid7


async def investigate_legal(state: SibylState) -> dict:
    """Specialist Agent stub: Legal Agent.
    
    Accepts routed claims and returns placeholder findings.
    Full implementation in FRD 6.
    
    Capabilities (when implemented):
    - Paragraph-level IFRS compliance mapping
    - Governance structure assessment (S1.26-27, S2.5-7)
    - Risk management disclosure validation (S1.38-42, S2.24-26)
    - Disclosure gap detection (omission analysis)
    
    Args:
        state: Current pipeline state with assigned legal/governance claims
        
    Returns:
        Partial state update with legal findings and disclosure gaps
    """
    agent_name = "legal"
    events: list[StreamEvent] = []
    findings: list[AgentFinding] = []
    
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
    routing_plan = state.get("routing_plan", [])
    assigned_claims = [
        a for a in routing_plan
        if agent_name in a.assigned_agents
    ]
    
    # Get current iteration count
    iteration_count = state.get("iteration_count", 0)
    
    # Emit thinking event
    events.append(
        StreamEvent(
            event_type="agent_thinking",
            agent_name=agent_name,
            data={
                "message": f"Processing {len(assigned_claims)} assigned claims... "
                "(stub -- full IFRS/SASB compliance analysis in FRD 6)"
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    
    # Generate placeholder findings (only NEW findings, reducer will merge)
    for assignment in assigned_claims:
        finding = AgentFinding(
            finding_id=str(generate_uuid7()),
            agent_name=agent_name,
            claim_id=assignment.claim_id,
            evidence_type="placeholder",
            summary=f"Placeholder finding from {agent_name} agent (stub). "
            "Full IFRS/SASB compliance investigation in FRD 6.",
            details={"stub": True, "agent": agent_name},
            supports_claim=None,
            confidence=None,
            iteration=iteration_count + 1,
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
    
    # Emit completion event
    events.append(
        StreamEvent(
            event_type="agent_completed",
            agent_name=agent_name,
            data={
                "claims_processed": len(assigned_claims),
                "findings_count": len(findings),
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    
    # Return only NEW items - the reducer (operator.add) will merge them
    return {
        "findings": findings,
        "agent_status": {
            agent_name: AgentStatus(
                agent_name=agent_name,
                status="completed",
                claims_assigned=len(assigned_claims),
                claims_completed=len(assigned_claims),
            )
        },
        "events": events,
    }
