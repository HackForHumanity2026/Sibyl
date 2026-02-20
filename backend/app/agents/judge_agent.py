"""Judge Agent - evaluates evidence and issues verdicts with cyclic validation.

Implements FRD 11.

Model: Claude Opus 4.5 (highest-quality reasoning for judgment calls)

The Judge Agent:
- Evaluates evidence from all specialist agents across 4 dimensions
- Issues verdicts for each claim (verified/unverified/contradicted/insufficient_evidence)
- Generates re-investigation requests when evidence is insufficient
- Maps verdicts to IFRS paragraphs
"""

import json
import logging
from datetime import datetime, timezone

from app.agents.state import (
    AgentFinding,
    AgentStatus,
    Claim,
    ClaimVerdict,
    ReinvestigationRequest,
    SibylState,
    StreamEvent,
)
from app.services.openrouter_client import Models, openrouter_client

logger = logging.getLogger(__name__)

# =============================================================================
# Model Configuration
# =============================================================================

MODEL = Models.CLAUDE_OPUS
TEMPERATURE = 0.1
MAX_TOKENS = 16384

# =============================================================================
# Constants
# =============================================================================

# Agent base quality weights (higher = more authoritative)
AGENT_QUALITY_WEIGHTS: dict[str, float] = {
    "legal": 0.95,
    "geography": 0.9,
    "data_metrics": 0.9,
    "academic": 0.85,
    "news_media": 0.7,
}

# Expected agents by claim type
CLAIM_TYPE_EXPECTED_AGENTS: dict[str, list[str]] = {
    "geographic": ["geography", "legal"],
    "quantitative": ["data_metrics", "legal"],
    "legal_governance": ["legal"],
    "strategic": ["legal", "academic", "news_media"],
    "environmental": ["academic", "geography", "data_metrics"],
}

# Dimension weights for overall score (must sum to 1.0)
DIMENSION_WEIGHTS = {
    "sufficiency": 0.3,
    "consistency": 0.25,
    "quality": 0.25,
    "completeness": 0.2,
}

# Score thresholds
VERIFIED_THRESHOLD = 0.7
REINVESTIGATION_THRESHOLD = 0.7

# =============================================================================
# Evidence Evaluation Functions
# =============================================================================


def evaluate_sufficiency(
    findings: list[AgentFinding], claim: Claim
) -> dict:
    """Evaluate whether evidence is sufficient for a verdict.
    
    Counts unique agents providing supporting/contradicting evidence.
    
    Args:
        findings: List of findings for this claim
        claim: The claim being evaluated
        
    Returns:
        Dict with sufficiency assessment
    """
    supporting_findings = [f for f in findings if f.supports_claim is True]
    contradicting_findings = [f for f in findings if f.supports_claim is False]
    
    # Count independent sources (by agent)
    supporting_agents = list(set(f.agent_name for f in supporting_findings))
    contradicting_agents = list(set(f.agent_name for f in contradicting_findings))
    
    source_count = len(supporting_agents)
    
    if source_count >= 3:
        sufficiency = "high"
    elif source_count == 2:
        sufficiency = "medium"
    elif source_count == 1:
        sufficiency = "low"
    else:
        sufficiency = "very_low"
    
    return {
        "sufficiency": sufficiency,
        "source_count": source_count,
        "supporting_agents": supporting_agents,
        "contradicting_agents": contradicting_agents,
        "has_contradictions": len(contradicting_agents) > 0,
        "total_findings": len(findings),
    }


