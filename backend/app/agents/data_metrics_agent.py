"""Data/Metrics Agent - validates quantitative claims for consistency.

Implements FRD 7 (stub implementation in FRD 5).

Model: Claude Sonnet 4.5 (strong numerical reasoning)
"""

from datetime import datetime, timezone

from app.agents.state import (
    AgentFinding,
    AgentStatus,
    SibylState,
    StreamEvent,
)
from app.core.database import generate_uuid7


async def investigate_data(state: SibylState) -> dict:
    """Specialist Agent stub: Data/Metrics Agent.
    
    Accepts routed claims and returns placeholder findings.
    Full implementation in FRD 7.
    
    Checks (when implemented):
    - Internal consistency (Scope 1+2+3 totals, year-over-year changes)
    - Unit and methodology validation (GHG Protocol alignment)
    - Benchmark comparison (industry sector plausibility)
    - Target assessment (mathematical achievability)
    - Historical consistency with prior reports
    
    Critical for S2.27-37 compliance (GHG emissions, targets, carbon pricing).
    
    Args:
        state: Current pipeline state with assigned quantitative claims
        
    Returns:
        Partial state update with data/metrics findings
    """
    agent_name = "data_metrics"
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
                "(stub -- full quantitative consistency analysis in FRD 7)"
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
            "Full data/metrics consistency investigation in FRD 7.",
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
