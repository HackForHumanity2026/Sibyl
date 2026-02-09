# Feature Requirements Document: FRD 11 -- Judge Agent & Cyclic Validation (v1.0)

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.3](../PRD.md) |
| **FRD Order** | [FRD Order](../FRD-order.md) |
| **PRD Sections** | 4.9 (Judge Agent -- Cyclic Validation) |
| **Type** | Feature |
| **Depends On** | FRD 5 (Orchestrator Agent & LangGraph Pipeline), FRDs 6-10 (all specialist agents) |
| **Delivers** | Evidence evaluation across all specialist findings, cyclic re-investigation with ReinvestigationRequest generation, iteration depth control, final verdict production (Verified/Unverified/Contradicted/Insufficient Evidence), verdict-to-IFRS paragraph mapping, conditional edge logic routing back to Orchestrator or forward to compile_report, LangGraph node implementation, StreamEvent emissions for detective dashboard |
| **Created** | 2026-02-09 |

---

## Summary

FRD 11 delivers the Judge Agent -- the final evaluative node in the Sibyl multi-agent pipeline and the mechanism that enables Sibyl's cyclic validation loop. The Judge Agent (`app/agents/judge_agent.py`) replaces the FRD 5 stub with a functional LangGraph node that receives all evidence gathered by specialist agents (Geography, Legal, News/Media, Academic/Research, Data/Metrics from FRDs 6-10), evaluates evidence across four dimensions (sufficiency, consistency, quality, completeness), and produces final verdicts for each claim: Verified (multiple independent sources corroborate, no contradictions), Unverified (no external evidence found), Contradicted (evidence directly contradicts the claim), or Insufficient Evidence (some evidence exists but not sufficient for a confident verdict). When evidence is insufficient, contradictory, or incomplete, the Judge does not issue a premature verdict but instead generates `ReinvestigationRequest` objects with refined queries, specific agent targets, evidence gap descriptions, and required evidence specifications, sending them back to the Orchestrator for re-routing to specialist agents. The cyclic validation loop continues until evidence is sufficient or the maximum iteration depth (configurable, default 3 cycles) is reached. Each verdict is mapped to specific IFRS S1/S2 paragraphs, creating the paragraph-level compliance mapping that forms the core of the Source of Truth report. The conditional edge `should_continue_or_compile` (defined in FRD 5) checks whether reinvestigation_requests are non-empty AND iteration_count < max_iterations, routing back to the Orchestrator if true, otherwise routing forward to `compile_report`. The Judge Agent uses Claude Opus 4.5 for highest-quality reasoning on nuanced judgment calls, weighing contradictory evidence and making defensible final assessments. The agent emits StreamEvents (verdict_issued, reinvestigation, evidence_evaluation) for the detective dashboard, which displays verdict cards with color-coded badges and cycle counts. After FRD 11, the complete agent pipeline runs end-to-end: claims are extracted, routed, investigated, judged (with re-investigation if needed), and final verdicts with IFRS mappings are produced and persisted.

---

## Given Context (Preconditions)

The following are assumed to be in place from prior FRDs:

| Prerequisite | Source FRD | Deliverable |
|---|---|---|
| LangGraph StateGraph compiled with `judge_evidence` node stub | FRD 5 | `app/agents/graph.py` |
| `SibylState` Pydantic schema with `AgentFinding`, `ClaimVerdict`, `ReinvestigationRequest`, `StreamEvent`, `agent_status` types | FRD 5 | `app/agents/state.py` |
| Judge Agent stub (`judge_evidence` function signature) | FRD 5 | `app/agents/judge_agent.py` |
| Conditional edge function `should_continue_or_compile` defined | FRD 5 | `app/agents/graph.py` |
| All specialist agents implemented and producing findings | FRDs 6-10 | `app/agents/geography_agent.py`, `legal_agent.py`, `news_media_agent.py`, `academic_agent.py`, `data_metrics_agent.py` |
| `AgentFinding` schema with `agent_name`, `claim_id`, `evidence_type`, `summary`, `details`, `supports_claim`, `confidence`, `iteration` | FRD 0 | `app/agents/state.py` |
| `agent_status` dictionary tracking which agents completed vs. errored | FRD 5 | `SibylState.agent_status` |
| Orchestrator re-investigation handling (receives ReinvestigationRequests, re-routes to specialists) | FRD 5 | `app/agents/orchestrator_agent.py` |
| SSE streaming infrastructure with callback handler | FRD 5 | `app/agents/callbacks.py`, `app/api/routes/stream.py` |
| OpenRouter client wrapper with `Models.CLAUDE_OPUS` constant | FRD 0 | `app/services/openrouter_client.py` |
| Claims with IFRS paragraph mappings from Claims Agent and Legal Agent | FRDs 3, 6 | `claims` database table, `findings` table |
| `ClaimVerdict` schema with `claim_id`, `verdict`, `reasoning`, `ifrs_mapping`, `confidence`, `iteration` | FRD 0 | `app/agents/state.py` |
| `ReinvestigationRequest` schema with `claim_id`, `target_agents`, `evidence_gap`, `refined_queries`, `required_evidence` | FRD 0 | `app/agents/state.py` |

### Terms

| Term | Definition |
|---|---|
| Evidence evaluation | The Judge Agent's assessment of gathered evidence across four dimensions: sufficiency, consistency, quality, completeness |
| Sufficiency | Whether there is enough evidence to reach a verdict; multiple independent sources corroborating the claim |
| Consistency | Whether findings from different agents align or contradict each other |
| Quality | Whether sources are credible; whether evidence is direct or circumstantial |
| Completeness | Whether all relevant angles have been investigated; whether there is a domain that should have been consulted but was not |
| Cyclic re-investigation | The process by which the Judge sends claims back to specialist agents with refined queries when evidence is insufficient |
| ReinvestigationRequest | A structured request from the Judge to re-investigate a claim with specific guidance on evidence gaps and required evidence |
| Iteration depth | The number of investigation cycles (default: 3, configurable via `max_iterations`) |
| Verdict | The Judge's final assessment: Verified, Unverified, Contradicted, or Insufficient Evidence |
| Verdict-to-IFRS mapping | The connection between a verdict and specific IFRS S1/S2 paragraphs, creating paragraph-level compliance mapping |
| Conditional edge | A LangGraph edge whose target is determined at runtime by a routing function (`should_continue_or_compile`) |
| Evidence synthesis | The process of combining findings from multiple specialist agents into a unified assessment |

---

## Executive Summary (Gherkin-Style)