def evaluate_consistency(findings: list[AgentFinding]) -> dict:
    """Evaluate consistency of findings across agents.
    
    Checks alignment between agents (support vs. contradict vs. inconclusive).
    
    Args:
        findings: List of findings for this claim
        
    Returns:
        Dict with consistency assessment
    """
    support_counts = {"support": 0, "contradict": 0, "inconclusive": 0}
    
    for finding in findings:
        if finding.supports_claim is True:
            support_counts["support"] += 1
        elif finding.supports_claim is False:
            support_counts["contradict"] += 1
        else:
            support_counts["inconclusive"] += 1
    
    total_findings = len(findings)
    support_ratio = support_counts["support"] / total_findings if total_findings > 0 else 0
    contradict_ratio = support_counts["contradict"] / total_findings if total_findings > 0 else 0
    
    if support_counts["contradict"] == 0 and support_counts["support"] > 0:
        consistency = "high"
        has_contradictions = False
    elif support_counts["contradict"] > 0 and support_counts["support"] > support_counts["contradict"]:
        consistency = "medium"
        has_contradictions = True
    elif support_counts["contradict"] > support_counts["support"]:
        consistency = "low"
        has_contradictions = True
    else:
        consistency = "unclear"
        has_contradictions = support_counts["contradict"] > 0
    
    return {
        "consistency": consistency,
        "has_contradictions": has_contradictions,
        "support_ratio": support_ratio,
        "contradict_ratio": contradict_ratio,
        "support_counts": support_counts,
    }


def evaluate_quality(findings: list[AgentFinding]) -> dict:
    """Evaluate quality of evidence sources.
    
    Weights findings by agent type and confidence level.
    
    Args:
        findings: List of findings for this claim
        
    Returns:
        Dict with quality assessment
    """
    if not findings:
        return {
            "quality": "low",
            "avg_quality_score": 0.0,
            "quality_scores": [],
        }
    
    quality_scores = []
    
    for finding in findings:
        agent_quality = AGENT_QUALITY_WEIGHTS.get(finding.agent_name, 0.5)
        
        # Adjust for source credibility (if available in details for news_media)
        if finding.agent_name == "news_media":
            source_tier = finding.details.get("source_tier", 3)
            tier_multiplier = {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.3}.get(source_tier, 0.6)
            agent_quality *= tier_multiplier
        
        # Adjust for confidence
        confidence_multiplier = {
            "high": 1.0,
            "medium": 0.7,
            "low": 0.4,
        }.get(finding.confidence, 0.5)
        
        quality_score = agent_quality * confidence_multiplier
        quality_scores.append(quality_score)
    
    avg_quality = sum(quality_scores) / len(quality_scores)
    
    if avg_quality >= 0.8:
        quality = "high"
    elif avg_quality >= 0.6:
        quality = "medium"
    else:
        quality = "low"
    
    return {
        "quality": quality,
        "avg_quality_score": avg_quality,
        "quality_scores": quality_scores,
    }


def evaluate_completeness(
    claim: Claim,
    findings: list[AgentFinding],
    agent_status: dict[str, AgentStatus],
) -> dict:
    """Evaluate whether all relevant domains have been investigated.
    
    Checks expected agents based on claim_type and accounts for errored agents.
    
    Args:
        claim: The claim being evaluated
        findings: List of findings for this claim
        agent_status: Status of all agents in the pipeline
        
    Returns:
        Dict with completeness assessment
    """
    # Expected agents based on claim type
    expected_agents = CLAIM_TYPE_EXPECTED_AGENTS.get(
        claim.claim_type, ["legal"]
    )
    
    # Agents that produced findings
    investigated_agents = list(set(f.agent_name for f in findings))
    
    # Agents that errored
    errored_agents = [
        name for name, status in agent_status.items()
        if isinstance(status, AgentStatus) and status.status == "error"
    ]
    
    # Handle case where agent_status contains dicts instead of AgentStatus
    if not errored_agents and agent_status:
        for name, status in agent_status.items():
            if isinstance(status, dict) and status.get("status") == "error":
                errored_agents.append(name)
    
    # Missing agents (expected but no findings)
    missing_agents = [a for a in expected_agents if a not in investigated_agents]
    
    # Agents that errored from expected
    errored_expected = [a for a in expected_agents if a in errored_agents]
    
    completeness_score = 1.0
    if missing_agents:
        completeness_score -= 0.2 * len(missing_agents)
    if errored_expected:
        completeness_score -= 0.3 * len(errored_expected)
    completeness_score = max(0.0, completeness_score)
    
    if completeness_score >= 0.8:
        completeness = "high"
    elif completeness_score >= 0.6:
        completeness = "medium"
    else:
        completeness = "low"
    
    return {
        "completeness": completeness,
        "completeness_score": completeness_score,
        "expected_agents": expected_agents,
        "investigated_agents": investigated_agents,
        "missing_agents": missing_agents,
        "errored_agents": errored_expected,
    }


