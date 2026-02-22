"""Utility functions for real-time event streaming from agents.

Implements real-time SSE streaming per the plan in docs/plans/real-time-agent-streaming.md.

Provides helper functions to emit StreamEvent objects via LangGraph's
custom streaming mechanism. Events are sent immediately to the frontend
rather than being batched until node completion.

Requirements:
- Python 3.11+ (for context variable propagation in asyncio)
- LangGraph 0.2.0+ (for get_stream_writer and stream_mode="custom")
"""

import logging
from datetime import datetime, timezone

from langgraph.config import get_stream_writer

from app.agents.state import StreamEvent

logger = logging.getLogger(__name__)


def emit_event(
    event_type: str,
    agent_name: str | None = None,
    data: dict | None = None,
) -> None:
    """Emit a StreamEvent immediately to the frontend via SSE.
    
    This function uses LangGraph's custom streaming to send events
    in real-time during node execution, rather than waiting for
    node completion.
    
    Args:
        event_type: Type of event (agent_started, agent_thinking, etc.)
        agent_name: Name of the emitting agent
        data: Optional event-specific data payload
    """
    try:
        writer = get_stream_writer()
        event = StreamEvent(
            event_type=event_type,
            agent_name=agent_name,
            data=data or {},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        writer(event)
    except Exception as e:
        # Log but don't fail - streaming is non-critical
        logger.debug("Failed to emit event %s: %s", event_type, e)


def emit_agent_started(agent_name: str, data: dict | None = None) -> None:
    """Emit an agent_started event."""
    emit_event("agent_started", agent_name, data or {})


def emit_agent_thinking(agent_name: str, message: str) -> None:
    """Emit an agent_thinking event with a message."""
    emit_event("agent_thinking", agent_name, {"message": message})


def emit_agent_completed(
    agent_name: str,
    claims_processed: int = 0,
    findings_count: int = 0,
    **kwargs,
) -> None:
    """Emit an agent_completed event with summary stats.
    
    Args:
        agent_name: Name of the agent completing
        claims_processed: Number of claims processed
        findings_count: Number of findings generated
        **kwargs: Additional key-value pairs to include in the event data
    """
    data = {"claims_processed": claims_processed, "findings_count": findings_count}
    data.update(kwargs)
    emit_event("agent_completed", agent_name, data)


def emit_evidence_found(
    agent_name: str,
    claim_id: str,
    evidence_type: str,
    summary: str,
    supports_claim: bool | None = None,
    confidence: str | None = None,
) -> None:
    """Emit an evidence_found event."""
    emit_event(
        "evidence_found",
        agent_name,
        {
            "claim_id": claim_id,
            "evidence_type": evidence_type,
            "summary": summary,
            "supports_claim": supports_claim,
            "confidence": confidence,
        },
    )


def emit_verdict_issued(
    agent_name: str,
    claim_id: str,
    verdict: str,
    confidence: str,
    reasoning: str,
    ifrs_mapping: list[str] | None = None,
    cycle_count: int | None = None,
) -> None:
    """Emit a verdict_issued event."""
    data = {
        "claim_id": claim_id,
        "verdict": verdict,
        "reasoning": reasoning[:300] if reasoning else "",
        "confidence": confidence,
    }
    if ifrs_mapping is not None:
        data["ifrs_mapping"] = ifrs_mapping
    if cycle_count is not None:
        data["cycle_count"] = cycle_count
    emit_event("verdict_issued", agent_name, data)


def emit_claim_routed(
    claim_id: str,
    assigned_agents: list[str],
    reasoning: str | None = None,
) -> None:
    """Emit a claim_routed event."""
    emit_event(
        "claim_routed",
        "orchestrator",
        {
            "claim_id": claim_id,
            "assigned_agents": assigned_agents,
            "reasoning": reasoning,
        },
    )


def emit_reinvestigation(
    claim_id: str,
    target_agents: list[str],
    cycle: int,
    evidence_gap: str,
) -> None:
    """Emit a reinvestigation event."""
    emit_event(
        "reinvestigation",
        "orchestrator",
        {
            "claim_id": claim_id,
            "target_agents": target_agents,
            "cycle": cycle,
            "evidence_gap": evidence_gap,
        },
    )


def emit_reinvestigation_batch(
    agent_name: str,
    claim_ids: list[str],
    target_agents: list[str],
    cycle: int,
) -> None:
    """Emit a reinvestigation event for multiple claims (from judge)."""
    emit_event(
        "reinvestigation",
        agent_name,
        {
            "claim_ids": claim_ids,
            "target_agents": target_agents,
            "cycle": cycle,
        },
    )


def emit_pipeline_completed(
    total_claims: int,
    total_verdicts: int,
    iterations: int,
    total_findings: int | None = None,
    verdict_breakdown: dict[str, int] | None = None,
    findings_by_agent: dict[str, int] | None = None,
) -> None:
    """Emit a pipeline_completed event."""
    data: dict = {
        "total_claims": total_claims,
        "total_verdicts": total_verdicts,
        "iterations": iterations,
    }
    if total_findings is not None:
        data["total_findings"] = total_findings
    if verdict_breakdown is not None:
        data["verdict_breakdown"] = verdict_breakdown
    if findings_by_agent is not None:
        data["findings_by_agent"] = findings_by_agent
    emit_event("pipeline_completed", None, data)


def emit_error(agent_name: str | None, message: str) -> None:
    """Emit an error event."""
    emit_event("error", agent_name, {"message": message})


def emit_evidence_evaluation(
    agent_name: str,
    claim_id: str,
    overall_score: float,
    sufficiency: str,
    consistency: str,
    quality: str,
    completeness: str,
) -> None:
    """Emit an evidence_evaluation event (from judge)."""
    emit_event(
        "evidence_evaluation",
        agent_name,
        {
            "claim_id": claim_id,
            "overall_score": overall_score,
            "sufficiency": sufficiency,
            "consistency": consistency,
            "quality": quality,
            "completeness": completeness,
        },
    )


def emit_info_request_routed(
    request_id: str,
    requesting_agent: str,
    target_agents: list[str],
    description: str,
) -> None:
    """Emit an info_request_routed event."""
    emit_event(
        "info_request_routed",
        "orchestrator",
        {
            "request_id": request_id,
            "requesting_agent": requesting_agent,
            "target_agents": target_agents,
            "description": description,
        },
    )


def emit_consistency_check(
    agent_name: str,
    check_name: str,
    claim_id: str,
    result: str,
    severity: str,
    details: str | dict | None = None,
    message: str | None = None,
) -> None:
    """Emit a consistency_check event (from data_metrics agent)."""
    emit_event(
        "consistency_check",
        agent_name,
        {
            "check_name": check_name,
            "claim_id": claim_id,
            "result": result,
            "severity": severity,
            "details": details if details else {},
            "message": message or "",
        },
    )


def emit_disclosure_gap_found(
    agent_name: str,
    gap_type: str,
    paragraph_id: str,
    description: str,
) -> None:
    """Emit a disclosure_gap_found event (from legal agent)."""
    emit_event(
        "disclosure_gap_found",
        agent_name,
        {
            "gap_type": gap_type,
            "paragraph_id": paragraph_id,
            "description": description,
        },
    )


def emit_ifrs_coverage_update(
    agent_name: str,
    total_paragraphs: int,
    covered_paragraphs: int,
    coverage_percentage: float,
) -> None:
    """Emit an ifrs_coverage_update event (from legal agent)."""
    emit_event(
        "ifrs_coverage_update",
        agent_name,
        {
            "total_paragraphs": total_paragraphs,
            "covered_paragraphs": covered_paragraphs,
            "coverage_percentage": coverage_percentage,
        },
    )


def emit_search_executed(
    agent_name: str,
    query: str,
    results_count: int,
    source: str | None = None,
) -> None:
    """Emit a search_executed event (from news/academic agents)."""
    emit_event(
        "search_executed",
        agent_name,
        {
            "query": query,
            "results_count": results_count,
            "source": source,
        },
    )


def emit_source_evaluated(
    agent_name: str,
    source_name: str,
    credibility_tier: int,
    url: str | None = None,
) -> None:
    """Emit a source_evaluated event (from news agent)."""
    emit_event(
        "source_evaluated",
        agent_name,
        {
            "source_name": source_name,
            "credibility_tier": credibility_tier,
            "url": url,
        },
    )


def emit_contradiction_detected(
    agent_name: str,
    claim_id: str,
    source1: str,
    source2: str,
    description: str,
) -> None:
    """Emit a contradiction_detected event (from news agent)."""
    emit_event(
        "contradiction_detected",
        agent_name,
        {
            "claim_id": claim_id,
            "source1": source1,
            "source2": source2,
            "description": description,
        },
    )
