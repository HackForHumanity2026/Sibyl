# Feature Requirements Document: FRD 6 -- Legal Agent (v1.0)

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.3](../PRD.md) |
| **FRD Order** | [FRD Order](../FRD-order.md) |
| **PRD Sections** | 4.5 (Legal Agent -- Compliance and Governance) |
| **Type** | Feature |
| **Depends On** | FRD 1 (RAG Pipeline), FRD 5 (Orchestrator Agent & LangGraph Pipeline) |
| **Delivers** | IFRS compliance mapping, disclosure gap detection, paragraph-level IFRS analysis, inter-agent communication participation, LangGraph node implementation |
| **Created** | 2026-02-09 |

---

## Summary

FRD 6 delivers the Legal Agent -- a specialist investigation agent in the Sibyl multi-agent pipeline that investigates legal, regulatory, and governance-related claims against IFRS S1/S2 requirements and related standards. The Legal Agent (`app/agents/legal_agent.py`) replaces the FRD 5 stub with a functional LangGraph node that receives routed claims from the Orchestrator (FRD 5), performs RAG retrieval against the IFRS S1/S2 and SASB knowledge base (FRD 1), and produces paragraph-level IFRS compliance mappings. The agent investigates governance claims (S1.26-27, S2.5-7), risk management claims (S1.38-42, S2.24-26), strategic claims (S2.14), and metrics claims (S2.27-37), assessing whether disclosed content meets the specific requirements of each IFRS paragraph. Beyond evaluating present claims, the Legal Agent performs disclosure gap detection: a systematic coverage analysis comparing the full set of IFRS S1/S2 disclosure requirements (at the paragraph level) against the report's content, flagging paragraphs that are fully unaddressed (zero corresponding content) or partially addressed (topic mentioned but specific sub-requirements missing). The agent participates in inter-agent communication (InfoRequest/InfoResponse) via the Orchestrator, enabling cross-domain collaboration when geographic verification, quantitative validation, or news corroboration would strengthen its compliance assessment. The Legal Agent uses Claude Sonnet 4.5 for legal reasoning and regulatory interpretation. After FRD 6, routed legal/governance claims receive paragraph-level IFRS compliance mappings, and the system produces a comprehensive disclosure gap analysis distinguishing fully unaddressed and partially addressed IFRS requirements.

---

## Given Context (Preconditions)

The following are assumed to be in place from prior FRDs:

| Prerequisite | Source FRD | Deliverable |
|---|---|---|
| Docker Compose with PostgreSQL 17 + pgvector, Redis, backend, frontend | FRD 0 | `docker-compose.yml` |
| `SibylState` Pydantic schema with `Claim`, `AgentFinding`, `InfoRequest`, `InfoResponse`, `StreamEvent` types | FRD 0 | `app/agents/state.py` |
| LangGraph StateGraph compiled with all nodes including `investigate_legal` stub | FRD 5 | `app/agents/graph.py` |
| Legal Agent stub (`investigate_legal` function signature) | FRD 5 | `app/agents/legal_agent.py` |
| RAG pipeline with hybrid search, `rag_lookup` tool, IFRS/SASB corpus ingested | FRD 1 | `app/services/rag_service.py`, `app/agents/tools/rag_lookup.py` |
| IFRS S1/S2 standard texts chunked and embedded in pgvector | FRD 1 | `data/ifrs/s1_full.md`, `s2_full.md`, embeddings table |
| SASB industry standards chunked and embedded | FRD 1 | `data/sasb/`, embeddings table |
| S1/S2 cross-reference mapping (`s1_s2_mapping.json`) | FRD 1 | `data/ifrs/s1_s2_mapping.json` |
| Orchestrator routing logic assigning legal/governance claims to Legal Agent | FRD 5 | `app/agents/orchestrator_agent.py` |
| Inter-agent communication protocol (InfoRequest/InfoResponse) | FRD 5 | `SibylState.info_requests`, `SibylState.info_responses` |
| SSE streaming infrastructure with callback handler | FRD 5 | `app/agents/callbacks.py`, `app/api/routes/stream.py` |
| OpenRouter client wrapper with `Models.CLAUDE_SONNET` constant | FRD 0 | `app/services/openrouter_client.py` |
| Claims extracted with preliminary IFRS mappings | FRD 3 | `claims` database table |
| Report content chunked and embedded in RAG | FRD 2 | `embeddings` table with `source_type = "report"` |
| `AgentFinding` schema with `agent_name`, `claim_id`, `evidence_type`, `summary`, `details`, `supports_claim`, `confidence` | FRD 0 | `app/agents/state.py` |

### Terms

| Term | Definition |
|---|---|
| Paragraph-level mapping | A precise mapping of a claim to a specific IFRS paragraph identifier (e.g., S2.14(a)(iv)), including assessment of whether the claim meets the paragraph's sub-requirements |
| Disclosure gap | An IFRS S1/S2 paragraph requirement that has no corresponding content in the report (fully unaddressed) or is only partially covered (partially addressed) |
| Fully unaddressed | An IFRS paragraph requirement with zero corresponding content in the report -- the topic is completely absent |
| Partially addressed | An IFRS paragraph requirement where the report touches on the topic but fails to meet specific sub-requirements (e.g., mentions a transition plan but omits key assumptions required by S2.14(a)(iv)) |
| Compliance assessment | The Legal Agent's evaluation of whether a disclosed claim meets the specific requirements of its mapped IFRS paragraph(s) |
| IFRS paragraph registry | A comprehensive checklist of all IFRS S1/S2 disclosure requirements at the paragraph level, used for gap detection |
| Sub-requirement | A specific element within an IFRS paragraph that must be disclosed (e.g., S2.14(a)(iv) requires key assumptions, dependencies, and timeline for transition plans) |
| Coverage analysis | The systematic comparison of the full IFRS requirement set against the report's content to identify gaps |

---

## Executive Summary (Gherkin-Style)

```gherkin
Feature: Legal Agent

  Background:
    Given  FRD 1, FRD 3, and FRD 5 are complete
    And    all services are running (backend, frontend, PostgreSQL, Redis)
    And    the IFRS/SASB corpus has been ingested into the RAG pipeline
    And    claims have been extracted from a sustainability report
    And    the Orchestrator has routed legal/governance claims to the Legal Agent

  Scenario: Legal Agent investigates routed claims
    Given  the Legal Agent receives routed claims from the Orchestrator
    When   it processes each claim
    Then   it performs RAG retrieval against IFRS S1/S2 and SASB knowledge base
    And    it produces paragraph-level IFRS compliance mappings
    And    it assesses whether each claim meets the specific requirements of its mapped paragraphs
    And    it generates findings with compliance verdicts and evidence

  Scenario: Paragraph-level IFRS mapping
    Given  a claim about governance oversight
    When   the Legal Agent investigates it
    Then   it maps the claim to specific IFRS paragraphs (e.g., S1.27(a)(iii), S2.5)
    And    it checks whether the claim meets sub-requirements (e.g., reporting frequency, competencies)
    And    it produces a finding with paragraph identifiers and compliance assessment

  Scenario: Governance claims investigation
    Given  claims related to board oversight, committee responsibilities, or remuneration links
    When   the Legal Agent investigates them
    Then   it retrieves relevant IFRS S1.26-27 and S2.5-7 paragraphs
    And    it assesses compliance with governance disclosure requirements
    And    it flags missing elements (e.g., competencies not disclosed, reporting frequency unclear)

  Scenario: Risk management claims investigation
    Given  claims about risk identification, assessment, or monitoring processes
    When   the Legal Agent investigates them
    Then   it retrieves relevant IFRS S1.38-42 and S2.24-26 paragraphs
    And    it assesses whether risk management disclosures meet the requirements
    And    it checks for integration with overall risk management (S1.41(d), S2.26)

  Scenario: Strategic claims investigation
    Given  claims about transition plans, resource allocation, or climate strategy
    When   the Legal Agent investigates them
    Then   it retrieves relevant IFRS S2.14 paragraphs (especially S2.14(a)(iv) for transition plans)
    And    it checks for required elements: key assumptions, dependencies, timeline
    And    it assesses whether strategic disclosures meet S2.14 sub-requirements

  Scenario: Metrics claims investigation
    Given  claims about GHG emissions, targets, or climate metrics
    When   the Legal Agent investigates them
    Then   it retrieves relevant IFRS S2.27-37 paragraphs
    And    it checks for required granularity (e.g., Scope 3 by category per S2.29(a)(iii))
    And    it assesses methodology alignment and disclosure completeness

  Scenario: Disclosure gap detection
    Given  the Legal Agent has investigated all routed claims
    When   it performs coverage analysis
    Then   it compares the full IFRS S1/S2 requirement set against the report's content
    And    it identifies paragraphs with zero corresponding content (fully unaddressed)
    And    it identifies paragraphs where content exists but sub-requirements are missing (partially addressed)
    And    it produces a disclosure gap analysis with gap severity and materiality context

  Scenario: Inter-agent communication
    Given  the Legal Agent needs geographic verification of a facility claim
    When   it posts an InfoRequest to the shared state
    Then   the Orchestrator routes the request to the Geography Agent
    And    the Geography Agent responds with satellite evidence
    And    the Legal Agent incorporates the evidence into its compliance assessment

  Scenario: Legal Agent emits findings
    Given  the Legal Agent completes its investigation
    When   it produces findings
    Then   each finding includes: claim_id, agent_name="legal", evidence_type, summary, details, supports_claim, confidence
    And    findings are written to the shared state
    And    findings are streamed to the frontend via SSE events
    And    findings are persisted to the database

  Scenario: Handle re-investigation requests
    Given  the Judge Agent requests re-investigation with refined queries
    When   the Legal Agent receives the re-investigation context
    Then   it focuses its investigation on the specific evidence gaps identified
    And    it performs targeted RAG retrieval based on the Judge's guidance
    And    it produces updated findings addressing the gaps
```

