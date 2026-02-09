# Feature Requirements Document: FRD 3 -- Claims Agent (v1.0)

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.3](../PRD.md) |
| **FRD Order** | [FRD Order](../FRD-order.md) |
| **PRD Sections** | 4.2 (Claims Agent -- Document Analysis) |
| **Type** | Feature |
| **Depends On** | FRD 0 (Setup Document), FRD 1 (RAG Pipeline), FRD 2 (PDF Upload & Ingestion) |
| **Delivers** | Claims extraction logic, claim categorization, IFRS paragraph mapping, LangGraph node, backend endpoints, analysis trigger |
| **Created** | 2026-02-09 |

---

## Summary

FRD 3 delivers the Claims Agent -- the first investigative agent in Sibyl's multi-agent pipeline. The Claims Agent receives the full parsed document content from a successfully uploaded and parsed sustainability report (FRD 2) and systematically identifies verifiable sustainability claims: statements asserting facts, metrics, commitments, or conditions that can be checked against external evidence or internal consistency. Each extracted claim is categorized by type (Geographic, Quantitative/Metrics, Legal/Governance, Strategic/Forward-looking, Environmental), tagged with source page number and text location (for PDF highlighting in FRD 4), assigned a preliminary IFRS S1/S2 paragraph mapping (via RAG retrieval from FRD 1), and prioritized by materiality and verifiability. The agent is implemented as a LangGraph node (`extract_claims`) in `app/agents/claims_agent.py`, powered by Gemini 3 Flash (1M token context window for full-document processing). FRD 3 also delivers the backend endpoint to trigger the analysis pipeline and retrieve extracted claims, the frontend "Begin Analysis" flow connecting FRD 2's upload to claim extraction, and persistence of extracted claims in the `claims` database table (defined in FRD 0).

---

## Given Context (Preconditions)

The following are assumed to be in place from FRD 0, FRD 1, and FRD 2:

| Prerequisite | Source FRD | Deliverable |
|---|---|---|
| Docker Compose with PostgreSQL 17 + pgvector, Redis, backend, frontend | FRD 0 | `docker-compose.yml` |
| `Claim` SQLAlchemy model with all columns (`claim_text`, `claim_type`, `source_page`, `source_location`, `ifrs_paragraphs`, `priority`, `agent_reasoning`) | FRD 0 | `app/models/claim.py` |
| `Report` SQLAlchemy model with `status`, `parsed_content`, `pdf_binary` columns | FRD 0 | `app/models/report.py` |
| `SibylState` Pydantic schema with `Claim`, `DocumentChunk`, `StreamEvent` types | FRD 0 | `app/agents/state.py` |
| Claims Agent stub (`extract_claims` function signature) | FRD 0 | `app/agents/claims_agent.py` |
| Graph stub with `extract_claims` node name | FRD 0 | `app/agents/graph.py` |
| Analysis route stub (`app/api/routes/analysis.py`) | FRD 0 | Empty `APIRouter` |
| Analysis schema stub (`app/schemas/analysis.py`) | FRD 0 | Empty file |
| OpenRouter client wrapper with retry logic | FRD 0 | `app/services/openrouter_client.py` |
| `Models.GEMINI_FLASH` constant | FRD 0 | `app/services/openrouter_client.py` |
| `Claim` and `ClaimType` TypeScript types | FRD 0 | `src/types/claim.ts` |
| `AnalysisPage` stub with routing at `/analysis/:reportId` | FRD 0 | `src/pages/AnalysisPage.tsx` |
| RAG pipeline with hybrid search and `rag_lookup` tool | FRD 1 | `app/services/rag_service.py`, `app/agents/tools/rag_lookup.py` |
| IFRS S1/S2 and SASB corpus ingested into pgvector | FRD 1 | Embedded standard text |
| PDF upload endpoint, parsing pipeline, background task worker | FRD 2 | `app/api/routes/upload.py`, `app/services/pdf_parser.py`, `app/services/task_worker.py` |
| Report record with `status = "parsed"`, `parsed_content` populated | FRD 2 | Database state after successful upload |
| Page boundary markers (`<!-- PAGE N -->`) in parsed content | FRD 2 | `PDFParserService` output |
| "Begin Analysis" button on `ContentPreview` component navigating to `/analysis/{reportId}` | FRD 2 | `src/components/Upload/ContentPreview.tsx` |
| Redis task queue with `LPUSH`/`BRPOP` pattern | FRD 2 | `app/services/task_worker.py` |

### Terms

| Term | Definition |
|---|---|
| Claim | A verifiable sustainability statement extracted from a report -- an assertion of fact, metric, commitment, or condition that can be checked against external evidence or internal consistency |
| Claim type | One of five categories (Geographic, Quantitative/Metrics, Legal/Governance, Strategic/Forward-looking, Environmental) describing the domain of the claim |
| Source location | Positional data (page number, approximate character offset, and bounding context) enabling PDF highlighting of the claim in the original document |
| Preliminary IFRS mapping | An initial mapping of the claim to likely IFRS S1/S2 paragraph(s), produced via RAG retrieval against the IFRS corpus; refined by the Legal Agent in FRD 6 |
| Priority | A materiality- and verifiability-based ranking (high, medium, low) that influences downstream investigation order |
| Extract pass | A single LLM invocation over a document section to identify claims; multiple passes may be made over large documents |
| Claims Agent reasoning | The agent's explanation for why a particular statement was flagged as a verifiable claim, including the rationale for its type, priority, and IFRS mapping |

---

## Executive Summary (Gherkin-Style)

```gherkin
Feature: Claims Agent

  Background:
    Given  FRD 0, FRD 1, and FRD 2 are complete
    And    all services are running (backend, frontend, PostgreSQL, Redis)
    And    the IFRS/SASB corpus has been ingested into the RAG pipeline
    And    a sustainability report PDF has been uploaded and parsed (status = "parsed")

  Scenario: Trigger claims extraction
    Given  the user is viewing the content preview after upload
    When   the user clicks "Begin Analysis"
    Then   the application navigates to /analysis/{reportId}
    And    the frontend sends POST /api/v1/analysis/{reportId}/start
    And    the backend sets the report status to "analyzing"
    And    the backend enqueues a claims extraction task
    And    the frontend begins polling for analysis status

  Scenario: Claims Agent extracts claims from the document
    Given  a claims extraction task is dequeued
    When   the Claims Agent processes the parsed document content
    Then   it identifies verifiable sustainability claims from the text
    And    each claim includes: claim text, source page number, text location
    And    each claim is categorized by type: geographic, quantitative, legal_governance, strategic, or environmental
    And    each claim is assigned a priority: high, medium, or low
    And    the agent provides reasoning for why each statement is a verifiable claim

  Scenario: Claims Agent performs preliminary IFRS mapping
    Given  claims have been extracted from the document
    When   the Claims Agent processes each claim
    Then   it queries the RAG pipeline for relevant IFRS S1/S2 paragraphs
    And    assigns preliminary IFRS paragraph identifiers to each claim
    And    the mapping includes the paragraph ID and a brief relevance explanation

  Scenario: Claims are persisted to the database
    Given  the Claims Agent has completed extraction
    When   the extraction results are finalized
    Then   each claim is stored in the claims table
    And    the claim record includes: claim_text, claim_type, source_page, source_location, ifrs_paragraphs, priority, agent_reasoning
    And    each claim is linked to the parent report via report_id

  Scenario: Frontend displays extraction progress
    Given  claims extraction is in progress
    When   the frontend polls GET /api/v1/analysis/{reportId}/status
    Then   it receives the current extraction status
    And    it shows the number of claims extracted so far (if available)
    And    once extraction is complete, it displays the full claim list

  Scenario: View extracted claims
    Given  claims extraction is complete
    When   the frontend requests GET /api/v1/analysis/{reportId}/claims
    Then   it receives a list of all extracted claims
    And    each claim includes: text, type, page, IFRS mappings, priority, reasoning
    And    the claims can be filtered by type and priority

  Scenario: Handle extraction failure
    Given  a claims extraction task is processing
    When   the Claims Agent encounters an error (LLM failure, parsing issue)
    Then   the report status is set to "error"
    And    an error message is stored in the report record
    And    the frontend displays a user-friendly error message

  Scenario: Handle document with no verifiable claims
    Given  a document contains no identifiable verifiable claims
    When   the Claims Agent completes processing
    Then   the system returns an empty claims list
    And    the report status is set to "analyzed" with zero claims
    And    the user is informed that no verifiable claims were found
```

