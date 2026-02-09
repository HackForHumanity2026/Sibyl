# Feature Requirements Document: FRD 9 -- Academic/Research Agent (v1.0)

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.3](../PRD.md) |
| **FRD Order** | [FRD Order](../FRD-order.md) |
| **PRD Sections** | 4.7 (Academic/Industry Research Agent -- Technical Verification) |
| **Type** | Feature |
| **Depends On** | FRD 5 (Orchestrator Agent & LangGraph Pipeline), FRD 8 (News/Media Agent -- reuses web search tool) |
| **Delivers** | Technical validation against academic literature and industry benchmarks, methodology validation, benchmark comparison, LangGraph node implementation, inter-agent communication participation |
| **Created** | 2026-02-09 |

---

## Summary

FRD 9 delivers the Academic/Research Agent -- a specialist investigation agent in the Sibyl multi-agent pipeline that validates technical and scientific claims against peer-reviewed research, industry benchmarks, and recognized standards. The Academic/Research Agent (`app/agents/academic_agent.py`) replaces the FRD 5 stub with a functional LangGraph node that receives routed technical claims from the Orchestrator (FRD 5), constructs academic search queries targeting peer-reviewed papers, industry benchmark databases, CDP disclosures, SBTi frameworks, and GHG Protocol standards, performs web searches using the `search_web.py` tool from FRD 8, analyzes search results to assess methodology validity, certification legitimacy, benchmark plausibility, and research support, and returns structured findings with academic references, benchmark comparisons, and methodology assessments. The agent validates emission reduction methodologies, renewable energy certifications, carbon offset legitimacy, science-based target alignment, emission intensity plausibility, and technology/practice support claims. The agent participates in the inter-agent communication protocol (InfoRequest/InfoResponse) and handles re-investigation requests from the Judge Agent with refined queries. The Academic/Research Agent uses DeepSeek V3.2 (fast and cost-effective for research synthesis) and emits StreamEvent objects for real-time detective dashboard visualization. After FRD 9, technical claims are validated against academic literature and industry benchmarks, returning referenced findings that contribute to the Judge Agent's evidence evaluation.

---

## Given Context (Preconditions)

The following are assumed to be in place from prior FRDs:

| Prerequisite | Source FRD | Deliverable |
|---|---|---|
| LangGraph StateGraph with `investigate_academic` node stub | FRD 5 | `app/agents/graph.py` |
| `SibylState` Pydantic schema with `AgentFinding`, `InfoRequest`, `InfoResponse`, `ReinvestigationRequest`, `StreamEvent` | FRD 5 | `app/agents/state.py` |
| Orchestrator routing logic assigning technical claims to Academic/Research Agent | FRD 5 | `app/agents/orchestrator_agent.py` |
| Web search tool (`search_web.py`) with web search capabilities | FRD 8 | `app/agents/tools/search_web.py` |
| Inter-agent communication protocol (InfoRequest/InfoResponse) | FRD 5 | Shared state mechanism |
| Re-investigation handling in Orchestrator | FRD 5 | `ReinvestigationRequest` processing |
| SSE streaming infrastructure | FRD 5 | `StreamEvent` emission and SSE endpoint |
| OpenRouter client wrapper with retry logic | FRD 0 | `app/services/openrouter_client.py` |
| `Models.DEEPSEEK_V3` constant | FRD 0 | `app/services/openrouter_client.py` |
| `AgentFinding` SQLAlchemy model | FRD 0 | `app/models/finding.py` |
| Academic/Research Agent stub (`investigate_academic` function signature) | FRD 5 | `app/agents/academic_agent.py` |
| Claim routing to Academic/Research Agent based on claim type and content | FRD 5 | Routing plan assignments |

### Terms

| Term | Definition |
|---|---|---|
| Academic search query | A structured search query targeting peer-reviewed academic papers, typically using Google Scholar-style syntax or specific journal databases |
| Industry benchmark | Sector-specific emission intensity metrics, best practice standards, or performance comparisons published by industry associations, CDP, or research organizations |
| Methodology validation | Assessment of whether a claimed emissions calculation method, reduction approach, or measurement technique aligns with recognized standards (GHG Protocol, SBTi, ISO 14064) |
| Certification legitimacy | Verification that renewable energy certificates, carbon offsets, or other environmental certifications are from recognized registries and meet validity criteria |
| Science-based target | A climate target aligned with the Science Based Targets initiative (SBTi) framework, requiring specific validation criteria and pathway alignment |
| Benchmark comparison | Quantitative comparison of reported metrics (e.g., emission intensities) against peer-reviewed research findings or industry benchmark databases |
| CDP disclosure | Carbon Disclosure Project data from comparable companies in the same industry sector, used for benchmark comparison |
| SBTi framework | Science Based Targets initiative methodologies and validation criteria for net-zero and emission reduction targets |
| GHG Protocol | Greenhouse Gas Protocol standards for Scope 1, 2, and 3 emissions accounting and reporting |
| Research synthesis | The process of analyzing multiple academic sources to extract consensus findings, methodology assessments, or benchmark ranges |

---

## Executive Summary (Gherkin-Style)

```gherkin
Feature: Academic/Research Agent

  Background:
    Given  FRD 5 and FRD 8 are complete
    And    all services are running (backend, frontend, PostgreSQL, Redis)
    And    the LangGraph pipeline is executing with routed technical claims
    And    the web search tool from FRD 8 is available
    And    claims have been routed to the Academic/Research Agent by the Orchestrator

  Scenario: Academic/Research Agent receives routed technical claims
    Given  the Orchestrator has created a routing plan assigning technical claims to the Academic/Research Agent
    When   the investigate_academic node executes
    Then   it receives claims assigned to the "academic" agent from the routing plan
    And    it filters claims to those requiring academic/research validation
    And    it groups related claims for efficient batch processing

  Scenario: Agent constructs academic search queries
    Given  the agent has received technical claims to investigate
    When   it analyzes each claim
    Then   it constructs targeted academic search queries
    And    queries target peer-reviewed papers, industry benchmarks, CDP disclosures, SBTi frameworks, or GHG Protocol standards
    And    queries use appropriate search syntax (Google Scholar-style, journal-specific, database-specific)
    And    queries include relevant keywords, methodology terms, and industry sector identifiers

  Scenario: Agent performs web searches for academic sources
    Given  the agent has constructed search queries
    When   it invokes the search_web tool from FRD 8
    Then   it searches for peer-reviewed academic papers on emissions methodologies
    And    it searches for industry benchmark reports and sector-specific emission intensities
    And    it searches for CDP disclosures from comparable companies
    And    it searches for SBTi methodology documentation and validation frameworks
    And    it searches for GHG Protocol standards and guidance documents
    And    search results include source URLs, titles, publication dates, and snippets

  Scenario: Agent validates emission reduction methodologies
    Given  a claim asserts a specific emission reduction methodology
    When   the agent searches for academic papers and standards on that methodology
    Then   it assesses whether the methodology is scientifically valid
    And    it checks alignment with GHG Protocol, ISO 14064, or other recognized standards
    And    it identifies any peer-reviewed research supporting or contradicting the methodology
    And    it produces a methodology assessment finding

  Scenario: Agent validates renewable energy certifications
    Given  a claim asserts renewable energy certification (e.g., "100% renewable electricity")
    When   the agent searches for certification standards and registries
    Then   it verifies the certification type is recognized (RECs, I-RECs, GOs, etc.)
    And    it checks whether the certification meets legitimacy criteria
    And    it identifies any academic research on certification validity or greenwashing risks
    And    it produces a certification assessment finding

  Scenario: Agent validates carbon offset legitimacy
    Given  a claim references carbon offsets or carbon credits
    When   the agent searches for offset standards and academic research
    Then   it verifies the offset standard is recognized (VCS, Gold Standard, CDM, etc.)
    And    it checks academic research on offset additionality, permanence, and leakage risks
    And    it identifies any controversies or legitimacy concerns in peer-reviewed literature
    And    it produces an offset assessment finding

  Scenario: Agent validates science-based targets
    Given  a claim asserts SBTi-aligned targets or net-zero commitments
    When   the agent searches for SBTi framework documentation and validation criteria
    Then   it checks whether the target structure aligns with SBTi requirements
    And    it verifies baseline year, scope, and pathway alignment claims
    And    it identifies any discrepancies between claimed SBTi validation and actual requirements
    And    it produces an SBTi validation finding

  Scenario: Agent performs benchmark comparison
    Given  a claim reports emission intensities or other quantitative metrics
    When   the agent searches for industry benchmark data and peer-reviewed research
    Then   it retrieves sector-specific emission intensity benchmarks
    And    it compares reported metrics against benchmark ranges
    And    it identifies whether reported values are plausible for the industry sector
    And    it produces a benchmark comparison finding with quantitative ranges

  Scenario: Agent validates technology and practice support
    Given  a claim asserts a specific technology or practice reduces emissions
    When   the agent searches for peer-reviewed research on that technology/practice
    Then   it identifies academic papers evaluating the technology's effectiveness
    And    it extracts consensus findings on emission reduction potential
    And    it identifies any contradictory research or limitations
    And    it produces a research support finding

  Scenario: Agent structures findings with references
    Given  the agent has gathered evidence from searches
    When   it produces findings
    Then   each finding includes academic references (paper titles, authors, publication dates, URLs)
    And    each finding includes benchmark comparisons with source citations
    And    each finding includes methodology assessments with standard references
    And    each finding includes a plain-language summary of whether evidence supports the claim
    And    findings are stored as AgentFinding objects in the shared state

  Scenario: Agent participates in inter-agent communication
    Given  the agent determines it needs cross-domain context
    When   it posts an InfoRequest to the shared state
    Then   the Orchestrator routes the request to the appropriate specialist agent(s)
    And    the agent receives InfoResponse objects with the requested context
    And    the agent incorporates the cross-domain context into its investigation
    And    all communication is visible in the SSE stream

  Scenario: Agent handles re-investigation requests
    Given  the Judge Agent has requested re-investigation with refined queries
    When   the Orchestrator re-routes the request to the Academic/Research Agent
    Then   the agent receives the refined queries and evidence gap description
    And    it performs targeted searches addressing the specific gaps
    And    it produces updated findings with the additional evidence
    And    it includes the iteration count in the findings

  Scenario: Agent emits streaming events
    Given  the agent is executing
    When   it processes claims and performs searches
    Then   it emits StreamEvent objects with event_type = "agent_started"
    And    it emits StreamEvent objects with event_type = "agent_thinking" showing progress
    And    it emits StreamEvent objects with event_type = "evidence_found" for each finding
    And    it emits StreamEvent objects with event_type = "agent_completed" with summary
    And    events are streamed to the frontend via SSE for the detective dashboard
```

