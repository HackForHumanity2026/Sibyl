# Feature Requirements Document: FRD 7 -- Data/Metrics Agent (v1.0)

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.3](../PRD.md) |
| **FRD Order** | [FRD Order](../FRD-order.md) |
| **PRD Sections** | 4.8 (Data/Metrics Agent -- Quantitative Validation) |
| **Type** | Feature |
| **Depends On** | FRD 5 (Orchestrator Agent & LangGraph Pipeline) |
| **Delivers** | Quantitative validation and consistency checks, mathematical consistency verification, unit and methodology validation, benchmark comparison, target achievability analysis, historical consistency checks, IFRS S2.27-37 metrics compliance assessment, LangGraph node implementation, inter-agent communication participation |
| **Created** | 2026-02-09 |

---

## Summary

FRD 7 delivers the Data/Metrics Agent -- a specialist investigation agent in the Sibyl multi-agent pipeline that validates all numerical and quantitative claims for mathematical consistency, methodological alignment, and benchmark plausibility. The agent replaces the `investigate_data` stub defined in FRD 5 Section 6 with a functional LangGraph node (`app/agents/data_metrics_agent.py`) that receives routed quantitative claims from the Orchestrator, performs comprehensive numerical analysis, and returns structured findings with mathematical verification results. The agent's investigation scope includes: internal consistency checks (e.g., Scope 1 + Scope 2 + Scope 3 = Total, year-over-year percentage validation, baseline consistency), unit and methodology validation (tCO2e units, GHG Protocol alignment, conversion factor verification), benchmark comparison for plausibility (emission intensities, energy consumption, financial impacts against industry standards), target assessment (mathematical achievability of reduction targets given baselines and timelines, interim target consistency), historical consistency checks (alignment with previously published reports, deviation explanations), and IFRS S2.27-37 metrics compliance assessment (absolute Scope 1/2/3 emissions, emission intensity metrics, climate-related targets with baseline periods and milestones, internal carbon pricing, climate-linked remuneration). The agent participates in the inter-agent communication protocol (InfoRequest/InfoResponse) to request industry benchmarks, geographic context, or regulatory guidance when needed. Findings are structured as `AgentFinding` objects with evidence summaries, mathematical verification results, benchmark comparisons, identified inconsistencies, and specific IFRS paragraph mappings. The agent emits `StreamEvent` objects during execution for real-time visibility in the detective dashboard (FRD 12). The agent uses Claude Sonnet 4.5 for strong numerical reasoning and consistency checking. After FRD 7, quantitative claims routed by the Orchestrator are validated for mathematical consistency, methodology alignment, and benchmark plausibility, with findings flowing to the Judge Agent for final evaluation.

---

## Given Context (Preconditions)

The following are assumed to be in place from prior FRDs:

| Prerequisite | Source FRD | Deliverable |
|---|---|---|
| Docker Compose with PostgreSQL 17 + pgvector, Redis, backend, frontend | FRD 0 | `docker-compose.yml` |
| `SibylState` Pydantic schema with `Claim`, `RoutingAssignment`, `AgentFinding`, `InfoRequest`, `InfoResponse`, `StreamEvent` types | FRD 0 | `app/agents/state.py` |
| LangGraph `StateGraph` compiled with all nodes including `investigate_data` stub | FRD 5 | `app/agents/graph.py` |
| Orchestrator routing logic that routes quantitative claims to `investigate_data` | FRD 5 | `app/agents/orchestrator_agent.py` |
| Inter-agent communication protocol (InfoRequest/InfoResponse through shared state) | FRD 5 | `app/agents/orchestrator_agent.py` |
| SSE streaming infrastructure with `StreamEvent` emission | FRD 5 | `app/agents/callbacks.py`, `app/api/routes/stream.py` |
| Data/Metrics Agent stub (`investigate_data` function signature) | FRD 5 | `app/agents/data_metrics_agent.py` |
| OpenRouter client wrapper with retry logic and `Models.CLAUDE_SONNET` constant | FRD 0 | `app/services/openrouter_client.py` |
| RAG pipeline with hybrid search for retrieving IFRS standards and methodology guidance | FRD 1 | `app/services/rag_service.py`, `app/agents/tools/rag_lookup.py` |
| IFRS S1/S2 corpus ingested into pgvector | FRD 1 | Embedded standard text |
| `Claim` SQLAlchemy model with `claim_text`, `claim_type`, `source_page`, `ifrs_paragraphs` | FRD 0 | `app/models/claim.py` |
| `Finding` SQLAlchemy model for persisting agent findings | FRD 0 | `app/models/finding.py` |
| Claims extracted with quantitative claims categorized and tagged | FRD 3 | `claims` database table |
| Detective dashboard infrastructure ready to display agent-specific content (consistency check list) | FRD 5 | `src/components/Dashboard/` (prepared for FRD 12) |

### Terms

| Term | Definition |
|---|---|
| Internal consistency check | Verification that reported numbers satisfy mathematical relationships (e.g., Scope 1 + Scope 2 + Scope 3 = Total, percentage calculations match underlying values) |
| Unit validation | Verification that emissions are reported in correct units (typically tCO2e for GHG emissions) and that conversion factors are appropriate |
| Methodology validation | Verification that the reported methodology aligns with recognized standards (GHG Protocol, ISO 14064, IFRS S2 requirements) |
| Benchmark comparison | Comparison of reported metrics (emission intensities, energy consumption, financial impacts) against industry sector averages or peer company data to assess plausibility |
| Target achievability analysis | Mathematical assessment of whether stated reduction targets are achievable given reported baselines, timelines, and historical trends |
| Historical consistency check | Verification that reported figures align with previously published reports or that deviations are explained |
| IFRS S2.27-37 | The IFRS S2 paragraphs covering Metrics and Targets, including absolute Scope 1/2/3 GHG emissions (S2.29(a)(i-iii)), emission intensity metrics, climate-related targets with baseline periods and milestones (S2.33-36), internal carbon pricing (S2.29(e)), and climate-linked remuneration (S2.29(g)) |
| GHG Protocol | The Greenhouse Gas Protocol Corporate Standard, the most widely used international standard for corporate GHG accounting |
| tCO2e | Tonnes of carbon dioxide equivalent, the standard unit for reporting GHG emissions |
| Scope 1 emissions | Direct GHG emissions from sources owned or controlled by the reporting entity |
| Scope 2 emissions | Indirect GHG emissions from purchased electricity, heat, or steam |
| Scope 3 emissions | All other indirect emissions occurring in the value chain, reported by category |
| Emission intensity | Emissions per unit of output (e.g., tCO2e per $1M revenue, tCO2e per unit produced) |
| Baseline period | The reference year or period against which reduction targets are measured |
| SBTi | Science Based Targets initiative, a third-party validation framework for climate targets aligned with climate science |

---

## Executive Summary (Gherkin-Style)