---

## Table of Contents

1. [Claims Extraction Logic](#1-claims-extraction-logic)
2. [Claim Categorization and Tagging](#2-claim-categorization-and-tagging)
3. [Preliminary IFRS Mapping](#3-preliminary-ifrs-mapping)
4. [LangGraph Node Implementation](#4-langgraph-node-implementation)
5. [Backend Endpoints](#5-backend-endpoints)
6. [Background Task Integration](#6-background-task-integration)
7. [Frontend Analysis Flow](#7-frontend-analysis-flow)
8. [Analysis Schemas](#8-analysis-schemas)
9. [Error Handling](#9-error-handling)
10. [Exit Criteria](#10-exit-criteria)
11. [Appendix A: Claims Extraction Prompt](#appendix-a-claims-extraction-prompt)
12. [Appendix B: Example Extracted Claims](#appendix-b-example-extracted-claims)
13. [Appendix C: Claim Extraction Flow Sequence Diagram](#appendix-c-claim-extraction-flow-sequence-diagram)
14. [Design Decisions Log](#design-decisions-log)

---

## 1. Claims Extraction Logic

### 1.1 Overview

The Claims Agent (`app/agents/claims_agent.py`) replaces the FRD 0 stub with a functional LangGraph node that extracts verifiable sustainability claims from parsed report content. The agent uses Gemini 3 Flash via OpenRouter, leveraging its 1M token context window to process full 200-page sustainability reports in a single pass.

### 1.2 What Constitutes a Verifiable Claim

A verifiable claim is a statement in the sustainability report that asserts a fact, metric, commitment, or condition that can, in principle, be checked against:

- **External evidence:** Satellite imagery, news sources, academic literature, regulatory filings
- **Internal consistency:** Mathematical relationships between reported numbers, alignment with previously published data
- **Standard requirements:** Compliance with specific IFRS S1/S2 paragraphs, SASB metrics, or other frameworks

**Examples of verifiable claims:**

- "Our Scope 1 emissions decreased by 12% year-over-year to 2.3 million tonnes CO2e" (quantitative -- checkable for mathematical consistency and benchmark plausibility)
- "We have committed to net-zero emissions by 2050, with an interim target of 42% reduction by 2030" (strategic -- checkable against SBTi frameworks and target achievability)
- "Our Board's Sustainability Committee meets quarterly to oversee climate risk" (legal/governance -- checkable against S1.27 requirements)
- "Our reforestation project in Borneo has restored 5,000 hectares of rainforest" (geographic -- checkable via satellite imagery)
- "100% of our electricity comes from certified renewable sources" (environmental -- checkable against certification databases and academic benchmarks)

**Examples of non-claims (should NOT be extracted):**

- Boilerplate language ("We are committed to a sustainable future")
- Table of contents and navigation text
- Definitions of terms or methodology descriptions (unless they assert a specific fact)
- Acknowledgments, disclaimers, and forward-looking statement safe harbors
- Generic industry context that is not specific to the reporting entity

### 1.3 Extraction Strategy

The system shall:

1. **Full-document processing:** Pass the entire parsed markdown content to Gemini 3 Flash in a single prompt. The 1M token context window accommodates full 200-page reports (typically 50,000-80,000 tokens). This avoids the complexity of multi-chunk extraction with deduplication.

2. **Structured output:** Request claims as a structured JSON array from the LLM using a response schema (see Section 1.5). Each claim object includes all required fields (text, type, page, location, priority, reasoning).

3. **Page number extraction:** The parsed content includes page boundary markers (`<!-- PAGE N -->` from FRD 2). The prompt instructs the model to identify the page number for each claim based on these markers.

4. **Context-aware extraction:** The prompt provides the model with:
   - The full document content
   - Definitions and examples of each claim type
   - Examples of verifiable vs. non-verifiable statements
   - Instructions for priority assessment
   - The page boundary marker format

5. **Deduplication:** The agent shall post-process the LLM output to remove duplicate or near-duplicate claims (same text from the same page). Deduplication uses exact text match and page number match -- if two claims have identical text and the same source page, the duplicate is removed.

### 1.4 Model Configuration

| Parameter | Value | Rationale |
|---|---|---|
| Model | `google/gemini-2.5-flash-preview` (`Models.GEMINI_FLASH`) | 1M token context handles full documents; cost-effective ($0.50/$3.00 per 1M tokens); fast inference |
| Temperature | `0.1` | Low temperature for consistent, deterministic extraction; slight randomness to avoid overly rigid pattern matching |
| Max output tokens | `32768` | Sufficient for 50-200 structured claim objects; Gemini 3 Flash supports up to 65K output tokens |
| Response format | JSON schema (structured output) | Ensures parseable output; eliminates regex/text parsing |

### 1.5 LLM Response Schema

The system shall request structured output from Gemini 3 Flash using the following JSON schema:

```python
class ExtractedClaim(BaseModel):
    """A single claim extracted from the document by the LLM."""
    claim_text: str            # The verbatim or closely paraphrased claim text
    claim_type: str            # geographic | quantitative | legal_governance | strategic | environmental
    source_page: int           # Page number where the claim appears
    source_context: str        # Surrounding text (1-2 sentences) for location anchoring
    priority: str              # high | medium | low
    reasoning: str             # Why this is a verifiable claim
    preliminary_ifrs: list[str]  # List of likely IFRS paragraph IDs (e.g., ["S2.29(a)(iii)", "S1.46"])

class ClaimsExtractionResult(BaseModel):
    """Complete extraction result from the LLM."""
    claims: list[ExtractedClaim]
    total_pages_analyzed: int
    extraction_summary: str    # Brief summary of the document and claim landscape
```

### 1.6 Claim Text Extraction Rules

The system shall instruct the LLM to:

1. **Extract the claim as stated** -- use the verbatim text from the report where possible, paraphrasing only when the original is too long (>300 characters) or spans non-contiguous text.
2. **Scope each claim to a single verifiable assertion** -- if a sentence contains multiple distinct claims (e.g., "Our Scope 1 emissions decreased 12% and Scope 2 decreased 8%"), split them into separate claims.
3. **Include quantitative context** -- for numerical claims, include the units, time period, and comparison basis in the claim text.
4. **Preserve the reporting entity's framing** -- do not reinterpret or editorialize the claim; extract what the company asserts.
5. **Target 50-200 claims** for a typical 100-200 page sustainability report. Fewer than 20 claims likely indicates under-extraction; more than 300 likely indicates over-extraction of non-verifiable statements.

---

## 2. Claim Categorization and Tagging

### 2.1 Claim Types

Each claim shall be categorized into exactly one of five types, matching the PRD Section 4.2 definitions:

| Type | Value | Description | Example Claims |
|---|---|---|---|
| **Geographic** | `geographic` | Facility locations, land use assertions, deforestation commitments, water usage in specific regions, geographic concentration of climate risks | "Our manufacturing facility in Surabaya, Indonesia operates on a 50-hectare site"; "We have planted 2 million trees across our concession in Borneo" |
| **Quantitative/Metrics** | `quantitative` | Emission figures, percentage targets, financial impacts, year-over-year comparisons, Scope 1/2/3 numbers, intensity metrics | "Our total Scope 1 emissions were 2.3 million tonnes CO2e in FY2024"; "We achieved a 15% reduction in energy intensity" |
| **Legal/Governance** | `legal_governance` | Board oversight structures, committee responsibilities, compliance assertions, policy commitments, remuneration links | "The Sustainability Committee meets quarterly and reports to the full Board"; "Climate performance accounts for 10% of executive bonus criteria" |
| **Strategic/Forward-looking** | `strategic` | Transition plans, future targets, investment commitments, timeline assertions, scenario analysis results | "We have committed to achieving net-zero by 2050 with a 1.5°C-aligned pathway"; "We plan to invest $2 billion in renewable energy infrastructure by 2030" |
| **Environmental** | `environmental` | Biodiversity, waste management, resource efficiency, renewable energy claims, water stewardship, circular economy | "100% of our electricity comes from certified renewable sources"; "We diverted 92% of operational waste from landfill" |

### 2.2 Priority Assignment

Each claim shall be assigned a priority based on materiality and verifiability:

| Priority | Value | Criteria |
|---|---|---|
| **High** | `high` | Quantitative claims with specific numbers that can be mathematically verified; claims central to the company's sustainability narrative; claims mapping to core IFRS S2 metrics requirements (S2.27-37); claims that, if false, would constitute material greenwashing |
| **Medium** | `medium` | Qualitative claims with some verifiable elements; governance and process claims; strategic commitments with timelines; claims that contribute to IFRS compliance but are not the primary metrics |
| **Low** | `low` | General assertions with limited independent verifiability; environmental commitments without specific metrics; claims where verification would require non-public information |

### 2.3 Source Location Tagging

Each claim shall include location data for PDF highlighting (consumed by FRD 4):

| Field | Type | Description |
|---|---|---|
| `source_page` | `int` | The 1-indexed page number where the claim appears, derived from the `<!-- PAGE N -->` markers in the parsed content |
| `source_context` | `str` | 1-2 sentences of surrounding text that anchor the claim's position on the page; used by FRD 4 to locate the claim text within the rendered PDF page for highlight positioning |

The `source_location` JSONB column (defined in FRD 0's `Claim` model) shall store the `source_context` for downstream use:

```json
{
  "source_context": "Our total Scope 1 emissions were 2.3 million tonnes CO2e in FY2024, representing a 6.1% decrease from 2.45 million tonnes in FY2023."
}
```

Precise bounding box coordinates for PDF highlighting are computed in FRD 4 by text-matching the claim text and source context against the rendered PDF page. The Claims Agent provides sufficient textual anchoring for FRD 4 to perform this match.

---

## 3. Preliminary IFRS Mapping

### 3.1 Overview

The Claims Agent assigns a preliminary mapping of each claim to likely IFRS S1/S2 paragraphs. This mapping is "preliminary" because it serves as a starting point for the Legal Agent (FRD 6), which performs the definitive paragraph-level compliance assessment. The preliminary mapping enables:

- Claim routing to the appropriate specialist agents by the Orchestrator (FRD 5)
- Early IFRS context in the PDF viewer tooltips (FRD 4)
- A first-pass view of which IFRS pillars the report addresses

### 3.2 Two-Phase Mapping Approach

The preliminary IFRS mapping uses a two-phase approach:

**Phase 1: LLM-based initial mapping (during extraction)**

The extraction prompt instructs Gemini 3 Flash to suggest likely IFRS paragraph IDs for each claim based on its content. The model is provided with a condensed summary of the IFRS S1/S2 structure (pillar → section → paragraph ID mapping) in the system prompt (see Appendix A). This produces a first approximation that is correct at the pillar level in most cases and at the paragraph level in many cases.

**Phase 2: RAG-validated mapping (post-extraction)**

After the LLM produces claims with initial IFRS mappings, the Claims Agent performs a RAG validation pass:

1. For each claim, query the RAG pipeline with the claim text, filtering to `source_types=["ifrs_s1", "ifrs_s2"]`.
2. Retrieve the top 3 most relevant IFRS paragraphs.
3. Compare the RAG results with the LLM's initial mapping:
   - If the RAG results confirm the LLM mapping (same paragraph IDs or same pillar/section), keep the LLM mapping.
   - If the RAG results surface more specific or different paragraphs, replace or augment the LLM mapping with the RAG-sourced paragraph IDs.
4. Store the final preliminary mapping as a list of paragraph identifiers on the claim.

### 3.3 IFRS Mapping Output Format

The `ifrs_paragraphs` field on the `Claim` model (JSONB, defined in FRD 0) shall store an array of objects:

```json
[
  {
    "paragraph_id": "S2.29(a)(iii)",
    "pillar": "metrics_targets",
    "relevance": "Claim reports Scope 3 emissions, which maps to S2.29(a)(iii) absolute Scope 3 GHG emissions requirement"
  },
  {
    "paragraph_id": "S1.46",
    "pillar": "metrics_targets",
    "relevance": "General metrics disclosure requirement"
  }
]
```

### 3.4 RAG Query Configuration

For the IFRS mapping RAG pass:

| Parameter | Value | Rationale |
|---|---|---|
| `top_k` | `3` | Sufficient to surface the most relevant paragraphs without noise |
| `mode` | `"hybrid"` | Combines semantic similarity (for meaning-based matching) with keyword matching (for paragraph ID terms like "Scope 3", "transition plan") |
| `source_types` | `["ifrs_s1", "ifrs_s2"]` | Restrict to IFRS corpus; SASB is not needed for preliminary mapping |

### 3.5 Batched RAG Queries

To manage performance, the system shall batch RAG queries:

1. Group claims by type (claims of the same type likely map to similar IFRS paragraphs).
2. For each group, construct a representative query combining key terms from 3-5 claims.
3. Use individual per-claim queries only when the group query returns insufficient results.
4. Target a maximum of 50-100 RAG queries per document (not one per claim) to keep latency reasonable.

The RAG query budget is approximate -- the system may exceed it for documents with highly diverse claims. The goal is to avoid O(n) RAG queries where n is the claim count (potentially 200+).

---

## 4. LangGraph Node Implementation

### 4.1 Node Function

The `extract_claims` function replaces the FRD 0 stub in `app/agents/claims_agent.py`:

```python
async def extract_claims(state: SibylState) -> dict:
    """Claims Agent: Extract verifiable sustainability claims from the document.

    Reads: state.report_id, state.document_content, state.document_chunks
    Writes: state.claims, state.events

    Uses Gemini 3 Flash via OpenRouter for full-document claim extraction.
    Performs preliminary IFRS mapping via RAG retrieval.

    Returns:
        Partial state update with extracted claims and stream events.
    """
```

### 4.2 Node Processing Steps

The `extract_claims` node shall execute the following steps:

1. **Emit start event:** Append a `StreamEvent` with `event_type = "agent_started"`, `agent_name = "claims"` to the state events list.

2. **Construct the extraction prompt:** Build the system prompt and user prompt (see Appendix A) using:
   - The full `state.document_content` (parsed markdown with page markers)
   - Claim type definitions and examples
   - Condensed IFRS S1/S2 paragraph structure
   - Extraction rules and output format

3. **Call Gemini 3 Flash:** Send the prompt to the LLM via the OpenRouter client, requesting structured JSON output.

4. **Parse the response:** Deserialize the LLM response into `ClaimsExtractionResult`. If parsing fails, retry with a simplified prompt (see Section 9).

5. **Emit thinking events:** During processing, emit `StreamEvent` objects with `event_type = "agent_thinking"` to provide real-time progress updates to the detective dashboard (FRD 12). Events include:
   - "Analyzing document structure..." (before LLM call)
   - "Extracting claims from {page_count} pages..." (during LLM call)
   - "Identified {n} potential claims. Validating IFRS mappings..." (after LLM response)
   - "Verifying IFRS mappings via RAG retrieval..." (during RAG pass)

6. **Run RAG validation pass:** For each extracted claim, perform the RAG-based IFRS mapping validation described in Section 3.2.

7. **Deduplicate claims:** Remove exact-text and same-page duplicates (see Section 1.3).

8. **Convert to state format:** Map each `ExtractedClaim` to the `Claim` Pydantic model from `state.py` (defined in FRD 0), generating unique `claim_id` values (UUID4).

9. **Persist claims to database:** Store each claim in the `claims` table, linking to the `report_id`.

10. **Emit completion event:** Append a `StreamEvent` with `event_type = "agent_completed"`, `agent_name = "claims"`, `data = {"claim_count": len(claims), "by_type": {...}, "by_priority": {...}}`.

11. **Return partial state:** Return `{"claims": claims, "events": new_events}` as the partial state update.

### 4.3 Graph Integration

FRD 3 does not yet compile or execute the full LangGraph pipeline (that is FRD 5's responsibility). However, the `extract_claims` node shall be registered in the graph stub (`app/agents/graph.py`) so that it can be invoked independently for testing and by the background task worker.

The system shall provide a standalone execution wrapper:

```python
async def run_claims_extraction(report_id: str, db: AsyncSession) -> list[Claim]:
    """Run the Claims Agent standalone (without the full LangGraph pipeline).

    Used by the background task worker until FRD 5 delivers the full pipeline.
    """
```

This wrapper:
1. Loads the report from the database.
2. Constructs a minimal `SibylState` with `report_id` and `document_content`.
3. Calls `extract_claims(state)`.
4. Returns the extracted claims.

### 4.4 Streaming Events

The Claims Agent emits the following `StreamEvent` types during execution:

| Event Type | Agent | Data | When |
|---|---|---|---|
| `agent_started` | `claims` | `{}` | Node begins execution |
| `agent_thinking` | `claims` | `{"message": "..."}` | Progress updates during processing |
| `agent_completed` | `claims` | `{"claim_count": N, "by_type": {...}, "by_priority": {...}}` | Extraction complete |
| `error` | `claims` | `{"message": "..."}` | If extraction fails |

These events are stored in the `SibylState.events` list. In FRD 3, they are consumed by the status polling endpoint. In FRD 5, they will be streamed to the frontend via SSE for the detective dashboard.

---

## 5. Backend Endpoints

### 5.1 Start Analysis Endpoint

The analysis route (`app/api/routes/analysis.py`) replaces the FRD 0 stub with functional endpoints. The start endpoint triggers claims extraction:

```
POST /api/v1/analysis/{reportId}/start

Response 200:
{
  "report_id": "uuid-...",
  "status": "analyzing",
  "message": "Claims extraction started."
}

Response 400 (report not parsed):
{
  "detail": "Report must be in 'parsed' status to start analysis. Current status: 'uploaded'."
}

Response 404:
{
  "detail": "Report not found."
}

Response 409 (already analyzing):
{
  "detail": "Analysis is already in progress for this report."
}
```

The endpoint shall:

1. Verify the report exists and has `status = "parsed"`.
2. If the report has `status = "analyzing"` or `status = "completed"`, return 409 Conflict.
3. Set the report status to `"analyzing"`.
4. Enqueue a claims extraction task in Redis (using the same `LPUSH` pattern from FRD 2, on a separate queue key: `sibyl:tasks:extract_claims`).
5. Return the report ID and updated status.

### 5.2 Analysis Status Endpoint

```
GET /api/v1/analysis/{reportId}/status

Response 200:
{
  "report_id": "uuid-...",
  "status": "analyzing",
  "claims_count": 42,
  "claims_by_type": {
    "geographic": 5,
    "quantitative": 18,
    "legal_governance": 8,
    "strategic": 7,
    "environmental": 4
  },
  "claims_by_priority": {
    "high": 15,
    "medium": 20,
    "low": 7
  },
  "error_message": null,
  "updated_at": "2026-02-09T15:30:00Z"
}

Response 404:
{
  "detail": "Report not found."
}
```

The endpoint shall:

1. Load the report and count its associated claims.
2. Return the current status, claim counts by type and priority, and any error message.
3. When `status = "analyzing"` and no claims exist yet, return `claims_count: 0` (extraction in progress).
4. When `status = "completed"` (or a future status set by FRD 5+), return the final claim counts.

### 5.3 List Claims Endpoint

```
GET /api/v1/analysis/{reportId}/claims

Query Parameters:
  - type: string (optional) -- filter by claim_type
  - priority: string (optional) -- filter by priority
  - page: int (optional, default: 1) -- pagination page
  - size: int (optional, default: 50, max: 100) -- pagination size

Response 200:
{
  "claims": [
    {
      "id": "uuid-...",
      "claim_text": "Our total Scope 1 emissions were 2.3 million tonnes CO2e in FY2024, a 6.1% decrease from 2.45 million tonnes in FY2023.",
      "claim_type": "quantitative",
      "source_page": 45,
      "source_location": {
        "source_context": "Our total Scope 1 emissions were 2.3 million tonnes CO2e in FY2024, representing a 6.1% decrease from 2.45 million tonnes in FY2023. This reduction was primarily driven by our transition to natural gas at three major facilities."
      },
      "ifrs_paragraphs": [
        {
          "paragraph_id": "S2.29(a)(i)",
          "pillar": "metrics_targets",
          "relevance": "Absolute Scope 1 GHG emissions disclosure"
        }
      ],
      "priority": "high",
      "agent_reasoning": "This claim asserts a specific Scope 1 emissions figure with year-over-year comparison. The absolute number (2.3M tCO2e), the percentage decrease (6.1%), and the prior year figure (2.45M tCO2e) are all independently verifiable for mathematical consistency. The claim directly maps to IFRS S2.29(a)(i) which requires disclosure of absolute Scope 1 GHG emissions.",
      "created_at": "2026-02-09T15:30:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "size": 50
}

Response 404:
{
  "detail": "Report not found."
}
```

The endpoint shall:

1. Load claims for the given report, applying optional type and priority filters.
2. Paginate results (default 50 per page, max 100).
3. Return claims ordered by page number (ascending), then by priority (high first).

### 5.4 Single Claim Endpoint

```
GET /api/v1/analysis/{reportId}/claims/{claimId}

Response 200:
{
  "id": "uuid-...",
  "claim_text": "...",
  "claim_type": "...",
  "source_page": 45,
  "source_location": { ... },
  "ifrs_paragraphs": [ ... ],
  "priority": "high",
  "agent_reasoning": "...",
  "created_at": "2026-02-09T15:30:00Z"
}

Response 404:
{
  "detail": "Claim not found."
}
```

### 5.5 Route Registration

All analysis endpoints shall be registered under the analysis router (`app/api/routes/analysis.py`) with prefix `/analysis` and tag `"Analysis"`.

---

## 6. Background Task Integration

### 6.1 Task Queue Extension

The system shall extend the task worker (from FRD 2) to handle claims extraction tasks:

1. Add a new queue key: `sibyl:tasks:extract_claims`.
2. The worker listens on both `sibyl:tasks:parse_pdf` and `sibyl:tasks:extract_claims` using a multi-queue `BRPOP`.
3. When a claims extraction task is dequeued, the worker calls `run_claims_extraction(report_id, db)`.

### 6.2 Claims Extraction Pipeline

When the worker processes a claims extraction task:

1. **Fetch the report:** Load the `Report` record by `report_id`. Verify status is `"analyzing"`.
2. **Run extraction:** Call `run_claims_extraction(report_id, db)`.
3. **Update status:** On success, set `status = "completed"`.
4. **Error handling:** On failure, set `status = "error"` and store the error message.

**Note on status values:** In FRD 3, the `"completed"` status means claims extraction is done. When FRD 5 delivers the full pipeline, this status will change to mean the entire pipeline is complete. FRD 3 uses `"completed"` because the Claims Agent is the only processing step available at this stage. FRD 5 will adjust the status transitions as needed.

### 6.3 Auto-Trigger Option

As a convenience for the hackathon demo flow, the system shall support an optional auto-trigger: when the PDF parsing task completes (status transitions to `"parsed"`), the worker can automatically enqueue a claims extraction task. This is controlled by a setting:

```python
# In Settings (app/core/config.py)
AUTO_START_ANALYSIS: bool = False  # Default: False; set True for demo mode
```

When `AUTO_START_ANALYSIS = True`, the parsing pipeline (FRD 2's task worker) sets the report status to `"analyzing"` instead of `"parsed"` after successful parsing, and immediately enqueues a claims extraction task. The user does not need to click "Begin Analysis" -- the pipeline flows automatically from upload to claims extraction.

---

## 7. Frontend Analysis Flow

### 7.1 Analysis Trigger

When the user clicks "Begin Analysis" on the `ContentPreview` component (FRD 2), the frontend shall:

1. Navigate to `/analysis/{reportId}`.
2. Call `POST /api/v1/analysis/{reportId}/start` to trigger claims extraction.
3. Begin polling `GET /api/v1/analysis/{reportId}/status` for progress updates.

### 7.2 Analysis Page Updates

The `AnalysisPage` (`src/pages/AnalysisPage.tsx`) replaces the FRD 0 stub with an initial analysis view. The full 3-panel layout (PDF viewer, detective dashboard, reasoning panel) is delivered in FRDs 4, 5, and 12. FRD 3 delivers:

1. **Report header:** Display the report filename, page count, and current analysis status.
2. **Progress section:** While `status = "analyzing"`:
   - Show a loading indicator with the text "Extracting claims from document..."
   - Once claims start appearing (polled via status endpoint), show the running claim count.
3. **Claims list section:** Once `status = "completed"`:
   - Display the full list of extracted claims.
   - Each claim is shown as a card with: claim text, type badge (color-coded by type), page number, priority badge, and a collapsible section for the agent's reasoning and IFRS mappings.
   - Filter controls at the top: filter by claim type (dropdown/chips) and priority (dropdown/chips).
   - Claims are ordered by page number, then by priority.
4. **Error state:** If `status = "error"`, show the error message and a "Retry Analysis" button.

### 7.3 Claims Card Component

The system shall implement a `ClaimCard` component (`src/components/Analysis/ClaimCard.tsx`):

```typescript
interface ClaimCardProps {
  claim: Claim;
}
```

**Visual design:**

1. A card with a left border colored by claim type (using the claim type colors defined below).
2. The claim text as the primary content.
3. A type badge and priority badge in the card header.
4. Source page reference: "Page {N}".
5. IFRS paragraph tags displayed as small badges below the claim text (e.g., "S2.29(a)(i)", "S1.46").
6. A collapsible "Reasoning" section showing the Claims Agent's reasoning for flagging this claim.

**Claim type colors:**

| Type | Color | CSS Variable |
|---|---|---|
| Geographic | Forest green | `--claim-geographic` |
| Quantitative | Coral/orange | `--claim-quantitative` |
| Legal/Governance | Deep purple | `--claim-legal` |
| Strategic | Amber/gold | `--claim-strategic` |
| Environmental | Teal | `--claim-environmental` |

### 7.4 Analysis Hook (`src/hooks/useAnalysis.ts`)

The system shall implement a custom React hook for the analysis lifecycle:

```typescript
interface UseAnalysisReturn {
  // State
  analysisState: 'idle' | 'starting' | 'analyzing' | 'complete' | 'error';
  claims: Claim[];
  claimsCount: number;
  claimsByType: Record<ClaimType, number>;
  claimsByPriority: Record<string, number>;
  error: string | null;

  // Actions
  startAnalysis: (reportId: string) => Promise<void>;
  retry: (reportId: string) => Promise<void>;

  // Filters
  typeFilter: ClaimType | null;
  priorityFilter: string | null;
  setTypeFilter: (type: ClaimType | null) => void;
  setPriorityFilter: (priority: string | null) => void;
  filteredClaims: Claim[];
}

function useAnalysis(reportId: string): UseAnalysisReturn;
```

### 7.5 Polling Behavior

The hook shall poll `GET /api/v1/analysis/{reportId}/status` every **3 seconds** while `status = "analyzing"`:

1. On each poll, update the claim counts displayed to the user.
2. When status transitions to `"completed"`, fetch the full claims list via `GET /api/v1/analysis/{reportId}/claims` and stop polling.
3. When status transitions to `"error"`, stop polling and display the error.
4. Maximum poll count: **100** (5 minutes at 3-second intervals). Claims extraction for a 200-page report should complete in 30-90 seconds.

---

## 8. Analysis Schemas

### 8.1 Backend Schemas (`app/schemas/analysis.py`)

The system shall define the following Pydantic schemas, replacing the FRD 0 stub:

```python
class StartAnalysisResponse(BaseModel):
    """Response after triggering analysis."""
    report_id: str
    status: str
    message: str

class AnalysisStatusResponse(BaseModel):
    """Response for analysis status polling."""
    report_id: str
    status: str
    claims_count: int
    claims_by_type: dict[str, int]
    claims_by_priority: dict[str, int]
    error_message: str | None = None
    updated_at: datetime

class ClaimResponse(BaseModel):
    """Response for a single claim."""
    id: str
    claim_text: str
    claim_type: str
    source_page: int
    source_location: dict | None = None
    ifrs_paragraphs: list[dict] = []
    priority: str
    agent_reasoning: str | None = None
    created_at: datetime

class ClaimsListResponse(BaseModel):
    """Paginated response for claims list."""
    claims: list[ClaimResponse]
    total: int
    page: int
    size: int
```

### 8.2 Frontend Types

The system shall update `src/types/claim.ts` with complete type definitions:

```typescript
type ClaimType = 'geographic' | 'quantitative' | 'legal_governance' | 'strategic' | 'environmental';
type ClaimPriority = 'high' | 'medium' | 'low';

interface IFRSMapping {
  paragraph_id: string;
  pillar: string;
  relevance: string;
}

interface Claim {
  id: string;
  claim_text: string;
  claim_type: ClaimType;
  source_page: number;
  source_location: {
    source_context: string;
  } | null;
  ifrs_paragraphs: IFRSMapping[];
  priority: ClaimPriority;
  agent_reasoning: string | null;
  created_at: string;
}

interface AnalysisStatusResponse {
  report_id: string;
  status: string;
  claims_count: number;
  claims_by_type: Record<ClaimType, number>;
  claims_by_priority: Record<ClaimPriority, number>;
  error_message: string | null;
  updated_at: string;
}

interface ClaimsListResponse {
  claims: Claim[];
  total: number;
  page: number;
  size: number;
}
```

### 8.3 API Client Methods (`src/services/api.ts`)

The system shall add the following API client methods:

```typescript
async function startAnalysis(reportId: string): Promise<{ report_id: string; status: string; message: string }> {
  const response = await fetch(`${BASE_URL}/analysis/${reportId}/start`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to start analysis');
  }
  return response.json();
}

async function getAnalysisStatus(reportId: string): Promise<AnalysisStatusResponse> {
  const response = await fetch(`${BASE_URL}/analysis/${reportId}/status`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get analysis status');
  }
  return response.json();
}

async function getClaims(
  reportId: string,
  params?: { type?: ClaimType; priority?: ClaimPriority; page?: number; size?: number }
): Promise<ClaimsListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.type) searchParams.set('type', params.type);
  if (params?.priority) searchParams.set('priority', params.priority);
  if (params?.page) searchParams.set('page', String(params.page));
  if (params?.size) searchParams.set('size', String(params.size));

  const url = `${BASE_URL}/analysis/${reportId}/claims${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get claims');
  }
  return response.json();
}
```

---

## 9. Error Handling

### 9.1 LLM Response Errors

| Error | Trigger | Handling |
|---|---|---|
| LLM returns non-JSON response | Gemini 3 Flash fails to produce structured output | Retry once with a simplified prompt that emphasizes JSON format; if still non-JSON, parse what is available using a lenient extractor |
| LLM returns malformed claims | Claims missing required fields or invalid types | Validate each claim individually; discard invalid claims with a logged warning; proceed with valid claims |
| LLM returns empty claims list | Document contains no recognizable claims (unlikely) | Accept the empty result; set report status to `"completed"` with zero claims |
| LLM timeout | OpenRouter API timeout (>60 seconds) | Retry up to 3 times (handled by OpenRouter client wrapper from FRD 0); on final failure, set report status to `"error"` |
| LLM rate limit | OpenRouter returns 429 | Exponential backoff retry (handled by OpenRouter client wrapper); propagate error after 3 retries |

### 9.2 RAG Mapping Errors

| Error | Trigger | Handling |
|---|---|---|
| RAG service unavailable | Database connection failure | Skip the RAG validation pass; use the LLM's initial IFRS mappings (Phase 1 only); log a warning |
| RAG returns no results for a claim | No relevant IFRS paragraphs found | Keep the LLM's initial mapping if present; if no mapping at all, set `ifrs_paragraphs = []` |
| Embedding API failure during RAG query | OpenRouter embedding endpoint error | Skip the RAG validation for that claim; use Phase 1 mapping; log the error |

### 9.3 Database Persistence Errors

| Error | Trigger | Handling |
|---|---|---|
| Database write failure | PostgreSQL connection issue or constraint violation | Retry the batch insert once; on failure, set report status to `"error"` with the error message |
| Duplicate claim insert | Race condition or re-run | Use `ON CONFLICT DO NOTHING` or check for existing claims before inserting |

### 9.4 Frontend Error Display

When the analysis status returns `"error"`:

1. Display the error message in a prominent error card.
2. Show a "Retry Analysis" button that calls `POST /api/v1/analysis/{reportId}/start` (which resets the status and re-enqueues the task).
3. If the report needs to be re-uploaded (e.g., corrupt content), provide a "Re-upload" link back to the home page.

---

## 10. Exit Criteria

FRD 3 is complete when ALL of the following are satisfied:

| # | Criterion | Verification |
|---|---|---|
| 1 | "Begin Analysis" button triggers extraction | Click "Begin Analysis" on the content preview; verify `POST /api/v1/analysis/{reportId}/start` is called and returns 200 |
| 2 | Report status transitions to "analyzing" | After starting analysis, query the report and verify `status = "analyzing"` |
| 3 | Claims Agent extracts claims from a test PDF | Upload a sample sustainability report; start analysis; verify claims are extracted |
| 4 | Extracted claims have all required fields | Query `GET /api/v1/analysis/{reportId}/claims`; verify each claim has `claim_text`, `claim_type`, `source_page`, `priority`, `agent_reasoning` |
| 5 | Claims are categorized correctly | Verify claims are assigned to one of the five types; spot-check a sample for accuracy |
| 6 | Priority is assigned to each claim | Verify all claims have `priority` set to `high`, `medium`, or `low` |
| 7 | Source page numbers are correct | Cross-reference extracted claims' `source_page` values against the original PDF to verify accuracy |
| 8 | Preliminary IFRS mappings are present | Verify at least 80% of claims have non-empty `ifrs_paragraphs` |
| 9 | IFRS mappings are reasonable | Spot-check a sample of claims: verify the mapped paragraphs are relevant to the claim content |
| 10 | Claims are persisted in the database | Query the `claims` table directly; verify records exist with correct `report_id` |
| 11 | Report status transitions to "completed" | After extraction finishes, verify `status = "completed"` |
| 12 | Frontend displays claims list | Navigate to `/analysis/{reportId}` after extraction; verify the claims list renders |
| 13 | Claim cards show all expected information | Verify each card displays: claim text, type badge, page number, priority badge, IFRS tags |
| 14 | Claim type filter works | Select a type filter; verify only claims of that type are shown |
| 15 | Claim priority filter works | Select a priority filter; verify only claims of that priority are shown |
| 16 | Collapsible reasoning section works | Expand a claim's reasoning section; verify the agent's reasoning text is displayed |
| 17 | Error handling works | Simulate an LLM failure; verify the report transitions to `"error"` and the frontend shows an error message |
| 18 | Retry after error works | After an error, click "Retry Analysis"; verify the extraction re-runs |
| 19 | Claim count is reasonable for the test document | For a 100+ page sustainability report, verify the agent extracts between 30 and 200 claims |
| 20 | Extraction completes in reasonable time | Verify the full extraction pipeline (LLM call + RAG mapping + persistence) completes in under 2 minutes for a 200-page report |

---

## Appendix A: Claims Extraction Prompt

### A.1 System Prompt

```
You are the Claims Agent in Sibyl, an AI system that verifies sustainability reports against IFRS S1/S2 disclosure standards. Your task is to extract verifiable sustainability claims from a corporate sustainability report.

A "verifiable claim" is a statement that asserts a fact, metric, commitment, or condition that can be checked against external evidence (satellite imagery, news sources, academic literature, regulatory filings) or internal consistency (mathematical relationships, benchmark plausibility).

## Claim Types

Categorize each claim into exactly ONE of these types:

1. **geographic**: Facility locations, land use, deforestation, reforestation, water usage in specific regions, geographic concentration of climate risks, physical risk exposure at specific locations
2. **quantitative**: Emission figures (Scope 1/2/3), percentage targets, financial impacts, year-over-year comparisons, intensity metrics, energy consumption numbers, waste figures
3. **legal_governance**: Board oversight structures, committee responsibilities, compliance assertions, policy commitments, remuneration links to climate performance, regulatory adherence claims
4. **strategic**: Transition plans, net-zero commitments, future targets, investment commitments, timeline assertions, scenario analysis results, SBTi alignment claims
5. **environmental**: Biodiversity commitments, waste management, resource efficiency, renewable energy claims, water stewardship, circular economy initiatives, certification claims

## Priority Assignment

- **high**: Specific numerical claims central to the company's sustainability narrative; core IFRS S2 metrics (Scope 1/2/3, targets); claims that would constitute material greenwashing if false
- **medium**: Qualitative claims with verifiable elements; governance process claims; strategic commitments with timelines
- **low**: General assertions with limited verifiability; environmental commitments without specific metrics

## IFRS S1/S2 Structure (for preliminary mapping)

### S1 Pillars:
- Governance (S1.26-27): Board oversight, competencies, reporting frequency, remuneration
- Strategy (S1.28-35): Risks/opportunities, business model effects, strategy response, financial effects
- Risk Management (S1.38-42): Risk identification, assessment, prioritization, monitoring, integration
- Metrics & Targets (S1.43-53): Performance metrics, targets, baseline, progress

### S2 Climate Paragraphs:
- Governance: S2.5-7 (climate-specific governance)
- Strategy: S2.8-12 (climate risks/opportunities), S2.13 (business model), S2.14 (decision-making/transition plan), S2.15-21 (financial effects), S2.22 (climate resilience)
- Risk Management: S2.24-26 (climate risk management)
- Metrics: S2.27-31 (GHG emissions -- S2.29(a)(i) Scope 1, S2.29(a)(ii) Scope 2, S2.29(a)(iii) Scope 3), S2.33-36 (climate targets)

## Extraction Rules

1. Extract the claim text verbatim where possible. Paraphrase only if the original exceeds 300 characters or spans non-contiguous text.
2. Each claim should be a single verifiable assertion. Split compound statements.
3. Include quantitative context (units, time periods, comparisons).
4. Do NOT extract: boilerplate language, table of contents, methodology definitions (unless asserting facts), disclaimers, generic industry context.
5. Use the <!-- PAGE N --> markers to determine each claim's source page.
6. Provide 1-2 sentences of surrounding context in source_context for location anchoring.
7. Target 50-200 claims for a typical 100-200 page report.
8. Assign preliminary IFRS paragraph IDs based on the structure above.
```

### A.2 User Prompt

```
Analyze the following sustainability report and extract all verifiable claims. Return your response as a JSON object matching the specified schema.

Document content:
{document_content}
```

---

## Appendix B: Example Extracted Claims

### B.1 Quantitative Claim (High Priority)

```json
{
  "claim_text": "Our total Scope 1 emissions were 2.3 million tonnes CO2e in FY2024, a 6.1% decrease from 2.45 million tonnes in FY2023.",
  "claim_type": "quantitative",
  "source_page": 45,
  "source_context": "Our total Scope 1 emissions were 2.3 million tonnes CO2e in FY2024, representing a 6.1% decrease from 2.45 million tonnes in FY2023. This reduction was primarily driven by our transition to natural gas at three major facilities.",
  "priority": "high",
  "reasoning": "Asserts specific Scope 1 emissions figures with year-over-year comparison. The absolute numbers and percentage change are independently verifiable for mathematical consistency. Maps directly to IFRS S2.29(a)(i) absolute Scope 1 GHG emissions requirement.",
  "preliminary_ifrs": ["S2.29(a)(i)", "S1.46"]
}
```

### B.2 Geographic Claim (Medium Priority)

```json
{
  "claim_text": "Our reforestation initiative in Central Kalimantan, Borneo has restored 5,000 hectares of degraded peatland forest since 2020.",
  "claim_type": "geographic",
  "source_page": 72,
  "source_context": "Our reforestation initiative in Central Kalimantan, Borneo has restored 5,000 hectares of degraded peatland forest since 2020. The project employs local communities and has been independently certified by the Verified Carbon Standard (VCS).",
  "priority": "medium",
  "reasoning": "Asserts a specific geographic location (Central Kalimantan, Borneo) and a quantified reforestation outcome (5,000 hectares). Verifiable via satellite imagery (NDVI vegetation analysis over the specified area and time period) and through VCS certification records.",
  "preliminary_ifrs": ["S2.14(a)(ii)"]
}
```

### B.3 Legal/Governance Claim (Medium Priority)

```json
{
  "claim_text": "The Board's Sustainability Committee meets quarterly and has direct oversight of climate-related risk management, with climate performance accounting for 10% of executive variable compensation.",
  "claim_type": "legal_governance",
  "source_page": 12,
  "source_context": "The Board's Sustainability Committee meets quarterly and has direct oversight of climate-related risk management, with climate performance accounting for 10% of executive variable compensation. The Committee is chaired by an independent non-executive director with 15 years of experience in environmental regulation.",
  "priority": "medium",
  "reasoning": "Asserts specific governance structures (quarterly meetings, direct oversight) and a remuneration link (10% of variable compensation). Maps to IFRS S2.5-7 climate governance requirements and S1.27(a)(v) remuneration disclosure. Verifiable against proxy statements and governance documentation.",
  "preliminary_ifrs": ["S2.5", "S2.6", "S1.27(a)(v)"]
}
```

### B.4 Strategic Claim (High Priority)

```json
{
  "claim_text": "We have committed to achieving net-zero greenhouse gas emissions across our full value chain by 2050, with an interim target of a 42% absolute reduction in Scope 1 and 2 emissions by 2030 from a 2019 baseline, validated by the Science Based Targets initiative.",
  "claim_type": "strategic",
  "source_page": 8,
  "source_context": "We have committed to achieving net-zero greenhouse gas emissions across our full value chain by 2050, with an interim target of a 42% absolute reduction in Scope 1 and 2 emissions by 2030 from a 2019 baseline, validated by the Science Based Targets initiative. This target is aligned with a 1.5°C warming pathway.",
  "priority": "high",
  "reasoning": "Asserts a net-zero commitment with specific timeline (2050), interim target (42% by 2030), baseline year (2019), scope (Scope 1 and 2), and third-party validation (SBTi). Each element is independently verifiable: SBTi validation status, mathematical achievability of the target, and 1.5°C pathway alignment. Maps to IFRS S2.33-36 climate targets requirements.",
  "preliminary_ifrs": ["S2.33", "S2.34", "S2.36", "S2.14(a)(iv)"]
}
```

### B.5 Environmental Claim (Low Priority)

```json
{
  "claim_text": "We source 100% of our electricity from certified renewable sources across all European operations.",
  "claim_type": "environmental",
  "source_page": 58,
  "source_context": "We source 100% of our electricity from certified renewable sources across all European operations. Energy attribute certificates (EACs) are procured for the full volume of electricity consumed at our 12 European facilities.",
  "priority": "low",
  "reasoning": "Asserts 100% renewable electricity claim with a geographic scope (European operations) and a certification mechanism (EACs). Verifiable through EAC registries and facility energy consumption records, though verification requires access to procurement data that may not be publicly available.",
  "preliminary_ifrs": ["S2.29(d)"]
}
```

---

## Appendix C: Claim Extraction Flow Sequence Diagram

```
User                Frontend              Backend             Redis          Worker           Database         OpenRouter       RAG Service
 │                     │                     │                  │               │                 │                │                │
 │  Click "Begin       │                     │                  │               │                 │                │                │
 │  Analysis"          │                     │                  │               │                 │                │                │
 │────────────────────►│                     │                  │               │                 │                │                │
 │                     │                     │                  │               │                 │                │                │
 │                     │  POST /analysis/    │                  │               │                 │                │                │
 │                     │  {id}/start         │                  │               │                 │                │                │
 │                     │────────────────────►│                  │               │                 │                │                │
 │                     │                     │  Set "analyzing" │               │                 │                │                │
 │                     │                     │────────────────────────────────────────────────────►│                │                │
 │                     │                     │                  │               │                 │                │                │
 │                     │                     │  Enqueue task    │               │                 │                │                │
 │                     │                     │─────────────────►│               │                 │                │                │
 │                     │                     │                  │               │                 │                │                │
 │                     │  200 {status}       │                  │               │                 │                │                │
 │                     │◄────────────────────│                  │               │                 │                │                │
 │                     │                     │                  │               │                 │                │                │
 │  Show analyzing     │                     │                  │  BRPOP        │                 │                │                │
 │◄────────────────────│                     │                  │──────────────►│                 │                │                │
 │                     │                     │                  │               │                 │                │                │
 │                     │                     │                  │               │  Load report     │                │                │
 │                     │                     │                  │               │────────────────►│                │                │
 │                     │                     │                  │               │◄────────────────│                │                │
 │                     │                     │                  │               │                 │                │                │
 │                     │                     │                  │               │  Extract claims  │                │                │
 │                     │                     │                  │               │  (full document) │                │                │
 │                     │                     │                  │               │────────────────────────────────►│                │
 │                     │                     │                  │               │                 │   Gemini Flash  │                │
 │                     │                     │                  │               │                 │   structured    │                │
 │                     │                     │                  │               │                 │   JSON output   │                │
 │                     │                     │                  │               │◄────────────────────────────────│                │
 │                     │                     │                  │               │                 │                │                │
 │                     │  GET /analysis/     │                  │               │  RAG mapping     │                │                │
 │                     │  {id}/status        │                  │               │  validation      │                │                │
 │                     │────────────────────►│                  │               │───────────────────────────────────────────────►│
 │                     │  {"analyzing",      │                  │               │                 │                │                │
 │                     │   claims_count: 0}  │                  │               │                 │                │   Hybrid IFRS  │
 │                     │◄────────────────────│                  │               │                 │                │   search       │
 │                     │                     │                  │               │◄──────────────────────────────────────────────│
 │                     │                     │                  │               │                 │                │                │
 │                     │                     │                  │               │  Persist claims  │                │                │
 │                     │                     │                  │               │────────────────►│                │                │
 │                     │                     │                  │               │                 │                │                │
 │                     │                     │                  │               │  Set "completed" │                │                │
 │                     │                     │                  │               │────────────────►│                │                │
 │                     │                     │                  │               │                 │                │                │
 │                     │  GET /analysis/     │                  │               │                 │                │                │
 │                     │  {id}/status        │                  │               │                 │                │                │
 │                     │────────────────────►│                  │               │                 │                │                │
 │                     │  {"completed",      │                  │               │                 │                │                │
 │                     │   claims_count: 87} │                  │               │                 │                │                │
 │                     │◄────────────────────│                  │               │                 │                │                │
 │                     │                     │                  │               │                 │                │                │
 │                     │  GET /analysis/     │                  │               │                 │                │                │
 │                     │  {id}/claims        │                  │               │                 │                │                │
 │                     │────────────────────►│                  │               │                 │                │                │
 │                     │  [claims list]      │                  │               │                 │                │                │
 │                     │◄────────────────────│                  │               │                 │                │                │
 │                     │                     │                  │               │                 │                │                │
 │  Display claims     │                     │                  │               │                 │                │                │
 │◄────────────────────│                     │                  │               │                 │                │                │
```

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| Full-document single-pass extraction over multi-chunk extraction | Gemini 3 Flash's 1M token context window (PRD Section 4.2) accommodates full 200-page reports. Single-pass avoids the complexity of chunk-boundary deduplication, cross-chunk context loss, and reassembly logic. Trade-off: higher per-request cost, but eliminated engineering complexity outweighs cost for hackathon scope. |
| Gemini 3 Flash over Claude Sonnet 4.5 for claims extraction | PRD explicitly specifies Gemini 3 Flash for the Claims Agent. The 1M token context window is critical for full-document processing; Claude's 200K window would require multi-chunk extraction. Gemini is also more cost-effective for this high-volume task ($0.50/$3.00 vs $3/$15 per 1M tokens). |
| Two-phase IFRS mapping (LLM + RAG) over RAG-only or LLM-only | LLM-only mapping is fast but may hallucinate paragraph IDs. RAG-only mapping requires accurate queries per claim (expensive and slow at scale). The two-phase approach gets good initial mappings from the LLM (which has IFRS knowledge) and validates/corrects them with RAG retrieval, balancing speed and accuracy. |
| Batched RAG queries over per-claim queries | 200 claims × 1 RAG query each = 200 embedding API calls + 200 database queries. Grouping claims by type and constructing representative queries reduces this to ~50-100 queries while maintaining mapping quality. |
| Structured JSON output over free-text extraction | Structured output (JSON schema) from Gemini 3 Flash eliminates the need for regex-based or heuristic text parsing. The schema enforces required fields and valid types. If structured output fails, a fallback lenient parser handles degraded responses. |
| Separate `sibyl:tasks:extract_claims` queue over reusing parse queue | Claims extraction is a distinct task type with different error handling and status semantics. Separate queues prevent confusion between parsing and analysis tasks and allow independent monitoring. |
| `source_context` for location anchoring over bounding box coordinates | The Claims Agent operates on markdown text, not PDF layout. Computing pixel-level bounding boxes requires PDF rendering (deferred to FRD 4). Providing textual context enables FRD 4 to text-match against the rendered PDF for precise highlight positioning. |
| Status `"completed"` for claims-only completion | In FRD 3, the Claims Agent is the only pipeline step. Using `"completed"` keeps the status model simple. FRD 5 will extend the pipeline and may introduce intermediate statuses (`"claims_extracted"`, `"investigating"`, etc.) as the full pipeline is built. |
| Auto-trigger as opt-in (`AUTO_START_ANALYSIS = False`) | Manual trigger is the default for development (allows testing upload and analysis separately). Auto-trigger is a demo convenience that can be enabled for the hackathon presentation to show a seamless upload-to-analysis flow. |
| 3-second polling interval (vs. 2-second for upload) | Claims extraction takes 30-90 seconds (longer than upload processing). A slightly slower polling interval reduces server load during the longer operation while still providing responsive updates. |
| `ClaimCard` component with type-based left border | Provides instant visual categorization of claims. Color coding by type is consistent with the PRD's agent color identity system (PRD Section 7.1) and extends naturally to the full analysis view in FRD 4+. |
| Claims ordered by page number, then priority | Page-ordered display creates a natural reading flow that mirrors the original document structure. Priority sub-ordering surfaces the most important claims first within each page region. |
| Temperature 0.1 over 0.0 | A slight temperature prevents the model from being overly deterministic, which can lead to missed claims when the model "locks in" to a narrow extraction pattern. 0.1 provides consistency with a small degree of creative flexibility. |