def evaluate_evidence(
    claim: Claim,
    findings: list[AgentFinding],
    agent_status: dict[str, AgentStatus],
) -> dict:
    """Perform four-dimensional evidence evaluation.
    
    Combines sufficiency, consistency, quality, and completeness evaluations
    into an overall score.
    
    Args:
        claim: The claim being evaluated
        findings: List of findings for this claim
        agent_status: Status of all agents
        
    Returns:
        Combined evaluation with overall score
    """
    sufficiency = evaluate_sufficiency(findings, claim)
    consistency = evaluate_consistency(findings)
    quality = evaluate_quality(findings)
    completeness = evaluate_completeness(claim, findings, agent_status)
    
    # Convert dimension levels to scores
    dimension_scores = {
        "sufficiency": {
            "high": 1.0, "medium": 0.6, "low": 0.3, "very_low": 0.0
        }[sufficiency["sufficiency"]],
        "consistency": {
            "high": 1.0, "medium": 0.6, "low": 0.3, "unclear": 0.5
        }[consistency["consistency"]],
        "quality": {
            "high": 1.0, "medium": 0.6, "low": 0.3
        }[quality["quality"]],
        "completeness": {
            "high": 1.0, "medium": 0.6, "low": 0.3
        }[completeness["completeness"]],
    }
    
    # Weighted combination
    overall_score = sum(
        DIMENSION_WEIGHTS[dim] * score
        for dim, score in dimension_scores.items()
    )
    
    return {
        "sufficiency": sufficiency,
        "consistency": consistency,
        "quality": quality,
        "completeness": completeness,
        "overall_score": overall_score,
        "dimension_scores": dimension_scores,
    }


# =============================================================================
# Verdict Production Functions
# =============================================================================


def determine_verdict(evaluation: dict) -> str:
    """Determine verdict based on evidence evaluation.
    
    Decision tree:
    - If contradictions majority: "contradicted"
    - If no sources: "unverified"
    - If high score, no contradictions: "verified"
    - Else: "insufficient_evidence"
    
    Args:
        evaluation: Combined evidence evaluation
        
    Returns:
        Verdict string
    """
    overall_score = evaluation["overall_score"]
    has_contradictions = evaluation["consistency"]["has_contradictions"]
    contradict_ratio = evaluation["consistency"]["contradict_ratio"]
    source_count = evaluation["sufficiency"]["source_count"]
    
    # Decision tree per FRD-11 Section 4.2
    if has_contradictions and contradict_ratio > 0.5:
        return "contradicted"
    
    if source_count == 0:
        return "unverified"
    
    if overall_score >= VERIFIED_THRESHOLD and not has_contradictions:
        return "verified"
    
    return "insufficient_evidence"