```gherkin
Feature: Data/Metrics Agent

  Background:
    Given  FRD 0, FRD 1, FRD 3, and FRD 5 are complete
    And    all services are running (backend, frontend, PostgreSQL, Redis)
    And    the LangGraph pipeline is compiled and functional
    And    quantitative claims have been extracted and routed to the Data/Metrics Agent

  Scenario: Agent receives and processes routed quantitative claims
    Given  the Orchestrator has routed quantitative claims to the Data/Metrics Agent
    When   the investigate_data node executes
    Then   it receives the assigned claims from the routing plan
    And    it emits a StreamEvent with event_type = "agent_started"
    And    it updates its agent_status to "working"
    And    it processes each claim for quantitative validation

  Scenario: Internal consistency checks validate mathematical relationships
    Given  a claim reports "Scope 1: 2.3M tCO2e, Scope 2: 1.1M tCO2e, Scope 3: 8.5M tCO2e, Total: 12.0M tCO2e"
    When   the agent performs internal consistency checks
    Then   it verifies that 2.3 + 1.1 + 8.5 = 12.0 (or identifies the discrepancy)
    And    it checks year-over-year percentage calculations match underlying numbers
    And    it verifies baseline years are applied consistently across related claims
    And    it flags any mathematical inconsistencies in the findings

  Scenario: Unit and methodology validation checks compliance
    Given  a claim reports emissions in tCO2e
    When   the agent validates units and methodology
    Then   it verifies the unit is correct (tCO2e, not tCO2 or other variants)
    And    it checks conversion factors are appropriate (GWP values, activity data conversions)
    And    it validates the methodology aligns with GHG Protocol standards
    And    it checks IFRS S2.27-31 requirements for measurement approach disclosure

  Scenario: Benchmark comparison assesses plausibility
    Given  a claim reports emission intensity of 0.5 tCO2e per $1M revenue for a manufacturing company
    When   the agent performs benchmark comparison
    Then   it requests industry benchmark data via InfoRequest (if not available locally)
    And    it compares the reported intensity against sector averages
    And    it assesses whether the figure is plausible for the company's size and sector
    And    it includes benchmark comparison results in the findings

  Scenario: Target achievability analysis evaluates reduction goals
    Given  a claim states "42% reduction in Scope 1+2 emissions by 2030 from a 2019 baseline"
    When   the agent performs target achievability analysis
    Then   it extracts the baseline year (2019) and baseline emissions
    And    it calculates the required annual reduction rate
    And    it compares this rate against historical trends and industry benchmarks
    And    it assesses whether the target is mathematically achievable
    And    it checks if interim targets are consistent with the long-term goal
    And    it validates IFRS S2.33-36 requirements (baseline period, milestones, progress)

  Scenario: Historical consistency checks compare against prior reports
    Given  a claim reports Scope 1 emissions of 2.3M tCO2e for FY2024
    When   the agent performs historical consistency checks
    Then   it attempts to retrieve prior year figures from the document or via InfoRequest
    And    it compares FY2024 against FY2023 and earlier years
    And    it verifies reported year-over-year changes are consistent
    And    it flags unexplained deviations or inconsistencies

  Scenario: IFRS S2.27-37 compliance assessment
    Given  claims related to GHG emissions and targets
    When   the agent assesses IFRS S2.27-37 compliance
    Then   it checks for absolute Scope 1 emissions disclosure (S2.29(a)(i))
    And    it checks for absolute Scope 2 emissions disclosure (S2.29(a)(ii))
    And    it checks for absolute Scope 3 emissions by category (S2.29(a)(iii))
    And    it checks for emission intensity metrics
    And    it checks for climate-related targets with baseline periods and milestones (S2.33-36)
    And    it checks for internal carbon pricing disclosure (S2.29(e))
    And    it checks for climate-linked remuneration disclosure (S2.29(g))
    And    it maps findings to specific IFRS paragraph requirements

  Scenario: Inter-agent communication requests benchmark data
    Given  the agent needs industry benchmark data for plausibility checks
    When   it determines cross-domain context would strengthen the analysis
    Then   it posts an InfoRequest to the shared state
    And    the Orchestrator routes the request to the Academic/Research Agent
    And    the Academic/Research Agent responds with benchmark data
    And    the Data/Metrics Agent incorporates the benchmark data into its findings

  Scenario: Agent emits findings and completes execution
    Given  the agent has processed all assigned claims
    When   it completes its investigation
    Then   it creates AgentFinding objects for each claim
    And    each finding includes: evidence summary, mathematical verification results, benchmark comparisons, identified inconsistencies, IFRS paragraph mappings
    And    it emits StreamEvent objects with event_type = "evidence_found" for each finding
    And    it updates agent_status to "completed"
    And    it emits a StreamEvent with event_type = "agent_completed"
    And    findings are written to the shared state for the Judge Agent

  Scenario: Consistency checks displayed in detective dashboard
    Given  the agent is executing and emitting StreamEvents
    When   the detective dashboard receives consistency check events
    Then   the Data/Metrics Agent node displays a running list of consistency checks
    And    each check shows a pass/fail indicator (e.g., "Scope 1 + 2 + 3 = Total: ✓" or "✗")
    And    failed checks are highlighted in the dashboard
```

---

## Table of Contents