```gherkin
Feature: Judge Agent & Cyclic Validation

  Background:
    Given  FRD 5, FRD 6, FRD 7, FRD 8, FRD 9, and FRD 10 are complete
    And    all services are running (backend, frontend, PostgreSQL, Redis)
    And    claims have been extracted and routed to specialist agents
    And    specialist agents have produced findings for their assigned claims
    And    all findings are stored in the shared state

  Scenario: Judge Agent evaluates evidence from all specialists
    Given  the Judge Agent receives the shared state with all findings
    When   it processes each claim
    Then   it collects all findings for that claim from all specialist agents
    And    it evaluates evidence across four dimensions: sufficiency, consistency, quality, completeness
    And    it considers agent_status to know which agents completed vs. errored
    And    it produces a verdict: Verified, Unverified, Contradicted, or Insufficient Evidence

  Scenario: Evidence sufficiency evaluation
    Given  a claim has findings from multiple specialist agents
    When   the Judge evaluates sufficiency
    Then   it checks if there are multiple independent sources corroborating the claim
    And    it assesses whether the evidence volume is sufficient for a confident verdict
    And    it flags insufficient evidence when only one source exists or sources are weak

  Scenario: Evidence consistency evaluation
    Given  a claim has findings from Geography, Legal, and News/Media agents
    When   the Judge evaluates consistency
    Then   it checks if findings from different agents align
    And    it identifies contradictions (e.g., Geography supports, News contradicts)
    And    it assesses the severity of contradictions (direct contradiction vs. minor inconsistency)

  Scenario: Evidence quality evaluation
    Given  findings include source credibility information
    When   the Judge evaluates quality
    Then   it assesses source credibility (Tier 1-4 for News, peer-reviewed for Academic, etc.)
    And    it distinguishes direct evidence from circumstantial evidence
    And    it weights high-quality sources more heavily than low-quality sources

  Scenario: Evidence completeness evaluation
    Given  a claim has findings from some specialist agents
    When   the Judge evaluates completeness
    Then   it checks if all relevant domains have been investigated
    And    it identifies missing agent perspectives (e.g., geographic claim but no Geography Agent finding)
    And    it flags incomplete evidence when critical domains are missing

  Scenario: Judge produces Verified verdict
    Given  a claim has multiple independent sources corroborating it
    And    findings are consistent across agents
    And    sources are credible and direct
    And    all relevant domains have been investigated
    When   the Judge evaluates the evidence
    Then   it produces a Verified verdict
    And    the verdict includes reasoning citing the corroborating evidence
    And    the verdict maps to relevant IFRS paragraphs

  Scenario: Judge produces Unverified verdict
    Given  a claim has no external evidence found by any specialist agent
    When   the Judge evaluates the evidence
    Then   it produces an Unverified verdict
    And    the verdict includes reasoning explaining why no evidence was found
    And    the verdict notes which agents were consulted

  Scenario: Judge produces Contradicted verdict
    Given  a claim has evidence from one or more sources directly contradicting it
    When   the Judge evaluates the evidence
    Then   it produces a Contradicted verdict
    And    the verdict includes reasoning citing the contradictory evidence
    And    the verdict identifies which agents found contradictions

  Scenario: Judge produces Insufficient Evidence verdict
    Given  a claim has some evidence but it is not sufficient for a confident verdict
    And    evidence may be weak, circumstantial, or from low-quality sources
    When   the Judge evaluates the evidence
    Then   it produces an Insufficient Evidence verdict
    And    the verdict includes reasoning explaining why evidence is insufficient
    And    the verdict may trigger re-investigation if iteration_count < max_iterations

  Scenario: Judge generates re-investigation requests
    Given  evidence is insufficient, contradictory, or incomplete
    And    iteration_count < max_iterations
    When   the Judge evaluates the evidence
    Then   it generates ReinvestigationRequest objects with:
      - claim_id: The claim to re-investigate
      - target_agents: Specific agents that should re-investigate
      - evidence_gap: Description of what evidence is missing
      - refined_queries: Specific questions to address
      - required_evidence: What would constitute sufficient evidence
    And    it posts the requests to state.reinvestigation_requests
    And    it increments iteration_count

  Scenario: Cyclic validation loop
    Given  the Judge has generated reinvestigation_requests
    And    iteration_count < max_iterations
    When   the conditional edge evaluates should_continue_or_compile
    Then   it routes back to the Orchestrator
    And    the Orchestrator re-routes refined queries to the specified agents
    And    the specialists re-investigate with the Judge's guidance
    And    the cycle continues until evidence is sufficient or max_iterations is reached

  Scenario: Conditional edge routes to compile_report
    Given  the Judge has evaluated all claims
    And    either reinvestigation_requests is empty OR iteration_count >= max_iterations
    When   the conditional edge evaluates should_continue_or_compile
    Then   it routes to compile_report
    And    the pipeline completes with final verdicts

  Scenario: Verdict-to-IFRS paragraph mapping
    Given  the Judge produces a verdict for a claim
    When   it maps the verdict to IFRS paragraphs
    Then   it uses the claim's IFRS mappings from Claims Agent and Legal Agent findings
    And    it creates a paragraph-level compliance mapping
    And    the mapping connects the verdict to specific IFRS paragraph identifiers (e.g., S2.14(a)(iv))

  Scenario: Judge emits StreamEvents for detective dashboard
    Given  the Judge is processing claims
    When   it performs evaluation steps
    Then   it emits StreamEvent objects:
      - verdict_issued: For each verdict produced
      - reinvestigation: When re-investigation is requested
      - evidence_evaluation: Progress updates during evaluation
      - agent_started: When Judge begins processing
      - agent_completed: When Judge finishes processing

  Scenario: Detective dashboard displays verdict cards
    Given  the Judge has issued verdicts
    When   the detective dashboard receives verdict_issued events
    Then   it displays verdict cards with:
      - Claim text
      - Color-coded verdict badge (Verified/Unverified/Contradicted/Insufficient Evidence)
      - Cycle count if re-investigation occurred
      - IFRS paragraph tags

  Scenario: Judge handles agent errors gracefully
    Given  some specialist agents have errored (agent_status shows "error")
    When   the Judge evaluates evidence
    Then   it notes which agents failed in its assessment
    And    it evaluates whatever evidence is available
    And    it may adjust confidence downward if critical agents failed
    And    it includes agent error information in verdict reasoning

  Scenario: Judge handles re-investigation requests
    Given  the Judge receives a claim for re-investigation (iteration_count > 0)
    When   it evaluates the evidence
    Then   it focuses on the specific evidence gaps identified in previous cycles
    And    it checks if new findings address the gaps
    And    it produces an updated verdict or requests further re-investigation
```

---

## Table of Contents