def generate_verdict_reasoning(
    evaluation: dict,
    findings: list[AgentFinding],
    verdict: str,
    claim: Claim,
) -> str:
    """Generate reasoning string for a verdict.
    
    Cites specific agents and their findings.
    
    Args:
        evaluation: Evidence evaluation results
        findings: List of findings for this claim
        verdict: The determined verdict
        claim: The claim being evaluated
        
    Returns:
        Reasoning string
    """
    lines = []
    
    sufficiency = evaluation["sufficiency"]
    consistency = evaluation["consistency"]
    completeness = evaluation["completeness"]
    
    if verdict == "verified":
        lines.append("Claim is VERIFIED. Multiple independent sources corroborate:")
        for agent in sufficiency["supporting_agents"]:
            agent_findings = [f for f in findings if f.agent_name == agent and f.supports_claim]
            if agent_findings:
                lines.append(f"- {agent.replace('_', ' ').title()} Agent: {agent_findings[0].summary[:150]}")
        lines.append("Evidence is consistent, high-quality, and sufficient. No contradictions found.")
    
    elif verdict == "unverified":
        lines.append("Claim is UNVERIFIED. No external evidence found by any specialist agent:")
        for agent in completeness["expected_agents"]:
            lines.append(f"- {agent.replace('_', ' ').title()} Agent: No evidence found")
        lines.append("The claim cannot be independently verified.")
    
    elif verdict == "contradicted":
        lines.append("Claim is CONTRADICTED. Evidence directly contradicts the claim:")
        for agent in sufficiency["contradicting_agents"]:
            agent_findings = [f for f in findings if f.agent_name == agent and f.supports_claim is False]
            if agent_findings:
                lines.append(f"- {agent.replace('_', ' ').title()} Agent: {agent_findings[0].summary[:150]}")
        if sufficiency["supporting_agents"]:
            lines.append(f"Supporting evidence from: {', '.join(sufficiency['supporting_agents'])}")
        lines.append("The weight of contradicting evidence outweighs supporting evidence.")
    
    else:  # insufficient_evidence
        lines.append("Claim has INSUFFICIENT EVIDENCE. Some evidence exists but is not sufficient:")
        issues = []
        if sufficiency["sufficiency"] in ["low", "very_low"]:
            issues.append(f"Only {sufficiency['source_count']} source(s) found")
        if consistency["has_contradictions"]:
            issues.append("Contradicting findings require resolution")
        if completeness["missing_agents"]:
            issues.append(f"Missing agent perspectives: {', '.join(completeness['missing_agents'])}")
        for issue in issues:
            lines.append(f"- {issue}")
        lines.append("Cannot reach a confident verdict with available evidence.")
    
    return "\n".join(lines)


def extract_ifrs_mapping(
    claim: Claim,
    findings: list[AgentFinding],
) -> list[dict]:
    """Extract IFRS paragraph mappings for a verdict.
    
    Combines mappings from claim and Legal Agent findings.
    
    Args:
        claim: The claim being evaluated
        findings: List of findings for this claim
        
    Returns:
        List of IFRS mapping dicts
    """
    ifrs_paragraphs = {}
    
    # From claim's preliminary mapping
    for paragraph in claim.ifrs_paragraphs:
        ifrs_paragraphs[paragraph] = {"paragraph": paragraph, "status": "pending"}
    
    # From Legal Agent findings
    legal_findings = [f for f in findings if f.agent_name == "legal"]
    for finding in legal_findings:
        ifrs_mappings = finding.details.get("ifrs_mappings", [])
        for mapping in ifrs_mappings:
            paragraph_id = mapping.get("paragraph_id") or mapping.get("paragraph")
            if paragraph_id:
                compliance_status = mapping.get("compliance_status", "pending")
                status_map = {
                    "fully_addressed": "compliant",
                    "partially_addressed": "partial",
                    "not_addressed": "non_compliant",
                }
                ifrs_paragraphs[paragraph_id] = {
                    "paragraph": paragraph_id,
                    "status": status_map.get(compliance_status, "pending"),
                }
    
    return list(ifrs_paragraphs.values())


def determine_confidence(overall_score: float) -> str:
    """Determine confidence level for verdict.
    
    Args:
        overall_score: Overall evaluation score
        
    Returns:
        Confidence level string
    """
    if overall_score >= 0.8:
        return "high"
    elif overall_score >= 0.6:
        return "medium"
    else:
        return "low"


# =============================================================================
# Re-investigation Functions
# =============================================================================