1. [LangGraph Node Implementation](#1-langgraph-node-implementation)
2. [Internal Consistency Checks](#2-internal-consistency-checks)
3. [Unit and Methodology Validation](#3-unit-and-methodology-validation)
4. [Benchmark Comparison](#4-benchmark-comparison)
5. [Target Achievability Analysis](#5-target-achievability-analysis)
6. [Historical Consistency Checks](#6-historical-consistency-checks)
7. [IFRS S2.27-37 Compliance Assessment](#7-ifrs-s227-37-compliance-assessment)
8. [Inter-Agent Communication](#8-inter-agent-communication)
9. [Findings Structure and Evidence Output](#9-findings-structure-and-evidence-output)
10. [StreamEvent Emissions](#10-streamevent-emissions)
11. [Model Configuration and Prompting](#11-model-configuration-and-prompting)
12. [Error Handling](#12-error-handling)
13. [Exit Criteria](#13-exit-criteria)
14. [Appendix A: Data/Metrics Agent Prompt Template](#appendix-a-datametrics-agent-prompt-template)
15. [Appendix B: Consistency Check Definitions](#appendix-b-consistency-check-definitions)
16. [Appendix C: Unit Conversion Reference](#appendix-c-unit-conversion-reference)
17. [Appendix D: IFRS S2.27-37 Requirements Checklist](#appendix-d-ifrs-s227-37-requirements-checklist)
18. [Design Decisions Log](#design-decisions-log)

---

## 1. LangGraph Node Implementation

### 1.1 Overview

The Data/Metrics Agent (`app/agents/data_metrics_agent.py`) replaces the FRD 5 stub with a functional LangGraph node that validates quantitative claims for mathematical consistency, methodological alignment, and benchmark plausibility as described in PRD Section 4.8.

### 1.2 Node Function

```python
async def investigate_data(state: SibylState) -> dict:
    """Data/Metrics Agent: Validate quantitative claims for consistency and plausibility.

    Reads: state.routing_plan, state.claims, state.info_responses,
           state.iteration_count, state.findings
    Writes: state.findings, state.agent_status, state.info_requests,
            state.events

    Responsibilities:
    1. Receive routed quantitative claims from the Orchestrator.
    2. Perform internal consistency checks (arithmetic, percentages, baselines).
    3. Validate units and methodology (tCO2e, GHG Protocol alignment).
    4. Compare against benchmarks for plausibility.
    5. Assess target achievability (reduction targets, timelines, baselines).
    6. Check historical consistency (alignment with prior reports).
    7. Assess IFRS S2.27-37 compliance.
    8. Participate in inter-agent communication (request benchmarks, context).
    9. Emit findings and StreamEvents.

    Returns:
        Partial state update with findings, agent status, info requests, and events.
    """
```

### 1.3 Node Processing Steps

The `investigate_data` node shall execute the following steps:

1. **Emit start event:** Append a `StreamEvent` with `event_type = "agent_started"`, `agent_name = "data_metrics"`.

2. **Find assigned claims:** Filter `state.claims` to find claims assigned to this agent via `state.routing_plan`:
   ```python
   assigned_claims = [
       claim for claim in state.claims
       if any(
           assignment.claim_id == claim.claim_id
           and "data_metrics" in assignment.assigned_agents
           for assignment in state.routing_plan
       )
   ]
   ```

3. **Update agent status:** Set `agent_status["data_metrics"] = AgentStatus(status="working", claims_assigned=len(assigned_claims), claims_completed=0)`.

4. **Group claims by analysis type:** Organize claims into groups for efficient processing:
   - **Emissions claims:** Scope 1/2/3, totals, intensities
   - **Target claims:** Reduction targets, net-zero commitments, interim milestones
   - **Financial claims:** Climate-related financial impacts, internal carbon pricing
   - **Other quantitative claims:** Energy consumption, waste figures, resource efficiency

5. **Process each claim group:**
   - For each claim, construct a validation prompt (see Section 11 and Appendix A).
   - Call Claude Sonnet 4.5 via OpenRouter.
   - Parse the structured response into validation results.
   - Perform consistency checks (Section 2).
   - Validate units and methodology (Section 3).
   - Compare against benchmarks (Section 4, may require InfoRequest).
   - Assess target achievability (Section 5).
   - Check historical consistency (Section 6).
   - Assess IFRS S2.27-37 compliance (Section 7).

6. **Emit thinking events:** During processing, emit `StreamEvent` objects with `event_type = "agent_thinking"` describing progress (e.g., "Validating Scope 1+2+3 totals...", "Checking target achievability for 2030 reduction goal...").

7. **Emit consistency check events:** For each consistency check performed, emit a `StreamEvent` with `event_type = "consistency_check"` containing the check name, result (pass/fail), and details (see Section 10).

8. **Create findings:** For each claim, create an `AgentFinding` object (see Section 9) with:
   - Evidence summary
   - Mathematical verification results
   - Benchmark comparisons
   - Identified inconsistencies
   - IFRS paragraph mappings

9. **Emit evidence found events:** For each finding, emit a `StreamEvent` with `event_type = "evidence_found"`.

10. **Update agent status:** Set `agent_status["data_metrics"] = AgentStatus(status="completed", claims_assigned=len(assigned_claims), claims_completed=len(assigned_claims))`.

11. **Emit completion event:** Append a `StreamEvent` with `event_type = "agent_completed"`, `agent_name = "data_metrics"`, including summary statistics.

12. **Return partial state:** Return the updated `findings`, `agent_status`, `info_requests`, and `events`.

### 1.4 Re-Investigation Handling

When the agent receives re-investigation requests from the Judge (via `state.reinvestigation_requests`):

1. Filter requests targeting `"data_metrics"` agent.
2. For each request, read the `evidence_gap` and `refined_queries`.
3. Re-process the affected claims with focused attention on the specific gaps identified by the Judge.
4. Produce refined findings addressing the Judge's concerns.

---

## 2. Internal Consistency Checks

### 2.1 Overview

Internal consistency checks verify that reported numbers satisfy mathematical relationships and that calculations are correct. These checks are fundamental to detecting errors, omissions, or intentional misrepresentations in quantitative claims.

### 2.2 Scope Addition Checks

The system shall verify that emissions totals add up correctly:

**Check: Scope 1 + Scope 2 + Scope 3 = Total**

1. **Extract values:** From claims or the document, identify:
   - Scope 1 emissions value (with units)
   - Scope 2 emissions value (with units)
   - Scope 3 emissions value (with units, may be by category)
   - Reported total emissions value (with units)

2. **Normalize units:** Convert all values to the same unit (typically tCO2e) if they differ.

3. **Sum components:** Calculate `calculated_total = Scope1 + Scope2 + Scope3` (or sum of Scope 3 categories if reported separately).

4. **Compare:** Compare `calculated_total` against `reported_total`:
   - If `abs(calculated_total - reported_total) / reported_total < 0.01` (1% tolerance), mark as **PASS**.
   - Otherwise, mark as **FAIL** and record the discrepancy.

5. **Emit consistency check event:** Emit a `StreamEvent` with:
   ```python
   {
       "event_type": "consistency_check",
       "agent_name": "data_metrics",
       "data": {
           "check_name": "scope_addition",
           "claim_id": "...",
           "result": "pass" | "fail",
           "details": {
               "scope1": 2.3e6,
               "scope2": 1.1e6,
               "scope3": 8.5e6,
               "calculated_total": 11.9e6,
               "reported_total": 12.0e6,
               "discrepancy": 0.1e6,
               "discrepancy_percent": 0.83
           }
       }
   }
   ```

### 2.3 Year-Over-Year Percentage Validation

**Check: Percentage change matches underlying numbers**

1. **Extract values:** Identify:
   - Prior year value (e.g., FY2023 emissions)
   - Current year value (e.g., FY2024 emissions)
   - Reported percentage change (e.g., "6.1% decrease")

2. **Calculate percentage:** `calculated_pct = ((current - prior) / prior) * 100`

3. **Compare:** Compare `calculated_pct` against the reported percentage:
   - If `abs(calculated_pct - reported_pct) < 0.1` (0.1 percentage point tolerance), mark as **PASS**.
   - Otherwise, mark as **FAIL** and record the discrepancy.

4. **Handle sign:** Verify the sign matches (decrease vs. increase).

### 2.4 Baseline Consistency Checks

**Check: Baseline years are applied consistently**

1. **Extract baseline references:** Identify all claims mentioning baseline years (e.g., "from a 2019 baseline", "compared to 2020").

2. **Group by metric:** Group claims by the metric type (e.g., Scope 1 emissions, Scope 2 emissions, total emissions).

3. **Verify consistency:** For each metric group, verify:
   - All claims use the same baseline year (or explain deviations).
   - Baseline values are consistent across claims (same baseline year should yield the same baseline value).

4. **Flag inconsistencies:** If baseline years differ without explanation, or baseline values differ for the same baseline year, mark as **FAIL**.

### 2.5 Recalculation Adjustment Checks

**Check: Recalculation adjustments are applied consistently**

1. **Identify recalculation mentions:** Look for claims mentioning recalculation adjustments (e.g., "restated to reflect updated methodology", "recalculated using revised GWP values").

2. **Verify consistency:** If a claim reports recalculation adjustments:
   - Verify that all related claims (same metric, same time period) also reflect the recalculation.
   - Verify that the adjustment is explained (methodology change, GWP update, etc.).

3. **Flag inconsistencies:** If some claims are recalculated but others are not (without explanation), mark as **FAIL**.

### 2.6 Percentage Calculation Validation

**Check: Percentage calculations are mathematically correct**

For any claim reporting percentages (e.g., "15% reduction", "42% of electricity from renewables"):

1. **Extract numerator and denominator:** Identify the values used to calculate the percentage.

2. **Calculate:** `calculated_pct = (numerator / denominator) * 100`

3. **Compare:** Compare against the reported percentage.

4. **Handle edge cases:** Verify division by zero is avoided, and that percentages sum correctly (e.g., if reporting "X% from source A, Y% from source B", verify X + Y = 100% or accounts for the remainder).

### 2.7 Consistency Check Output Format

Each consistency check produces a structured result:

```python
class ConsistencyCheckResult(BaseModel):
    check_name: str                    # e.g., "scope_addition", "yoy_percentage"
    claim_id: str
    result: Literal["pass", "fail", "inconclusive"]
    details: dict                      # Check-specific details (values, calculations, discrepancies)
    severity: Literal["critical", "warning", "info"]  # Critical = major inconsistency, Warning = minor issue, Info = informational
    message: str                       # Human-readable summary
```

---

## 3. Unit and Methodology Validation

### 3.1 Overview

Unit and methodology validation ensures that emissions are reported in correct units, conversion factors are appropriate, and the methodology aligns with recognized standards (GHG Protocol, ISO 14064, IFRS S2).

### 3.2 Unit Validation

**Check: Emissions are reported in correct units**

1. **Identify unit:** Extract the unit from the claim (e.g., "2.3 million tonnes CO2e", "tCO2e", "MtCO2e").

2. **Validate unit format:** Verify the unit is one of:
   - `tCO2e` (tonnes CO2e) -- standard
   - `MtCO2e` (megatonnes CO2e) -- acceptable for large values
   - `ktCO2e` (kilotonnes CO2e) -- acceptable
   - `GtCO2e` (gigatonnes CO2e) -- acceptable for very large values
   - `CO2e` (without "t") -- acceptable if context makes "tonnes" clear

3. **Flag incorrect units:** If the unit is not recognized or ambiguous (e.g., "tonnes CO2" without "equivalent"), mark as **FAIL** and note the issue.

4. **Check unit consistency:** Verify that all emissions claims use consistent units (or conversions are provided).

### 3.3 Conversion Factor Validation

**Check: Conversion factors are appropriate**

1. **Identify conversion factors:** Look for claims mentioning conversion factors (e.g., "using GWP-100 values", "converted using emission factors from X database").

2. **Validate GWP values:** If Global Warming Potential (GWP) values are mentioned:
   - Verify they align with IPCC AR6 or AR5 values (e.g., CH4 GWP-100 = 27.9 in AR6, 28 in AR5).
   - Flag if outdated GWP values are used (e.g., AR4 values) without explanation.

3. **Validate activity data conversions:** If activity data is converted to emissions (e.g., kWh to tCO2e):
   - Verify the conversion factor is appropriate for the region/grid (e.g., grid emission factors vary by country).
   - Flag if generic factors are used where region-specific factors are available.

### 3.4 Methodology Validation

**Check: Methodology aligns with GHG Protocol**

1. **Identify methodology references:** Extract mentions of methodology (e.g., "GHG Protocol Corporate Standard", "ISO 14064-1", "IFRS S2").

2. **Validate GHG Protocol alignment:** For Scope 1/2/3 claims:
   - Verify Scope 1 includes direct emissions from owned/controlled sources.
   - Verify Scope 2 uses location-based or market-based method (or both) as required by IFRS S2.
   - Verify Scope 3 categories align with GHG Protocol's 15 categories (if applicable).

3. **Check IFRS S2.27-31 requirements:** Verify the claim includes:
   - Measurement approach and inputs (S2.30).
   - Disaggregation by constituent gas (if material) (S2.30).
   - Consolidation approach (S2.31).

4. **Flag methodology gaps:** If methodology is not mentioned or does not align with standards, mark as **FAIL** or **WARNING**.

### 3.5 Unit Conversion Handling

The system shall handle unit conversions when comparing values:

```python
def normalize_emissions(value: float, unit: str) -> float:
    """Convert emissions to tCO2e."""
    unit_lower = unit.lower()
    if "mtco2e" in unit_lower or "megatonne" in unit_lower:
        return value * 1_000_000
    elif "ktco2e" in unit_lower or "kilotonne" in unit_lower:
        return value * 1_000
    elif "gtco2e" in unit_lower or "gigatonne" in unit_lower:
        return value * 1_000_000_000
    elif "tco2e" in unit_lower or "tonne" in unit_lower:
        return value
    else:
        raise ValueError(f"Unrecognized unit: {unit}")
```

---

## 4. Benchmark Comparison

### 4.1 Overview

Benchmark comparison assesses whether reported metrics (emission intensities, energy consumption, financial impacts) are plausible for the company's industry sector and size. This helps detect outliers that may indicate errors, misreporting, or exceptional performance (which may require verification).

### 4.2 Benchmark Data Sources

The agent shall use the following sources for benchmark data (in priority order):

1. **InfoRequest to Academic/Research Agent:** Request industry-specific benchmarks (most reliable, but requires inter-agent communication).

2. **RAG retrieval:** Query the RAG pipeline for industry benchmark data stored in the corpus (e.g., SASB metrics, CDP sector averages).

3. **LLM knowledge:** Use Claude Sonnet 4.5's training knowledge for common industry benchmarks (fallback, less reliable).

### 4.3 Emission Intensity Comparison

**Check: Emission intensity is plausible for the sector**

1. **Extract intensity metric:** Identify the reported emission intensity (e.g., "0.5 tCO2e per $1M revenue", "2.3 tCO2e per unit produced").

2. **Identify sector:** Extract the company's industry sector from the document or via InfoRequest to the Legal Agent.

3. **Request benchmark:** Post an InfoRequest to the Academic/Research Agent:
   ```python
   InfoRequest(
       requesting_agent="data_metrics",
       description=f"Industry benchmark for emission intensity in {sector}: {intensity_metric}. Need average intensity for companies of similar size.",
       status="pending"
   )
   ```

4. **Compare:** Once benchmark data is received (via `state.info_responses`):
   - Compare reported intensity against sector average.
   - Assess if the reported value is within a reasonable range (e.g., within 2 standard deviations of the mean).
   - Flag if the value is an extreme outlier (may indicate error or exceptional performance requiring verification).

5. **Include in findings:** Document the benchmark comparison in the finding, including:
   - Reported intensity
   - Sector average (with source)
   - Assessment (plausible, outlier, etc.)

### 4.4 Energy Consumption Comparison

**Check: Energy consumption is plausible**

Similar to emission intensity, compare reported energy consumption (MWh, GJ) against sector benchmarks for companies of similar size.

### 4.5 Financial Impact Comparison

**Check: Climate-related financial impacts are plausible**

For claims reporting financial impacts (e.g., "$2 billion investment in renewable energy", "15% of capex allocated to climate initiatives"):

1. **Extract financial metrics:** Identify the reported value and context (revenue, capex, etc.).

2. **Calculate percentage:** If applicable, calculate the percentage of total revenue/capex.

3. **Compare:** Compare against industry norms (e.g., typical % of capex allocated to climate initiatives in the sector).

4. **Assess plausibility:** Flag if the percentage is unusually high or low.

### 4.6 Benchmark Comparison Output

Each benchmark comparison produces:

```python
class BenchmarkComparison(BaseModel):
    metric_name: str                   # e.g., "emission_intensity", "energy_consumption"
    reported_value: float
    reported_unit: str
    sector_average: float | None
    sector_unit: str | None
    benchmark_source: str | None       # e.g., "SASB", "CDP", "Academic/Research Agent"
    assessment: Literal["plausible", "outlier_high", "outlier_low", "inconclusive"]
    reasoning: str
```

---

## 5. Target Achievability Analysis

### 5.1 Overview

Target achievability analysis evaluates whether stated reduction targets are mathematically achievable given reported baselines, timelines, and historical trends. This helps detect unrealistic targets that may indicate greenwashing or insufficient planning.

### 5.2 Target Extraction

**Extract target components:**

1. **Target type:** Identify the target type:
   - Absolute reduction (e.g., "reduce by 42%")
   - Intensity reduction (e.g., "reduce intensity by 30%")
   - Net-zero commitment (e.g., "net-zero by 2050")

2. **Baseline period:** Extract the baseline year or period (e.g., "from a 2019 baseline").

3. **Baseline value:** Extract the baseline emissions value (e.g., "2019 emissions: 2.45M tCO2e").

4. **Target value:** Extract the target emissions value or percentage (e.g., "42% reduction", "1.42M tCO2e by 2030").

5. **Timeline:** Extract the target year and any interim milestones (e.g., "by 2030", "interim target: 20% by 2025").

### 5.3 Mathematical Achievability Check

**Check: Target is mathematically achievable**

1. **Calculate required reduction rate:**
   ```python
   baseline_value = 2.45e6  # tCO2e
   target_value = baseline_value * (1 - 0.42)  # 42% reduction
   years_to_target = 2030 - 2019  # 11 years
   annual_reduction_rate = (baseline_value - target_value) / years_to_target
   annual_percentage_reduction = (annual_reduction_rate / baseline_value) * 100
   ```

2. **Compare against historical trends:** If historical data is available:
   - Calculate historical annual reduction rate.
   - Compare required rate against historical rate.
   - Flag if required rate is significantly higher than historical (may indicate unrealistic target).

3. **Compare against industry benchmarks:** Request benchmark data for typical reduction rates in the sector (via InfoRequest to Academic/Research Agent).

4. **Assess achievability:** 
   - If required rate is within 2x of historical rate and industry average: **ACHIEVABLE**.
   - If required rate is 2-5x higher: **CHALLENGING** (may require significant investment).
   - If required rate is >5x higher: **QUESTIONABLE** (may be unrealistic without major changes).

### 5.4 Interim Target Consistency Check

**Check: Interim targets are consistent with long-term goals**

1. **Extract interim targets:** Identify all interim milestones (e.g., "20% by 2025", "30% by 2027").

2. **Verify progression:** Check that interim targets progress toward the long-term target:
   - Interim targets should be between baseline and final target.
   - Interim targets should increase over time (for reduction targets).
   - The path from baseline → interim → final should be roughly linear or accelerating (not decelerating).

3. **Flag inconsistencies:** If interim targets are inconsistent (e.g., 2027 target is lower than 2025 target for a reduction goal), mark as **FAIL**.

### 5.5 Baseline Validation

**Check: Baseline is appropriate**

1. **Verify baseline year:** Check that the baseline year is reasonable (typically within the last 5-10 years, not too old).

2. **Verify baseline value:** Check that the baseline value aligns with reported historical data (if available).

3. **Check baseline recalculation:** If baseline was recalculated, verify the recalculation is explained and applied consistently.

### 5.6 IFRS S2.33-36 Compliance Check

**Check: Target disclosure meets IFRS S2.33-36 requirements**

Verify the claim includes:

1. **Metric used:** Whether absolute or intensity-based (S2.33).

2. **Baseline period and base year emissions:** Baseline year and value (S2.34).

3. **Time horizon and milestones:** Target year and interim milestones (S2.34).

4. **Sector decarbonization approach:** If applicable, how the target aligns with sector decarbonization pathways (S2.35).

5. **Third-party validation:** If SBTi or other validation is mentioned, verify it's current and valid (S2.35).

6. **Progress against target:** If progress is reported, verify it's calculated correctly (S2.36).

### 5.7 Target Achievability Output

```python
class TargetAchievabilityResult(BaseModel):
    claim_id: str
    target_type: Literal["absolute_reduction", "intensity_reduction", "net_zero"]
    baseline_year: int
    baseline_value: float
    target_year: int
    target_value: float | None  # None if percentage-based
    target_percentage: float | None  # None if absolute-based
    required_annual_reduction_rate: float
    required_annual_percentage_reduction: float
    historical_annual_reduction_rate: float | None
    industry_average_reduction_rate: float | None
    achievability_assessment: Literal["achievable", "challenging", "questionable", "inconclusive"]
    interim_targets_consistent: bool
    ifrs_s2_33_36_compliant: bool
    missing_ifrs_requirements: list[str]  # e.g., ["baseline_period", "milestones"]
    reasoning: str
```

---

## 6. Historical Consistency Checks

### 6.1 Overview

Historical consistency checks verify that reported figures align with previously published reports or that deviations are explained. This helps detect restatements, methodology changes, or inconsistencies that may indicate errors or selective disclosure.

### 6.2 Historical Data Retrieval

**Retrieve prior year figures:**

1. **From current document:** Extract prior year figures mentioned in the current report (e.g., "FY2023 emissions: 2.45M tCO2e").

2. **Via InfoRequest:** If prior year data is not in the current document, post an InfoRequest to the News/Media Agent or Academic/Research Agent to retrieve prior year sustainability reports or public disclosures.

3. **From claims:** Check if other claims in the same document reference prior year data.

### 6.3 Year-Over-Year Consistency Check

**Check: Reported changes are consistent**

1. **Extract current and prior values:** Identify:
   - Current year value (e.g., FY2024: 2.3M tCO2e)
   - Prior year value (e.g., FY2023: 2.45M tCO2e)
   - Reported change (e.g., "6.1% decrease")

2. **Verify calculation:** Verify the percentage change matches (see Section 2.3).

3. **Check for restatements:** Look for mentions of restatements or recalculations. If prior year value was restated, verify the restatement is explained.

4. **Flag inconsistencies:** If the reported change doesn't match the calculated change, or if prior year values differ from previously reported values without explanation, mark as **FAIL**.

### 6.4 Multi-Year Trend Analysis

**Check: Multi-year trends are consistent**

1. **Extract multi-year data:** If multiple years are reported (e.g., "2019: 2.5M, 2020: 2.4M, 2021: 2.35M, 2022: 2.3M"), analyze the trend.

2. **Verify progression:** Check that the progression is logical (e.g., for reduction targets, values should decrease over time, possibly with some year-to-year variation).

3. **Flag anomalies:** If there are sudden jumps or reversals without explanation (e.g., 2021: 2.35M, 2022: 3.0M, 2023: 2.45M), mark as **WARNING** and note the anomaly.

### 6.5 Methodology Change Detection

**Check: Methodology changes are explained**

1. **Identify methodology mentions:** Look for claims mentioning methodology changes (e.g., "switched to market-based Scope 2", "updated GWP values to AR6").

2. **Verify explanation:** Check that methodology changes are explained and that the impact on reported values is quantified (e.g., "restated 2023 emissions to reflect market-based Scope 2, resulting in a 5% decrease").

3. **Flag unexplained changes:** If values change significantly without a methodology explanation, mark as **WARNING**.

### 6.6 Historical Consistency Output

```python
class HistoricalConsistencyResult(BaseModel):
    claim_id: str
    current_year: int
    current_value: float
    prior_years: list[dict]  # [{"year": 2023, "value": 2.45e6, "source": "current_report"}, ...]
    yoy_change_calculated: float
    yoy_change_reported: float | None
    yoy_change_consistent: bool
    trend_consistent: bool
    methodology_changes: list[str]  # List of detected methodology changes
    unexplained_deviations: list[str]  # List of unexplained deviations
    assessment: Literal["consistent", "inconsistent", "partially_consistent", "inconclusive"]
    reasoning: str
```

---

## 7. IFRS S2.27-37 Compliance Assessment

### 7.1 Overview

The Data/Metrics Agent is critical for assessing compliance with IFRS S2.27-37, which covers Metrics and Targets. The agent verifies that reported metrics meet the specific disclosure requirements of these paragraphs.

### 7.2 S2.29(a)(i): Absolute Scope 1 GHG Emissions

**Requirement:** Entities must disclose absolute Scope 1 GHG emissions.

**Check:**

1. **Identify Scope 1 claim:** Find claims reporting Scope 1 emissions.

2. **Verify absolute value:** Verify the claim reports an absolute value (not just intensity or percentage change).

3. **Verify unit:** Verify the unit is tCO2e (or equivalent).

4. **Check disclosure completeness:** Verify the claim includes:
   - The absolute value
   - The reporting period (e.g., FY2024)
   - The consolidation approach (if material)

5. **Map to IFRS:** If compliant, map the finding to `S2.29(a)(i)`. If not compliant, note missing requirements.

### 7.3 S2.29(a)(ii): Absolute Scope 2 GHG Emissions

**Requirement:** Entities must disclose absolute Scope 2 GHG emissions.

**Check:** Similar to Scope 1, but also verify:
- Whether location-based or market-based method is used (or both)
- If market-based, verify the approach is disclosed

### 7.4 S2.29(a)(iii): Absolute Scope 3 GHG Emissions by Category

**Requirement:** Entities must disclose absolute Scope 3 GHG emissions by category.

**Check:**

1. **Identify Scope 3 claim:** Find claims reporting Scope 3 emissions.

2. **Verify by category:** Verify emissions are reported by category (e.g., "Category 1: Purchased goods and services: 3.2M tCO2e", "Category 11: Use of sold products: 2.1M tCO2e").

3. **Verify total:** Verify a total Scope 3 value is provided (sum of categories).

4. **Check category alignment:** Verify categories align with GHG Protocol's 15 categories (if applicable).

5. **Map to IFRS:** Map to `S2.29(a)(iii)`.

### 7.5 S2.29(b-c): Physical and Transition Risk Exposure

**Requirement:** Entities must disclose the amount and percentage of assets/activities exposed to physical risks (S2.29(b)) and transition risks (S2.29(c)).

**Check:**

1. **Identify risk exposure claims:** Find claims reporting asset/activity exposure to climate risks.

2. **Verify amount and percentage:** Verify both absolute amount and percentage are reported.

3. **Verify risk type:** Verify whether physical or transition risk (or both) is specified.

4. **Map to IFRS:** Map to `S2.29(b)` or `S2.29(c)`.

### 7.6 S2.29(d): Capital Deployment Toward Climate Opportunities

**Requirement:** Entities must disclose capital deployment toward climate-related opportunities.

**Check:**

1. **Identify capital deployment claims:** Find claims reporting climate-related investments or capital allocation.

2. **Verify amount:** Verify an absolute amount is reported (e.g., "$2 billion").

3. **Verify context:** Verify the amount is contextualized (e.g., "% of total capex", "% of revenue").

4. **Map to IFRS:** Map to `S2.29(d)`.

### 7.7 S2.29(e): Internal Carbon Price

**Requirement:** Entities must disclose internal carbon pricing (if used).

**Check:**

1. **Identify carbon pricing claims:** Find claims mentioning internal carbon pricing.

2. **Verify disclosure:** If carbon pricing is used, verify:
   - The price per tCO2e
   - How it's applied (e.g., "used in capital allocation decisions")
   - The scope (Scope 1, 2, 3, or all)

3. **Check if required:** If the entity uses carbon pricing but doesn't disclose it, note as a gap.

4. **Map to IFRS:** Map to `S2.29(e)`.

### 7.8 S2.29(g): Climate-Linked Remuneration

**Requirement:** Entities must disclose whether climate performance is linked to remuneration.

**Check:**

1. **Identify remuneration claims:** Find claims mentioning executive compensation or remuneration linked to climate.

2. **Verify disclosure:** If climate-linked remuneration exists, verify:
   - How it's linked (e.g., "% of variable compensation")
   - Which metrics are used (e.g., "emission reduction targets", "renewable energy percentage")

3. **Check if required:** If climate-linked remuneration exists but isn't disclosed, note as a gap.

4. **Map to IFRS:** Map to `S2.29(g)`.

### 7.9 S2.33-36: Climate-Related Targets

**Requirement:** Entities must disclose climate-related targets with specific requirements (see Section 5.6).

**Check:** Perform the target achievability analysis (Section 5) and verify IFRS S2.33-36 compliance as part of that analysis.

### 7.10 IFRS Compliance Output

```python
class IFRSComplianceResult(BaseModel):
    claim_id: str
    ifrs_paragraphs: list[str]  # e.g., ["S2.29(a)(i)", "S2.29(a)(ii)"]
    compliance_status: Literal["compliant", "partially_compliant", "non_compliant", "not_applicable"]
    missing_requirements: list[str]  # e.g., ["baseline_period", "milestones"]
    compliance_details: dict  # Paragraph-specific compliance details
    reasoning: str
```

---

## 8. Inter-Agent Communication

### 8.1 Overview

The Data/Metrics Agent participates in the inter-agent communication protocol (PRD Section 5.4) to request cross-domain context that strengthens its quantitative analysis.

### 8.2 InfoRequest Scenarios

The agent shall post `InfoRequest` objects in the following scenarios:

1. **Industry benchmark data:** Request sector-specific emission intensities, energy consumption benchmarks, or reduction rate averages from the Academic/Research Agent.

2. **Geographic context:** Request geographic data from the Geography Agent for location-specific emissions validation (e.g., verifying facility-specific emission claims).

3. **Regulatory context:** Request IFRS S2 paragraph details from the Legal Agent for compliance assessment (though RAG retrieval is primary).

4. **Historical data:** Request prior year sustainability reports or public disclosures from the News/Media Agent or Academic/Research Agent.

### 8.3 InfoRequest Format

```python
InfoRequest(
    requesting_agent="data_metrics",
    description="Industry benchmark for emission intensity in manufacturing sector: tCO2e per $1M revenue. Need average intensity for companies with revenue $10B-$50B.",
    status="pending",
    metadata={
        "claim_id": "...",
        "request_type": "benchmark",
        "metric": "emission_intensity",
        "sector": "manufacturing"
    }
)
```

### 8.4 InfoResponse Processing

When the agent receives `InfoResponse` objects (via `state.info_responses`):

1. **Filter relevant responses:** Filter responses addressed to `"data_metrics"` or matching the request metadata.

2. **Extract data:** Extract benchmark data, geographic context, or other information from the response.

3. **Incorporate into analysis:** Use the received data in benchmark comparisons, geographic validations, or other checks.

4. **Document source:** Include the responding agent and data source in the finding.

### 8.5 InfoRequest Visibility

All InfoRequests and InfoResponses are emitted as `StreamEvent` objects (see Section 10) for visibility in the detective dashboard.

---

## 9. Findings Structure and Evidence Output

### 9.1 AgentFinding Schema

The agent creates `AgentFinding` objects (defined in FRD 0's `state.py`):

```python
AgentFinding(
    finding_id=str(generate_uuid7()),
    agent_name="data_metrics",
    claim_id=claim.claim_id,
    evidence_type="quantitative_validation",
    summary="Mathematical consistency check: Scope 1+2+3 totals verified. Target achievability: 42% reduction by 2030 requires 4.2% annual reduction rate, which is challenging but achievable given historical trends.",
    details={
        "consistency_checks": [
            {
                "check_name": "scope_addition",
                "result": "pass",
                "details": {...}
            },
            ...
        ],
        "unit_validation": {
            "units_valid": True,
            "methodology_aligned": True,
            ...
        },
        "benchmark_comparison": {
            "emission_intensity": {
                "reported": 0.5,
                "sector_average": 0.52,
                "assessment": "plausible"
            },
            ...
        },
        "target_achievability": {
            "assessment": "challenging",
            "required_annual_reduction": 4.2,
            ...
        },
        "historical_consistency": {
            "assessment": "consistent",
            ...
        },
        "ifrs_compliance": {
            "paragraphs": ["S2.29(a)(i)", "S2.33"],
            "compliance_status": "compliant",
            "missing_requirements": []
        }
    },
    supports_claim=True,  # True if validation supports the claim, False if inconsistencies found
    confidence=0.85,  # Confidence in the validation (0.0-1.0)
    iteration=state.iteration_count + 1
)
```

### 9.2 Evidence Summary Format

The `summary` field shall be a concise, human-readable summary (2-4 sentences) covering:

1. **Consistency check results:** Key consistency checks and their outcomes.

2. **Benchmark assessment:** Whether reported values are plausible.

3. **Target achievability:** Assessment of reduction targets (if applicable).

4. **IFRS compliance:** Key IFRS paragraph mappings and compliance status.

### 9.3 Details Structure

The `details` field contains structured validation results:

```python
{
    "consistency_checks": list[ConsistencyCheckResult],
    "unit_validation": {
        "units_valid": bool,
        "methodology_aligned": bool,
        "conversion_factors_appropriate": bool,
        "issues": list[str]
    },
    "benchmark_comparison": {
        "emission_intensity": BenchmarkComparison | None,
        "energy_consumption": BenchmarkComparison | None,
        "financial_impact": BenchmarkComparison | None
    },
    "target_achievability": TargetAchievabilityResult | None,
    "historical_consistency": HistoricalConsistencyResult | None,
    "ifrs_compliance": IFRSComplianceResult
}
```

### 9.4 Supports Claim Logic

The `supports_claim` field is determined by:

- **True:** All critical consistency checks pass, units are valid, benchmarks are plausible, targets are achievable (or challenging but reasonable), IFRS requirements are met.
- **False:** Critical inconsistencies found, invalid units, extreme outliers in benchmarks, unrealistic targets, major IFRS gaps.

### 9.5 Confidence Scoring

The `confidence` field (0.0-1.0) is calculated based on:

- **Data completeness:** Higher confidence if all required data is available.
- **Consistency check results:** Lower confidence if inconsistencies are found.
- **Benchmark data quality:** Higher confidence if benchmark data is from reliable sources (Academic/Research Agent vs. LLM knowledge).
- **Historical data availability:** Higher confidence if historical data is available for trend analysis.

---

## 10. StreamEvent Emissions

### 10.1 Event Types

The agent emits the following `StreamEvent` types:

| Event Type | Agent | Data Fields | When |
|---|---|---|---|
| `agent_started` | `data_metrics` | `{}` | Node begins execution |
| `agent_thinking` | `data_metrics` | `{"message": "..."}` | Progress updates during processing |
| `consistency_check` | `data_metrics` | `{"check_name": str, "claim_id": str, "result": "pass"\|"fail"\|"inconclusive", "details": dict}` | Each consistency check completes |
| `evidence_found` | `data_metrics` | `{"claim_id": str, "summary": str, "supports_claim": bool, "confidence": float}` | Each finding is created |
| `info_request_posted` | `data_metrics` | `{"description": str, "request_type": str}` | Agent posts an InfoRequest |
| `agent_completed` | `data_metrics` | `{"claims_processed": int, "findings_count": int, "consistency_checks_passed": int, "consistency_checks_failed": int}` | Node finishes successfully |

### 10.2 Consistency Check Events

Consistency check events are emitted for each check performed:

```python
StreamEvent(
    event_type="consistency_check",
    agent_name="data_metrics",
    data={
        "check_name": "scope_addition",
        "claim_id": "uuid-...",
        "result": "pass",  # or "fail", "inconclusive"
        "details": {
            "scope1": 2.3e6,
            "scope2": 1.1e6,
            "scope3": 8.5e6,
            "calculated_total": 11.9e6,
            "reported_total": 12.0e6,
            "discrepancy": 0.1e6,
            "discrepancy_percent": 0.83
        }
    },
    timestamp=datetime.utcnow().isoformat()
)
```

These events are consumed by the detective dashboard (FRD 12) to display the running consistency check list with pass/fail indicators.

### 10.3 Thinking Events

Thinking events provide real-time visibility into the agent's reasoning:

```python
StreamEvent(
    event_type="agent_thinking",
    agent_name="data_metrics",
    data={
        "message": "Validating Scope 1+2+3 totals for claim 'Total emissions: 12.0M tCO2e'..."
    },
    timestamp=datetime.utcnow().isoformat()
)
```

---

## 11. Model Configuration and Prompting

### 11.1 Model Configuration

| Parameter | Value | Rationale |
|---|---|---|
| Model | `anthropic/claude-sonnet-4-5` (`Models.CLAUDE_SONNET`) | Strong numerical reasoning, consistency checking, and ability to work with complex financial and emissions data (PRD Section 4.8) |
| Temperature | `0.1` | Low temperature for consistent, deterministic numerical analysis |
| Max output tokens | `8192` | Sufficient for structured validation results covering multiple checks per claim |
| Response format | JSON schema (structured output) | Ensures parseable validation results |

### 11.2 Prompt Structure

The agent constructs prompts for each claim (or claim group) following the template in Appendix A. The prompt includes:

1. **System prompt:** Role definition, validation scope, output format.

2. **Claim context:** The claim text, claim type, preliminary IFRS mappings.

3. **Document context:** Relevant surrounding text from the document (for extracting related values).

4. **Validation instructions:** Specific checks to perform (consistency, units, benchmarks, targets, IFRS compliance).

5. **Output schema:** Structured JSON schema for the validation results.

### 11.3 Structured Output Schema

The agent requests structured output matching:

```python
class QuantitativeValidationResult(BaseModel):
    """Complete validation result for a quantitative claim."""
    claim_id: str
    consistency_checks: list[ConsistencyCheckResult]
    unit_validation: UnitValidationResult
    benchmark_comparison: BenchmarkComparison | None  # None if benchmark data unavailable
    target_achievability: TargetAchievabilityResult | None  # None if not a target claim
    historical_consistency: HistoricalConsistencyResult | None  # None if historical data unavailable
    ifrs_compliance: IFRSComplianceResult
    summary: str
    supports_claim: bool
    confidence: float
    missing_data: list[str]  # e.g., ["baseline_value", "sector_benchmark"]
```

---

## 12. Error Handling

### 12.1 LLM Response Errors

| Error | Trigger | Handling |
|---|---|---|
| LLM returns non-JSON response | Claude Sonnet 4.5 fails to produce structured output | Retry once with a simplified prompt emphasizing JSON format; if still non-JSON, parse what is available using a lenient extractor |
| LLM returns malformed validation results | Validation results missing required fields or invalid types | Validate each result individually; discard invalid results with a logged warning; proceed with valid results |
| LLM timeout | OpenRouter API timeout (>60 seconds) | Retry up to 3 times (handled by OpenRouter client wrapper); on final failure, emit error StreamEvent and return partial findings for successfully processed claims |
| LLM rate limit | OpenRouter returns 429 | Exponential backoff retry (handled by OpenRouter client wrapper); propagate error after 3 retries |

### 12.2 Data Extraction Errors

| Error | Trigger | Handling |
|---|---|---|
| Cannot extract numerical values from claim | Claim text is ambiguous or lacks numerical data | Mark validation as "inconclusive"; note missing data in findings; proceed with other checks that don't require the missing data |
| Cannot identify related claims | Related claims (e.g., Scope 1, Scope 2, Total) are not found in the document | Mark consistency checks as "inconclusive"; note missing related claims in findings |
| Unit conversion failure | Unrecognized unit format | Mark unit validation as "fail"; note the unrecognized unit in findings |

### 12.3 Benchmark Data Errors

| Error | Trigger | Handling |
|---|---|---|
| InfoRequest for benchmark data receives no response | Academic/Research Agent doesn't respond or responds with no data | Proceed without benchmark comparison; note "benchmark_data_unavailable" in findings; use LLM knowledge as fallback if available |
| Benchmark data is invalid | InfoResponse contains malformed or implausible benchmark data | Validate benchmark data; if invalid, proceed without benchmark comparison; note "benchmark_data_invalid" in findings |

### 12.4 Graceful Degradation

The agent shall degrade gracefully when data is missing:

1. **Missing related claims:** If Scope 1, Scope 2, or Scope 3 claims are not found, skip scope addition check but perform other checks (unit validation, IFRS compliance).

2. **Missing benchmark data:** If benchmark data is unavailable, perform other checks and note benchmark comparison as "inconclusive".

3. **Missing historical data:** If historical data is unavailable, skip historical consistency checks but perform other checks.

4. **Partial findings:** Return findings for successfully processed claims even if some claims fail validation.

---

## 13. Exit Criteria

FRD 7 is complete when ALL of the following are satisfied:

| # | Criterion | Verification |
|---|---|---|
| 1 | Data/Metrics Agent node executes successfully | Start analysis on a report with quantitative claims; verify the `investigate_data` node runs and processes assigned claims |
| 2 | Agent receives routed claims from Orchestrator | Verify the agent filters `state.claims` correctly based on `state.routing_plan` |
| 3 | Internal consistency checks are performed | Verify scope addition checks, YoY percentage validation, baseline consistency checks are executed |
| 4 | Scope 1+2+3 addition check works correctly | Test with a claim reporting all three scopes and a total; verify the check passes if totals match and fails if they don't |
| 5 | Unit validation works | Test with claims using correct units (tCO2e) and incorrect units; verify validation passes/fails appropriately |
| 6 | Methodology validation checks GHG Protocol alignment | Test with claims mentioning GHG Protocol vs. claims with no methodology; verify validation assesses alignment |
| 7 | Benchmark comparison requests data via InfoRequest | Verify the agent posts InfoRequests to Academic/Research Agent for benchmark data |
| 8 | Benchmark comparison incorporates received data | Verify the agent processes InfoResponses and includes benchmark comparisons in findings |
| 9 | Target achievability analysis works | Test with a reduction target claim; verify the agent calculates required annual reduction rate and assesses achievability |
| 10 | Interim target consistency check works | Test with claims reporting multiple interim targets; verify consistency is checked |
| 11 | Historical consistency checks work | Test with claims reporting prior year data; verify YoY consistency is checked |
| 12 | IFRS S2.27-37 compliance assessment works | Test with emissions and target claims; verify the agent maps findings to specific IFRS paragraphs (S2.29(a)(i-iii), S2.33-36, etc.) |
| 13 | Findings are created for each claim | Verify each processed claim produces an `AgentFinding` object |
| 14 | Findings include all required fields | Verify findings include: summary, consistency checks, unit validation, benchmark comparison, target achievability, IFRS compliance |
| 15 | StreamEvents are emitted | Verify `agent_started`, `agent_thinking`, `consistency_check`, `evidence_found`, `agent_completed` events are emitted |
| 16 | Consistency check events are emitted | Verify each consistency check produces a `consistency_check` StreamEvent |
| 17 | Detective dashboard displays consistency checks | Verify the Data/Metrics Agent node in the dashboard shows a running list of consistency checks with pass/fail indicators (FRD 12) |
| 18 | Inter-agent communication works | Verify InfoRequests are posted and InfoResponses are processed |
| 19 | Agent handles missing data gracefully | Test with claims missing related values; verify the agent skips checks requiring missing data but performs other checks |
| 20 | Agent handles errors gracefully | Simulate an LLM failure; verify the agent emits error StreamEvents and returns partial findings for successfully processed claims |
| 21 | Findings flow to Judge Agent | Verify findings are written to `state.findings` and are available to the Judge Agent |
| 22 | Agent completes execution | Verify the agent updates `agent_status` to "completed" and emits `agent_completed` event |

---

## Appendix A: Data/Metrics Agent Prompt Template

### A.1 System Prompt

```
You are the Data/Metrics Agent in Sibyl, an AI system that verifies sustainability reports against IFRS S1/S2 disclosure standards. Your task is to validate quantitative and numerical claims for mathematical consistency, methodological alignment, and benchmark plausibility.

## Validation Scope

For each quantitative claim assigned to you, perform the following validations:

1. **Internal Consistency Checks:**
   - Verify that Scope 1 + Scope 2 + Scope 3 = Total (if all components are reported)
   - Verify year-over-year percentage changes match underlying numbers
   - Verify baseline years are applied consistently
   - Verify recalculation adjustments are applied consistently
   - Verify percentage calculations are mathematically correct

2. **Unit and Methodology Validation:**
   - Verify emissions are reported in correct units (tCO2e, MtCO2e, etc.)
   - Verify conversion factors are appropriate (GWP values, activity data conversions)
   - Verify methodology aligns with GHG Protocol standards
   - Check IFRS S2.27-31 requirements for measurement approach disclosure

3. **Benchmark Comparison:**
   - Compare reported emission intensities against industry sector averages (if benchmark data is available)
   - Compare energy consumption against sector benchmarks
   - Compare financial impacts against industry norms
   - Assess whether reported values are plausible for the company's sector and size

4. **Target Achievability Analysis:**
   - Extract target components (baseline year, baseline value, target year, target value/percentage)
   - Calculate required annual reduction rate
   - Compare against historical trends (if available)
   - Compare against industry benchmarks (if available)
   - Assess whether the target is mathematically achievable
   - Verify interim targets are consistent with long-term goals
   - Check IFRS S2.33-36 compliance (baseline period, milestones, progress)

5. **Historical Consistency Checks:**
   - Compare reported values against prior year data (if available)
   - Verify year-over-year changes are consistent
   - Check for unexplained deviations or restatements
   - Verify methodology changes are explained

6. **IFRS S2.27-37 Compliance Assessment:**
   - Check for absolute Scope 1 emissions disclosure (S2.29(a)(i))
   - Check for absolute Scope 2 emissions disclosure (S2.29(a)(ii))
   - Check for absolute Scope 3 emissions by category (S2.29(a)(iii))
   - Check for emission intensity metrics
   - Check for climate-related targets with baseline periods and milestones (S2.33-36)
   - Check for internal carbon pricing disclosure (S2.29(e))
   - Check for climate-linked remuneration disclosure (S2.29(g))

## Output Format

Return a structured JSON object matching the specified schema. For each validation, provide:
- Result: "pass", "fail", or "inconclusive"
- Details: Check-specific information (values, calculations, discrepancies)
- Severity: "critical", "warning", or "info"
- Message: Human-readable summary

If data is missing for a particular check (e.g., benchmark data unavailable, historical data not found), mark that check as "inconclusive" and note the missing data.
```

### A.2 User Prompt Template

```
Validate the following quantitative claim for mathematical consistency, methodological alignment, and benchmark plausibility.

Claim:
{claim_text}

Claim Type: {claim_type}
Preliminary IFRS Mappings: {ifrs_paragraphs}
Source Page: {source_page}

Related Claims (for consistency checks):
{related_claims_json}

Document Context (surrounding text):
{document_context}

Available Benchmark Data (if any):
{benchmark_data_json}

Historical Data (if any):
{historical_data_json}

Perform all applicable validations and return a structured JSON object matching the specified schema.
```

---

## Appendix B: Consistency Check Definitions

### B.1 Scope Addition Check

**Check Name:** `scope_addition`

**Description:** Verifies that Scope 1 + Scope 2 + Scope 3 emissions equal the reported total.

**Input:** Scope 1 value, Scope 2 value, Scope 3 value (or sum of Scope 3 categories), reported total value.

**Calculation:** `calculated_total = Scope1 + Scope2 + Scope3`

**Tolerance:** 1% of reported total (to account for rounding).

**Output:**
- `result`: "pass" if within tolerance, "fail" otherwise
- `details`: `{"scope1": float, "scope2": float, "scope3": float, "calculated_total": float, "reported_total": float, "discrepancy": float, "discrepancy_percent": float}`

### B.2 Year-Over-Year Percentage Check

**Check Name:** `yoy_percentage`

**Description:** Verifies that reported percentage change matches the calculated percentage change from prior and current values.

**Input:** Prior year value, current year value, reported percentage change.

**Calculation:** `calculated_pct = ((current - prior) / prior) * 100`

**Tolerance:** 0.1 percentage points.

**Output:**
- `result`: "pass" if within tolerance, "fail" otherwise
- `details`: `{"prior_value": float, "current_value": float, "calculated_pct": float, "reported_pct": float, "discrepancy": float}`

### B.3 Baseline Consistency Check

**Check Name:** `baseline_consistency`

**Description:** Verifies that baseline years are applied consistently across related claims.

**Input:** List of claims mentioning baseline years, grouped by metric type.

**Output:**
- `result`: "pass" if all claims use the same baseline year (or deviations are explained), "fail" otherwise
- `details`: `{"baseline_years": list[int], "inconsistencies": list[str]}`

### B.4 Recalculation Adjustment Check

**Check Name:** `recalculation_consistency`

**Description:** Verifies that recalculation adjustments are applied consistently across related claims.

**Input:** Claims mentioning recalculation adjustments.

**Output:**
- `result`: "pass" if recalculation is applied consistently, "fail" otherwise
- `details`: `{"recalculation_claims": list[str], "inconsistencies": list[str]}`

### B.5 Percentage Calculation Check

**Check Name:** `percentage_calculation`

**Description:** Verifies that percentage calculations are mathematically correct.

**Input:** Numerator value, denominator value, reported percentage.

**Calculation:** `calculated_pct = (numerator / denominator) * 100`

**Tolerance:** 0.1 percentage points.

**Output:**
- `result`: "pass" if within tolerance, "fail" otherwise
- `details`: `{"numerator": float, "denominator": float, "calculated_pct": float, "reported_pct": float, "discrepancy": float}`

---

## Appendix C: Unit Conversion Reference

### C.1 Emissions Units

| Unit | Abbreviation | Conversion to tCO2e |
|---|---|---|
| Tonnes CO2e | tCO2e | 1.0 |
| Kilotonnes CO2e | ktCO2e | 1,000 |
| Megatonnes CO2e | MtCO2e | 1,000,000 |
| Gigatonnes CO2e | GtCO2e | 1,000,000,000 |

### C.2 Common Conversion Factors

| Conversion | Factor | Notes |
|---|---|---|
| kWh to tCO2e (grid average) | Varies by region | Typically 0.0004-0.0008 tCO2e per kWh (depends on grid mix) |
| MWh to tCO2e | Varies by region | Typically 0.4-0.8 tCO2e per MWh |
| GJ to tCO2e (natural gas) | ~0.05 tCO2e per GJ | Depends on gas composition |
| Liters gasoline to tCO2e | ~0.0023 tCO2e per liter | Approximate |

### C.3 GWP Values (AR6)

| Gas | GWP-100 | Notes |
|---|---|---|
| CO2 | 1 | Reference gas |
| CH4 | 27.9 | Methane |
| N2O | 273 | Nitrous oxide |
| SF6 | 25,200 | Sulfur hexafluoride |

---

## Appendix D: IFRS S2.27-37 Requirements Checklist

### D.1 S2.29(a): GHG Emissions

- [ ] **S2.29(a)(i):** Absolute Scope 1 GHG emissions disclosed
- [ ] **S2.29(a)(ii):** Absolute Scope 2 GHG emissions disclosed (location-based or market-based, or both)
- [ ] **S2.29(a)(iii):** Absolute Scope 3 GHG emissions disclosed by category
- [ ] **S2.30:** Measurement approach and inputs disclosed
- [ ] **S2.30:** Disaggregation by constituent gas (if material)
- [ ] **S2.31:** Consolidation approach disclosed

### D.2 S2.29(b-c): Risk Exposure

- [ ] **S2.29(b):** Amount and percentage of assets/activities exposed to physical risks disclosed
- [ ] **S2.29(c):** Amount and percentage of assets/activities exposed to transition risks disclosed

### D.3 S2.29(d-e, g): Other Metrics

- [ ] **S2.29(d):** Capital deployment toward climate-related opportunities disclosed
- [ ] **S2.29(e):** Internal carbon price disclosed (if used)
- [ ] **S2.29(g):** Climate-linked remuneration disclosed

### D.4 S2.33-36: Climate-Related Targets

- [ ] **S2.33:** Metric used (absolute or intensity) disclosed
- [ ] **S2.34:** Baseline period and base year emissions disclosed
- [ ] **S2.34:** Time horizon and milestones disclosed
- [ ] **S2.34:** Interim targets disclosed (if applicable)
- [ ] **S2.35:** Sector decarbonization approach disclosed (if applicable)
- [ ] **S2.35:** Third-party validation (e.g., SBTi) disclosed (if applicable)
- [ ] **S2.36:** Progress against each target disclosed

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| Claude Sonnet 4.5 for numerical reasoning over Gemini 3 Flash | PRD explicitly specifies Claude Sonnet 4.5 for the Data/Metrics Agent (Section 4.8). Sonnet 4.5 has stronger numerical reasoning capabilities than Gemini Flash, which is critical for complex mathematical consistency checks and target achievability analysis. |
| Structured JSON output over free-text analysis | Structured output ensures parseable validation results that can be programmatically processed, displayed in the dashboard, and incorporated into findings. Free-text analysis would require complex parsing and be less reliable. |
| Percentage-based tolerance (1% for totals, 0.1pp for percentages) over exact matching | Real-world reporting involves rounding, so exact matching would produce false positives. Percentage-based tolerance accounts for rounding while still catching significant discrepancies. |
| InfoRequest for benchmark data over hardcoded benchmarks | Industry benchmarks vary by sector, region, and company size. Hardcoding benchmarks would be inaccurate and inflexible. Requesting benchmarks from the Academic/Research Agent ensures up-to-date, sector-specific data. |
| Per-claim processing over batch processing | Each quantitative claim may require different validation checks (some are emissions, some are targets, some are financial). Per-claim processing allows focused, claim-specific validation. Batch processing would be less efficient and less accurate. |
| Graceful degradation when data is missing | Missing related claims, benchmark data, or historical data should not prevent the agent from performing other validations. Graceful degradation ensures maximum value is extracted from available data. |
| Consistency check events emitted individually over aggregated events | Individual events enable real-time display in the detective dashboard (FRD 12), showing pass/fail indicators as checks complete. Aggregated events would delay visibility and reduce transparency. |
| IFRS S2.27-37 compliance assessment integrated into validation over separate pass | IFRS compliance is a core validation dimension. Integrating it into the main validation pass ensures compliance is assessed alongside consistency and plausibility, producing a unified finding. |
| Target achievability analysis includes mathematical achievability over only IFRS compliance | Mathematical achievability (required reduction rate vs. historical/industry rates) is critical for detecting unrealistic targets that may indicate greenwashing. IFRS compliance alone would miss this dimension. |
| Historical consistency checks attempt retrieval via InfoRequest over requiring prior data in document | Prior year data may not be in the current document. Attempting retrieval via InfoRequest maximizes the chance of finding historical data for consistency checks, improving validation quality. |
| Unit normalization before comparison over comparing values in original units | Normalizing all values to tCO2e before comparison ensures accurate arithmetic (e.g., Scope 1 in MtCO2e + Scope 2 in tCO2e). Comparing in original units would require complex unit-aware arithmetic. |
| Confidence scoring based on data completeness and check results over binary pass/fail | Confidence scoring provides nuance: a claim may pass checks but with low confidence if data is incomplete, or fail checks but with high confidence if the failure is clear. This helps the Judge Agent make better decisions. |
| Re-investigation handling focuses on Judge's evidence gaps over re-running all checks | When the Judge requests re-investigation, it identifies specific gaps (e.g., "need benchmark data", "verify baseline value"). Focusing on these gaps is more efficient than re-running all checks. |