1. [LangGraph Node Implementation](#1-langgraph-node-implementation)
2. [Evidence Evaluation Logic](#2-evidence-evaluation-logic)
3. [Cyclic Re-Investigation](#3-cyclic-re-investigation)
4. [Final Verdict Production](#4-final-verdict-production)
5. [Verdict-to-IFRS Paragraph Mapping](#5-verdict-to-ifrs-paragraph-mapping)
6. [Cross-Agent Evidence Synthesis](#6-cross-agent-evidence-synthesis)
7. [Conditional Edge Logic](#7-conditional-edge-logic)
8. [StreamEvent Emissions](#8-streamevent-emissions)
9. [Database Persistence](#9-database-persistence)
10. [Error Handling](#10-error-handling)
11. [Exit Criteria](#11-exit-criteria)
12. [Appendix A: Judge Agent System Prompt](#appendix-a-judge-agent-system-prompt)
13. [Appendix B: Evidence Evaluation Rubric](#appendix-b-evidence-evaluation-rubric)
14. [Appendix C: Example Verdicts](#appendix-c-example-verdicts)
15. [Appendix D: Re-Investigation Request Examples](#appendix-d-re-investigation-request-examples)
16. [Design Decisions Log](#design-decisions-log)

---

## 1. LangGraph Node Implementation

### 1.1 Overview

The Judge Agent (`app/agents/judge_agent.py`) replaces the FRD 5 stub with a functional LangGraph node. It is the final evaluative node in the pipeline, receiving all findings from specialist agents and producing final verdicts with cyclic re-investigation capability.

### 1.2 Node Function

```python
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

    Returns:
        Partial state update with verdicts, reinvestigation_requests, iteration_count, and events.
    """
```

### 1.3 Model Configuration

| Parameter | Value | Rationale |
|---|---|---|
| Model | `anthropic/claude-opus-4-5` (`Models.CLAUDE_OPUS`) | Highest-quality reasoning for nuanced judgment calls; ability to weigh contradictory evidence and make defensible final assessments (PRD Section 4.9) |
| Temperature | `0.1` | Very low temperature for deterministic, consistent judgments across similar evidence patterns |
| Max output tokens | `16384` | Sufficient for detailed verdict reasoning and re-investigation request generation covering multiple claims |
| Response format | JSON schema (structured output) | Ensures parseable verdicts and re-investigation requests |

### 1.4 Processing Steps

The `judge_evidence` node shall execute the following steps:

1. **Emit start event:** Append a `StreamEvent` with `event_type = "agent_started"`, `agent_name = "judge"`.

2. **Collect findings per claim:** Group `state.findings` by `claim_id` to create a mapping of each claim to all its findings from all specialist agents.

3. **Check agent status:** Review `state.agent_status` to identify which agents completed successfully vs. errored. This informs completeness evaluation.

4. **For each claim:**
   a. **Collect all findings:** Retrieve all `AgentFinding` objects for this claim from the grouped findings.
   b. **Evaluate evidence:** Perform four-dimensional evaluation (see Section 2).
   c. **Synthesize evidence:** Combine findings from multiple agents into a unified assessment (see Section 6).
   d. **Produce verdict:** Generate a `ClaimVerdict` based on evaluation results (see Section 4).
   e. **Map to IFRS:** Connect the verdict to relevant IFRS paragraphs (see Section 5).
   f. **Generate re-investigation request (if needed):** If evidence is insufficient and `iteration_count < max_iterations`, create a `ReinvestigationRequest` (see Section 3).
   g. **Emit verdict event:** Append a `StreamEvent` with `event_type = "verdict_issued"`.

5. **Increment iteration count:** If any re-investigation requests were generated, increment `state.iteration_count`.

6. **Emit re-investigation events:** For each `ReinvestigationRequest` generated, emit a `StreamEvent` with `event_type = "reinvestigation"`.

7. **Emit completion event:** Append a `StreamEvent` with `event_type = "agent_completed"`, `agent_name = "judge"`, including summary statistics.

8. **Return partial state:** Return updated `verdicts`, `reinvestigation_requests`, `iteration_count`, and `events`.

### 1.5 Agent Status Consideration

The Judge Agent considers `agent_status` when evaluating completeness:

```python
# Example: Check which agents completed
completed_agents = {
    name: status for name, status in state.agent_status.items()
    if status.status == "completed"
}

errored_agents = {
    name: status for name, status in state.agent_status.items()
    if status.status == "error"
}

# For a geographic claim, if Geography Agent errored:
if claim.claim_type == "geographic" and "geography" in errored_agents:
    completeness_score -= 0.3  # Significant gap
    verdict_reasoning += " Note: Geography Agent failed; satellite verification unavailable."
```

---

## 2. Evidence Evaluation Logic

### 2.1 Overview

The Judge Agent evaluates evidence across four dimensions: sufficiency, consistency, quality, and completeness. Each dimension contributes to the final verdict decision.

### 2.2 Sufficiency Evaluation

**Definition:** Whether there is enough evidence to reach a verdict; multiple independent sources corroborating the claim.

**Evaluation criteria:**

| Criterion | Score | Description |
|---|---|---|
| **Multiple independent sources** | High | 3+ agents with findings supporting the claim |
| **Two sources** | Medium | 2 agents with findings supporting the claim |
| **Single source** | Low | Only 1 agent found evidence |
| **No sources** | Very Low | Zero agents found evidence |

**Implementation:**

```python
def evaluate_sufficiency(findings: list[AgentFinding], claim: Claim) -> dict:
    """Evaluate whether evidence is sufficient for a verdict."""
    supporting_findings = [f for f in findings if f.supports_claim is True]
    contradicting_findings = [f for f in findings if f.supports_claim is False]
    inconclusive_findings = [f for f in findings if f.supports_claim is None]
    
    # Count independent sources (by agent)
    supporting_agents = set(f.agent_name for f in supporting_findings)
    contradicting_agents = set(f.agent_name for f in contradicting_findings)
    
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
        "supporting_agents": list(supporting_agents),
        "contradicting_agents": list(contradicting_agents),
        "has_contradictions": len(contradicting_agents) > 0,
    }
```

### 2.3 Consistency Evaluation

**Definition:** Whether findings from different agents align or contradict each other.

**Evaluation criteria:**

| Pattern | Consistency | Impact |
|---|---|---|
| **All agents support** | High | Strong consistency |
| **Most agents support, one contradicts** | Medium | Minor inconsistency |
| **Mixed support/contradiction** | Low | Significant inconsistency |
| **All agents contradict** | High (contradiction) | Consistent contradiction |

**Implementation:**

```python
def evaluate_consistency(findings: list[AgentFinding]) -> dict:
    """Evaluate consistency of findings across agents."""
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
        has_contradictions = False
    
    return {
        "consistency": consistency,
        "has_contradictions": has_contradictions,
        "support_ratio": support_ratio,
        "contradict_ratio": contradict_ratio,
        "support_counts": support_counts,
    }
```

### 2.4 Quality Evaluation

**Definition:** Whether sources are credible; whether evidence is direct or circumstantial.

**Evaluation criteria:**

| Source Type | Quality Indicator | Weight |
|---|---|---|
| **Geography Agent** | Satellite imagery (direct visual evidence) | High |
| **Legal Agent** | IFRS standard text (authoritative) | High |
| **News/Media Agent** | Tier 1 sources (investigative journalism, regulatory actions) | High |
| **News/Media Agent** | Tier 4 sources (blogs, social media) | Low |
| **Academic/Research Agent** | Peer-reviewed papers | High |
| **Academic/Research Agent** | Industry benchmarks | Medium |
| **Data/Metrics Agent** | Mathematical consistency (objective) | High |

**Implementation:**

```python
def evaluate_quality(findings: list[AgentFinding]) -> dict:
    """Evaluate quality of evidence sources."""
    quality_scores = []
    
    for finding in findings:
        agent_quality = {
            "geography": 0.9,  # Satellite imagery is direct evidence
            "legal": 0.95,     # IFRS standards are authoritative
            "news_media": 0.7, # Default; adjust by source tier
            "academic": 0.85,  # Peer-reviewed research
            "data_metrics": 0.9, # Mathematical consistency
        }.get(finding.agent_name, 0.5)
        
        # Adjust for source credibility (if available in details)
        if finding.agent_name == "news_media":
            source_tier = finding.details.get("source_tier", 3)
            tier_multiplier = {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.3}[source_tier]
            agent_quality *= tier_multiplier
        
        # Adjust for confidence
        confidence_multiplier = {
            "high": 1.0,
            "medium": 0.7,
            "low": 0.4,
        }.get(finding.confidence, 0.5)
        
        quality_score = agent_quality * confidence_multiplier
        quality_scores.append(quality_score)
    
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
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
```

### 2.5 Completeness Evaluation

**Definition:** Whether all relevant angles have been investigated; whether there is a domain that should have been consulted but was not.

**Evaluation criteria:**

| Claim Type | Expected Agents | Completeness Impact |
|---|---|---|
| **Geographic** | Geography (required), Legal (for IFRS mapping) | Missing Geography = major gap |
| **Quantitative** | Data/Metrics (required), Legal (for IFRS mapping) | Missing Data/Metrics = major gap |
| **Legal/Governance** | Legal (required) | Missing Legal = critical gap |
| **Strategic** | Legal, Academic/Research, News/Media | Missing multiple = moderate gap |
| **Environmental** | Academic/Research, Geography, Data/Metrics | Missing Academic = moderate gap |

**Implementation:**

```python
def evaluate_completeness(
    claim: Claim,
    findings: list[AgentFinding],
    agent_status: dict[str, AgentStatus]
) -> dict:
    """Evaluate whether all relevant domains have been investigated."""
    # Expected agents based on claim type
    expected_agents = {
        "geographic": ["geography", "legal"],
        "quantitative": ["data_metrics", "legal"],
        "legal_governance": ["legal"],
        "strategic": ["legal", "academic", "news_media"],
        "environmental": ["academic", "geography", "data_metrics"],
    }.get(claim.claim_type, ["legal"])  # Default: at least Legal
    
    # Agents that produced findings
    investigated_agents = set(f.agent_name for f in findings)
    
    # Agents that completed (not errored)
    completed_agents = {
        name for name, status in agent_status.items()
        if status.status == "completed"
    }
    
    # Missing agents (expected but no findings)
    missing_agents = set(expected_agents) - investigated_agents
    
    # Agents that errored (should have investigated but failed)
    errored_expected = set(expected_agents) & {
        name for name, status in agent_status.items()
        if status.status == "error"
    }
    
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
        "investigated_agents": list(investigated_agents),
        "missing_agents": list(missing_agents),
        "errored_agents": list(errored_expected),
    }
```

### 2.6 Combined Evaluation

The four dimensions are combined into an overall evidence assessment:

```python
def evaluate_evidence(
    claim: Claim,
    findings: list[AgentFinding],
    agent_status: dict[str, AgentStatus]
) -> dict:
    """Perform four-dimensional evidence evaluation."""
    sufficiency = evaluate_sufficiency(findings, claim)
    consistency = evaluate_consistency(findings)
    quality = evaluate_quality(findings)
    completeness = evaluate_completeness(claim, findings, agent_status)
    
    # Weighted combination (weights sum to 1.0)
    weights = {
        "sufficiency": 0.3,
        "consistency": 0.25,
        "quality": 0.25,
        "completeness": 0.2,
    }
    
    dimension_scores = {
        "sufficiency": {"high": 1.0, "medium": 0.6, "low": 0.3, "very_low": 0.0}[sufficiency["sufficiency"]],
        "consistency": {"high": 1.0, "medium": 0.6, "low": 0.3, "unclear": 0.5}[consistency["consistency"]],
        "quality": {"high": 1.0, "medium": 0.6, "low": 0.3}[quality["quality"]],
        "completeness": {"high": 1.0, "medium": 0.6, "low": 0.3}[completeness["completeness"]],
    }
    
    overall_score = sum(
        weights[dim] * score
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
```

---

## 3. Cyclic Re-Investigation

### 3.1 Overview

When evidence is insufficient, contradictory, or incomplete, the Judge generates `ReinvestigationRequest` objects that guide specialist agents to address specific evidence gaps. The conditional edge routes back to the Orchestrator, which re-routes the refined queries to the appropriate agents.

### 3.2 When to Request Re-Investigation

The Judge shall generate re-investigation requests when:

| Condition | Trigger | Example |
|---|---|---|
| **Insufficient evidence** | `overall_score < 0.6` AND `iteration_count < max_iterations` | Only one source found, need more corroboration |
| **Contradictions** | `consistency["has_contradictions"] = True` AND `iteration_count < max_iterations` | Geography supports, News contradicts; need resolution |
| **Missing agents** | `completeness["missing_agents"]` is non-empty AND `iteration_count < max_iterations` | Geographic claim but no Geography Agent finding |
| **Low quality sources** | `quality["quality"] = "low"` AND `iteration_count < max_iterations` | Only Tier 4 news sources; need higher-quality evidence |
| **Incomplete sub-requirements** | Legal Agent flags partial compliance AND `iteration_count < max_iterations` | Transition plan missing key assumptions |

### 3.3 ReinvestigationRequest Generation

```python
def generate_reinvestigation_request(
    claim: Claim,
    evaluation: dict,
    findings: list[AgentFinding],
    iteration_count: int
) -> ReinvestigationRequest | None:
    """Generate a re-investigation request if evidence is insufficient."""
    
    # Check if re-investigation is needed
    if evaluation["overall_score"] >= 0.7:
        return None  # Evidence is sufficient
    
    if iteration_count >= max_iterations:
        return None  # Max iterations reached
    
    # Identify evidence gaps
    evidence_gap = identify_evidence_gap(evaluation, findings)
    
    # Determine target agents
    target_agents = determine_target_agents(claim, evaluation, findings)
    
    # Generate refined queries
    refined_queries = generate_refined_queries(claim, evidence_gap, target_agents)
    
    # Specify required evidence
    required_evidence = specify_required_evidence(evidence_gap, target_agents)
    
    return ReinvestigationRequest(
        claim_id=claim.claim_id,
        target_agents=target_agents,
        evidence_gap=evidence_gap,
        refined_queries=refined_queries,
        required_evidence=required_evidence,
        cycle_number=iteration_count + 1,
    )
```

### 3.4 Evidence Gap Identification

```python
def identify_evidence_gap(evaluation: dict, findings: list[AgentFinding]) -> str:
    """Identify the specific evidence gap that needs to be addressed."""
    gaps = []
    
    if evaluation["sufficiency"]["sufficiency"] in ["low", "very_low"]:
        gaps.append(f"Insufficient sources: only {evaluation['sufficiency']['source_count']} agent(s) found evidence. Need multiple independent sources.")
    
    if evaluation["consistency"]["has_contradictions"]:
        gaps.append(f"Contradictions found: {evaluation['consistency']['contradicting_agents']} contradict while {evaluation['consistency']['supporting_agents']} support. Need resolution.")
    
    if evaluation["quality"]["quality"] == "low":
        gaps.append(f"Low-quality sources: average quality score {evaluation['quality']['avg_quality_score']:.2f}. Need higher-credibility sources.")
    
    if evaluation["completeness"]["missing_agents"]:
        gaps.append(f"Missing agent perspectives: {evaluation['completeness']['missing_agents']} should have investigated but did not.")
    
    return " ".join(gaps)
```

### 3.5 Target Agent Determination

```python
def determine_target_agents(
    claim: Claim,
    evaluation: dict,
    findings: list[AgentFinding]
) -> list[str]:
    """Determine which agents should re-investigate."""
    target_agents = []
    
    # If missing agents, prioritize them
    if evaluation["completeness"]["missing_agents"]:
        target_agents.extend(evaluation["completeness"]["missing_agents"])
    
    # If contradictions, re-investigate contradicting agents
    if evaluation["consistency"]["has_contradictions"]:
        # Re-investigate both supporting and contradicting agents for resolution
        target_agents.extend(evaluation["consistency"]["supporting_agents"])
        target_agents.extend(evaluation["consistency"]["contradicting_agents"])
    
    # If low quality, re-investigate low-quality source agents
    if evaluation["quality"]["quality"] == "low":
        low_quality_agents = [
            f.agent_name for f in findings
            if evaluation["quality"]["quality_scores"][findings.index(f)] < 0.5
        ]
        target_agents.extend(low_quality_agents)
    
    # If insufficient sources, add expected agents that didn't investigate
    if evaluation["sufficiency"]["sufficiency"] in ["low", "very_low"]:
        expected_agents = get_expected_agents_for_claim_type(claim.claim_type)
        missing_expected = set(expected_agents) - set(f.agent_name for f in findings)
        target_agents.extend(list(missing_expected))
    
    # Deduplicate
    return list(set(target_agents))
```

### 3.6 Refined Query Generation

```python
def generate_refined_queries(
    claim: Claim,
    evidence_gap: str,
    target_agents: list[str]
) -> list[str]:
    """Generate specific queries for re-investigation."""
    queries = []
    
    for agent in target_agents:
        if agent == "geography":
            queries.append(f"Verify geographic claim: '{claim.claim_text}'. Focus on satellite imagery analysis for the stated location and time period.")
        elif agent == "legal":
            queries.append(f"Re-assess IFRS compliance for: '{claim.claim_text}'. Check if all sub-requirements are addressed, especially those flagged as missing.")
        elif agent == "news_media":
            queries.append(f"Search for recent news coverage (prioritize Tier 1-2 sources) about: '{claim.claim_text}'. Look for corroboration or contradiction.")
        elif agent == "academic":
            queries.append(f"Validate technical claim against peer-reviewed research: '{claim.claim_text}'. Check methodology alignment with recognized standards.")
        elif agent == "data_metrics":
            queries.append(f"Re-verify quantitative claim for mathematical consistency: '{claim.claim_text}'. Check calculations, units, and benchmark plausibility.")
    
    return queries
```

### 3.7 Required Evidence Specification

```python
def specify_required_evidence(
    evidence_gap: str,
    target_agents: list[str]
) -> str:
    """Specify what would constitute sufficient evidence."""
    requirements = []
    
    if "geography" in target_agents:
        requirements.append("Satellite imagery showing the claimed location/condition with NDVI analysis and temporal comparison if applicable.")
    
    if "legal" in target_agents:
        requirements.append("IFRS paragraph-level compliance assessment with all sub-requirements addressed.")
    
    if "news_media" in target_agents:
        requirements.append("News coverage from Tier 1-2 sources (investigative journalism, regulatory actions) corroborating or contradicting the claim.")
    
    if "academic" in target_agents:
        requirements.append("Peer-reviewed research or recognized industry benchmarks validating the technical claim.")
    
    if "data_metrics" in target_agents:
        requirements.append("Mathematical consistency verification with benchmark comparison and unit validation.")
    
    return " ".join(requirements)
```

### 3.8 Iteration Depth Control

The system enforces the maximum iteration limit:

```python
# In judge_evidence node
if iteration_count >= state.max_iterations:
    # Do not generate re-investigation requests
    # Issue final verdicts even if evidence is insufficient
    for claim in claims:
        if not has_verdict(claim, state.verdicts):
            verdict = produce_final_verdict(claim, findings, evaluation)
            # Verdict may be "Insufficient Evidence" if overall_score < 0.6
            state.verdicts.append(verdict)
```

Default `max_iterations = 3` (configurable via `settings.MAX_JUDGE_ITERATIONS`).

---

## 4. Final Verdict Production

### 4.1 Overview

The Judge produces final verdicts based on evidence evaluation: Verified, Unverified, Contradicted, or Insufficient Evidence.

### 4.2 Verdict Decision Logic

```python
def produce_verdict(
    claim: Claim,
    evaluation: dict,
    findings: list[AgentFinding]
) -> ClaimVerdict:
    """Produce final verdict based on evidence evaluation."""
    
    overall_score = evaluation["overall_score"]
    has_contradictions = evaluation["consistency"]["has_contradictions"]
    source_count = evaluation["sufficiency"]["source_count"]
    
    # Decision tree
    if has_contradictions and evaluation["consistency"]["contradict_ratio"] > 0.5:
        verdict = "contradicted"
        reasoning = generate_contradiction_reasoning(evaluation, findings)
    
    elif source_count == 0:
        verdict = "unverified"
        reasoning = generate_unverified_reasoning(claim, findings)
    
    elif overall_score >= 0.7 and not has_contradictions:
        verdict = "verified"
        reasoning = generate_verified_reasoning(evaluation, findings)
    
    else:
        verdict = "insufficient_evidence"
        reasoning = generate_insufficient_reasoning(evaluation, findings)
    
    return ClaimVerdict(
        claim_id=claim.claim_id,
        verdict=verdict,
        reasoning=reasoning,
        ifrs_mapping=extract_ifrs_mapping(claim, findings),
        confidence=determine_confidence(overall_score, evaluation),
        iteration=state.iteration_count + 1,
    )
```

### 4.3 Verified Verdict

**Criteria:**
- `overall_score >= 0.7`
- `has_contradictions = False`
- `source_count >= 2`
- `quality["quality"] in ["high", "medium"]`

**Reasoning template:**
```
"Claim is VERIFIED. Multiple independent sources corroborate:
- {Agent1}: {finding1.summary}
- {Agent2}: {finding2.summary}
Evidence is consistent, high-quality, and sufficient. No contradictions found."
```

### 4.4 Unverified Verdict

**Criteria:**
- `source_count == 0`
- No findings from any specialist agent

**Reasoning template:**
```
"Claim is UNVERIFIED. No external evidence found by any specialist agent:
- Geography Agent: No satellite imagery available
- News/Media Agent: No public reporting found
- Legal Agent: No IFRS compliance assessment possible
- Academic/Research Agent: No research validation found
- Data/Metrics Agent: No quantitative verification possible
The claim cannot be independently verified."
```

### 4.5 Contradicted Verdict

**Criteria:**
- `has_contradictions = True`
- `contradict_ratio > 0.5` (more contradicting than supporting)

**Reasoning template:**
```
"Claim is CONTRADICTED. Evidence directly contradicts the claim:
- {ContradictingAgent1}: {contradicting_finding1.summary}
- {ContradictingAgent2}: {contradicting_finding2.summary}
Supporting evidence: {SupportingAgent}: {supporting_finding.summary}
The weight of contradicting evidence outweighs supporting evidence."
```

### 4.6 Insufficient Evidence Verdict

**Criteria:**
- `overall_score < 0.7`
- `source_count > 0` (some evidence exists)
- Not contradicted (contradictions would yield "Contradicted")

**Reasoning template:**
```
"Claim has INSUFFICIENT EVIDENCE. Some evidence exists but is not sufficient:
- {Issue1}: {description}
- {Issue2}: {description}
Evidence gaps: {evidence_gap}
Cannot reach a confident verdict with available evidence."
```

### 4.7 Confidence Assignment

```python
def determine_confidence(overall_score: float, evaluation: dict) -> str:
    """Determine confidence level for verdict."""
    if overall_score >= 0.8:
        return "high"
    elif overall_score >= 0.6:
        return "medium"
    else:
        return "low"
```

---

## 5. Verdict-to-IFRS Paragraph Mapping

### 5.1 Overview

Each verdict is mapped to specific IFRS S1/S2 paragraphs, creating paragraph-level compliance mapping for the Source of Truth report.

### 5.2 Mapping Sources

The Judge extracts IFRS mappings from:

1. **Claims Agent preliminary mappings:** `claim.ifrs_paragraphs` (from FRD 3)
2. **Legal Agent findings:** `finding.details["ifrs_mappings"]` (from FRD 6)

### 5.3 Mapping Extraction

```python
def extract_ifrs_mapping(
    claim: Claim,
    findings: list[AgentFinding]
) -> list[str]:
    """Extract IFRS paragraph mappings for a verdict."""
    ifrs_paragraphs = set()
    
    # From claim's preliminary mapping
    if claim.ifrs_paragraphs:
        ifrs_paragraphs.update(claim.ifrs_paragraphs)
    
    # From Legal Agent findings
    legal_findings = [f for f in findings if f.agent_name == "legal"]
    for finding in legal_findings:
        ifrs_mappings = finding.details.get("ifrs_mappings", [])
        for mapping in ifrs_mappings:
            paragraph_id = mapping.get("paragraph_id")
            if paragraph_id:
                ifrs_paragraphs.add(paragraph_id)
    
    return sorted(list(ifrs_paragraphs))
```

### 5.4 Verdict-IFRS Relationship

The verdict's relationship to IFRS paragraphs:

| Verdict | IFRS Relationship | Example |
|---|---|---|
| **Verified** | Claim meets IFRS requirements | "Transition plan claim verified; meets S2.14(a)(iv)" |
| **Unverified** | Cannot assess IFRS compliance (no evidence) | "Governance claim unverified; cannot assess S1.27(a) compliance" |
| **Contradicted** | Claim contradicts IFRS requirements or external evidence | "Emission reduction claim contradicted; does not meet S2.33 requirements" |
| **Insufficient Evidence** | IFRS compliance unclear (partial evidence) | "Risk management claim has insufficient evidence; S1.41 compliance unclear" |

### 5.5 Mapping Storage

IFRS mappings are stored in the `ClaimVerdict`:

```python
class ClaimVerdict(BaseModel):
    claim_id: str
    verdict: str  # "verified" | "unverified" | "contradicted" | "insufficient_evidence"
    reasoning: str
    ifrs_mapping: list[str]  # List of paragraph IDs, e.g., ["S2.14(a)(iv)", "S1.33"]
    confidence: str  # "high" | "medium" | "low"
    iteration: int
```

---

## 6. Cross-Agent Evidence Synthesis

### 6.1 Overview

The Judge synthesizes findings from multiple specialist agents into a unified assessment, weighing each agent's contribution based on relevance and quality.

### 6.2 Synthesis Strategy

```python
def synthesize_evidence(
    claim: Claim,
    findings: list[AgentFinding]
) -> dict:
    """Synthesize findings from multiple agents into unified assessment."""
    
    # Group findings by agent
    findings_by_agent = {}
    for finding in findings:
        agent = finding.agent_name
        if agent not in findings_by_agent:
            findings_by_agent[agent] = []
        findings_by_agent[agent].append(finding)
    
    # Weight findings by agent relevance
    agent_weights = get_agent_weights_for_claim_type(claim.claim_type)
    
    # Combine findings
    synthesized = {
        "supporting_evidence": [],
        "contradicting_evidence": [],
        "inconclusive_evidence": [],
        "agent_contributions": {},
    }
    
    for agent, agent_findings in findings_by_agent.items():
        weight = agent_weights.get(agent, 0.5)
        
        for finding in agent_findings:
            contribution = {
                "agent": agent,
                "finding": finding,
                "weight": weight,
            }
            
            if finding.supports_claim is True:
                synthesized["supporting_evidence"].append(contribution)
            elif finding.supports_claim is False:
                synthesized["contradicting_evidence"].append(contribution)
            else:
                synthesized["inconclusive_evidence"].append(contribution)
        
        synthesized["agent_contributions"][agent] = {
            "findings_count": len(agent_findings),
            "weight": weight,
            "primary_support": determine_primary_support(agent_findings),
        }
    
    return synthesized
```

### 6.3 Agent Weight Assignment

```python
def get_agent_weights_for_claim_type(claim_type: str) -> dict[str, float]:
    """Get agent relevance weights for a claim type."""
    weights = {
        "geographic": {
            "geography": 0.6,
            "legal": 0.2,
            "news_media": 0.1,
            "academic": 0.05,
            "data_metrics": 0.05,
        },
        "quantitative": {
            "data_metrics": 0.5,
            "legal": 0.3,
            "academic": 0.1,
            "news_media": 0.05,
            "geography": 0.05,
        },
        "legal_governance": {
            "legal": 0.7,
            "news_media": 0.15,
            "academic": 0.1,
            "geography": 0.03,
            "data_metrics": 0.02,
        },
        "strategic": {
            "legal": 0.4,
            "academic": 0.3,
            "news_media": 0.2,
            "data_metrics": 0.05,
            "geography": 0.05,
        },
        "environmental": {
            "academic": 0.4,
            "geography": 0.3,
            "data_metrics": 0.2,
            "legal": 0.05,
            "news_media": 0.05,
        },
    }
    
    return weights.get(claim_type, {
        "legal": 0.3,
        "academic": 0.2,
        "news_media": 0.2,
        "geography": 0.15,
        "data_metrics": 0.15,
    })
```

---

## 7. Conditional Edge Logic

### 7.1 Overview

The conditional edge `should_continue_or_compile` (defined in FRD 5) determines whether to route back to the Orchestrator for re-investigation or forward to `compile_report`.

### 7.2 Edge Function Implementation

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

### 7.3 Edge Activation

The conditional edge is activated after the Judge Agent completes:

```python
# In graph.py (FRD 5)
graph.add_conditional_edges(
    "judge_evidence",
    should_continue_or_compile,
    {
        "orchestrate": "orchestrate",
        "compile_report": "compile_report",
    }
)
```

### 7.4 Cycle Termination

The cycle terminates when:
1. **No re-investigation requests:** All claims have sufficient evidence
2. **Max iterations reached:** `iteration_count >= max_iterations` (default: 3)
3. **All claims have verdicts:** Every claim has been evaluated and issued a verdict

---

## 8. StreamEvent Emissions

### 8.1 Overview

The Judge Agent emits `StreamEvent` objects for the detective dashboard, enabling real-time visualization of verdicts and re-investigation cycles.

### 8.2 Event Types

| Event Type | Agent | Data Fields | When |
|---|---|---|---|
| `agent_started` | `judge` | `{}` | Node begins execution |
| `agent_thinking` | `judge` | `{"message": "..."}` | Progress updates during evaluation |
| `evidence_evaluation` | `judge` | `{"claim_id": "...", "evaluation_summary": "..."}` | Evidence evaluation completed for a claim |
| `verdict_issued` | `judge` | `{"claim_id": "...", "verdict": "...", "reasoning": "...", "ifrs_mapping": [...]}` | A verdict is produced |
| `reinvestigation` | `judge` | `{"claim_ids": [...], "target_agents": [...], "cycle": N, "evidence_gaps": [...]}` | Re-investigation requested |
| `agent_completed` | `judge` | `{"verdicts_count": N, "reinvestigation_requests": M, "iteration": K}` | Evaluation complete |

### 8.3 Verdict Issued Event

```python
StreamEvent(
    event_type="verdict_issued",
    agent_name="judge",
    data={
        "claim_id": claim.claim_id,
        "verdict": verdict.verdict,  # "verified" | "unverified" | "contradicted" | "insufficient_evidence"
        "reasoning": verdict.reasoning,
        "ifrs_mapping": verdict.ifrs_mapping,
        "confidence": verdict.confidence,
        "iteration": verdict.iteration,
        "cycle_count": state.iteration_count + 1,
    },
    timestamp=datetime.utcnow().isoformat()
)
```

### 8.4 Re-Investigation Event

```python
StreamEvent(
    event_type="reinvestigation",
    agent_name="judge",
    data={
        "claim_ids": [req.claim_id for req in reinvestigation_requests],
        "target_agents": list(set(
            agent for req in reinvestigation_requests
            for agent in req.target_agents
        )),
        "cycle": state.iteration_count + 1,
        "evidence_gaps": [req.evidence_gap for req in reinvestigation_requests],
        "refined_queries_count": sum(
            len(req.refined_queries) for req in reinvestigation_requests
        ),
    },
    timestamp=datetime.utcnow().isoformat()
)
```

### 8.5 Detective Dashboard Display

The detective dashboard (FRD 12) displays:
- **Verdict cards:** Each `verdict_issued` event creates a card with color-coded badge
- **Cycle count:** Shows iteration number if re-investigation occurred
- **IFRS tags:** Displays IFRS paragraph identifiers on each verdict card

---

## 9. Database Persistence

### 9.1 Overview

Verdicts and findings are persisted to the database by the `compile_report` node (FRD 13 stub in FRD 5, full implementation in FRD 13).

### 9.2 Verdict Persistence

```python
# In compile_report node (FRD 13)
for verdict in state.verdicts:
    db_verdict = Verdict(
        verdict_id=str(uuid4()),
        report_id=state.report_id,
        claim_id=verdict.claim_id,
        verdict=verdict.verdict,
        reasoning=verdict.reasoning,
        ifrs_mapping=verdict.ifrs_mapping,  # JSON array
        confidence=verdict.confidence,
        iteration=verdict.iteration,
        created_at=datetime.utcnow(),
    )
    db.add(db_verdict)
```

### 9.3 Finding Persistence

Findings are already persisted by specialist agents (FRDs 6-10). The Judge does not persist findings directly.

---

## 10. Error Handling

### 10.1 LLM Evaluation Errors

| Error | Trigger | Handling |
|---|---|---|
| LLM returns non-JSON | Claude Opus 4.5 fails structured output | Retry once with simplified prompt; if still non-JSON, parse free-text response with lenient extractor |
| LLM timeout | OpenRouter API timeout (>60 seconds) | Retry up to 3 times (handled by OpenRouter client); on failure, use rule-based verdict assignment |
| LLM rate limit | OpenRouter returns 429 | Exponential backoff retry (handled by OpenRouter client); propagate error after 3 retries |

### 10.2 Evidence Evaluation Errors

| Error | Trigger | Handling |
|---|---|---|
| No findings for claim | Claim has zero findings from any agent | Issue "Unverified" verdict with reasoning: "No evidence found by any specialist agent" |
| All agents errored | `agent_status` shows all agents as "error" | Issue "Unverified" verdict with reasoning noting agent failures |
| Invalid finding format | Finding missing required fields | Skip invalid finding; log warning; evaluate with available findings |

### 10.3 Re-Investigation Errors

| Error | Trigger | Handling |
|---|---|---|
| Max iterations reached | `iteration_count >= max_iterations` | Issue final verdicts (may be "Insufficient Evidence") without generating re-investigation requests |
| Invalid target agents | `target_agents` contains non-existent agent names | Filter out invalid agents; log warning; proceed with valid agents |

### 10.4 Graceful Degradation

If the Judge Agent encounters errors:

1. **Continue with available data:** Use rule-based verdict assignment if LLM fails
2. **Mark verdicts with low confidence:** Set `confidence = "low"` when evaluation is incomplete
3. **Emit error events:** Include error details in `StreamEvent` objects
4. **Issue final verdicts:** Even if evaluation is incomplete, issue verdicts to prevent pipeline stall

---

## 11. Exit Criteria

FRD 11 is complete when ALL of the following are satisfied:

| # | Criterion | Verification |
|---|---|---|
| 1 | Judge Agent node replaces FRD 5 stub | `judge_evidence` function is implemented and functional |
| 2 | Evidence evaluation works across four dimensions | Judge evaluates sufficiency, consistency, quality, completeness for test claims |
| 3 | Sufficiency evaluation works | Judge correctly identifies when evidence is sufficient vs. insufficient |
| 4 | Consistency evaluation works | Judge correctly identifies contradictions between agents |
| 5 | Quality evaluation works | Judge correctly assesses source credibility and evidence quality |
| 6 | Completeness evaluation works | Judge correctly identifies missing agent perspectives |
| 7 | Verified verdicts are produced | Claims with sufficient, consistent, high-quality evidence receive "Verified" verdicts |
| 8 | Unverified verdicts are produced | Claims with no evidence receive "Unverified" verdicts |
| 9 | Contradicted verdicts are produced | Claims with contradicting evidence receive "Contradicted" verdicts |
| 10 | Insufficient Evidence verdicts are produced | Claims with partial evidence receive "Insufficient Evidence" verdicts |
| 11 | Re-investigation requests are generated | Judge generates ReinvestigationRequests when evidence is insufficient |
| 12 | Refined queries are specific | Re-investigation requests include specific queries targeting evidence gaps |
| 13 | Target agents are correctly identified | Re-investigation requests target the right specialist agents |
| 14 | Cyclic validation loop works | Conditional edge routes back to Orchestrator when re-investigation is needed |
| 15 | Cycle terminates correctly | Conditional edge routes to compile_report when no re-investigation or max iterations reached |
| 16 | Iteration depth control works | System enforces max_iterations limit (default: 3) |
| 17 | Verdict-to-IFRS mapping works | Verdicts include IFRS paragraph mappings from claims and Legal Agent findings |
| 18 | Cross-agent evidence synthesis works | Judge combines findings from multiple agents with appropriate weights |
| 19 | StreamEvents are emitted | Judge emits verdict_issued, reinvestigation, evidence_evaluation events |
| 20 | Detective dashboard displays verdicts | Verdict cards appear in Judge Agent node with color-coded badges (FRD 12) |
| 21 | Agent status is considered | Judge notes errored agents in evaluation and adjusts completeness accordingly |
| 22 | Error handling is graceful | LLM failures, missing findings, and invalid data are handled without crashing |
| 23 | Performance is acceptable | Judge completes evaluation of 50 claims in under 2 minutes |
| 24 | End-to-end pipeline works | Complete pipeline runs: claims → routing → investigation → judging → verdicts |

---

## Appendix A: Judge Agent System Prompt

### A.1 System Prompt

```
You are the Judge Agent in Sibyl, an AI system that verifies sustainability reports against IFRS S1/S2 disclosure standards. Your task is to evaluate evidence gathered by specialist investigation agents and produce final verdicts for each claim.

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

3. **Re-Investigation:** When evidence is insufficient, generate specific re-investigation requests with:
   - Target agents that should re-investigate
   - Evidence gaps that need to be addressed
   - Refined queries for focused investigation
   - Required evidence specifications

4. **IFRS Mapping:** Connect each verdict to relevant IFRS S1/S2 paragraphs for compliance mapping.

## Evidence Evaluation Rubric

See Appendix B for detailed evaluation criteria.

## Output Format

Return a JSON object with:
- `verdicts`: Array of verdict objects (claim_id, verdict, reasoning, ifrs_mapping, confidence)
- `reinvestigation_requests`: Array of re-investigation requests (if evidence is insufficient)
- `evaluation_summary`: Summary of evidence evaluation across all claims
```

### A.2 User Prompt Template

```
Evaluate evidence for the following claims and produce final verdicts.

Claims and Findings:
{claims_and_findings_json}

Agent Status:
{agent_status_json}

Current Iteration: {iteration_count}
Max Iterations: {max_iterations}

For each claim:
1. Collect all findings from all specialist agents
2. Evaluate evidence across four dimensions (sufficiency, consistency, quality, completeness)
3. Produce a verdict: Verified, Unverified, Contradicted, or Insufficient Evidence
4. Map the verdict to relevant IFRS paragraphs
5. If evidence is insufficient and iteration < max_iterations, generate a re-investigation request

Return your evaluation as a JSON object matching the specified schema.
```

---

## Appendix B: Evidence Evaluation Rubric

### B.1 Sufficiency Rubric

| Score | Criteria | Verdict Impact |
|---|---|---|
| **High** | 3+ independent sources supporting | Strong support for Verified |
| **Medium** | 2 sources supporting | Supports Verified if consistent |
| **Low** | 1 source supporting | Likely Insufficient Evidence |
| **Very Low** | 0 sources | Unverified |

### B.2 Consistency Rubric

| Pattern | Consistency | Verdict Impact |
|---|---|---|
| All agents support | High | Verified |
| Most support, one contradicts | Medium | Verified (minor inconsistency noted) |
| Mixed support/contradiction | Low | Contradicted or Insufficient Evidence |
| All contradict | High (contradiction) | Contradicted |

### B.3 Quality Rubric

| Source Type | Quality | Weight |
|---|---|---|
| Satellite imagery (Geography) | High | 0.9 |
| IFRS standards (Legal) | High | 0.95 |
| Tier 1 news (News/Media) | High | 0.9 |
| Tier 4 news (News/Media) | Low | 0.3 |
| Peer-reviewed research (Academic) | High | 0.85 |
| Mathematical consistency (Data/Metrics) | High | 0.9 |

### B.4 Completeness Rubric

| Claim Type | Expected Agents | Missing Impact |
|---|---|---|
| Geographic | Geography, Legal | Missing Geography = -0.3 score |
| Quantitative | Data/Metrics, Legal | Missing Data/Metrics = -0.3 score |
| Legal/Governance | Legal | Missing Legal = -0.5 score |
| Strategic | Legal, Academic, News/Media | Missing multiple = -0.2 per agent |

---

## Appendix C: Example Verdicts

### C.1 Verified Verdict

```json
{
  "claim_id": "claim-123",
  "verdict": "verified",
  "reasoning": "Claim is VERIFIED. Multiple independent sources corroborate:\n- Geography Agent: Satellite imagery from 2024 shows dense forest cover consistent with reforestation claim (NDVI 0.72, +60% increase from 2020).\n- Legal Agent: Transition plan disclosure meets S2.14(a)(iv) requirements (key assumptions, dependencies, timeline all present).\n- Academic/Research Agent: Reforestation methodology aligns with peer-reviewed best practices.\nEvidence is consistent, high-quality, and sufficient. No contradictions found.",
  "ifrs_mapping": ["S2.14(a)(iv)", "S1.33", "S2.13"],
  "confidence": "high",
  "iteration": 1
}
```

### C.2 Unverified Verdict

```json
{
  "claim_id": "claim-456",
  "verdict": "unverified",
  "reasoning": "Claim is UNVERIFIED. No external evidence found by any specialist agent:\n- Geography Agent: No satellite imagery available for the stated location/time period.\n- News/Media Agent: No public reporting found about this claim.\n- Legal Agent: Cannot assess IFRS compliance without supporting evidence.\n- Academic/Research Agent: No research validation found.\n- Data/Metrics Agent: No quantitative verification possible.\nThe claim cannot be independently verified.",
  "ifrs_mapping": ["S1.27(a)"],
  "confidence": "high",
  "iteration": 1
}
```

### C.3 Contradicted Verdict

```json
{
  "claim_id": "claim-789",
  "verdict": "contradicted",
  "reasoning": "Claim is CONTRADICTED. Evidence directly contradicts the claim:\n- News/Media Agent (Tier 1): Investigative journalism reports regulatory action against the company for emissions violations, contradicting the claimed 30% reduction.\n- Data/Metrics Agent: Mathematical analysis shows reported figures are inconsistent with claimed reduction percentage.\nSupporting evidence: Legal Agent notes IFRS compliance, but this does not override contradicting factual evidence.\nThe weight of contradicting evidence outweighs supporting evidence.",
  "ifrs_mapping": ["S2.33", "S2.29(a)(i)"],
  "confidence": "high",
  "iteration": 1
}
```

### C.4 Insufficient Evidence Verdict

```json
{
  "claim_id": "claim-012",
  "verdict": "insufficient_evidence",
  "reasoning": "Claim has INSUFFICIENT EVIDENCE. Some evidence exists but is not sufficient:\n- Legal Agent: Partial IFRS compliance (transition plan mentioned but missing key assumptions).\n- News/Media Agent: Only Tier 4 sources (blogs) mention the claim; no Tier 1-2 sources found.\nEvidence gaps: Only 1 source found; low-quality sources; missing Geography Agent perspective.\nCannot reach a confident verdict with available evidence.",
  "ifrs_mapping": ["S2.14(a)(iv)"],
  "confidence": "medium",
  "iteration": 1
}
```

---

## Appendix D: Re-Investigation Request Examples

### D.1 Insufficient Sources Request

```json
{
  "claim_id": "claim-345",
  "target_agents": ["geography", "news_media"],
  "evidence_gap": "Insufficient sources: only 1 agent (Legal) found evidence. Need multiple independent sources. Missing Geography Agent perspective for geographic claim.",
  "refined_queries": [
    "Geography Agent: Verify geographic claim: 'Our Borneo facility reduced deforestation by 50% since 2020.' Focus on satellite imagery analysis for Borneo, Indonesia, comparing 2020 vs. 2024 NDVI values.",
    "News/Media Agent: Search for recent news coverage (prioritize Tier 1-2 sources) about deforestation reduction in Borneo. Look for corroboration or contradiction."
  ],
  "required_evidence": "Satellite imagery showing deforestation reduction with NDVI analysis and temporal comparison. News coverage from Tier 1-2 sources (investigative journalism, regulatory actions) corroborating or contradicting the claim.",
  "cycle_number": 2
}
```

### D.2 Contradiction Resolution Request

```json
{
  "claim_id": "claim-678",
  "target_agents": ["news_media", "data_metrics"],
  "evidence_gap": "Contradictions found: News/Media Agent contradicts while Legal Agent supports. Need resolution. Low-quality sources: average quality score 0.45. Need higher-credibility sources.",
  "refined_queries": [
    "News/Media Agent: Re-search for Tier 1-2 sources (investigative journalism, regulatory filings) about emission reduction claim. Previous search found only Tier 4 sources.",
    "Data/Metrics Agent: Re-verify quantitative claim for mathematical consistency: 'Reduced emissions by 30% from 2020 baseline.' Check calculations, units, and benchmark plausibility. Resolve inconsistency with News/Media findings."
  ],
  "required_evidence": "News coverage from Tier 1-2 sources (investigative journalism, regulatory actions) corroborating or contradicting the claim. Mathematical consistency verification with benchmark comparison and unit validation.",
  "cycle_number": 2
}
```

### D.3 Missing Sub-Requirements Request

```json
{
  "claim_id": "claim-901",
  "target_agents": ["legal"],
  "evidence_gap": "Incomplete sub-requirements: Transition plan mentioned but missing key assumptions and dependencies required by S2.14(a)(iv).",
  "refined_queries": [
    "Legal Agent: Re-assess IFRS compliance for transition plan claim. Check if all sub-requirements are addressed, especially key assumptions and dependencies. Search report content directly (not just claims) for missing information."
  ],
  "required_evidence": "IFRS paragraph-level compliance assessment with all sub-requirements addressed, including key assumptions and dependencies for transition plan.",
  "cycle_number": 2
}
```

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| Claude Opus 4.5 for Judge over Claude Sonnet 4.5 | PRD Section 4.9 specifies Claude Opus 4.5 for "highest-quality reasoning for nuanced judgment calls." Judge Agent makes final, defensible assessments that require the highest reasoning quality. Sonnet 4.5 is used for specialist agents; Opus 4.5 is reserved for the critical judgment task. |
| Four-dimensional evaluation (sufficiency, consistency, quality, completeness) over single score | Evidence assessment is multi-faceted. A single score would lose nuance. Four dimensions enable targeted re-investigation (e.g., "need more sources" vs. "need higher-quality sources"). The dimensions align with PRD Section 4.9's evaluation criteria. |
| Weighted combination of dimensions over equal weighting | Sufficiency (0.3) and consistency (0.25) are more critical than completeness (0.2). Quality (0.25) is important but secondary to having enough consistent sources. Weighted combination reflects the relative importance of each dimension. |
| ReinvestigationRequest generation over immediate verdict | PRD Section 4.9 specifies "the Judge does not issue a premature verdict" when evidence is insufficient. Re-investigation enables thorough investigation before final judgment. This prevents false negatives (unverified when evidence exists but wasn't found) and false positives (verified with weak evidence). |
| Max iterations default 3 over unlimited or 1 | Unlimited iterations risk infinite loops. 1 iteration prevents re-investigation, reducing thoroughness. 3 iterations balances thoroughness with efficiency. Configurable via settings allows adjustment per use case. |
| Verdict-to-IFRS mapping from claims + Legal Agent findings over Judge-only mapping | Claims Agent provides preliminary mappings; Legal Agent provides authoritative compliance assessments. Judge synthesizes these rather than re-doing IFRS analysis, avoiding duplication and leveraging specialist expertise. |
| Conditional edge routing based on reinvestigation_requests AND iteration_count over just requests | Prevents infinite loops by enforcing max_iterations. Even if re-investigation requests exist, the cycle terminates after max_iterations. This ensures pipeline completion even if evidence remains insufficient. |
| Agent status consideration in completeness evaluation over ignoring errors | If Geography Agent errored for a geographic claim, completeness is low even if other agents investigated. Ignoring agent errors would overstate evidence completeness. Agent status provides critical context for evaluation. |
| Cross-agent evidence synthesis with weights over equal weighting | Different agents have different relevance per claim type. Geography Agent is more relevant for geographic claims than Academic Agent. Weighted synthesis reflects agent relevance, improving verdict accuracy. |
| Structured output (JSON schema) from Judge over free-text | Verdicts and re-investigation requests must be parseable for downstream processing (compile_report, Orchestrator re-routing). Free-text would require complex parsing and be error-prone. Structured output ensures reliability. |
| Verdict reasoning includes agent citations over generic reasoning | PRD Section 4.11 specifies verdicts should show "which agents contributed evidence." Including agent names and finding summaries in reasoning provides transparency and traceability. Users can see exactly which agents supported or contradicted each claim. |
| Detective dashboard verdict cards with cycle count over simple badges | PRD Section 4.10 specifies "verdict cards... with color-coded badges and cycle counts." Cycle count shows how many re-investigation cycles occurred, indicating investigation thoroughness. This provides visibility into the cyclic validation process. |
| Insufficient Evidence as separate verdict over forcing Verified/Unverified | Some claims have partial evidence that doesn't meet the threshold for Verified but isn't zero (Unverified). Insufficient Evidence accurately represents this state. Forcing binary Verified/Unverified would misrepresent evidence quality. |
| Re-investigation request includes required_evidence specification over just queries | Required_evidence helps specialist agents understand what would constitute sufficient evidence, guiding their investigation focus. This improves re-investigation effectiveness compared to generic queries alone. |
| Iteration count incremented only when re-investigation requests generated over always incrementing | Iteration count tracks investigation cycles, not just Judge invocations. If no re-investigation is needed (evidence is sufficient), the iteration count shouldn't increment. This accurately reflects the cyclic validation process. |
| Confidence levels (high/medium/low) over binary confidence | Verdict confidence has degrees. A verdict based on 3 high-quality sources has higher confidence than one based on 1 medium-quality source. Confidence levels provide nuance for downstream use (e.g., Source of Truth report filtering). |
| Evidence evaluation uses LLM reasoning over pure rule-based | Evidence evaluation requires nuanced judgment (e.g., "is this contradiction severe enough to override supporting evidence?"). Rule-based logic cannot capture this nuance. LLM reasoning enables sophisticated evidence synthesis. |
| Verdicts persisted by compile_report over Judge directly | Centralizing persistence in compile_report ensures all verdicts are persisted together with findings and report metadata. Judge focuses on evaluation; compile_report handles output compilation. This separation of concerns improves maintainability. |

---