def should_request_reinvestigation(
    evaluation: dict,
    iteration_count: int,
    max_iterations: int,
) -> bool:
    """Determine if re-investigation should be requested.
    
    Args:
        evaluation: Evidence evaluation results
        iteration_count: Current iteration
        max_iterations: Maximum allowed iterations
        
    Returns:
        True if re-investigation should be requested
    """
    if iteration_count >= max_iterations:
        return False
    
    return evaluation["overall_score"] < REINVESTIGATION_THRESHOLD


def _identify_evidence_gap(evaluation: dict) -> str:
    """Identify the specific evidence gap that needs to be addressed.
    
    Args:
        evaluation: Evidence evaluation results
        
    Returns:
        Description of evidence gaps
    """
    gaps = []
    
    sufficiency = evaluation["sufficiency"]
    consistency = evaluation["consistency"]
    quality = evaluation["quality"]
    completeness = evaluation["completeness"]
    
    if sufficiency["sufficiency"] in ["low", "very_low"]:
        gaps.append(
            f"Insufficient sources: only {sufficiency['source_count']} agent(s) found evidence. "
            "Need multiple independent sources."
        )
    
    if consistency["has_contradictions"]:
        supporting = ", ".join(sufficiency["supporting_agents"]) or "none"
        contradicting = ", ".join(sufficiency["contradicting_agents"]) or "none"
        gaps.append(
            f"Contradictions found: [{contradicting}] contradict while [{supporting}] support. "
            "Need resolution."
        )
    
    if quality["quality"] == "low":
        gaps.append(
            f"Low-quality sources: average quality score {quality['avg_quality_score']:.2f}. "
            "Need higher-credibility sources."
        )
    
    if completeness["missing_agents"]:
        gaps.append(
            f"Missing agent perspectives: {completeness['missing_agents']} should have investigated but did not."
        )
    
    return " ".join(gaps) if gaps else "Evidence incomplete."


def _determine_target_agents(
    claim: Claim,
    evaluation: dict,
    findings: list[AgentFinding],
) -> list[str]:
    """Determine which agents should re-investigate.
    
    Args:
        claim: The claim to re-investigate
        evaluation: Evidence evaluation results
        findings: Current findings
        
    Returns:
        List of agent names to target
    """
    target_agents = set()
    
    completeness = evaluation["completeness"]
    consistency = evaluation["consistency"]
    sufficiency = evaluation["sufficiency"]
    quality = evaluation["quality"]
    
    # If missing agents, prioritize them
    if completeness["missing_agents"]:
        target_agents.update(completeness["missing_agents"])
    
    # If contradictions, re-investigate both sides
    if consistency["has_contradictions"]:
        target_agents.update(sufficiency["supporting_agents"])
        target_agents.update(sufficiency["contradicting_agents"])
    
    # If low quality, re-investigate low-quality source agents
    if quality["quality"] == "low" and findings:
        for i, finding in enumerate(findings):
            if i < len(quality["quality_scores"]) and quality["quality_scores"][i] < 0.5:
                target_agents.add(finding.agent_name)
    
    # If insufficient sources, add expected agents
    if sufficiency["sufficiency"] in ["low", "very_low"]:
        expected = set(completeness["expected_agents"])
        investigated = set(f.agent_name for f in findings)
        target_agents.update(expected - investigated)
    
    # Ensure we have at least one agent
    if not target_agents:
        target_agents.update(completeness["expected_agents"][:2])
    
    return list(target_agents)