---

## Table of Contents

1. [Legal Agent Node Implementation](#1-legal-agent-node-implementation)
2. [RAG Retrieval Strategy](#2-rag-retrieval-strategy)
3. [Paragraph-Level IFRS Mapping](#3-paragraph-level-ifrs-mapping)
4. [Compliance Assessment](#4-compliance-assessment)
5. [Disclosure Gap Detection](#5-disclosure-gap-detection)
6. [IFRS Paragraph Registry](#6-ifrs-paragraph-registry)
7. [Investigation by Claim Type](#7-investigation-by-claim-type)
8. [Inter-Agent Communication](#8-inter-agent-communication)
9. [Re-Investigation Handling](#9-re-investigation-handling)
10. [Finding Generation](#10-finding-generation)
11. [StreamEvent Emissions](#11-streamevent-emissions)
12. [Error Handling](#12-error-handling)
13. [Exit Criteria](#13-exit-criteria)
14. [Appendix A: Legal Agent Investigation Prompt](#appendix-a-legal-agent-investigation-prompt)
15. [Appendix B: IFRS Paragraph Registry Structure](#appendix-b-ifrs-paragraph-registry-structure)
16. [Appendix C: Disclosure Gap Detection Algorithm](#appendix-c-disclosure-gap-detection-algorithm)
17. [Appendix D: Example Findings](#appendix-d-example-findings)
18. [Design Decisions Log](#design-decisions-log)

---

## 1. Legal Agent Node Implementation

### 1.1 Overview

The Legal Agent (`app/agents/legal_agent.py`) replaces the FRD 5 stub with a functional LangGraph node. It is a specialist investigation agent that evaluates legal, regulatory, and governance-related claims against IFRS S1/S2 requirements, producing paragraph-level compliance mappings and disclosure gap analysis.

### 1.2 Node Function

```python
async def investigate_legal(state: SibylState) -> dict:
    """Legal Agent: Investigate legal/governance claims against IFRS S1/S2.

    Reads: state.routing_plan, state.claims, state.report_id,
           state.info_responses, state.reinvestigation_requests
    Writes: state.findings, state.events, state.info_requests

    Responsibilities:
    1. Identify claims assigned to the Legal Agent from routing_plan
    2. For each claim, perform RAG retrieval against IFRS/SASB corpus
    3. Map claims to specific IFRS paragraphs (paragraph-level precision)
    4. Assess compliance: does the claim meet the paragraph's requirements?
    5. Perform disclosure gap detection: compare full IFRS set against report content
    6. Generate findings with compliance verdicts and evidence
    7. Participate in inter-agent communication when cross-domain context is needed

    Returns:
        Partial state update with findings, events, and info_requests.
    """
```

### 1.3 Model Configuration

| Parameter | Value | Rationale |
|---|---|---|
| Model | `anthropic/claude-sonnet-4-5` (`Models.CLAUDE_SONNET`) | Excellent legal and compliance reasoning; strong at interpreting regulatory language and assessing nuanced governance structures (PRD Section 4.5) |
| Temperature | `0.2` | Slightly higher than Orchestrator (0.1) to allow nuanced interpretation of regulatory language while maintaining consistency |
| Max output tokens | `16384` | Sufficient for detailed compliance assessments and gap analysis covering multiple paragraphs |
| Response format | JSON schema (structured output) | Ensures parseable findings and gap analysis output |

### 1.4 Processing Steps

The `investigate_legal` node shall execute the following steps:

1. **Emit start event:** Append a `StreamEvent` with `event_type = "agent_started"`, `agent_name = "legal"`.

2. **Identify assigned claims:** Filter `state.claims` to find claims where the Legal Agent is in the `assigned_agents` list of the corresponding `RoutingAssignment` in `state.routing_plan`.

3. **Check for re-investigation context:** If `state.reinvestigation_requests` contains requests targeting the Legal Agent, load the refined queries and evidence gaps. Otherwise, proceed with standard investigation.

4. **For each assigned claim:**
   a. **RAG retrieval:** Query the RAG pipeline for relevant IFRS paragraphs (see Section 2).
   b. **Paragraph mapping:** Map the claim to specific IFRS paragraph identifiers (see Section 3).
   c. **Compliance assessment:** Evaluate whether the claim meets the paragraph's requirements (see Section 4).
   d. **Generate finding:** Create an `AgentFinding` with compliance verdict and evidence (see Section 10).

5. **Disclosure gap detection:** After processing all claims, perform systematic coverage analysis (see Section 5).

6. **Inter-agent communication:** If cross-domain context is needed (e.g., geographic verification, quantitative validation), post `InfoRequest` objects (see Section 8).

7. **Emit completion event:** Append a `StreamEvent` with `event_type = "agent_completed"`, `agent_name = "legal"`, including summary statistics.

8. **Return partial state:** Return updated `findings`, `events`, `info_requests`, and `agent_status`.

### 1.5 Agent Status Management

The Legal Agent updates its status in `state.agent_status`:

- **Before processing:** Set `status = "working"`, `claims_assigned = len(assigned_claims)`, `claims_completed = 0`.
- **During processing:** Increment `claims_completed` as each claim is investigated.
- **After completion:** Set `status = "completed"`, `claims_completed = len(assigned_claims)`.

---

## 2. RAG Retrieval Strategy

### 2.1 Overview

The Legal Agent uses the `rag_lookup` tool (FRD 1) to retrieve relevant IFRS S1/S2 paragraphs and SASB standards for each claim. The retrieval strategy is optimized for paragraph-level precision and compliance assessment.

### 2.2 Retrieval Modes

The system shall support three retrieval modes:

| Mode | Use Case | Query Strategy |
|---|---|---|
| **Claim-scoped retrieval** | Initial investigation of a claim | Query with claim text, filter to `source_types=["ifrs_s1", "ifrs_s2"]`, `top_k=5` |
| **Paragraph-specific lookup** | When a paragraph ID is known (from preliminary mapping) | Use `paragraph_id` parameter to retrieve exact paragraph |
| **SASB industry lookup** | For industry-specific metrics and topics | Query with claim text + industry sector, filter to `source_types=["sasb"]` |

### 2.3 Query Construction

For claim-scoped retrieval, the system shall construct queries that:

1. **Include claim text:** The verbatim claim text provides the primary semantic signal.
2. **Include claim type:** Append claim type context (e.g., "governance claim", "metrics claim") to guide retrieval.
3. **Include preliminary IFRS hints:** If the claim has preliminary IFRS mappings from FRD 3, include paragraph IDs in the query to boost exact matches.
4. **Include pillar context:** For governance claims, append "IFRS S1 governance S2.5-7"; for metrics, append "IFRS S2 metrics S2.27-37".

**Example query construction:**

```python
# For a governance claim with preliminary mapping to S1.27
query = f"{claim.claim_text} governance claim IFRS S1.26-27 S2.5-7 {preliminary_paragraph_ids}"

# For a metrics claim about Scope 3 emissions
query = f"{claim.claim_text} metrics claim Scope 3 emissions IFRS S2.29(a)(iii) S2.27-37"
```

### 2.4 Hybrid Search Configuration

| Parameter | Value | Rationale |
|---|---|---|
| `mode` | `"hybrid"` | Combines semantic similarity (for meaning-based matching) with keyword search (for paragraph ID terms like "S2.14(a)(iv)", "Scope 3") |
| `top_k` | `5` | Sufficient to surface the most relevant paragraphs without noise; multiple paragraphs may be relevant for complex claims |
| `source_types` | `["ifrs_s1", "ifrs_s2"]` or `["sasb"]` | Restrict to IFRS corpus for compliance assessment; SASB for industry-specific validation |
| `rrf_k` | `60` | Default RRF constant from FRD 1 |

### 2.5 Result Processing

After RAG retrieval, the system shall:

1. **Extract paragraph IDs:** Parse `chunk_metadata.paragraph_id` from each result.
2. **Deduplicate:** If multiple results map to the same paragraph ID, keep the highest-scoring result.
3. **Validate relevance:** Filter results where `score < 0.3` (low relevance threshold) unless the paragraph ID matches a preliminary mapping (exact match overrides low score).
4. **Sort by relevance:** Order results by score (descending) and paragraph hierarchy (more specific paragraphs first, e.g., S2.14(a)(iv) before S2.14).

---

## 3. Paragraph-Level IFRS Mapping

### 3.1 Overview

The Legal Agent produces precise paragraph-level mappings, identifying specific IFRS paragraph identifiers (e.g., S2.14(a)(iv)) and assessing whether claims meet the paragraph's sub-requirements.

### 3.2 Mapping Process

For each claim, the system shall:

1. **Retrieve relevant paragraphs:** Use RAG retrieval (Section 2) to find IFRS paragraphs semantically related to the claim.
2. **Parse paragraph structure:** Extract paragraph identifiers, sub-requirements, and requirement text from RAG results.
3. **Map to specific paragraphs:** Identify which paragraph(s) the claim addresses, with paragraph-level precision (not just pillar-level).
4. **Identify sub-requirements:** For each mapped paragraph, extract the specific sub-requirements (e.g., S2.14(a)(iv) requires: key assumptions, dependencies, timeline).
5. **Assess coverage:** Determine which sub-requirements are addressed by the claim and which are missing.

### 3.3 Paragraph Identifier Format

IFRS paragraph identifiers follow this structure:

- **Top-level paragraphs:** `S1.26`, `S2.14`
- **Sub-paragraphs:** `S1.27(a)`, `S2.14(a)(iv)`
- **Nested sub-requirements:** `S1.27(a)(ii)(1)`, `S2.29(a)(iii)`

The system shall parse and validate paragraph identifiers using a regex pattern:

```python
IFRS_PARAGRAPH_PATTERN = re.compile(
    r'^S[12]\.\d+([a-z]?)(\([a-z]\))?(\([ivx]+\))?(\([0-9]+\))?$'
)
```

### 3.4 Mapping Output Format

Each claim's IFRS mapping shall be stored in the finding's `details` field as:

```json
{
  "ifrs_mappings": [
    {
      "paragraph_id": "S2.14(a)(iv)",
      "pillar": "strategy",
      "section": "Decision-Making",
      "requirement_text": "An entity shall disclose its transition plan, including information about: key assumptions used in developing its transition plan; dependencies on which the entity's transition plan relies;...",
      "sub_requirements": [
        {
          "requirement": "key assumptions",
          "addressed": true,
          "evidence": "The report states: 'Our transition plan assumes a 2.5% annual GDP growth rate and carbon price of $75/tCO2e by 2030.'"
        },
        {
          "requirement": "dependencies",
          "addressed": false,
          "evidence": null,
          "gap_reason": "The report mentions a transition plan but does not disclose dependencies on which the plan relies."
        },
        {
          "requirement": "timeline",
          "addressed": true,
          "evidence": "The report includes a timeline showing milestones through 2050."
        }
      ],
      "compliance_status": "partially_addressed",
      "s1_counterpart": "S1.33"
    }
  ]
}
```

### 3.5 Multi-Paragraph Mapping

A single claim may map to multiple IFRS paragraphs. For example, a governance claim about board oversight may map to both S1.27(a) (general governance) and S2.5 (climate-specific governance). The system shall:

1. Identify all relevant paragraphs from RAG results.
2. Assess compliance for each paragraph independently.
3. Include all mappings in the finding's `details.ifrs_mappings` array.
4. Set the finding's `supports_claim` based on the overall compliance status (if all paragraphs are fully addressed, `supports_claim = true`; if any are partially or unaddressed, `supports_claim = false` or `null`).

---

## 4. Compliance Assessment

### 4.1 Overview

Compliance assessment evaluates whether a disclosed claim meets the specific requirements of its mapped IFRS paragraph(s). The assessment considers both the presence of required elements and the quality/completeness of disclosure.

### 4.2 Assessment Criteria

For each mapped IFRS paragraph, the system shall assess:

| Criterion | Description | Example |
|---|---|---|
| **Presence** | Is the required topic/content present in the claim? | Does the claim mention a transition plan? (required by S2.14(a)(iv)) |
| **Completeness** | Are all sub-requirements addressed? | Does the transition plan include key assumptions, dependencies, and timeline? |
| **Specificity** | Is the disclosure specific enough to meet the requirement? | Does "we have a transition plan" meet S2.14(a)(iv), or is more detail required? |
| **Methodology alignment** | For metrics, does the methodology align with IFRS requirements? | Does Scope 3 calculation follow GHG Protocol as required by S2.29(a)(iii)? |
| **Granularity** | Does the disclosure meet the required level of detail? | Are Scope 3 emissions disclosed by category as required by S2.29(a)(iii)? |

### 4.3 Compliance Status Values

Each mapped paragraph shall receive a compliance status:

| Status | Meaning | Finding Impact |
|---|---|---|
| **fully_addressed** | The claim meets all sub-requirements of the paragraph | `supports_claim = true`, `confidence = "high"` |
| **partially_addressed** | The claim addresses the topic but misses specific sub-requirements | `supports_claim = null` (uncertain), `confidence = "medium"` |
| **not_addressed** | The claim does not address the paragraph requirement | `supports_claim = false`, `confidence = "high"` |
| **unclear** | The claim's relationship to the paragraph is ambiguous | `supports_claim = null`, `confidence = "low"` |

### 4.4 LLM-Based Assessment

The compliance assessment uses Claude Sonnet 4.5 to:

1. **Parse paragraph requirements:** Extract sub-requirements from the retrieved IFRS paragraph text.
2. **Compare against claim:** Analyze whether the claim text addresses each sub-requirement.
3. **Generate assessment:** Produce structured output with compliance status, evidence citations, and gap descriptions.

The system shall construct a prompt (see Appendix A) that includes:
- The claim text
- The IFRS paragraph text and metadata
- Sub-requirements extracted from the paragraph
- Instructions for compliance assessment
- Output schema for structured assessment

### 4.5 Evidence Extraction

For each sub-requirement, the system shall extract:

1. **Evidence text:** The specific portion of the claim (or surrounding report content) that addresses the requirement.
2. **Gap description:** If a sub-requirement is not addressed, a description of what is missing.
3. **Confidence:** A confidence level (high/medium/low) for the assessment.

---

## 5. Disclosure Gap Detection

### 5.1 Overview

Disclosure gap detection performs a systematic coverage analysis comparing the full set of IFRS S1/S2 disclosure requirements (at the paragraph level) against the report's content. This addresses the *selective disclosure* form of greenwashing by detecting what a report chose not to say.

### 5.2 Gap Detection Process

The system shall:

1. **Load IFRS paragraph registry:** Retrieve the complete list of IFRS S1/S2 paragraphs from the registry (see Section 6).
2. **For each paragraph in the registry:**
   a. **Check claim coverage:** Search `state.claims` for claims mapped to this paragraph (via preliminary mappings or Legal Agent findings).
   b. **Check report content coverage:** Query the RAG pipeline with `source_types=["report"]` and `report_id=state.report_id` to find report chunks mentioning the paragraph topic.
   c. **Assess coverage:** Determine if the paragraph is fully addressed, partially addressed, or fully unaddressed.
3. **Generate gap findings:** Create `AgentFinding` objects for each identified gap (see Section 5.4).

### 5.3 Coverage Assessment Logic

For each IFRS paragraph, coverage is assessed as follows:

```python
def assess_paragraph_coverage(paragraph_id: str, claims: list[Claim], report_chunks: list[RAGResult]) -> str:
    """Assess whether an IFRS paragraph is covered in the report.
    
    Returns: "fully_addressed" | "partially_addressed" | "fully_unaddressed"
    """
    # Check if any claim maps to this paragraph
    relevant_claims = [c for c in claims if paragraph_id in get_mapped_paragraphs(c)]
    
    # Check if report content mentions this paragraph topic
    relevant_chunks = [chunk for chunk in report_chunks if is_relevant_to_paragraph(chunk, paragraph_id)]
    
    if not relevant_claims and not relevant_chunks:
        return "fully_unaddressed"
    
    # If content exists, check completeness
    if relevant_claims:
        # Assess compliance of mapped claims
        compliance_statuses = [get_compliance_status(c, paragraph_id) for c in relevant_claims]
        if all(s == "fully_addressed" for s in compliance_statuses):
            return "fully_addressed"
        elif any(s == "partially_addressed" for s in compliance_statuses):
            return "partially_addressed"
    
    # If only report chunks (no explicit claim mapping), check if they cover sub-requirements
    if relevant_chunks and not relevant_claims:
        # Use LLM to assess whether chunks meet paragraph requirements
        return assess_chunk_coverage(relevant_chunks, paragraph_id)
    
    return "partially_addressed"  # Default: content exists but completeness unclear
```

### 5.4 Gap Finding Generation

For each identified gap, the system shall create an `AgentFinding`:

```python
gap_finding = AgentFinding(
    finding_id=str(uuid4()),
    agent_name="legal",
    claim_id=None,  # Gap findings are not tied to a specific claim
    evidence_type="disclosure_gap",
    summary=f"IFRS {paragraph_id} requirement is {gap_status}",
    details={
        "paragraph_id": paragraph_id,
        "pillar": paragraph.pillar,
        "section": paragraph.section,
        "requirement_text": paragraph.requirement_text,
        "gap_status": gap_status,  # "fully_unaddressed" | "partially_addressed"
        "missing_sub_requirements": [...],  # If partially_addressed
        "materiality_context": "...",  # Why this gap matters
    },
    supports_claim=False,  # Gaps indicate non-compliance
    confidence="high",
    iteration=state.iteration_count + 1,
)
```

### 5.5 Materiality Context

Each gap finding shall include a materiality context explaining why the omission matters:

- **For fully unaddressed gaps:** Explain what the requirement mandates and why its absence is significant (e.g., "Scope 3 emissions typically represent the majority of a company's total GHG footprint; omitting them understates climate exposure").
- **For partially addressed gaps:** Explain which sub-requirements are missing and why they are critical (e.g., "Transition plan mentions timeline but omits key assumptions and dependencies, making it impossible to assess plan credibility").

The materiality context is generated by Claude Sonnet 4.5 based on the paragraph requirement text and industry context.

### 5.6 Gap Detection Scope

The gap detection shall cover:

- **All S1 paragraphs:** S1.26-27 (Governance), S1.28-35 (Strategy), S1.38-42 (Risk Management), S1.43-53 (Metrics & Targets)
- **All S2 paragraphs:** S2.5-7 (Governance), S2.8-12 (Risks/Opportunities), S2.13 (Business Model), S2.14 (Decision-Making), S2.15-21 (Financial Effects), S2.22 (Climate Resilience), S2.24-26 (Risk Management), S2.27-31 (GHG Emissions), S2.33-36 (Targets)

The system shall NOT flag gaps for:
- Appendices and application guidance (informative, not mandatory)
- Industry-based guidance (optional enhancements)
- Paragraphs that are explicitly not applicable (e.g., S2.29(e) internal carbon pricing for entities without carbon pricing)

---

## 6. IFRS Paragraph Registry

### 6.1 Overview

The IFRS paragraph registry is a comprehensive checklist of all IFRS S1/S2 disclosure requirements at the paragraph level. It is used for systematic gap detection and ensures complete coverage analysis.

### 6.2 Registry Structure

The registry shall be stored as a JSON file (`data/ifrs/paragraph_registry.json`) with the following structure:

```json
{
  "paragraphs": [
    {
      "paragraph_id": "S2.14(a)(iv)",
      "standard": "S2",
      "pillar": "strategy",
      "section": "Decision-Making",
      "requirement_text": "An entity shall disclose its transition plan, including information about: key assumptions used in developing its transition plan; dependencies on which the entity's transition plan relies;...",
      "sub_requirements": [
        {
          "requirement": "key assumptions",
          "required": true,
          "description": "The key assumptions used in developing the transition plan (e.g., economic growth, carbon price, technology availability)"
        },
        {
          "requirement": "dependencies",
          "required": true,
          "description": "Dependencies on which the entity's transition plan relies (e.g., policy support, market conditions, technology deployment)"
        },
        {
          "requirement": "timeline",
          "required": true,
          "description": "The timeline for achieving transition plan objectives"
        }
      ],
      "s1_counterpart": "S1.33",
      "materiality_note": "Transition plans are critical for assessing an entity's climate strategy credibility. Missing assumptions or dependencies makes it impossible to evaluate plan feasibility.",
      "applicability": "all_entities"
    }
  ]
}
```

### 6.3 Registry Population

The registry shall be populated from:

1. **IFRS standard texts:** Parse `data/ifrs/s1_full.md` and `s2_full.md` to extract paragraph identifiers and requirement text.
2. **Sub-requirement extraction:** Use Claude Sonnet 4.5 to extract sub-requirements from paragraph text (one-time parsing during setup).
3. **S1/S2 mapping:** Enrich S2 paragraphs with their S1 counterparts from `s1_s2_mapping.json`.
4. **Materiality notes:** Generate materiality context for each paragraph (one-time LLM pass).

The registry is static (does not change per report) and is loaded once during Legal Agent initialization or on first use.

### 6.4 Registry Usage

The Legal Agent uses the registry to:

1. **Gap detection:** Iterate through all paragraphs to check coverage.
2. **Sub-requirement validation:** Compare claim content against registered sub-requirements.
3. **Materiality context:** Include materiality notes in gap findings.

---

## 7. Investigation by Claim Type

### 7.1 Governance Claims (S1.26-27, S2.5-7)

**Investigation focus:**
- Board oversight structures (S1.27(a), S2.5)
- Competencies and expertise (S1.27(a)(ii), S2.6)
- Reporting frequency (S1.27(a)(iii), S2.6)
- Integration with strategy and risk decisions (S1.27(a)(iv), S2.6)
- Remuneration links (S1.27(a)(v), S2.7)
- Management's role and controls (S1.27(b))

**RAG query strategy:**
- Query: `"{claim_text} governance claim IFRS S1.26-27 S2.5-7 board oversight competencies"`
- Filter: `source_types=["ifrs_s1", "ifrs_s2"]`
- Focus paragraphs: S1.27(a), S1.27(a)(ii), S1.27(a)(iii), S1.27(a)(iv), S1.27(a)(v), S2.5, S2.6, S2.7

**Compliance checks:**
- Is the governance body/individual identified? (S1.27(a))
- Are competencies disclosed? (S1.27(a)(ii))
- Is reporting frequency stated? (S1.27(a)(iii))
- Is integration with strategy/risk described? (S1.27(a)(iv))
- Is remuneration link disclosed? (S1.27(a)(v), S2.7)

### 7.2 Risk Management Claims (S1.38-42, S2.24-26)

**Investigation focus:**
- Risk identification processes (S1.41(a), S2.25(a))
- Risk assessment and prioritization (S1.41(b), S2.25(b))
- Risk monitoring (S1.41(c), S2.25(c))
- Integration with overall risk management (S1.41(d), S2.26)
- Changes from prior period (S1.42)

**RAG query strategy:**
- Query: `"{claim_text} risk management claim IFRS S1.38-42 S2.24-26 risk identification assessment"`
- Filter: `source_types=["ifrs_s1", "ifrs_s2"]`
- Focus paragraphs: S1.41(a), S1.41(b), S1.41(c), S1.41(d), S2.25(a), S2.25(b), S2.25(c), S2.26

**Compliance checks:**
- Are risk identification processes described? (S1.41(a), S2.25(a))
- Are assessment and prioritization methods disclosed? (S1.41(b), S2.25(b))
- Is monitoring described? (S1.41(c), S2.25(c))
- Is integration with overall risk management explained? (S1.41(d), S2.26)

### 7.3 Strategic Claims (S2.14)

**Investigation focus:**
- Resource allocation changes (S2.14(a)(i))
- Direct mitigation/adaptation (S2.14(a)(ii))
- Indirect mitigation (S2.14(a)(iii))
- Transition plan with assumptions and dependencies (S2.14(a)(iv))
- Plans to achieve targets (S2.14(a)(v))
- Resourcing (S2.14(b))
- Progress on prior plans (S2.14(c))

**RAG query strategy:**
- Query: `"{claim_text} strategy claim transition plan IFRS S2.14 decision-making resource allocation"`
- Filter: `source_types=["ifrs_s2"]`
- Focus paragraphs: S2.14(a)(i), S2.14(a)(ii), S2.14(a)(iii), S2.14(a)(iv), S2.14(a)(v), S2.14(b), S2.14(c)

**Compliance checks:**
- For transition plans (S2.14(a)(iv)): Are key assumptions disclosed? Dependencies? Timeline?
- For resource allocation (S2.14(a)(i)): Are changes described with specificity?
- For target achievement (S2.14(a)(v)): Are plans detailed enough to assess feasibility?

### 7.4 Metrics Claims (S2.27-37)

**Investigation focus:**
- Scope 1 GHG emissions (S2.29(a)(i))
- Scope 2 GHG emissions (S2.29(a)(ii))
- Scope 3 GHG emissions by category (S2.29(a)(iii))
- Total GHG emissions (S2.29(a))
- Measurement approach and inputs (S2.30)
- Disaggregation by constituent gas (S2.30)
- Consolidation approach (S2.31)
- Emission intensity (S2.28)
- Climate targets (S2.33-36)
- Internal carbon pricing (S2.29(e))
- Climate-linked remuneration (S2.29(g))

**RAG query strategy:**
- Query: `"{claim_text} metrics claim GHG emissions Scope IFRS S2.27-37 S2.29"`
- Filter: `source_types=["ifrs_s2"]`
- Focus paragraphs: S2.29(a)(i), S2.29(a)(ii), S2.29(a)(iii), S2.30, S2.31, S2.33-36

**Compliance checks:**
- Are Scope 1, 2, 3 disclosed separately? (S2.29(a)(i), (ii), (iii))
- Are Scope 3 emissions disclosed by category? (S2.29(a)(iii))
- Is measurement methodology described? (S2.30)
- Are targets disclosed with baseline, milestones, progress? (S2.33-36)

---

## 8. Inter-Agent Communication

### 8.1 Overview

The Legal Agent participates in the inter-agent communication protocol (FRD 5) to request cross-domain context when it would strengthen compliance assessment.

### 8.2 When to Request Information

The Legal Agent shall post `InfoRequest` objects when:

1. **Geographic verification needed:** A governance claim mentions a specific facility or location that should be verified (e.g., "Our Sustainability Committee oversees operations at our Singapore facility").
2. **Quantitative validation needed:** A metrics claim needs mathematical consistency checking (e.g., "Scope 1 + Scope 2 + Scope 3 = Total").
3. **News corroboration needed:** A governance or compliance claim should be verified against public reporting (e.g., "We have received ISO 14001 certification").
4. **Academic validation needed:** A methodology claim needs validation against recognized standards (e.g., "Our Scope 3 calculation follows GHG Protocol").

### 8.3 InfoRequest Format

```python
info_request = InfoRequest(
    request_id=str(uuid4()),
    requesting_agent="legal",
    description="Verify that the Singapore facility mentioned in governance claim {claim_id} exists and matches reported location coordinates.",
    context={
        "claim_id": claim.claim_id,
        "facility_name": "Singapore facility",
        "location_hint": "Singapore",
    },
    status="pending",
    timestamp=datetime.utcnow().isoformat(),
)
```

### 8.4 Processing InfoResponses

When the Legal Agent receives `InfoResponse` objects (routed by the Orchestrator):

1. **Match to request:** Find the corresponding `InfoRequest` by `request_id` or context matching.
2. **Incorporate evidence:** Add the response data to the claim's finding `details` as cross-domain evidence.
3. **Update compliance assessment:** If the response contradicts or supports the claim, update the compliance status accordingly.
4. **Emit event:** Emit a `StreamEvent` with `event_type = "info_response_received"` describing how the response influenced the assessment.

---

## 9. Re-Investigation Handling

### 9.1 Overview

When the Judge Agent requests re-investigation with refined queries (FRD 11), the Legal Agent receives `ReinvestigationRequest` objects with specific evidence gaps and guidance.

### 9.2 Re-Investigation Context

The `ReinvestigationRequest` includes:

```python
class ReinvestigationRequest(BaseModel):
    claim_id: str
    evidence_gap: str  # What specific evidence is missing
    refined_queries: list[str]  # Specific questions to investigate
    required_evidence: str | None  # What would constitute sufficient evidence
    cycle_number: int  # Current iteration count
```

### 9.3 Re-Investigation Process

When processing a re-investigation request:

1. **Load the original claim:** Retrieve the claim from `state.claims`.
2. **Focus on the gap:** Use `refined_queries` to perform targeted RAG retrieval.
3. **Deep dive:** If the gap is about missing sub-requirements, query the report content directly (not just claims) to see if the information exists elsewhere.
4. **Generate updated finding:** Create a new finding that addresses the specific gap, referencing the original finding and explaining what additional investigation was performed.

### 9.4 Example Re-Investigation

**Original finding:** "Claim mentions transition plan but compliance status is unclear -- missing key assumptions."

**Re-investigation request:**
```python
ReinvestigationRequest(
    claim_id="claim-123",
    evidence_gap="Transition plan lacks key assumptions required by S2.14(a)(iv)",
    refined_queries=[
        "Does the report disclose key assumptions for the transition plan anywhere?",
        "Search report content for 'transition plan assumptions' or 'carbon price assumptions'",
    ],
    required_evidence="Specific assumptions (e.g., carbon price, GDP growth) used in developing the transition plan",
    cycle_number=2,
)
```

**Re-investigation process:**
1. Query RAG with `source_types=["report"]` and query: "transition plan assumptions carbon price GDP growth".
2. If found, update finding: "Key assumptions found in report page 23: 'Our transition plan assumes $75/tCO2e carbon price by 2030.' Compliance status updated to partially_addressed."
3. If not found, confirm gap: "No key assumptions found in report. Gap confirmed: fully_unaddressed for S2.14(a)(iv) key assumptions sub-requirement."

---

## 10. Finding Generation

### 10.1 Finding Schema

Each `AgentFinding` produced by the Legal Agent shall include:

```python
finding = AgentFinding(
    finding_id=str(uuid4()),
    agent_name="legal",
    claim_id=claim.claim_id,  # None for gap findings
    evidence_type="ifrs_compliance" | "disclosure_gap",
    summary="Brief summary of the compliance assessment or gap",
    details={
        "ifrs_mappings": [...],  # See Section 3.4
        "compliance_status": "fully_addressed" | "partially_addressed" | "not_addressed" | "unclear",
        "evidence": [...],  # Extracted evidence text
        "gaps": [...],  # Missing sub-requirements if partially_addressed
        "materiality_context": "...",  # For gap findings
    },
    supports_claim=True | False | None,  # True if compliant, False if non-compliant, None if unclear
    confidence="high" | "medium" | "low",
    iteration=state.iteration_count + 1,
)
```

### 10.2 Finding Types

| Finding Type | `evidence_type` | `claim_id` | `supports_claim` | Use Case |
|---|---|---|---|---|
| **Claim compliance** | `"ifrs_compliance"` | Present | True/False/None | Assessment of a specific claim against IFRS |
| **Disclosure gap** | `"disclosure_gap"` | None | False | IFRS requirement not addressed in the report |

### 10.3 Summary Generation

The finding `summary` shall be a concise (1-2 sentence) description:

- **For claim compliance:** "Claim about {topic} maps to {paragraph_id}. Compliance status: {status}. {Brief reason}."
- **For disclosure gaps:** "IFRS {paragraph_id} requirement is {gap_status}. {Materiality note}."

Examples:
- "Claim about transition plan maps to S2.14(a)(iv). Compliance status: partially_addressed. Missing key assumptions and dependencies."
- "IFRS S2.29(a)(iii) requirement (Scope 3 emissions by category) is fully_unaddressed. Scope 3 emissions typically represent the majority of a company's total GHG footprint."

### 10.4 Confidence Assignment

| Confidence | Criteria |
|---|---|
| **High** | Clear evidence for or against compliance; all sub-requirements assessed; RAG retrieval returned high-scoring results |
| **Medium** | Some evidence but ambiguity remains; partial sub-requirement coverage; RAG results are moderate relevance |
| **Low** | Unclear relationship between claim and IFRS paragraph; insufficient evidence; RAG retrieval returned low-scoring results |

---

## 11. StreamEvent Emissions

### 11.1 Event Types

The Legal Agent emits the following `StreamEvent` types:

| Event Type | Agent | Data | When |
|---|---|---|---|
| `agent_started` | `legal` | `{}` | Node begins execution |
| `agent_thinking` | `legal` | `{"message": "..."}` | Progress updates during investigation |
| `evidence_found` | `legal` | `{"claim_id": "...", "paragraph_id": "...", "compliance_status": "..."}` | A compliance assessment is completed for a claim |
| `disclosure_gap_found` | `legal` | `{"paragraph_id": "...", "gap_status": "..."}` | A disclosure gap is identified |
| `info_request_posted` | `legal` | `{"requesting_agent": "legal", "description": "..."}` | Agent posts a cross-domain request |
| `info_response_received` | `legal` | `{"responding_agent": "...", "summary": "..."}` | Agent receives a response to its request |
| `agent_completed` | `legal` | `{"claims_processed": N, "findings_count": M, "gaps_found": K}` | Investigation complete |

### 11.2 Thinking Messages

Example `agent_thinking` messages:

- "Investigating {N} governance claims against IFRS S1.26-27 and S2.5-7..."
- "Retrieving IFRS paragraphs for claim about transition plan..."
- "Assessing compliance with S2.14(a)(iv) sub-requirements: key assumptions, dependencies, timeline..."
- "Performing disclosure gap analysis: checking {N} IFRS paragraphs against report content..."
- "Found disclosure gap: S2.29(a)(iii) (Scope 3 emissions by category) is fully_unaddressed."

### 11.3 IFRS Coverage Progress

For the detective dashboard (FRD 12), the Legal Agent emits progress events showing IFRS coverage by pillar:

```python
StreamEvent(
    event_type="ifrs_coverage_update",
    agent_name="legal",
    data={
        "pillar": "governance",
        "paragraphs_covered": 12,
        "paragraphs_total": 15,
        "paragraphs_gaps": 3,
        "coverage_percentage": 80.0,
    },
    timestamp=datetime.utcnow().isoformat(),
)
```

This enables the dashboard to display IFRS coverage progress bars per pillar (green for covered, orange for partial, grey for gaps).

---

## 12. Error Handling

### 12.1 RAG Retrieval Errors

| Error | Trigger | Handling |
|---|---|---|
| RAG service unavailable | Database connection failure | Skip RAG retrieval; use preliminary IFRS mappings from FRD 3; log error; set `confidence = "low"` |
| Embedding API failure | OpenRouter embedding endpoint error | Retry up to 3 times (handled by OpenRouter client); on failure, skip RAG and use preliminary mappings |
| No RAG results | Query returns zero results | Use preliminary IFRS mappings; set `confidence = "medium"`; log warning |

### 12.2 LLM Assessment Errors

| Error | Trigger | Handling |
|---|---|---|
| LLM returns non-JSON | Claude Sonnet 4.5 fails structured output | Retry once with simplified prompt; if still non-JSON, parse free-text response with lenient extractor |
| LLM timeout | OpenRouter API timeout (>60 seconds) | Retry up to 3 times (handled by OpenRouter client); on failure, mark claim as `"unclear"` compliance status |
| LLM rate limit | OpenRouter returns 429 | Exponential backoff retry (handled by OpenRouter client); propagate error after 3 retries |

### 12.3 Gap Detection Errors

| Error | Trigger | Handling |
|---|---|---|
| Registry load failure | `paragraph_registry.json` not found or malformed | Fall back to RAG-based gap detection: query IFRS corpus for all paragraph IDs, then check coverage |
| Coverage assessment timeout | Gap detection takes >5 minutes | Process gaps in batches; emit progress events; continue processing remaining gaps asynchronously |

### 12.4 Graceful Degradation

If the Legal Agent encounters errors:

1. **Continue with available data:** Use preliminary IFRS mappings from FRD 3 if RAG fails.
2. **Mark findings with low confidence:** Set `confidence = "low"` when assessment is incomplete.
3. **Emit error events:** Include error details in `StreamEvent` objects for frontend display.
4. **Partial gap detection:** If full gap detection fails, at least flag gaps for claims that were successfully investigated.

---

## 13. Exit Criteria

FRD 6 is complete when ALL of the following are satisfied:

| # | Criterion | Verification |
|---|---|---|
| 1 | Legal Agent node replaces FRD 5 stub | `investigate_legal` function is implemented and functional |
| 2 | RAG retrieval works for IFRS paragraphs | Legal Agent successfully retrieves relevant IFRS paragraphs for test claims |
| 3 | Paragraph-level mapping is precise | Claims are mapped to specific paragraph IDs (e.g., S2.14(a)(iv)), not just pillar-level |
| 4 | Compliance assessment works | Legal Agent assesses whether claims meet paragraph sub-requirements |
| 5 | Governance claims are investigated | Claims about board oversight, competencies, remuneration are assessed against S1.26-27, S2.5-7 |
| 6 | Risk management claims are investigated | Claims about risk processes are assessed against S1.38-42, S2.24-26 |
| 7 | Strategic claims are investigated | Claims about transition plans are assessed against S2.14, especially S2.14(a)(iv) |
| 8 | Metrics claims are investigated | Claims about emissions are assessed against S2.27-37 |
| 9 | Disclosure gap detection works | Legal Agent identifies IFRS paragraphs with zero or partial coverage in the report |
| 10 | Fully unaddressed gaps are flagged | Gaps where paragraph has zero corresponding content are identified |
| 11 | Partially addressed gaps are flagged | Gaps where topic is mentioned but sub-requirements are missing are identified |
| 12 | Gap findings include materiality context | Each gap finding explains why the omission matters |
| 13 | Findings are generated correctly | Each finding includes: claim_id (or None for gaps), evidence_type, summary, details, supports_claim, confidence |
| 14 | Findings are written to shared state | `state.findings` is updated with Legal Agent findings |
| 15 | Findings are streamed via SSE | `StreamEvent` objects are emitted and received by the frontend |
| 16 | Inter-agent communication works | Legal Agent posts InfoRequests and processes InfoResponses |
| 17 | Re-investigation handling works | Legal Agent processes ReinvestigationRequests with refined queries |
| 18 | IFRS coverage progress is tracked | Progress events show coverage by pillar (governance, strategy, risk management, metrics) |
| 19 | Error handling is graceful | RAG failures, LLM errors, and gap detection errors are handled without crashing the pipeline |
| 20 | Performance is acceptable | Legal Agent completes investigation of 50 claims in under 3 minutes |

---

## Appendix A: Legal Agent Investigation Prompt

### A.1 System Prompt

```
You are the Legal Agent in Sibyl, an AI system that verifies sustainability reports against IFRS S1/S2 disclosure standards. Your task is to investigate legal, regulatory, and governance-related claims and assess their compliance with IFRS S1/S2 requirements at the paragraph level.

## Your Responsibilities

1. **Paragraph-level IFRS mapping:** Map each claim to specific IFRS paragraph identifiers (e.g., S2.14(a)(iv)), not just pillar-level categories.

2. **Compliance assessment:** For each mapped paragraph, assess whether the claim meets the paragraph's specific sub-requirements. Check for:
   - Presence: Is the required topic/content present?
   - Completeness: Are all sub-requirements addressed?
   - Specificity: Is the disclosure specific enough?
   - Methodology alignment: For metrics, does methodology align with IFRS?
   - Granularity: Does disclosure meet required level of detail?

3. **Sub-requirement extraction:** For each IFRS paragraph, identify its sub-requirements from the paragraph text. For example, S2.14(a)(iv) requires: key assumptions, dependencies, timeline.

4. **Evidence extraction:** Extract specific evidence from the claim text (or surrounding report content) that addresses each sub-requirement.

5. **Gap identification:** If a sub-requirement is not addressed, describe what is missing.

## IFRS Structure

### S1 Pillars:
- Governance (S1.26-27): Board oversight, competencies, reporting frequency, remuneration
- Strategy (S1.28-35): Risks/opportunities, business model effects, strategy response, financial effects
- Risk Management (S1.38-42): Risk identification, assessment, prioritization, monitoring, integration
- Metrics & Targets (S1.43-53): Performance metrics, targets, baseline, progress

### S2 Climate Paragraphs:
- Governance: S2.5-7 (climate-specific governance)
- Strategy: S2.8-12 (climate risks/opportunities), S2.13 (business model), S2.14 (decision-making/transition plan), S2.15-21 (financial effects), S2.22 (climate resilience)
- Risk Management: S2.24-26 (climate risk management)
- Metrics: S2.27-31 (GHG emissions), S2.33-36 (climate targets)

## Output Format

Return a JSON object with:
- `ifrs_mappings`: Array of paragraph mappings, each with paragraph_id, compliance_status, sub_requirements assessment
- `evidence`: Extracted evidence text for each sub-requirement
- `gaps`: Missing sub-requirements if compliance_status is "partially_addressed"
- `confidence`: "high" | "medium" | "low"
```

### A.2 User Prompt Template

```
Investigate the following claim against IFRS S1/S2 requirements:

Claim: {claim_text}
Claim Type: {claim_type}
Preliminary IFRS Mapping: {preliminary_ifrs_paragraphs}

Retrieved IFRS Paragraphs:
{rag_results_formatted}

Assess:
1. Which specific IFRS paragraphs does this claim map to? (paragraph-level precision)
2. For each mapped paragraph, does the claim meet all sub-requirements?
3. Extract evidence for each addressed sub-requirement.
4. Identify any missing sub-requirements.

Return your assessment as a JSON object matching the specified schema.
```

---

## Appendix B: IFRS Paragraph Registry Structure

### B.1 Registry File Format

The registry file (`data/ifrs/paragraph_registry.json`) contains a complete list of all IFRS S1/S2 disclosure requirements:

```json
{
  "version": "1.0",
  "last_updated": "2026-02-09",
  "paragraphs": [
    {
      "paragraph_id": "S2.14(a)(iv)",
      "standard": "S2",
      "pillar": "strategy",
      "section": "Decision-Making",
      "requirement_text": "An entity shall disclose its transition plan, including information about: (1) key assumptions used in developing its transition plan; (2) dependencies on which the entity's transition plan relies; (3) the timeline for achieving transition plan objectives.",
      "sub_requirements": [
        {
          "requirement": "key assumptions",
          "required": true,
          "description": "The key assumptions used in developing the transition plan (e.g., economic growth, carbon price, technology availability)"
        },
        {
          "requirement": "dependencies",
          "required": true,
          "description": "Dependencies on which the entity's transition plan relies (e.g., policy support, market conditions, technology deployment)"
        },
        {
          "requirement": "timeline",
          "required": true,
          "description": "The timeline for achieving transition plan objectives"
        }
      ],
      "s1_counterpart": "S1.33",
      "materiality_note": "Transition plans are critical for assessing an entity's climate strategy credibility. Missing assumptions or dependencies makes it impossible to evaluate plan feasibility.",
      "applicability": "all_entities"
    },
    {
      "paragraph_id": "S2.29(a)(iii)",
      "standard": "S2",
      "pillar": "metrics_targets",
      "section": "GHG Emissions",
      "requirement_text": "An entity shall disclose absolute Scope 3 GHG emissions by category, measured in accordance with the GHG Protocol.",
      "sub_requirements": [
        {
          "requirement": "Scope 3 emissions disclosure",
          "required": true,
          "description": "Absolute Scope 3 GHG emissions must be disclosed"
        },
        {
          "requirement": "disclosure by category",
          "required": true,
          "description": "Scope 3 emissions must be disclosed by the 15 categories defined in the GHG Protocol (e.g., Category 1: Purchased goods and services, Category 11: Use of sold products)"
        },
        {
          "requirement": "GHG Protocol alignment",
          "required": true,
          "description": "Measurement must follow the GHG Protocol Corporate Value Chain (Scope 3) Standard"
        }
      ],
      "s1_counterpart": "S1.46",
      "materiality_note": "Scope 3 emissions typically represent the majority of a company's total GHG footprint. Omitting Scope 3 emissions understates climate exposure and fails to provide a complete picture of the entity's climate impact.",
      "applicability": "all_entities"
    }
  ]
}
```

### B.2 Registry Population Process

The registry is populated via a one-time setup script:

1. **Parse IFRS standard texts:** Extract all paragraph identifiers and requirement text from `s1_full.md` and `s2_full.md`.
2. **Extract sub-requirements:** Use Claude Sonnet 4.5 to parse paragraph text and extract sub-requirements (one-time LLM pass).
3. **Enrich with S1/S2 mapping:** Add `s1_counterpart` from `s1_s2_mapping.json`.
4. **Generate materiality notes:** Use Claude Sonnet 4.5 to generate materiality context for each paragraph (one-time LLM pass).
5. **Validate completeness:** Ensure all paragraphs from PRD Appendices A and B are included.

---

## Appendix C: Disclosure Gap Detection Algorithm

### C.1 Pseudocode

```
function detect_disclosure_gaps(state: SibylState, registry: ParagraphRegistry) -> list[AgentFinding]:
    gaps = []
    
    # Load report content chunks
    report_chunks = rag_service.search(
        query="report content",
        source_types=["report"],
        report_id=state.report_id,
        top_k=1000  # Get all report chunks
    )
    
    # For each IFRS paragraph in registry
    for paragraph in registry.paragraphs:
        # Check claim coverage
        relevant_claims = find_claims_mapped_to_paragraph(state.claims, paragraph.paragraph_id)
        
        # Check report content coverage
        relevant_chunks = find_chunks_mentioning_paragraph(report_chunks, paragraph)
        
        # Assess coverage
        coverage_status = assess_coverage(paragraph, relevant_claims, relevant_chunks)
        
        if coverage_status == "fully_unaddressed":
            gap = create_gap_finding(
                paragraph_id=paragraph.paragraph_id,
                gap_status="fully_unaddressed",
                materiality_context=paragraph.materiality_note
            )
            gaps.append(gap)
        
        elif coverage_status == "partially_addressed":
            missing_sub_reqs = identify_missing_sub_requirements(
                paragraph, relevant_claims, relevant_chunks
            )
            gap = create_gap_finding(
                paragraph_id=paragraph.paragraph_id,
                gap_status="partially_addressed",
                missing_sub_requirements=missing_sub_reqs,
                materiality_context=paragraph.materiality_note
            )
            gaps.append(gap)
    
    return gaps

function assess_coverage(paragraph, claims, chunks) -> str:
    if not claims and not chunks:
        return "fully_unaddressed"
    
    # If claims exist, check their compliance status
    if claims:
        compliance_statuses = [get_compliance_status(c, paragraph) for c in claims]
        if all(s == "fully_addressed" for s in compliance_statuses):
            return "fully_addressed"
        elif any(s == "partially_addressed" for s in compliance_statuses):
            return "partially_addressed"
    
    # If only chunks (no explicit claim), assess chunk coverage
    if chunks and not claims:
        # Use LLM to assess whether chunks meet paragraph requirements
        return assess_chunk_coverage_via_llm(chunks, paragraph)
    
    return "partially_addressed"  # Default: content exists but completeness unclear
```

### C.2 Chunk Coverage Assessment

When only report chunks exist (no explicit claim mapping), use Claude Sonnet 4.5 to assess whether the chunks meet paragraph requirements:

```
Prompt: "Do the following report excerpts meet the requirements of IFRS {paragraph_id}? 
The requirement is: {requirement_text}
Sub-requirements: {sub_requirements}

Report excerpts:
{chunk_texts}

Assess: (1) Which sub-requirements are addressed? (2) Which are missing? (3) Overall compliance status."
```

---

## Appendix D: Example Findings

### D.1 Claim Compliance Finding (Fully Addressed)

```json
{
  "finding_id": "finding-abc-123",
  "agent_name": "legal",
  "claim_id": "claim-456",
  "evidence_type": "ifrs_compliance",
  "summary": "Claim about transition plan maps to S2.14(a)(iv). Compliance status: fully_addressed. All sub-requirements (key assumptions, dependencies, timeline) are present.",
  "details": {
    "ifrs_mappings": [
      {
        "paragraph_id": "S2.14(a)(iv)",
        "pillar": "strategy",
        "section": "Decision-Making",
        "requirement_text": "An entity shall disclose its transition plan, including information about: key assumptions; dependencies; timeline.",
        "sub_requirements": [
          {
            "requirement": "key assumptions",
            "addressed": true,
            "evidence": "The report states: 'Our transition plan assumes a 2.5% annual GDP growth rate, carbon price of $75/tCO2e by 2030, and availability of carbon capture and storage technology by 2028.'"
          },
          {
            "requirement": "dependencies",
            "addressed": true,
            "evidence": "The report discloses: 'Our transition plan relies on policy support for carbon pricing, market demand for low-carbon products, and deployment of renewable energy infrastructure.'"
          },
          {
            "requirement": "timeline",
            "addressed": true,
            "evidence": "The report includes a detailed timeline showing milestones: 2025 (20% reduction), 2030 (42% reduction), 2040 (70% reduction), 2050 (net-zero)."
          }
        ],
        "compliance_status": "fully_addressed",
        "s1_counterpart": "S1.33"
      }
    ],
    "compliance_status": "fully_addressed",
    "confidence": "high"
  },
  "supports_claim": true,
  "confidence": "high",
  "iteration": 1
}
```

### D.2 Claim Compliance Finding (Partially Addressed)

```json
{
  "finding_id": "finding-def-456",
  "agent_name": "legal",
  "claim_id": "claim-789",
  "evidence_type": "ifrs_compliance",
  "summary": "Claim about transition plan maps to S2.14(a)(iv). Compliance status: partially_addressed. Missing key assumptions and dependencies sub-requirements.",
  "details": {
    "ifrs_mappings": [
      {
        "paragraph_id": "S2.14(a)(iv)",
        "pillar": "strategy",
        "section": "Decision-Making",
        "sub_requirements": [
          {
            "requirement": "key assumptions",
            "addressed": false,
            "evidence": null,
            "gap_reason": "The report mentions a transition plan but does not disclose the key assumptions used in developing it (e.g., economic growth, carbon price, technology availability)."
          },
          {
            "requirement": "dependencies",
            "addressed": false,
            "evidence": null,
            "gap_reason": "The report does not disclose dependencies on which the transition plan relies."
          },
          {
            "requirement": "timeline",
            "addressed": true,
            "evidence": "The report includes a timeline: 'We aim to achieve net-zero by 2050 with interim targets in 2030 and 2040.'"
          }
        ],
        "compliance_status": "partially_addressed"
      }
    ],
    "compliance_status": "partially_addressed",
    "gaps": [
      "Missing key assumptions sub-requirement",
      "Missing dependencies sub-requirement"
    ],
    "confidence": "high"
  },
  "supports_claim": null,
  "confidence": "high",
  "iteration": 1
}
```

### D.3 Disclosure Gap Finding (Fully Unaddressed)

```json
{
  "finding_id": "finding-ghi-789",
  "agent_name": "legal",
  "claim_id": null,
  "evidence_type": "disclosure_gap",
  "summary": "IFRS S2.29(a)(iii) requirement (Scope 3 emissions by category) is fully_unaddressed. Scope 3 emissions typically represent the majority of a company's total GHG footprint; omitting them understates climate exposure.",
  "details": {
    "paragraph_id": "S2.29(a)(iii)",
    "pillar": "metrics_targets",
    "section": "GHG Emissions",
    "requirement_text": "An entity shall disclose absolute Scope 3 GHG emissions by category, measured in accordance with the GHG Protocol.",
    "sub_requirements": [
      {
        "requirement": "Scope 3 emissions disclosure",
        "required": true,
        "addressed": false
      },
      {
        "requirement": "disclosure by category",
        "required": true,
        "addressed": false
      },
      {
        "requirement": "GHG Protocol alignment",
        "required": true,
        "addressed": false
      }
    ],
    "gap_status": "fully_unaddressed",
    "materiality_context": "Scope 3 emissions typically represent the majority of a company's total GHG footprint. Omitting Scope 3 emissions understates climate exposure and fails to provide a complete picture of the entity's climate impact. For many sectors (e.g., consumer goods, financial services), Scope 3 emissions can be 5-10x larger than Scope 1+2 combined.",
    "s1_counterpart": "S1.46"
  },
  "supports_claim": false,
  "confidence": "high",
  "iteration": 1
}
```

### D.4 Disclosure Gap Finding (Partially Addressed)

```json
{
  "finding_id": "finding-jkl-012",
  "agent_name": "legal",
  "claim_id": null,
  "evidence_type": "disclosure_gap",
  "summary": "IFRS S2.29(a)(iii) requirement (Scope 3 emissions by category) is partially_addressed. Report discloses total Scope 3 emissions but omits category-level breakdown required by the standard.",
  "details": {
    "paragraph_id": "S2.29(a)(iii)",
    "pillar": "metrics_targets",
    "section": "GHG Emissions",
    "gap_status": "partially_addressed",
    "missing_sub_requirements": [
      {
        "requirement": "disclosure by category",
        "required": true,
        "addressed": false,
        "gap_reason": "The report discloses total Scope 3 emissions (12.4 million tCO2e) but does not break down emissions by the 15 categories defined in the GHG Protocol (e.g., Category 1: Purchased goods and services, Category 11: Use of sold products). S2.29(a)(iii) requires category-level disclosure."
      }
    ],
    "materiality_context": "Category-level Scope 3 disclosure is critical for understanding where climate exposure is concentrated in the value chain. Without category breakdown, stakeholders cannot assess which value chain activities drive the majority of emissions or where reduction efforts should be focused.",
    "evidence_found": "Report page 45 states: 'Our total Scope 3 emissions were 12.4 million tonnes CO2e in FY2024.'"
  },
  "supports_claim": false,
  "confidence": "high",
  "iteration": 1
}
```

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| Paragraph-level mapping over pillar-level mapping | PRD Section 4.5 specifies "paragraph-level IFRS mapping (e.g., S2.14(a)(iv))". Pillar-level mapping (e.g., "Strategy pillar") is insufficient for compliance assessment -- sub-requirements must be checked at the paragraph level. |
| Two-phase RAG retrieval (claim-scoped + paragraph-specific) over single retrieval | Initial claim-scoped retrieval surfaces relevant paragraphs; paragraph-specific lookup ensures exact paragraph text is retrieved for compliance assessment. This balances discovery (finding relevant paragraphs) with precision (getting exact requirement text). |
| LLM-based compliance assessment over rule-based matching | IFRS paragraph requirements are nuanced and context-dependent. Rule-based matching (keyword search for "assumptions", "dependencies") would miss paraphrasing and context. LLM assessment interprets regulatory language and assesses completeness. |
| Disclosure gap detection as separate process over claim-only analysis | PRD Section 4.5 explicitly requires gap detection to address selective disclosure. Claim-only analysis misses requirements that are completely absent from the report. Gap detection ensures comprehensive compliance coverage. |
| IFRS paragraph registry as static JSON file over dynamic RAG query | Registry provides a complete, validated checklist of all IFRS requirements. Dynamic RAG query might miss paragraphs or return incomplete results. Static registry ensures systematic coverage analysis. |
| Materiality context in gap findings over bare gap identification | PRD Section 4.11 specifies gap findings should include "why this omission matters". Materiality context helps users understand the significance of gaps and prioritize remediation. |
| Inter-agent communication for cross-domain context over Legal-only assessment | PRD Section 4.5 specifies Legal Agent participates in inter-agent communication. Cross-domain context (geographic verification, quantitative validation) strengthens compliance assessment accuracy. |
| Re-investigation handling with refined queries over re-running full investigation | FRD 5's re-investigation protocol provides Judge guidance on specific evidence gaps. Targeted re-investigation is more efficient and focused than re-running the entire investigation. |
| Confidence levels (high/medium/low) over binary supports_claim | Compliance assessment has degrees of certainty. A claim may be partially addressed (uncertain) or assessment may be based on incomplete evidence (low confidence). Confidence levels provide nuance. |
| Gap findings with `claim_id=None` over linking gaps to nearest claim | Disclosure gaps are not tied to specific claims -- they represent requirements that are absent from the report entirely. Using `claim_id=None` clearly distinguishes gap findings from claim compliance findings. |
| IFRS coverage progress events for dashboard over no progress tracking | PRD Section 4.10 specifies Legal Agent dashboard display shows "IFRS coverage progress bar per pillar". Progress events enable real-time visualization of compliance coverage. |
| Hybrid search (semantic + keyword) over semantic-only | Paragraph IDs (e.g., "S2.14(a)(iv)") are precise identifiers that benefit from keyword matching. Semantic search alone might miss exact paragraph matches. Hybrid search combines meaning-based retrieval with exact ID matching. |
| Sub-requirement extraction via LLM over manual parsing | IFRS paragraph text is structured but not uniformly formatted. LLM extraction handles variations in paragraph structure and identifies implicit sub-requirements that manual parsing might miss. |
| Batch gap detection over per-claim gap checking | Gap detection compares the full IFRS set against report content. Per-claim checking would miss gaps for requirements that have no corresponding claims. Batch detection ensures comprehensive coverage. |
| Materiality context generation via LLM over static templates | Materiality context should be tailored to the specific paragraph and industry context. LLM generation provides nuanced explanations that static templates cannot match. |