---

## Table of Contents

1. [Academic/Research Agent Implementation](#1-academicresearch-agent-implementation)
2. [Claim Filtering and Grouping](#2-claim-filtering-and-grouping)
3. [Academic Search Query Construction](#3-academic-search-query-construction)
4. [Web Search Execution](#4-web-search-execution)
5. [Methodology Validation](#5-methodology-validation)
6. [Certification and Offset Validation](#6-certification-and-offset-validation)
7. [Science-Based Target Validation](#7-science-based-target-validation)
8. [Benchmark Comparison](#8-benchmark-comparison)
9. [Research Support Validation](#9-research-support-validation)
10. [Finding Structure and Output](#10-finding-structure-and-output)
11. [Inter-Agent Communication](#11-inter-agent-communication)
12. [Re-Investigation Handling](#12-re-investigation-handling)
13. [Model Configuration and LLM Usage](#13-model-configuration-and-llm-usage)
14. [Error Handling](#14-error-handling)
15. [Exit Criteria](#15-exit-criteria)
16. [Appendix A: Academic Search Query Templates](#appendix-a-academic-search-query-templates)
17. [Appendix B: Methodology Validation Frameworks](#appendix-b-methodology-validation-frameworks)
18. [Appendix C: Benchmark Database References](#appendix-c-benchmark-database-references)
19. [Appendix D: Example Findings](#appendix-d-example-findings)
20. [Design Decisions Log](#design-decisions-log)

---

## 1. Academic/Research Agent Implementation

### 1.1 Overview

The Academic/Research Agent (`app/agents/academic_agent.py`) replaces the FRD 5 stub with a functional LangGraph node that validates technical and scientific claims against peer-reviewed research, industry benchmarks, and recognized standards as described in PRD Section 4.7.

### 1.2 Node Function

```python
async def investigate_academic(state: SibylState) -> dict:
    """Academic/Research Agent: Validate technical claims against academic literature and benchmarks.

    Reads: state.routing_plan, state.claims, state.agent_status,
           state.info_requests, state.reinvestigation_requests,
           state.iteration_count, state.findings
    Writes: state.findings, state.agent_status, state.info_requests,
            state.info_responses, state.events

    Responsibilities:
    1. Receive routed technical claims from the Orchestrator.
    2. Construct academic search queries targeting peer-reviewed papers, benchmarks, standards.
    3. Execute web searches using the search_web tool from FRD 8.
    4. Analyze search results to validate methodologies, certifications, targets, benchmarks.
    5. Produce structured findings with academic references and assessments.
    6. Participate in inter-agent communication (InfoRequest/InfoResponse).
    7. Handle re-investigation requests with refined queries.

    Returns:
        Partial state update with findings, agent status, and events.
    """
```

### 1.3 Processing Steps

The `investigate_academic` node shall execute the following steps:

1. **Emit start event:** Append a `StreamEvent` with `event_type = "agent_started"`, `agent_name = "academic"`.

2. **Identify assigned claims:** Filter `state.routing_plan` to find `RoutingAssignment` objects where `"academic"` is in `assigned_agents`. Extract the corresponding `Claim` objects from `state.claims`.

3. **Group claims by investigation type:** Group claims into categories:
   - Methodology validation (emission reduction methods, calculation approaches)
   - Certification validation (renewable energy, carbon offsets)
   - Target validation (SBTi, net-zero commitments)
   - Benchmark comparison (emission intensities, sector metrics)
   - Research support (technology effectiveness, practice validation)

4. **Construct search queries:** For each claim group, construct targeted academic search queries (see Section 3).

5. **Execute web searches:** Invoke the `search_web` tool from FRD 8 for each query, collecting search results.

6. **Analyze results with LLM:** Use DeepSeek V3.2 to analyze search results, extract relevant information, and assess claim validity (see Section 13).

7. **Produce findings:** Create `AgentFinding` objects for each claim with evidence summaries, references, and assessments.

8. **Emit progress events:** During processing, emit `StreamEvent` objects with `event_type = "agent_thinking"` showing current investigation status.

9. **Process InfoRequests:** Check for pending `InfoRequest` objects addressed to the Academic/Research Agent; process and respond via `InfoResponse`.

10. **Emit completion event:** Append a `StreamEvent` with `event_type = "agent_completed"`, `agent_name = "academic"`, including findings summary.

11. **Return partial state:** Return updated `findings`, `agent_status`, `info_responses`, and `events`.

### 1.4 Agent Status Management

The agent shall update its status in `state.agent_status`:

```python
agent_status["academic"] = AgentStatus(
    agent_name="academic",
    status="working",
    claims_assigned=len(assigned_claims),
    claims_completed=0,
)
```

Status transitions:
- `idle` → `working`: When the node begins execution (set by the agent)
- `working` → `completed`: When all claims are processed successfully (set by the agent)
- `working` → `error`: On unhandled exception (set by error handler)

---

## 2. Claim Filtering and Grouping

### 2.1 Claim Type Filtering

The Academic/Research Agent primarily handles claims of types that require technical validation:

| Claim Type | Handled By Academic Agent | Rationale |
|---|---|---|
| `quantitative` | Yes (if technical) | Emission figures, intensities, reduction percentages need benchmark validation |
| `strategic` | Yes (if SBTi/target-related) | Net-zero commitments, SBTi targets need framework validation |
| `environmental` | Yes (if certification-related) | Renewable energy claims, carbon offsets need certification validation |
| `geographic` | No (Geography Agent) | Geographic claims are handled by Geography Agent |
| `legal_governance` | No (Legal Agent) | Governance claims are handled by Legal Agent |

### 2.2 Content-Based Filtering

Beyond claim type, the agent filters claims based on content keywords:

**Include claims containing:**
- Methodology terms: "emission reduction methodology", "calculation method", "accounting standard", "GHG Protocol", "ISO 14064"
- Certification terms: "renewable energy certificate", "REC", "I-REC", "carbon offset", "carbon credit", "VCS", "Gold Standard"
- Target terms: "science-based target", "SBTi", "net-zero", "1.5°C pathway", "SBTi validated"
- Benchmark terms: "emission intensity", "sector benchmark", "industry average", "peer comparison"
- Technology terms: "technology reduces emissions", "practice reduces carbon", "innovation"

**Exclude claims:**
- Pure governance structures (handled by Legal Agent)
- Pure geographic locations (handled by Geography Agent)
- Pure news/media events (handled by News/Media Agent)

### 2.3 Claim Grouping Strategy

Claims are grouped to enable efficient batch processing:

| Group | Criteria | Processing Approach |
|---|---|---|
| **Methodology** | Claims mentioning calculation methods, accounting standards, reduction approaches | Single search query covering multiple related methodologies |
| **Certification** | Claims mentioning renewable energy certificates, carbon offsets, environmental certifications | Batch validation against certification registries and standards |
| **SBTi/Targets** | Claims mentioning science-based targets, net-zero commitments, SBTi validation | Single search query for SBTi framework documentation and validation criteria |
| **Benchmark** | Claims reporting quantitative metrics (emission intensities, percentages) | Batch benchmark comparison against sector databases |
| **Research Support** | Claims asserting technology or practice effectiveness | Grouped by technology/practice type for consolidated research review |

### 2.4 Re-Investigation Context

When processing re-investigation requests, the agent receives `ReinvestigationRequest` objects with:
- `refined_queries`: Specific search queries from the Judge
- `evidence_gap`: Description of what additional evidence is needed
- `required_evidence`: Specific evidence types requested

The agent prioritizes these refined queries over initial investigation queries.

---

## 3. Academic Search Query Construction

### 3.1 Query Types

The agent constructs different query types depending on the investigation need:

| Query Type | Target Sources | Query Structure |
|---|---|---|
| **Academic Papers** | Google Scholar, arXiv, journal databases | `"{methodology} emissions reduction peer-reviewed"`, `"{technology} carbon footprint research"` |
| **Industry Benchmarks** | CDP, industry associations, research reports | `"{industry} emission intensity benchmark"`, `"{sector} Scope 1 emissions per revenue"` |
| **CDP Disclosures** | CDP database, company disclosures | `"CDP {company_name} {year} emissions"`, `"CDP {industry} disclosure benchmark"` |
| **SBTi Frameworks** | SBTi website, methodology documents | `"SBTi methodology {target_type}"`, `"SBTi validation criteria net-zero"` |
| **GHG Protocol** | GHG Protocol website, standards documents | `"GHG Protocol Scope {N} calculation"`, `"GHG Protocol {methodology} guidance"` |
| **Certification Standards** | Certification registries, standard documents | `"{certification_type} standard validity"`, `"{registry} renewable energy certificate"` |

### 3.2 Query Construction Rules

The system shall construct queries using the following rules:

1. **Extract key terms from claim:** Identify methodology names, technology types, certification types, target structures, and quantitative metrics.

2. **Add domain-specific modifiers:**
   - For academic papers: Add "peer-reviewed", "research", "study", "journal"
   - For benchmarks: Add "benchmark", "industry average", "sector comparison"
   - For standards: Add "standard", "methodology", "guidance", "framework"

3. **Include industry sector:** If the claim mentions an industry sector or the report's company is in a known sector, add sector terms to narrow results.

4. **Use Boolean operators:** Construct queries with AND/OR operators where appropriate (e.g., `"(emission reduction) AND (methodology) AND (peer-reviewed)"`).

5. **Target specific sources:** For standards and frameworks, prefer direct queries to official sources (e.g., `"site:sciencebasedtargets.org methodology"`).

### 3.3 Query Templates

See Appendix A for detailed query templates for each investigation type.

### 3.4 Query Optimization

To manage search volume and latency:

1. **Batch related queries:** Group claims with similar investigation needs into a single query.
2. **Limit query count:** Target a maximum of 10-15 queries per claim batch to avoid excessive API calls.
3. **Prioritize high-priority claims:** Construct more detailed queries for high-priority claims.
4. **Cache common queries:** Cache results for standard queries (e.g., "GHG Protocol Scope 3 calculation") that are reused across multiple reports.

---

## 4. Web Search Execution

### 4.1 Tool Integration

The agent uses the `search_web` tool from FRD 8:

```python
from app.agents.tools.search_web import search_web

# Example usage
results = await search_web(
    query="emission reduction methodology peer-reviewed research",
    max_results=10,
    source_types=["academic", "research"]
)
```

### 4.2 Search Result Structure

The `search_web` tool returns results in the following format (from FRD 8):

```python
class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source_type: str  # "academic", "benchmark", "standard", "news", etc.
    publication_date: str | None
    credibility_tier: int  # 1-4 (1 = highest)
```

### 4.3 Search Execution Flow

For each constructed query:

1. **Invoke search_web:** Call the tool with the query and appropriate `source_types` filter.
2. **Collect results:** Gather up to 10 results per query (configurable via `max_results`).
3. **Filter by relevance:** The search tool may return results that are not directly relevant. The agent filters results based on snippet content and title keywords.
4. **Deduplicate:** Remove duplicate URLs across multiple queries.
5. **Rank by credibility:** Prioritize results from higher credibility tiers (Tier 1: peer-reviewed journals, official standards; Tier 2: industry reports, CDP; Tier 3: company disclosures; Tier 4: blogs, unverified sources).

### 4.4 Search Result Limits

To manage processing time and API costs:

- **Maximum results per query:** 10
- **Maximum total results per claim:** 20 (if multiple queries are needed)
- **Maximum queries per claim batch:** 5

These limits ensure thorough investigation while maintaining reasonable latency.

---

## 5. Methodology Validation

### 5.1 Overview

The agent validates whether claimed emission reduction methodologies, calculation methods, or accounting approaches are scientifically valid and align with recognized standards.

### 5.2 Validation Frameworks

The agent checks alignment against:

| Framework | Scope | Validation Criteria |
|---|---|---|
| **GHG Protocol** | Scope 1/2/3 calculations, emission factors, activity data | Method aligns with GHG Protocol Corporate Standard or relevant sector guidance |
| **ISO 14064** | Greenhouse gas accounting and verification | Method follows ISO 14064-1 principles (relevance, completeness, consistency, accuracy, transparency) |
| **SBTi Sectoral Decarbonization Approach (SDA)** | Sector-specific reduction pathways | Method aligns with SBTi SDA methodology for the relevant sector |
| **IPCC Guidelines** | National inventory methodologies | Method references IPCC 2006 Guidelines or 2019 Refinement where applicable |

### 5.3 Validation Process

For each methodology claim:

1. **Extract methodology details:** Identify the specific method name, calculation approach, emission factors used, and scope boundaries.

2. **Search for standard alignment:** Query for the methodology name + "GHG Protocol" or "ISO 14064" to find official guidance.

3. **Search for academic validation:** Query for peer-reviewed papers evaluating the methodology's scientific validity.

4. **Assess alignment:** Use DeepSeek V3.2 to analyze search results and determine:
   - Whether the methodology is recognized in official standards
   - Whether it aligns with GHG Protocol or ISO 14064 requirements
   - Whether peer-reviewed research supports or questions the methodology
   - Whether there are known limitations or controversies

5. **Produce assessment:** Create a finding with:
   - Methodology name and description
   - Standard alignment status (aligned / partially aligned / not aligned / unknown)
   - References to official standards or guidance
   - Academic research findings
   - Any limitations or concerns identified

### 5.4 Example Validation Scenarios

**Scenario 1: Scope 3 Calculation Method**
- Claim: "We calculate Scope 3 emissions using the spend-based method from the GHG Protocol."
- Validation: Search for "GHG Protocol Scope 3 spend-based method"; verify the method is recognized; check for peer-reviewed research on spend-based vs. activity-based accuracy.

**Scenario 2: Custom Reduction Methodology**
- Claim: "Our proprietary carbon capture technology reduces emissions by 30%."
- Validation: Search for peer-reviewed research on carbon capture effectiveness; verify the claimed reduction percentage aligns with published research; identify any limitations or controversies.

See Appendix B for detailed methodology validation frameworks.

---

## 6. Certification and Offset Validation

### 6.1 Renewable Energy Certification Validation

The agent validates claims about renewable energy certificates (RECs, I-RECs, GOs, etc.):

**Validation criteria:**
1. **Certification type recognition:** Verify the certificate type (REC, I-REC, GO, etc.) is a recognized standard.
2. **Registry legitimacy:** Check whether the certificate is from a recognized registry (e.g., I-REC Standard, APX, GOs in Europe).
3. **Academic research:** Search for peer-reviewed research on certificate validity, additionality, and greenwashing risks.
4. **Double counting risks:** Identify whether the certificate avoids double counting (not sold to multiple buyers).

**Search queries:**
- `"{certificate_type} renewable energy certificate standard"`
- `"{certificate_type} additionality peer-reviewed"`
- `"{certificate_type} greenwashing research"`

**Finding structure:**
- Certificate type and registry
- Legitimacy assessment (legitimate / questionable / not recognized)
- Academic research findings
- Any identified risks or limitations

### 6.2 Carbon Offset Validation

The agent validates claims about carbon offsets or carbon credits:

**Validation criteria:**
1. **Offset standard recognition:** Verify the offset standard (VCS, Gold Standard, CDM, CAR, etc.) is recognized.
2. **Academic research on additionality:** Search for peer-reviewed research on whether offset projects demonstrate additionality (emissions reductions that would not have occurred without the project).
3. **Permanence assessment:** Identify research on permanence risks (e.g., forest offsets vulnerable to fire).
4. **Leakage risks:** Check for research on leakage (emissions shifting to other locations).
5. **Controversy identification:** Search for academic papers or investigative reports identifying controversies or legitimacy concerns.

**Search queries:**
- `"{offset_standard} carbon offset additionality research"`
- `"{offset_standard} permanence leakage peer-reviewed"`
- `"{offset_standard} controversy legitimacy"`

**Finding structure:**
- Offset standard and project type
- Legitimacy assessment (legitimate / questionable / controversial)
- Academic research on additionality, permanence, leakage
- Any identified controversies or concerns

### 6.3 Example Validation Scenarios

**Scenario 1: 100% Renewable Electricity Claim**
- Claim: "100% of our electricity comes from certified renewable sources via I-REC certificates."
- Validation: Search for I-REC standard legitimacy; verify I-REC registry recognition; check academic research on I-REC additionality and greenwashing risks.

**Scenario 2: Carbon Offset Purchase**
- Claim: "We offset 50,000 tonnes CO2e through Verified Carbon Standard (VCS) forestry projects."
- Validation: Search for VCS standard recognition; find peer-reviewed research on forestry offset additionality and permanence; identify any controversies or limitations.

---

## 7. Science-Based Target Validation

### 7.1 Overview

The agent validates whether claimed science-based targets align with SBTi frameworks and validation criteria.

### 7.2 SBTi Framework Elements

The agent checks alignment with:

| Element | SBTi Requirement | Validation Approach |
|---|---|---|
| **Target structure** | Absolute or intensity-based; Scope 1/2 separately; Scope 3 by category | Verify target structure matches SBTi requirements |
| **Baseline year** | Valid baseline year (not more than 5 years before target year) | Check baseline year validity |
| **Pathway alignment** | 1.5°C or well-below-2°C pathway alignment | Verify pathway alignment claims |
| **SBTi validation status** | Whether the target is actually validated by SBTi | Search SBTi database for company validation status |
| **Interim targets** | Milestones between baseline and target year | Check for interim target requirements |

### 7.3 Validation Process

For each SBTi-related claim:

1. **Extract target details:** Identify target type (net-zero, absolute reduction, intensity reduction), scope, baseline year, target year, and percentage.

2. **Search SBTi framework:** Query for SBTi methodology documents relevant to the target type and sector.

3. **Search SBTi validation database:** Query for the company name + "SBTi validated" to check actual validation status.

4. **Search pathway alignment:** Query for SBTi pathway alignment criteria and sector-specific requirements.

5. **Assess alignment:** Use DeepSeek V3.2 to analyze:
   - Whether the target structure aligns with SBTi requirements
   - Whether the baseline year is valid
   - Whether pathway alignment claims are accurate
   - Whether the target is actually validated by SBTi (if claimed)
   - Whether interim targets are required and present

6. **Produce assessment:** Create a finding with:
   - Target structure and details
   - SBTi alignment status (aligned / partially aligned / not aligned / validation status unknown)
   - SBTi validation status (validated / not validated / status unclear)
   - Pathway alignment assessment
   - References to SBTi framework documents

### 7.4 Search Queries

- `"SBTi methodology {target_type} {sector}"`
- `"{company_name} SBTi validated target"`
- `"SBTi {target_type} validation criteria"`
- `"SBTi 1.5°C pathway alignment {sector}"`

### 7.5 Example Validation Scenarios

**Scenario 1: Net-Zero Commitment**
- Claim: "We have committed to achieving net-zero emissions by 2050, validated by the Science Based Targets initiative."
- Validation: Search SBTi database for company validation; verify net-zero target structure aligns with SBTi Net-Zero Standard; check pathway alignment requirements.

**Scenario 2: Scope 1/2 Reduction Target**
- Claim: "We have set a science-based target to reduce Scope 1 and 2 emissions by 42% by 2030 from a 2019 baseline, aligned with a 1.5°C pathway."
- Validation: Search SBTi methodology for Scope 1/2 targets; verify 42% reduction aligns with 1.5°C pathway for the sector; check baseline year validity (2019 is acceptable if target year is 2030).

---

## 8. Benchmark Comparison

### 8.1 Overview

The agent compares reported quantitative metrics (emission intensities, percentages, absolute figures) against industry benchmarks and peer-reviewed research to assess plausibility.

### 8.2 Benchmark Sources

The agent retrieves benchmarks from:

| Source | Data Type | Access Method |
|---|---|---|
| **CDP Disclosures** | Company-specific and sector-average emission intensities | Web search for CDP disclosure reports |
| **Industry Associations** | Sector-specific benchmark reports | Web search for industry association publications |
| **Academic Research** | Peer-reviewed papers with sector emission intensity analyses | Academic search queries |
| **SASB Metrics** | Industry-specific metrics and benchmarks | SASB standard documents (from RAG corpus) |

### 8.3 Comparison Process

For each quantitative claim:

1. **Extract metrics:** Identify the reported value, units, scope (Scope 1/2/3), and industry sector.

2. **Identify benchmark type:** Determine the appropriate benchmark metric (emission intensity per revenue, per unit produced, per employee, absolute sector average, etc.).

3. **Search for benchmarks:** Query for sector-specific benchmarks:
   - `"{industry} emission intensity benchmark {year}"`
   - `"CDP {industry} Scope {N} emissions average"`
   - `"{industry} {metric} peer-reviewed research"`

4. **Extract benchmark ranges:** From search results, extract:
   - Sector average or median values
   - Percentile ranges (25th, 75th percentile)
   - Peer-reviewed research findings on typical ranges
   - Year-over-year trends

5. **Compare and assess:** Use DeepSeek V3.2 to:
   - Compare reported value against benchmark range
   - Assess plausibility (plausible / high / low / outlier / unknown)
   - Identify any significant deviations and potential explanations
   - Consider year, scope, and sector context

6. **Produce comparison:** Create a finding with:
   - Reported metric and value
   - Benchmark range (with source citations)
   - Plausibility assessment
   - Comparison explanation
   - References to benchmark sources

### 8.4 Benchmark Database References

See Appendix C for common benchmark databases and access methods.

### 8.5 Example Comparison Scenarios

**Scenario 1: Emission Intensity**
- Claim: "Our Scope 1 emission intensity is 0.15 tCO2e per $1M revenue."
- Comparison: Search for "{industry} Scope 1 emission intensity benchmark"; extract sector average (e.g., 0.12-0.18 tCO2e/$1M); assess whether 0.15 is within plausible range.

**Scenario 2: Reduction Percentage**
- Claim: "We achieved a 25% reduction in Scope 2 emissions year-over-year."
- Comparison: Search for peer-reviewed research on typical Scope 2 reduction rates; compare 25% against typical ranges (e.g., 5-15% for operational improvements, 20-40% for renewable energy transition); assess plausibility.

---

## 9. Research Support Validation

### 9.1 Overview

The agent validates whether claimed technologies or practices are supported by peer-reviewed research.

### 9.2 Validation Process

For claims asserting technology or practice effectiveness:

1. **Extract technology/practice details:** Identify the specific technology, practice, or innovation name and the claimed emission reduction or benefit.

2. **Search for academic research:** Query for peer-reviewed papers evaluating the technology/practice:
   - `"{technology_name} emission reduction peer-reviewed"`
   - `"{practice_name} carbon footprint research"`
   - `"{technology_name} effectiveness study journal"`

3. **Extract research findings:** From search results, identify:
   - Consensus findings on effectiveness
   - Typical emission reduction ranges found in research
   - Limitations or constraints identified
   - Contradictory research or controversies

4. **Assess support:** Use DeepSeek V3.2 to:
   - Determine whether peer-reviewed research supports the claim
   - Compare claimed benefits against research findings
   - Identify any gaps between claim and research
   - Note any limitations or controversies

5. **Produce assessment:** Create a finding with:
   - Technology/practice name and claimed benefit
   - Research support status (supported / partially supported / not supported / insufficient research)
   - Summary of peer-reviewed findings
   - Comparison of claim vs. research
   - References to academic papers

### 9.3 Example Validation Scenarios

**Scenario 1: Technology Effectiveness**
- Claim: "Our new carbon capture technology reduces facility emissions by 30%."
- Validation: Search for peer-reviewed research on carbon capture effectiveness; compare 30% reduction against published research ranges; identify any limitations or constraints.

**Scenario 2: Practice Adoption**
- Claim: "Adopting circular economy practices has reduced our waste-related emissions by 40%."
- Validation: Search for academic research on circular economy emission reduction potential; verify 40% aligns with research findings; identify sector-specific variations.

---

## 10. Finding Structure and Output

### 10.1 AgentFinding Schema

Each finding produced by the Academic/Research Agent follows the `AgentFinding` schema from FRD 0:

```python
class AgentFinding(BaseModel):
    finding_id: str
    agent_name: str  # "academic"
    claim_id: str
    evidence_type: str  # "methodology_validation", "certification_validation", "sbti_validation", "benchmark_comparison", "research_support"
    summary: str  # Plain-language summary of whether evidence supports the claim
    details: dict  # Structured evidence data
    supports_claim: bool | None  # True = supports, False = contradicts, None = insufficient evidence
    confidence: float | None  # 0.0-1.0 confidence score
    iteration: int  # Investigation cycle number
    references: list[dict]  # Academic references, benchmark sources, standard documents
```

### 10.2 Finding Details Structure

The `details` field contains structured evidence:

```python
{
    "investigation_type": "methodology_validation" | "certification_validation" | "sbti_validation" | "benchmark_comparison" | "research_support",
    "methodology_name": str | None,  # For methodology validation
    "standard_alignment": "aligned" | "partially_aligned" | "not_aligned" | "unknown",
    "certification_type": str | None,  # For certification validation
    "legitimacy_assessment": "legitimate" | "questionable" | "not_recognized" | "unknown",
    "sbti_validation_status": "validated" | "not_validated" | "status_unclear" | None,  # For SBTi validation
    "benchmark_range": dict | None,  # For benchmark comparison: {"min": float, "max": float, "reported": float, "unit": str}
    "plausibility": "plausible" | "high" | "low" | "outlier" | "unknown" | None,
    "research_consensus": str | None,  # Summary of peer-reviewed research findings
    "limitations": list[str],  # Any identified limitations or concerns
    "academic_references": list[dict],  # [{title, authors, publication_date, url, snippet}]
    "standard_references": list[dict],  # [{standard_name, document_title, url, section}]
}
```

### 10.3 References Structure

The `references` field contains citations:

```python
[
    {
        "type": "academic_paper" | "benchmark_report" | "standard_document" | "cdp_disclosure",
        "title": str,
        "authors": str | None,  # For academic papers
        "publication_date": str | None,
        "url": str,
        "snippet": str,  # Relevant excerpt
        "source_credibility": int  # 1-4 (1 = highest)
    }
]
```

### 10.4 Summary Generation

The `summary` field provides a plain-language assessment:

**Template examples:**
- Methodology: "The claimed {methodology_name} methodology {aligns/partially aligns/does not align} with {GHG Protocol/ISO 14064} standards. {Peer-reviewed research supports/questions} the methodology's scientific validity. {Limitations/concerns identified}."
- Certification: "The {certification_type} certification {is/is not} recognized by {registry/standard}. Academic research {supports/raises concerns about} the certification's {additionality/legitimacy}. {Risks identified}."
- SBTi: "The claimed science-based target {aligns/does not align} with SBTi framework requirements. SBTi validation status: {validated/not validated/unknown}. Pathway alignment: {aligned/not aligned}."
- Benchmark: "The reported {metric} of {value} {is/is not} within the plausible range for {industry} sector benchmarks ({range}). {Comparison explanation}."
- Research Support: "Peer-reviewed research {supports/partially supports/does not support} the claimed effectiveness of {technology/practice}. {Consensus findings}. {Limitations identified}."

---

## 11. Inter-Agent Communication

### 11.1 InfoRequest Participation

The Academic/Research Agent can post `InfoRequest` objects when it needs cross-domain context:

**Example requests:**
- **To Data/Metrics Agent:** "What are the reported Scope 3 emission figures for benchmark comparison?"
- **To Legal Agent:** "What IFRS paragraph requirements apply to this methodology claim?"
- **To Geography Agent:** "What is the geographic location of the facility mentioned in this technology claim?"
- **To News/Media Agent:** "Has there been public reporting on controversies related to this certification?"

### 11.2 InfoResponse Provision

The agent responds to `InfoRequest` objects from other agents:

**Example responses:**
- **To Data/Metrics Agent:** "Industry benchmark for Scope 1 emission intensity in {sector} is {range} tCO2e/$1M revenue, based on CDP disclosures and academic research."
- **To Legal Agent:** "The {methodology} aligns with GHG Protocol requirements for {scope}. Reference: GHG Protocol Corporate Standard Section {X}."
- **To Judge Agent:** "Peer-reviewed research on {technology} shows typical emission reduction ranges of {X-Y}%, which {supports/contradicts} the claimed {Z}% reduction."

### 11.3 Communication Flow

1. **Post InfoRequest:** Agent determines it needs cross-domain context and posts an `InfoRequest` to `state.info_requests`.
2. **Orchestrator routing:** Orchestrator detects the request and routes it to the appropriate agent(s).
3. **Process request:** Target agent processes the request and posts an `InfoResponse` to `state.info_responses`.
4. **Access response:** Requesting agent accesses the response on its next execution (if re-invoked) or in the current execution if the response is available.

All communication is visible in the SSE stream via `info_request_posted`, `info_request_routed`, and `info_response_posted` events.

---

## 12. Re-Investigation Handling

### 12.1 Receiving Re-Investigation Requests

When the Judge Agent requests re-investigation, the Academic/Research Agent receives `ReinvestigationRequest` objects with:

- `claim_id`: The claim to re-investigate
- `target_agents`: List including `"academic"`
- `evidence_gap`: Description of what additional evidence is needed
- `refined_queries`: Specific search queries from the Judge
- `required_evidence`: Types of evidence needed (e.g., "peer-reviewed research on additionality", "SBTi validation database check")

### 12.2 Re-Investigation Process

1. **Read requests:** Load `ReinvestigationRequest` objects from `state.reinvestigation_requests` where `"academic"` is in `target_agents`.

2. **Prioritize refined queries:** Use the Judge's `refined_queries` as the primary search queries, supplementing with agent-generated queries if needed.

3. **Targeted searches:** Execute searches specifically addressing the `evidence_gap` and `required_evidence`.

4. **Produce updated findings:** Create new or updated `AgentFinding` objects with:
   - `iteration` set to the current `state.iteration_count + 1`
   - Additional evidence addressing the gap
   - Updated `summary` reflecting the new evidence

5. **Emit re-investigation events:** Emit `StreamEvent` with `event_type = "agent_thinking"` describing the re-investigation focus.

### 12.3 Iteration Context

The agent includes the iteration count in findings to distinguish initial investigations from re-investigations. The Judge uses this to track evidence evolution across cycles.

---

## 13. Model Configuration and LLM Usage

### 13.1 Model Selection

| Parameter | Value | Rationale |
|---|---|---|
| Model | `deepseek/deepseek-chat` (`Models.DEEPSEEK_V3`) | Fast and cost-effective for research synthesis ($0.25/$0.38 per 1M tokens); strong at processing academic and technical content (PRD Section 4.7) |
| Temperature | `0.2` | Low temperature for consistent, factual analysis of research findings; slight randomness to avoid overly rigid interpretation |
| Max output tokens | `8192` | Sufficient for detailed methodology assessments, benchmark comparisons, and research summaries |
| Response format | Structured JSON (via function calling or JSON mode) | Ensures parseable finding output |

### 13.2 LLM Usage Patterns

The agent uses DeepSeek V3.2 for:

1. **Search result analysis:** Analyzing web search results to extract relevant information, assess claim validity, and synthesize findings.

2. **Benchmark extraction:** Extracting quantitative benchmark ranges from search results (sector averages, percentile ranges, research findings).

3. **Methodology assessment:** Comparing claimed methodologies against standard requirements and research findings.

4. **Research synthesis:** Summarizing peer-reviewed research findings into consensus statements and identifying limitations or controversies.

5. **Finding generation:** Producing structured `AgentFinding` objects with summaries, assessments, and references.

### 13.3 Prompt Construction

The agent constructs prompts for DeepSeek V3.2:

**System prompt template:**
```
You are the Academic/Research Agent in Sibyl, an AI system that validates technical sustainability claims against peer-reviewed research, industry benchmarks, and recognized standards.

Your task is to analyze search results and produce structured findings that assess whether technical claims are supported by academic literature, benchmarks, and standards.

Focus on:
- Methodology validation against GHG Protocol, ISO 14064, SBTi frameworks
- Certification and offset legitimacy assessment
- Science-based target alignment validation
- Benchmark comparison for plausibility assessment
- Research support for technology/practice effectiveness claims

Provide evidence-based assessments with academic references and standard citations.
```

**User prompt template:**
```
Analyze the following search results for claim: "{claim_text}"

Investigation type: {investigation_type}
Search results:
{search_results_json}

Produce a structured finding assessing:
1. Whether the evidence supports, contradicts, or is insufficient for the claim
2. Methodology/certification/target alignment status
3. Benchmark comparison (if applicable)
4. Research consensus findings
5. Any limitations or concerns

Return a JSON object matching the AgentFinding schema.
```

### 13.4 Cost and Latency Considerations

- **Search result analysis:** ~2000-4000 tokens per claim (input: search results; output: structured finding)
- **Batch processing:** Process multiple claims in a single LLM call when they share investigation type to reduce API calls
- **Target latency:** < 30 seconds per claim (including search + LLM analysis)
- **Cost target:** < $0.10 per claim investigation (search + LLM)

---

## 14. Error Handling

### 14.1 Web Search Errors

| Error | Trigger | Handling |
|---|---|---|
| `search_web` tool unavailable | FRD 8 tool not implemented or API failure | Fall back to direct web search API calls if available; if not, mark claim as "insufficient evidence" with error note |
| Search API rate limit | Too many requests to search API | Implement exponential backoff retry; reduce query batch size; mark affected claims for retry |
| Search returns no results | Query too specific or no relevant sources | Broaden query terms; try alternative query formulations; if still no results, mark as "insufficient evidence" |
| Search results are low quality | Results are from low-credibility sources (Tier 4) | Filter out Tier 4 results; if no Tier 1-3 results remain, mark as "insufficient evidence" |

### 14.2 LLM Analysis Errors

| Error | Trigger | Handling |
|---|---|---|
| DeepSeek V3.2 returns non-JSON | Structured output fails | Retry once with explicit JSON format instruction; if still fails, parse free-text response with lenient extractor |
| LLM timeout | API call exceeds 60 seconds | Retry up to 2 times with shorter context; on final failure, produce finding with "insufficient evidence" and error note |
| LLM rate limit | OpenRouter returns 429 | Exponential backoff retry (handled by OpenRouter client); propagate error after 3 retries |
| Malformed finding output | LLM returns invalid `AgentFinding` structure | Validate and fix missing fields; discard only if critical fields are missing; log warning |

### 14.3 Data Processing Errors

| Error | Trigger | Handling |
|---|---|---|
| Claim has no technical content | Claim filtered but lacks investigation keywords | Skip the claim; emit a thinking event noting the skip; continue with other claims |
| Benchmark data extraction fails | Cannot parse quantitative ranges from search results | Mark benchmark comparison as "unknown"; proceed with other investigation aspects |
| Reference extraction fails | Cannot parse academic paper metadata from search results | Include raw URL and snippet in references; proceed with assessment |

### 14.4 Graceful Degradation

If the agent encounters errors that prevent investigation:

1. **Partial findings:** Produce findings with available evidence, marking missing aspects as "insufficient evidence."
2. **Error notes:** Include error descriptions in finding `details` for transparency.
3. **Continue pipeline:** Do not crash the pipeline; return whatever findings are available and let the Judge evaluate partial evidence.
4. **Emit error events:** Emit `StreamEvent` with `event_type = "error"` describing the issue.

---

## 15. Exit Criteria

FRD 9 is complete when ALL of the following are satisfied:

| # | Criterion | Verification |
|---|---|---|
| 1 | Academic/Research Agent node executes | Start analysis on a report with technical claims; verify the `investigate_academic` node runs |
| 2 | Agent receives routed claims | Verify the agent receives claims assigned to "academic" from the routing plan |
| 3 | Agent filters technical claims | Verify the agent correctly identifies and processes technical claims requiring academic validation |
| 4 | Search queries are constructed | Verify the agent constructs appropriate academic search queries for different investigation types |
| 5 | Web search tool is invoked | Verify the agent calls `search_web` from FRD 8 with constructed queries |
| 6 | Search results are collected | Verify search results are retrieved and stored for analysis |
| 7 | Methodology validation works | Test with a claim about emission reduction methodology; verify the agent validates against GHG Protocol/ISO 14064 |
| 8 | Certification validation works | Test with a renewable energy certificate claim; verify the agent validates certification legitimacy |
| 9 | Carbon offset validation works | Test with a carbon offset claim; verify the agent validates offset standard and additionality |
| 10 | SBTi validation works | Test with a science-based target claim; verify the agent validates SBTi alignment and validation status |
| 11 | Benchmark comparison works | Test with a quantitative metric claim; verify the agent compares against industry benchmarks |
| 12 | Research support validation works | Test with a technology effectiveness claim; verify the agent validates against peer-reviewed research |
| 13 | Findings are structured correctly | Verify findings include `evidence_type`, `summary`, `details`, `supports_claim`, `references` |
| 14 | Academic references are included | Verify findings include references to academic papers with titles, URLs, publication dates |
| 15 | Benchmark comparisons include ranges | Verify benchmark comparison findings include quantitative ranges with sources |
| 16 | Agent participates in inter-agent communication | Post an InfoRequest from another agent; verify the Academic/Research Agent responds with InfoResponse |
| 17 | Re-investigation handling works | Simulate a re-investigation request from the Judge; verify the agent performs targeted searches |
| 18 | StreamEvent emissions work | Verify the agent emits `agent_started`, `agent_thinking`, `evidence_found`, `agent_completed` events |
| 19 | Events stream to frontend | Verify SSE events from the Academic/Research Agent appear in the detective dashboard |
| 20 | Error handling works | Simulate a search API failure; verify the agent degrades gracefully and continues with other claims |
| 21 | Agent status updates correctly | Verify `agent_status["academic"]` transitions: idle → working → completed |
| 22 | Findings are persisted | Verify findings are stored in the database and linked to claims |
| 23 | Performance is acceptable | Verify the agent completes investigation for 10 technical claims in under 5 minutes |

---

## Appendix A: Academic Search Query Templates

### A.1 Methodology Validation Queries

**GHG Protocol alignment:**
- `"GHG Protocol {methodology_name} calculation method"`
- `"GHG Protocol Scope {N} {methodology_name} guidance"`
- `"{methodology_name} ISO 14064 alignment"`

**Academic validation:**
- `"{methodology_name} emission reduction peer-reviewed research"`
- `"{methodology_name} scientific validity journal"`
- `"{methodology_name} accuracy assessment study"`

### A.2 Certification Validation Queries

**Renewable energy certificates:**
- `"{certificate_type} renewable energy certificate standard registry"`
- `"{certificate_type} additionality peer-reviewed"`
- `"{certificate_type} greenwashing research"`

**Carbon offsets:**
- `"{offset_standard} carbon offset additionality research"`
- `"{offset_standard} permanence leakage peer-reviewed"`
- `"{offset_standard} legitimacy controversy"`

### A.3 SBTi Validation Queries

**Framework documentation:**
- `"SBTi methodology {target_type} {sector}"`
- `"SBTi Net-Zero Standard requirements"`
- `"SBTi {target_type} validation criteria"`

**Validation status:**
- `"{company_name} SBTi validated target"`
- `"SBTi validated companies {sector} {year}"`

**Pathway alignment:**
- `"SBTi 1.5°C pathway alignment {sector}"`
- `"SBTi sectoral decarbonization approach {sector}"`

### A.4 Benchmark Comparison Queries

**CDP disclosures:**
- `"CDP {industry} Scope {N} emissions {year}"`
- `"CDP disclosure {industry} emission intensity"`
- `"CDP {industry} benchmark average"`

**Industry associations:**
- `"{industry} emission intensity benchmark report"`
- `"{industry} association sustainability metrics"`
- `"{industry} Scope {N} emissions per revenue"`

**Academic research:**
- `"{industry} emission intensity peer-reviewed research"`
- `"{metric} {industry} sector analysis journal"`
- `"{industry} {scope} emissions benchmark study"`

### A.5 Research Support Queries

**Technology effectiveness:**
- `"{technology_name} emission reduction peer-reviewed"`
- `"{technology_name} carbon footprint research"`
- `"{technology_name} effectiveness study journal"`

**Practice validation:**
- `"{practice_name} emission reduction research"`
- `"{practice_name} sustainability impact peer-reviewed"`
- `"{practice_name} carbon reduction study"`

---

## Appendix B: Methodology Validation Frameworks

### B.1 GHG Protocol Standards

| Standard | Scope | Key Requirements |
|---|---|---|
| **Corporate Standard** | Scope 1/2/3 accounting | Activity data × emission factors; scope boundaries; consolidation approach |
| **Scope 2 Guidance** | Purchased electricity, heat, steam, cooling | Location-based and market-based methods; renewable energy certificates |
| **Scope 3 Standard** | Value chain emissions | 15 categories; calculation methods (activity-based, spend-based, hybrid) |
| **Sector Guidance** | Industry-specific | Sector-specific emission factors and calculation methods |

**Validation checklist:**
- [ ] Method aligns with Corporate Standard or relevant sector guidance
- [ ] Activity data sources are appropriate
- [ ] Emission factors are from recognized databases (e.g., IPCC, EPA)
- [ ] Scope boundaries are correctly defined
- [ ] Consolidation approach (equity share, operational control, financial control) is appropriate

### B.2 ISO 14064 Standards

| Standard | Scope | Key Principles |
|---|---|---|
| **ISO 14064-1** | Organization-level GHG accounting | Relevance, completeness, consistency, accuracy, transparency |
| **ISO 14064-2** | Project-level GHG quantification | Baseline scenario, additionality, leakage, permanence |
| **ISO 14064-3** | Verification and validation | Verification principles, validation criteria |

**Validation checklist:**
- [ ] Method follows ISO 14064-1 principles
- [ ] Completeness: All relevant sources and sinks included
- [ ] Consistency: Methods applied consistently over time
- [ ] Accuracy: Uncertainty quantified and minimized
- [ ] Transparency: Methods and assumptions documented

### B.3 SBTi Methodologies

| Methodology | Scope | Key Elements |
|---|---|---|
| **Sectoral Decarbonization Approach (SDA)** | Sector-specific pathways | Sector intensity pathways; absolute vs. intensity targets |
| **Absolute Contraction Approach** | Economy-wide reduction | Uniform percentage reduction across all sectors |
| **Science-Based Target Setting Manual** | Target structure | Scope boundaries; baseline year; target year; reduction percentage |

**Validation checklist:**
- [ ] Target structure aligns with SBTi requirements
- [ ] Baseline year is valid (not more than 5 years before target year)
- [ ] Pathway alignment is correctly claimed (1.5°C vs. well-below-2°C)
- [ ] Scope boundaries match SBTi requirements
- [ ] Target is validated by SBTi (if claimed)

---

## Appendix C: Benchmark Database References

### C.1 CDP (Carbon Disclosure Project)

**Access:** Web search for CDP disclosure reports and databases

**Data types:**
- Company-specific disclosures (Scope 1/2/3 emissions, intensities)
- Sector averages and benchmarks
- Year-over-year trends

**Query patterns:**
- `"CDP {company_name} {year} emissions disclosure"`
- `"CDP {industry} sector average emissions"`
- `"CDP disclosure database {industry}"`

### C.2 Industry Association Reports

**Examples:**
- World Business Council for Sustainable Development (WBCSD) sector reports
- Industry-specific associations (e.g., International Council on Mining and Metals for mining)
- Trade association sustainability benchmarks

**Query patterns:**
- `"{industry} association emission intensity benchmark"`
- `"{industry} sustainability metrics report"`
- `"WBCSD {industry} emissions benchmark"`

### C.3 Academic Research Databases

**Sources:**
- Google Scholar for peer-reviewed papers
- Academic journal databases (ScienceDirect, JSTOR, etc.)
- Research institution reports (e.g., IEA, IPCC)

**Query patterns:**
- `"{industry} emission intensity peer-reviewed research"`
- `"{metric} {sector} benchmark study journal"`
- `"IPCC {industry} emission factors"`

### C.4 SASB Metrics

**Access:** SASB standard documents (from RAG corpus in FRD 1)

**Data types:**
- Industry-specific metrics and benchmarks
- Disclosure guidance with typical ranges

**Query method:** RAG retrieval from SASB corpus (not web search)

---

## Appendix D: Example Findings

### D.1 Methodology Validation Finding

```json
{
  "finding_id": "uuid-...",
  "agent_name": "academic",
  "claim_id": "claim-uuid-...",
  "evidence_type": "methodology_validation",
  "summary": "The claimed spend-based method for Scope 3 Category 1 (Purchased Goods and Services) emissions aligns with GHG Protocol Scope 3 Standard guidance. The method is recognized as an acceptable approach when activity-based data is unavailable. Peer-reviewed research supports the method's use for initial estimates but notes limitations in accuracy compared to activity-based methods.",
  "details": {
    "investigation_type": "methodology_validation",
    "methodology_name": "GHG Protocol spend-based method for Scope 3 Category 1",
    "standard_alignment": "aligned",
    "research_consensus": "Spend-based methods are acceptable for Scope 3 estimates but have higher uncertainty than activity-based methods. Research suggests accuracy within ±30% for initial estimates.",
    "limitations": ["Higher uncertainty compared to activity-based methods", "Requires accurate spend data and appropriate emission factors"],
    "academic_references": [
      {
        "type": "academic_paper",
        "title": "Accuracy of Spend-Based Carbon Footprinting: A Comparative Analysis",
        "authors": "Smith et al.",
        "publication_date": "2023",
        "url": "https://...",
        "snippet": "Spend-based methods show acceptable accuracy for Scope 3 estimates...",
        "source_credibility": 1
      }
    ],
    "standard_references": [
      {
        "type": "standard_document",
        "title": "GHG Protocol Scope 3 Standard",
        "url": "https://ghgprotocol.org/scope-3-standard",
        "section": "Chapter 5: Calculation Methods"
      }
    ]
  },
  "supports_claim": true,
  "confidence": 0.85,
  "iteration": 1,
  "references": [...]
}
```

### D.2 Certification Validation Finding

```json
{
  "finding_id": "uuid-...",
  "agent_name": "academic",
  "claim_id": "claim-uuid-...",
  "evidence_type": "certification_validation",
  "summary": "The claimed I-REC (International Renewable Energy Certificate) certification is recognized by the I-REC Standard registry. However, academic research raises concerns about additionality and greenwashing risks for I-RECs, particularly when certificates are purchased separately from physical electricity. The certification is legitimate but may not represent additional renewable energy generation.",
  "details": {
    "investigation_type": "certification_validation",
    "certification_type": "I-REC (International Renewable Energy Certificate)",
    "legitimacy_assessment": "legitimate",
    "research_consensus": "I-RECs are recognized certificates but research questions additionality when certificates are unbundled from physical electricity. Studies suggest I-RECs may not drive additional renewable energy investment.",
    "limitations": ["Additionality concerns for unbundled certificates", "Greenwashing risks identified in academic literature"],
    "academic_references": [
      {
        "type": "academic_paper",
        "title": "Renewable Energy Certificates and Additionality: A Critical Review",
        "authors": "Jones et al.",
        "publication_date": "2024",
        "url": "https://...",
        "snippet": "I-RECs and similar certificates show limited additionality when...",
        "source_credibility": 1
      }
    ],
    "standard_references": [
      {
        "type": "standard_document",
        "title": "I-REC Standard Registry",
        "url": "https://irecstandard.org"
      }
    ]
  },
  "supports_claim": null,
  "confidence": 0.70,
  "iteration": 1,
  "references": [...]
}
```

### D.3 Benchmark Comparison Finding

```json
{
  "finding_id": "uuid-...",
  "agent_name": "academic",
  "claim_id": "claim-uuid-...",
  "evidence_type": "benchmark_comparison",
  "summary": "The reported Scope 1 emission intensity of 0.15 tCO2e per $1M revenue is within the plausible range for the manufacturing sector. CDP disclosures and academic research indicate typical ranges of 0.12-0.18 tCO2e/$1M revenue for similar companies. The reported value falls at the upper end of the range but remains plausible.",
  "details": {
    "investigation_type": "benchmark_comparison",
    "benchmark_range": {
      "min": 0.12,
      "max": 0.18,
      "median": 0.14,
      "reported": 0.15,
      "unit": "tCO2e per $1M revenue"
    },
    "plausibility": "plausible",
    "academic_references": [
      {
        "type": "academic_paper",
        "title": "Emission Intensity Benchmarks for Manufacturing Sector",
        "authors": "Brown et al.",
        "publication_date": "2023",
        "url": "https://...",
        "snippet": "Manufacturing sector Scope 1 intensities range from 0.12-0.18...",
        "source_credibility": 1
      }
    ],
    "standard_references": [
      {
        "type": "cdp_disclosure",
        "title": "CDP Manufacturing Sector Disclosure Report 2024",
        "url": "https://cdp.net/...",
        "snippet": "Sector average Scope 1 intensity: 0.14 tCO2e/$1M revenue"
      }
    ]
  },
  "supports_claim": true,
  "confidence": 0.80,
  "iteration": 1,
  "references": [...]
}
```

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| Reuse `search_web` tool from FRD 8 over implementing separate academic search | FRD 8's web search tool provides the necessary search capabilities. Reusing it avoids duplication and ensures consistent search result formatting. The Academic/Research Agent focuses on query construction and result analysis rather than search infrastructure. |
| DeepSeek V3.2 over Claude Sonnet 4.5 for Academic/Research Agent | PRD explicitly specifies DeepSeek V3.2 for cost-effectiveness and research synthesis capabilities. DeepSeek is significantly cheaper ($0.25/$0.38 vs $3/$15 per 1M tokens) and sufficient for analyzing search results and producing structured findings. Claude Sonnet 4.5 is reserved for more complex reasoning tasks (Legal, Orchestrator, Judge). |
| Batch claim processing over one-at-a-time investigation | Grouping related claims enables efficient batch queries (e.g., single query for multiple methodology claims). This reduces API calls and improves latency. Trade-off: slightly less claim-specific query precision, but acceptable given the cost and speed benefits. |
| Structured JSON output from LLM over free-text parsing | DeepSeek V3.2 supports structured output (function calling or JSON mode). Structured output ensures parseable `AgentFinding` objects and eliminates regex-based parsing complexity. Fallback lenient parser handles degraded responses. |
| Multiple investigation types (methodology, certification, SBTi, benchmark, research) over single validation approach | Different claim types require different validation strategies. Methodology validation needs standard alignment checks; certification validation needs registry verification; benchmark comparison needs quantitative extraction. Separate investigation types enable targeted, efficient validation. |
| Academic references in findings over summary-only output | Including full references (titles, URLs, publication dates) enables users to verify findings and access source material. This transparency is critical for auditability and trust. References also support the Judge Agent's evidence evaluation. |
| Confidence scores in findings over binary support/contradict | Some investigations produce ambiguous results (e.g., certification is legitimate but research raises concerns). Confidence scores (0.0-1.0) provide nuance beyond binary support/contradict, enabling the Judge Agent to weigh evidence quality. |
| Iteration count in findings over single-pass investigation | Re-investigation requests from the Judge require tracking which findings are from initial vs. refined investigations. The iteration count enables the Judge to assess evidence evolution across cycles and determine when sufficient evidence has been gathered. |
| Query templates and construction rules over hardcoded queries | Different claims require different query formulations. Template-based construction with rules enables flexible, claim-specific queries while maintaining consistency. Hardcoded queries would be too rigid and miss claim-specific nuances. |
| Benchmark range extraction over single-point comparisons | Benchmark data comes as ranges (min-max, percentiles) rather than single values. Extracting and comparing against ranges provides more accurate plausibility assessment than single-point comparisons. |
| Graceful degradation on search/LLM errors over failing completely | If search or LLM analysis fails for one claim, the agent should continue with other claims rather than crashing the pipeline. Partial findings are better than no findings, and the Judge can evaluate whatever evidence is available. |
| InfoRequest participation over isolated investigation | Cross-domain context strengthens investigations (e.g., benchmark comparison benefits from Data/Metrics Agent's reported figures). The inter-agent communication protocol enables this collaboration while keeping agents loosely coupled. |
| Re-investigation with refined queries over generic re-search | The Judge's refined queries target specific evidence gaps. Using these queries directly is more efficient than re-running generic searches. The agent supplements refined queries with its own queries if needed. |
| Maximum 10 results per query over unlimited results | Limiting results per query balances thoroughness with processing time and API costs. 10 results typically provide sufficient evidence for assessment. If more results are needed, the agent can construct follow-up queries. |
| Evidence type categorization in findings over generic findings | Categorizing findings by type (methodology_validation, certification_validation, etc.) enables downstream processing (e.g., Judge Agent can prioritize methodology findings for technical claims). Generic findings would lose this structure. |
| Academic search query optimization (batching, limiting) over exhaustive search | Exhaustive search (hundreds of queries per claim) would be slow and expensive. Optimized query construction (batching related claims, limiting query count) maintains investigation quality while keeping latency and costs reasonable. |