def _generate_refined_queries(
    claim: Claim,
    target_agents: list[str],
) -> list[str]:
    """Generate specific queries for re-investigation.
    
    Args:
        claim: The claim to re-investigate
        target_agents: Agents to target
        
    Returns:
        List of refined query strings
    """
    queries = []
    claim_text = claim.text[:200]
    
    for agent in target_agents:
        if agent == "geography":
            queries.append(
                f"Verify geographic claim: '{claim_text}'. "
                "Focus on satellite imagery analysis for the stated location and time period."
            )
        elif agent == "legal":
            queries.append(
                f"Re-assess IFRS compliance for: '{claim_text}'. "
                "Check if all sub-requirements are addressed, especially those flagged as missing."
            )
        elif agent == "news_media":
            queries.append(
                f"Search for recent news coverage (prioritize Tier 1-2 sources) about: '{claim_text}'. "
                "Look for corroboration or contradiction."
            )
        elif agent == "academic":
            queries.append(
                f"Validate technical claim against peer-reviewed research: '{claim_text}'. "
                "Check methodology alignment with recognized standards."
            )
        elif agent == "data_metrics":
            queries.append(
                f"Re-verify quantitative claim for mathematical consistency: '{claim_text}'. "
                "Check calculations, units, and benchmark plausibility."
            )
    
    return queries


def _specify_required_evidence(target_agents: list[str]) -> str:
    """Specify what would constitute sufficient evidence.
    
    Args:
        target_agents: Agents being targeted
        
    Returns:
        Required evidence specification
    """
    requirements = []
    
    if "geography" in target_agents:
        requirements.append(
            "Satellite imagery showing the claimed location/condition with NDVI analysis "
            "and temporal comparison if applicable."
        )
    
    if "legal" in target_agents:
        requirements.append(
            "IFRS paragraph-level compliance assessment with all sub-requirements addressed."
        )
    
    if "news_media" in target_agents:
        requirements.append(
            "News coverage from Tier 1-2 sources (investigative journalism, regulatory actions) "
            "corroborating or contradicting the claim."
        )
    
    if "academic" in target_agents:
        requirements.append(
            "Peer-reviewed research or recognized industry benchmarks validating the technical claim."
        )
    
    if "data_metrics" in target_agents:
        requirements.append(
            "Mathematical consistency verification with benchmark comparison and unit validation."
        )
    
    return " ".join(requirements) if requirements else "Additional corroborating evidence required."


def generate_reinvestigation_request(
    claim: Claim,
    evaluation: dict,
    findings: list[AgentFinding],
    iteration_count: int,
) -> ReinvestigationRequest:
    """Generate a re-investigation request for a claim.
    
    Args:
        claim: The claim to re-investigate
        evaluation: Evidence evaluation results
        findings: Current findings
        iteration_count: Current iteration
        
    Returns:
        ReinvestigationRequest object
    """
    evidence_gap = _identify_evidence_gap(evaluation)
    target_agents = _determine_target_agents(claim, evaluation, findings)
    refined_queries = _generate_refined_queries(claim, target_agents)
    required_evidence = _specify_required_evidence(target_agents)
    
    return ReinvestigationRequest(
        claim_id=claim.claim_id,
        target_agents=target_agents,
        evidence_gap=evidence_gap,
        refined_queries=refined_queries,
        required_evidence=required_evidence,
    )


# =============================================================================
# LLM Integration (for complex cases)
# =============================================================================

JUDGE_SYSTEM_PROMPT = """You are the Judge Agent in Sibyl, an AI system that verifies sustainability reports against IFRS S1/S2 disclosure standards. Your task is to evaluate evidence gathered by specialist investigation agents and produce final verdicts for each claim.

## Your Responsibilities

1. **Evidence Evaluation:** Evaluate evidence across four dimensions:
   - **Sufficiency:** Is there enough evidence? Multiple independent sources?
   - **Consistency:** Do findings from different agents align or contradict?
   - **Quality:** Are sources credible? Is evidence direct or circumstantial?
   - **Completeness:** Have all relevant angles been investigated?

2. **Verdict Production:** Produce one of four verdicts:
   - **Verified:** Multiple independent sources corroborate; no contradictions
   - **Unverified:** No external evidence found
   - **Contradicted:** Evidence directly contradicts the claim
   - **Insufficient Evidence:** Some evidence exists but not sufficient

3. **IFRS Mapping:** Connect each verdict to relevant IFRS S1/S2 paragraphs.

## Output Format

Return a JSON object with:
- verdict: One of "verified", "unverified", "contradicted", "insufficient_evidence"
- reasoning: Detailed explanation citing specific agent findings
- confidence: One of "high", "medium", "low"
"""


