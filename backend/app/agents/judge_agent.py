"""Judge Agent - evaluates evidence and issues verdicts with cyclic validation.

Implements FRD 11 (stub implementation in FRD 5).

Model: Claude Opus 4.5 (highest-quality reasoning for judgment calls)

The Judge Agent:
- Evaluates evidence from all specialist agents
- Issues verdicts for each claim
- May request re-investigation if evidence is insufficient
"""

from datetime import datetime, timezone

from app.agents.state import (
    ClaimVerdict,
    SibylState,
    StreamEvent,
)


async def judge_evidence(state: SibylState) -> dict:
    """Judge Agent stub: Evaluate evidence and issue verdicts.
    
    This stub implementation:
    1. Receives all findings from specialist agents
    2. Produces placeholder "unverified" verdicts for each claim
    3. Does NOT generate reinvestigation requests (avoids infinite loops)
    4. Emits verdict events
    
    Full implementation in FRD 11 will include:
    - Evidence sufficiency evaluation
    - Cross-agent consistency checks
    - Source credibility assessment
    - Confidence scoring
    - Re-investigation request generation
    
    Verdicts:
    - verified: Multiple independent sources corroborate
    - unverified: No external evidence found
    - contradicted: Evidence directly contradicts claim
    - insufficient_evidence: Some evidence but not enough
    
    Args:
        state: Current pipeline state with all agent findings
        
    Returns:
        Partial state update with verdicts and/or reinvestigation requests
    """
    agent_name = "judge"
    events: list[StreamEvent] = []
    
    # Get state values using dict access
    claims = state.get("claims", [])
    findings = state.get("findings", [])
    iteration_count = state.get("iteration_count", 0)
    
    # Emit start event
    events.append(
        StreamEvent(
            event_type="agent_started",
            agent_name=agent_name,
            data={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    
    # Emit thinking event
    events.append(
        StreamEvent(
            event_type="agent_thinking",
            agent_name=agent_name,
            data={
                "message": f"Evaluating evidence for {len(claims)} claims "
                f"from {len(findings)} findings... "
                "(stub -- full evidence evaluation in FRD 11)"
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    
    # Group findings by claim_id
    findings_by_claim: dict[str, list] = {}
    for finding in findings:
        if finding.claim_id not in findings_by_claim:
            findings_by_claim[finding.claim_id] = []
        findings_by_claim[finding.claim_id].append(finding)
    
    # Generate placeholder verdicts for each claim
    verdicts: list[ClaimVerdict] = []
    
    for claim in claims:
        claim_findings = findings_by_claim.get(claim.claim_id, [])
        
        # Stub verdict: always "unverified"
        verdict = ClaimVerdict(
            claim_id=claim.claim_id,
            verdict="unverified",
            reasoning=f"Stub verdict -- specialist agents not yet implemented. "
            f"Full evaluation in FRD 11. "
            f"Found {len(claim_findings)} placeholder findings.",
            ifrs_mapping=[
                {"paragraph": p, "status": "pending"}
                for p in claim.ifrs_paragraphs[:3]
            ],
            evidence_summary={
                "findings_count": len(claim_findings),
                "agents_consulted": list(set(f.agent_name for f in claim_findings)),
                "stub": True,
            },
            iteration_count=iteration_count + 1,
        )
        verdicts.append(verdict)
        
        # Emit verdict event
        events.append(
            StreamEvent(
                event_type="verdict_issued",
                agent_name=agent_name,
                data={
                    "claim_id": claim.claim_id,
                    "verdict": verdict.verdict,
                    "reasoning": verdict.reasoning[:200],
                    "findings_count": len(claim_findings),
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )
    
    # NOTE: Stub does NOT generate reinvestigation requests
    # This avoids infinite loops with stub specialist agents
    # The conditional edge will route to compile_report
    
    # Emit completion event
    events.append(
        StreamEvent(
            event_type="agent_completed",
            agent_name=agent_name,
            data={
                "claims_evaluated": len(verdicts),
                "verdicts_issued": len(verdicts),
                "reinvestigation_requests": 0,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    
    # Return only NEW items - the reducer will merge them
    return {
        "verdicts": verdicts,
        "reinvestigation_requests": [],  # Empty to avoid cycles
        "iteration_count": iteration_count + 1,
        "events": events,
    }
