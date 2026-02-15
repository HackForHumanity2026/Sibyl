"""News/Media Agent - verifies claims against public news sources.

Implements FRD 8 (stub implementation in FRD 5).

Model: Claude Sonnet 4.5 (strong source analysis and credibility assessment)
"""

from datetime import datetime, timezone

from app.agents.state import (
    AgentFinding,
    AgentStatus,
    SibylState,
    StreamEvent,
)
from app.core.database import generate_uuid7


async def investigate_news(state: SibylState) -> dict:
    """Specialist Agent stub: News/Media Agent.
    
    Accepts routed claims and returns placeholder findings.
    Full implementation in FRD 8.
    
    Source credibility tiers (when implemented):
    - Tier 1: Major investigative journalism, regulatory actions, court filings
    - Tier 2: Established news organizations, industry publications
    - Tier 3: Company press releases, wire services, analyst reports
    - Tier 4: Blogs, social media, unverified sources
    
    Args:
        state: Current pipeline state with assigned claims
        
    Returns:
        Partial state update with news/media findings
    """
    agent_name = "news_media"
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
                "(stub -- full news/media investigation in FRD 8)"
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
            "Full news/media credibility investigation in FRD 8.",
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