async def _get_llm_verdict(
    claim: Claim,
    findings: list[AgentFinding],
    evaluation: dict,
) -> dict | None:
    """Get LLM-generated verdict for complex cases.
    
    Args:
        claim: The claim being evaluated
        findings: List of findings for this claim
        evaluation: Pre-computed evaluation
        
    Returns:
        Dict with verdict details or None if LLM fails
    """
    try:
        findings_json = [
            {
                "agent": f.agent_name,
                "summary": f.summary,
                "supports_claim": f.supports_claim,
                "confidence": f.confidence,
                "details": f.details,
            }
            for f in findings
        ]
        
        user_prompt = f"""Evaluate the following claim and produce a verdict.

Claim: {claim.text}
Claim Type: {claim.claim_type}
IFRS Paragraphs: {claim.ifrs_paragraphs}

Findings from specialist agents:
{json.dumps(findings_json, indent=2)}

Pre-computed evaluation:
- Overall score: {evaluation['overall_score']:.2f}
- Has contradictions: {evaluation['consistency']['has_contradictions']}
- Source count: {evaluation['sufficiency']['source_count']}
- Quality: {evaluation['quality']['quality']}

Based on this evidence, produce your verdict as JSON with keys: verdict, reasoning, confidence"""

        response = await openrouter_client.chat_completion(
            model=MODEL,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        
        # Parse JSON response
        response_clean = response.strip()
        if response_clean.startswith("```"):
            lines = response_clean.split("\n")
            response_clean = "\n".join(lines[1:-1])
        
        return json.loads(response_clean)
        
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning("LLM verdict parsing failed, using rule-based: %s", e)
        return None
    except (ConnectionError, TimeoutError, RuntimeError) as e:
        logger.warning("LLM verdict request failed, using rule-based: %s", e)
        return None


# =============================================================================
# Main Node Function
# =============================================================================


async def judge_evidence(state: SibylState) -> dict:
    """Judge Agent: Evaluate evidence and produce final verdicts with cyclic validation.
    
    Reads: state.findings, state.claims, state.agent_status,
           state.iteration_count, state.max_iterations
    Writes: state.verdicts, state.reinvestigation_requests,
            state.iteration_count, state.events
    
    Responsibilities:
    1. Collect all findings for each claim from all specialist agents
    2. Evaluate evidence across four dimensions: sufficiency, consistency, quality, completeness
    3. Consider agent_status to know which agents completed vs. errored
    4. Produce final verdicts: Verified, Unverified, Contradicted, Insufficient Evidence
    5. Map verdicts to IFRS S1/S2 paragraphs
    6. Generate ReinvestigationRequests when evidence is insufficient
    7. Emit StreamEvents for detective dashboard
    
    Args:
        state: Current pipeline state with all agent findings
        
    Returns:
        Partial state update with verdicts, reinvestigation_requests, iteration_count, events
    """
    agent_name = "judge"
    events: list[StreamEvent] = []
    
    # Get state values
    claims = state.get("claims", [])
    findings = state.get("findings", [])
    agent_status = state.get("agent_status", {})
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 3)
    
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
                f"from {len(findings)} findings (iteration {iteration_count + 1}/{max_iterations})"
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    
    # Group findings by claim_id
    findings_by_claim: dict[str, list[AgentFinding]] = {}
    for finding in findings:
        claim_id = finding.claim_id
        if claim_id not in findings_by_claim:
            findings_by_claim[claim_id] = []
        findings_by_claim[claim_id].append(finding)
    
    # Process each claim
    verdicts: list[ClaimVerdict] = []
    reinvestigation_requests: list[ReinvestigationRequest] = []
    
    for claim in claims:
        claim_findings = findings_by_claim.get(claim.claim_id, [])
        
        # Evaluate evidence
        evaluation = evaluate_evidence(claim, claim_findings, agent_status)
        
        # Emit evaluation event
        events.append(
            StreamEvent(
                event_type="evidence_evaluation",
                agent_name=agent_name,
                data={
                    "claim_id": claim.claim_id,
                    "overall_score": evaluation["overall_score"],
                    "sufficiency": evaluation["sufficiency"]["sufficiency"],
                    "consistency": evaluation["consistency"]["consistency"],
                    "quality": evaluation["quality"]["quality"],
                    "completeness": evaluation["completeness"]["completeness"],
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )
        
        # Determine verdict (rule-based first)
        verdict_str = determine_verdict(evaluation)
        
        # For complex cases with contradictions, optionally use LLM
        use_llm = (
            evaluation["consistency"]["has_contradictions"]
            and evaluation["sufficiency"]["source_count"] >= 2
        )
        
        if use_llm:
            llm_result = await _get_llm_verdict(claim, claim_findings, evaluation)
            if llm_result:
                verdict_str = llm_result.get("verdict", verdict_str)
        
        # Generate reasoning
        reasoning = generate_verdict_reasoning(
            evaluation, claim_findings, verdict_str, claim
        )
        
        # Extract IFRS mapping
        ifrs_mapping = extract_ifrs_mapping(claim, claim_findings)
        
        # Determine confidence
        confidence = determine_confidence(evaluation["overall_score"])
        
        # Create verdict
        verdict = ClaimVerdict(
            claim_id=claim.claim_id,
            verdict=verdict_str,
            reasoning=reasoning,
            ifrs_mapping=ifrs_mapping,
            evidence_summary={
                "findings_count": len(claim_findings),
                "agents_consulted": list(set(f.agent_name for f in claim_findings)),
                "overall_score": evaluation["overall_score"],
                "dimension_scores": evaluation["dimension_scores"],
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
                    "verdict": verdict_str,
                    "reasoning": reasoning[:300],
                    "confidence": confidence,
                    "ifrs_mapping": [m["paragraph"] for m in ifrs_mapping],
                    "cycle_count": iteration_count + 1,
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )
        
        # Check if re-investigation needed
        if verdict_str == "insufficient_evidence" and should_request_reinvestigation(
            evaluation, iteration_count, max_iterations
        ):
            reinvest_request = generate_reinvestigation_request(
                claim, evaluation, claim_findings, iteration_count
            )
            reinvestigation_requests.append(reinvest_request)
    
    # Increment iteration count if any re-investigation requests
    new_iteration_count = iteration_count
    if reinvestigation_requests:
        new_iteration_count = iteration_count + 1
        
        # Emit reinvestigation event
        events.append(
            StreamEvent(
                event_type="reinvestigation",
                agent_name=agent_name,
                data={
                    "claim_ids": [r.claim_id for r in reinvestigation_requests],
                    "target_agents": list(set(
                        agent for r in reinvestigation_requests
                        for agent in r.target_agents
                    )),
                    "cycle": new_iteration_count,
                    "evidence_gaps": [r.evidence_gap[:100] for r in reinvestigation_requests],
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
                "claims_evaluated": len(verdicts),
                "verdicts_issued": len(verdicts),
                "verified_count": len([v for v in verdicts if v.verdict == "verified"]),
                "contradicted_count": len([v for v in verdicts if v.verdict == "contradicted"]),
                "unverified_count": len([v for v in verdicts if v.verdict == "unverified"]),
                "insufficient_count": len([v for v in verdicts if v.verdict == "insufficient_evidence"]),
                "reinvestigation_requests": len(reinvestigation_requests),
                "iteration": new_iteration_count,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    
    return {
        "verdicts": verdicts,
        "reinvestigation_requests": reinvestigation_requests,
        "iteration_count": new_iteration_count,
        "events": events,
    }
