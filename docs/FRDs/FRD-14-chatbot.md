# Feature Requirements Document: FRD 14 -- Chatbot (v1.0)

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.3](../PRD.md) |
| **FRD Order** | [FRD Order](../FRD-order.md) |
| **PRD Sections** | 4.12 (Chatbot -- Contextual Q&A), 7.2 (Chatbot Panel) |
| **Type** | Feature |
| **Depends On** | FRD 1 (RAG Pipeline), FRD 11 (Judge Agent & Cyclic Validation), FRD 13 (Source of Truth Report) |
| **Delivers** | RAG-powered conversational Q&A with inline citations, persistent conversation across page navigation, slide-out chat panel UI, backend chat endpoint, conversation history storage |
| **Created** | 2026-02-09 |

---

## Summary

FRD 14 delivers the Chatbot -- a conversational interface that allows users to ask natural-language questions about the analyzed sustainability report and receive contextual, evidence-backed answers with inline citations. The chatbot (`app/api/routes/chat.py`) provides a backend chat endpoint that performs multi-source RAG retrieval across the original report content, agent findings, IFRS/SASB standards, Source of Truth verdicts, and disclosure gaps, assembles retrieved chunks into LLM context with source attribution, and generates responses using Gemini 3 Flash via OpenRouter with streaming support. The chatbot understands the structure of the analysis -- it can reference specific agents, claims, IFRS paragraphs, evidence, and gaps, providing answers grounded in the actual analysis results. Inline citations are generated linking to source entities (claims, findings, IFRS paragraphs, verdicts, gaps) with navigation targets. The frontend delivers a slide-out chat panel (`ChatPanel.tsx`, `ChatMessage.tsx`, `ChatInput.tsx`) accessible via a floating button from any page, with persistent conversation history maintained across page navigation. Responses stream in real-time via Server-Sent Events (SSE) for progressive text appearance. The conversation data model stores messages, citations, and timestamps in PostgreSQL, enabling conversation persistence and history retrieval. After FRD 14, users can ask natural-language questions about the analysis from any page and receive contextual, evidence-backed answers with inline citations linking to specific claims, agent findings, or IFRS paragraphs.

---

## Given Context (Preconditions)

The following are assumed to be in place from prior FRDs:

| Prerequisite | Source FRD | Deliverable |
|---|---|---|
| Docker Compose with PostgreSQL 17 + pgvector, Redis, backend, frontend | FRD 0 | `docker-compose.yml` |
| RAG pipeline with hybrid search, multi-source retrieval (report, finding, ifrs_s1, ifrs_s2, sasb, verdict, gap) | FRD 1 | `app/services/rag_service.py`, `app/agents/tools/rag_lookup.py` |
| Agent findings stored in database with `agent_name`, `claim_id`, `evidence_type`, `summary`, `details` | FRD 11 | `app/models/finding.py` |
| Source of Truth verdicts stored with `claim_id`, `verdict`, `ifrs_mappings` | FRD 11, FRD 13 | `app/models/verdict.py` |
| Disclosure gaps stored with `paragraph_id`, `gap_status`, `materiality_context` | FRD 6, FRD 13 | `app/models/finding.py` (evidence_type="disclosure_gap") |
| Claims stored with `claim_id`, `claim_text`, `claim_type`, `source_page`, `ifrs_paragraphs` | FRD 3 | `app/models/claim.py` |
| Report content chunked and embedded in RAG | FRD 2 | `embeddings` table with `source_type="report"` |
| OpenRouter client wrapper with `Models.GEMINI_FLASH` constant | FRD 0 | `app/services/openrouter_client.py` |
| SSE streaming infrastructure | FRD 5 | `app/api/routes/stream.py`, SSE client patterns |
| Frontend routing and layout shell | FRD 0 | `src/pages/`, `src/components/Layout/` |
| React + TypeScript + shadcn/ui + TailwindCSS v4 | FRD 0 | Frontend stack |

### Terms

| Term | Definition |
|---|---|
| Inline citation | A reference marker (e.g., `[1]`, `[2]`) within chatbot response text that links to a source entity (claim, finding, IFRS paragraph, verdict, gap) |
| Citation type | The category of source being cited: `claim`, `finding`, `ifrs_paragraph`, `verdict`, `gap` |
| Citation navigation target | The UI destination when a citation is clicked: PDF viewer (claim), agent finding panel (finding), IFRS paragraph viewer (ifrs_paragraph), Source of Truth claim card (verdict), Disclosure Gaps section (gap) |
| Conversation persistence | The ability to maintain conversation history across page navigation, storing messages in the database and retrieving them when the chat panel is reopened |
| Multi-source RAG retrieval | RAG queries that search across multiple source types simultaneously: report content, agent findings, IFRS/SASB standards, verdicts, disclosure gaps |
| Context assembly | The process of combining retrieved RAG chunks into a single LLM context prompt with source attribution and citation markers |
| Response streaming | Progressive text appearance where the chatbot response appears word-by-word in real-time via SSE, similar to ChatGPT |
| Chat panel | A slide-out panel component anchored to the right edge of the screen, accessible from any page via a floating button |

---

## Executive Summary (Gherkin-Style)

```gherkin
Feature: Chatbot -- Contextual Q&A with Inline Citations

  Background:
    Given  FRD 1, FRD 11, and FRD 13 are complete
    And    all services are running (backend, frontend, PostgreSQL, Redis)
    And    a sustainability report has been analyzed with claims, findings, verdicts, and disclosure gaps
    And    the RAG pipeline contains report content, agent findings, IFRS/SASB standards, verdicts, and gaps

  Scenario: User asks a question about agent findings
    Given  the user opens the chat panel from any page
    When   they type "What did the Geography Agent find about the Borneo facility?"
    Then   the chatbot performs RAG retrieval across agent findings
    And    retrieves relevant Geography Agent findings
    And    generates a response referencing the specific findings
    And    includes inline citations linking to the findings
    And    the response streams in real-time via SSE

  Scenario: User asks about IFRS compliance
    Given  the user asks "Does the report meet S2.14(a)(iv) transition plan requirements?"
    When   the chatbot processes the query
    Then   it retrieves relevant IFRS paragraphs (S2.14(a)(iv))
    And    retrieves related claims and verdicts
    And    generates a response explaining compliance status
    And    includes citations to the IFRS paragraph and relevant claims

  Scenario: User asks about disclosure gaps
    Given  the user asks "What are the main compliance gaps in the Governance pillar?"
    When   the chatbot processes the query
    Then   it retrieves disclosure gaps from the Legal Agent
    And    filters gaps by Governance pillar
    And    generates a response listing the gaps with materiality context
    And    includes citations linking to each gap

  Scenario: User asks about evidence supporting a claim
    Given  the user asks "What evidence supports the company's Scope 3 emission reduction claim?"
    When   the chatbot processes the query
    Then   it retrieves the claim from the database
    And    retrieves all agent findings related to that claim
    And    retrieves the Judge verdict for the claim
    And    generates a response summarizing the evidence chain
    And    includes citations to claims, findings, and verdicts

  Scenario: Conversation persists across page navigation
    Given  the user has a conversation with multiple messages
    When   they navigate from the Analysis Page to the Source of Truth Page
    Then   the chat panel remains open with conversation history intact
    And    when they navigate to the Home Page, the conversation persists
    And    when they reopen the chat panel later, the full history is restored

  Scenario: Citations are clickable and navigate to sources
    Given  a chatbot response contains inline citations
    When   the user clicks citation [1] (claim citation)
    Then   the application navigates to the PDF viewer highlighting the claim
    When   the user clicks citation [2] (IFRS paragraph citation)
    Then   the application shows the IFRS paragraph requirement text
    When   the user clicks citation [3] (finding citation)
    Then   the application navigates to the agent finding panel

  Scenario: Multi-turn conversation maintains context
    Given  the user asks "What did the Legal Agent find?"
    And    the chatbot responds with Legal Agent findings
    When   the user follows up with "What about the Geography Agent?"
    Then   the chatbot understands the context (continuing the agent comparison)
    And    retrieves Geography Agent findings
    And    generates a response comparing Legal and Geography findings

  Scenario: Chat panel is accessible from any page
    Given  the user is on the Home Page
    Then   a floating chat button is visible in the bottom-right corner
    When   they click the button
    Then   the chat panel slides out from the right
    When   they navigate to the Analysis Page
    Then   the chat panel remains accessible and persistent
    When   they navigate to the Source of Truth Page
    Then   the chat panel remains accessible and persistent

  Scenario: Response streaming appears progressively
    Given  the user submits a question
    When   the chatbot generates a response
    Then   the response text appears word-by-word in real-time
    And    citations appear as the response is generated
    And    the streaming completes within 5 seconds for typical queries

  Scenario: Error handling for unavailable data
    Given  the user asks about a claim that has no findings yet
    When   the chatbot processes the query
    Then   it responds explaining that investigation is incomplete
    And    does not crash or return an error
    And    suggests waiting for analysis to complete
```

---

## Table of Contents

1. [Backend Chat Architecture](#1-backend-chat-architecture)
2. [RAG Retrieval Strategy](#2-rag-retrieval-strategy)
3. [Context Assembly](#3-context-assembly)
4. [LLM Integration](#4-llm-integration)
5. [Inline Citation System](#5-inline-citation-system)
6. [Citation Types and Navigation Targets](#6-citation-types-and-navigation-targets)
7. [Conversation Persistence](#7-conversation-persistence)
8. [Chat Panel UI](#8-chat-panel-ui)
9. [Chat Message Component](#9-chat-message-component)
10. [Chat Input Component](#10-chat-input-component)
11. [Streaming Response Display](#11-streaming-response-display)
12. [Cross-Page Persistence](#12-cross-page-persistence)
13. [Backend Chat Endpoint](#13-backend-chat-endpoint)
14. [Chat Data Model](#14-chat-data-model)
15. [Error Handling](#15-error-handling)
16. [Exit Criteria](#16-exit-criteria)
17. [Appendix A: Chatbot System Prompt](#appendix-a-chatbot-system-prompt)
18. [Appendix B: RAG Query Construction Examples](#appendix-b-rag-query-construction-examples)
19. [Appendix C: Citation Format Specification](#appendix-c-citation-format-specification)
20. [Appendix D: Example Conversations](#appendix-d-example-conversations)
21. [Appendix E: Chat API Response Schemas](#appendix-e-chat-api-response-schemas)
22. [Design Decisions Log](#design-decisions-log)

---

## 1. Backend Chat Architecture

### 1.1 Overview

The chatbot backend (`app/api/routes/chat.py`) provides a conversational Q&A interface that leverages the RAG pipeline to answer questions about the analyzed sustainability report. The architecture consists of three main components:

1. **Chat endpoint** (`POST /api/v1/chat/{reportId}/message`) -- Receives user messages, performs RAG retrieval, generates responses with citations, and streams responses via SSE.
2. **Conversation history endpoint** (`GET /api/v1/chat/{reportId}/history`) -- Retrieves stored conversation history for a report.
3. **Chat service** (`app/services/chat_service.py`) -- Core logic for RAG retrieval, context assembly, LLM interaction, and citation generation.

### 1.2 Request Flow

```
User Message → Chat Endpoint → Chat Service → RAG Retrieval (multi-source)
                                                      ↓
                                    Context Assembly + Citation Mapping
                                                      ↓
                                    LLM (Gemini 3 Flash) → Response Generation
                                                      ↓
                                    Citation Extraction → Response + Citations
                                                      ↓
                                    SSE Stream → Frontend
                                                      ↓
                                    Database Persistence
```

### 1.3 Chat Service Interface

```python
# app/services/chat_service.py

class ChatService:
    """Service for chatbot Q&A with RAG retrieval and citation generation."""

    def __init__(
        self,
        db: AsyncSession,
        rag_service: RAGService,
        openrouter_client: OpenRouterClient
    ):
        self.db = db
        self.rag_service = rag_service
        self.openrouter_client = openrouter_client

    async def generate_response(
        self,
        report_id: str,
        user_message: str,
        conversation_history: list[dict],
        stream: bool = True
    ) -> AsyncIterator[dict]:
        """Generate chatbot response with RAG retrieval and citations.

        Args:
            report_id: The report being discussed
            user_message: User's question
            conversation_history: Previous messages in the conversation
            stream: Whether to stream the response (SSE) or return complete

        Yields:
            Dicts with 'type' ('token', 'citation', 'done') and 'data'
        """
```

### 1.4 Processing Steps

The `generate_response` method executes:

1. **RAG retrieval:** Perform multi-source retrieval (see Section 2).
2. **Context assembly:** Combine retrieved chunks into LLM context with source attribution (see Section 3).
3. **LLM generation:** Call Gemini 3 Flash with system prompt and context (see Section 4).
4. **Citation extraction:** Parse citations from LLM response and map to source entities (see Section 5).
5. **Response streaming:** Stream tokens and citations via SSE (if `stream=True`).
6. **Database persistence:** Store message and citations in the database (see Section 7).

---

## 2. RAG Retrieval Strategy

### 2.1 Overview

The chatbot performs multi-source RAG retrieval across all available knowledge sources to provide comprehensive, contextual answers. Unlike agent-specific retrieval (which filters by `source_types`), the chatbot searches broadly and then filters results by relevance.

### 2.2 Source Types

The chatbot retrieves from the following source types:

| Source Type | Description | Retrieval Method |
|---|---|---|
| `report` | Original sustainability report content | RAG search with `source_types=["report"]`, `report_id=report_id` |
| `finding` | Agent findings from investigation | Query `findings` table, embed `summary` + `details`, or RAG search if findings are embedded |
| `ifrs_s1` | IFRS S1 standard paragraphs | RAG search with `source_types=["ifrs_s1"]` |
| `ifrs_s2` | IFRS S2 standard paragraphs | RAG search with `source_types=["ifrs_s2"]` |
| `sasb` | SASB industry standards | RAG search with `source_types=["sasb"]` |
| `verdict` | Judge verdicts for claims | Query `verdicts` table, embed `reasoning` + `ifrs_mappings` |
| `gap` | Disclosure gaps from Legal Agent | Query `findings` table where `evidence_type="disclosure_gap"` |

### 2.3 Multi-Source Query Strategy

The system performs parallel RAG queries across source types:

```python
async def retrieve_multi_source(
    self,
    query: str,
    report_id: str,
    top_k_per_source: int = 5
) -> dict[str, list[RAGResult]]:
    """Retrieve from all source types in parallel.

    Returns:
        Dict mapping source_type to list of RAGResult objects.
    """
    # Parallel retrieval
    results = await asyncio.gather(
        self.rag_service.search(
            query, top_k=top_k_per_source,
            source_types=["report"], report_id=report_id
        ),
        self.rag_service.search(
            query, top_k=top_k_per_source,
            source_types=["ifrs_s1", "ifrs_s2"]
        ),
        self.rag_service.search(
            query, top_k=top_k_per_source,
            source_types=["sasb"]
        ),
        self._retrieve_findings(query, report_id, top_k_per_source),
        self._retrieve_verdicts(query, report_id, top_k_per_source),
        self._retrieve_gaps(query, report_id, top_k_per_source),
    )

    return {
        "report": results[0],
        "ifrs": results[1],
        "sasb": results[2],
        "finding": results[3],
        "verdict": results[4],
        "gap": results[5],
    }
```

### 2.4 Finding Retrieval

Agent findings are retrieved by:

1. **Database query:** Search `findings` table for `summary` or `details` containing query keywords.
2. **Embedding search:** If findings are embedded in RAG (optional enhancement), use RAG search with `source_types=["finding"]`.
3. **Filter by report:** Ensure findings belong to the current report (`report_id`).

```python
async def _retrieve_findings(
    self,
    query: str,
    report_id: str,
    top_k: int
) -> list[RAGResult]:
    """Retrieve agent findings relevant to the query."""
    # Query database for findings
    stmt = select(Finding).where(
        Finding.report_id == report_id
    ).where(
        or_(
            Finding.summary.ilike(f"%{query}%"),
            Finding.details.cast(String).ilike(f"%{query}%")
        )
    ).limit(top_k)

    findings = await self.db.execute(stmt)
    
    # Convert to RAGResult format
    results = []
    for finding in findings.scalars():
        # Embed finding summary for similarity scoring
        embedding = await self.rag_service.embedding_service.embed_text(
            f"{finding.summary} {finding.details}"
        )
        # Compute similarity (simplified -- full implementation uses RAG)
        results.append(RAGResult(
            chunk_id=finding.finding_id,
            chunk_text=finding.summary,
            metadata={
                "agent_name": finding.agent_name,
                "claim_id": finding.claim_id,
                "evidence_type": finding.evidence_type,
            },
            source_type="finding",
            report_id=report_id,
            score=0.8,  # Placeholder -- actual score from embedding similarity
            search_method="semantic"
        ))
    
    return results
```

### 2.5 Verdict Retrieval

Judge verdicts are retrieved by:

1. **Database query:** Search `verdicts` table for `reasoning` containing query keywords.
2. **Claim association:** Include related claims via `claim_id` foreign key.
3. **IFRS mapping:** Include IFRS paragraph mappings from `ifrs_mappings`.

```python
async def _retrieve_verdicts(
    self,
    query: str,
    report_id: str,
    top_k: int
) -> list[RAGResult]:
    """Retrieve Judge verdicts relevant to the query."""
    stmt = select(Verdict).join(Claim).where(
        Claim.report_id == report_id
    ).where(
        Verdict.reasoning.ilike(f"%{query}%")
    ).limit(top_k)

    verdicts = await self.db.execute(stmt)
    
    results = []
    for verdict in verdicts.scalars():
        results.append(RAGResult(
            chunk_id=verdict.verdict_id,
            chunk_text=verdict.reasoning,
            metadata={
                "claim_id": verdict.claim_id,
                "verdict": verdict.verdict,
                "ifrs_mappings": verdict.ifrs_mappings,
            },
            source_type="verdict",
            report_id=report_id,
            score=0.8,
            search_method="keyword"
        ))
    
    return results
```

### 2.6 Gap Retrieval

Disclosure gaps are retrieved by:

1. **Database query:** Search `findings` table where `evidence_type="disclosure_gap"`.
2. **Filter by pillar:** If query mentions a pillar (e.g., "Governance"), filter gaps by `chunk_metadata.pillar`.
3. **Include materiality context:** Include `materiality_context` in retrieved text.

```python
async def _retrieve_gaps(
    self,
    query: str,
    report_id: str,
    top_k: int
) -> list[RAGResult]:
    """Retrieve disclosure gaps relevant to the query."""
    stmt = select(Finding).where(
        Finding.report_id == report_id,
        Finding.evidence_type == "disclosure_gap"
    ).limit(top_k)

    gaps = await self.db.execute(stmt)
    
    results = []
    for gap in gaps.scalars():
        details = gap.details or {}
        results.append(RAGResult(
            chunk_id=gap.finding_id,
            chunk_text=f"{details.get('requirement_text', '')} {details.get('materiality_context', '')}",
            metadata={
                "paragraph_id": details.get("paragraph_id"),
                "pillar": details.get("pillar"),
                "gap_status": details.get("gap_status"),
            },
            source_type="gap",
            report_id=report_id,
            score=0.8,
            search_method="keyword"
        ))
    
    return results
```

### 2.7 Result Merging and Re-Ranking

After retrieving from all sources, the system:

1. **Merge results:** Combine all `RAGResult` objects into a single list.
2. **Re-rank by relevance:** Sort by `score` (descending) across all source types.
3. **Deduplicate:** Remove duplicate chunks (same `chunk_id` or highly similar text).
4. **Limit to top-k:** Select top 15-20 results for context assembly (sufficient for comprehensive answers without exceeding token limits).

---

## 3. Context Assembly

### 3.1 Overview

Context assembly combines retrieved RAG chunks into a single LLM context prompt with source attribution and citation markers. The assembled context enables the LLM to generate responses that reference specific sources and include inline citations.

### 3.2 Context Structure

The assembled context follows this structure:

```
## Context Sources

### Report Content
[Citation 1] [Report > Environmental Performance > GHG Emissions > Scope 3]
Our Scope 3 emissions totaled 12.4 million tonnes CO2e in FY2024...

### IFRS Standards
[Citation 2] [IFRS S2 > Metrics & Targets > GHG Emissions > S2.29(a)(iii)]
An entity shall disclose absolute Scope 3 GHG emissions by category...

### Agent Findings
[Citation 3] [Legal Agent Finding]
Claim about Scope 3 emissions maps to S2.29(a)(iii). Compliance status: partially_addressed...

### Judge Verdicts
[Citation 4] [Judge Verdict for Claim #123]
Verdict: Verified. Multiple sources corroborate the Scope 3 emission reduction claim...

### Disclosure Gaps
[Citation 5] [Disclosure Gap: S2.29(a)(iii)]
IFRS S2.29(a)(iii) requirement (Scope 3 emissions by category) is partially_addressed...
```

### 3.3 Citation Marker Assignment

Each retrieved chunk receives a sequential citation marker (`[1]`, `[2]`, etc.):

```python
def assemble_context(
    self,
    retrieved_results: list[RAGResult]
) -> tuple[str, dict[int, CitationMetadata]]:
    """Assemble context with citation markers.

    Returns:
        (context_text, citation_map) where citation_map maps citation_number to metadata.
    """
    context_parts = []
    citation_map = {}
    citation_number = 1

    # Group by source type for organization
    by_source = {}
    for result in retrieved_results:
        by_source.setdefault(result.source_type, []).append(result)

    # Assemble context by source type
    for source_type in ["report", "ifrs", "sasb", "finding", "verdict", "gap"]:
        if source_type not in by_source:
            continue

        context_parts.append(f"\n### {source_type.upper().replace('_', ' ')}")
        
        for result in by_source[source_type]:
            citation_marker = f"[{citation_number}]"
            context_parts.append(
                f"{citation_marker} {self._format_result(result)}"
            )
            
            # Store citation metadata
            citation_map[citation_number] = CitationMetadata(
                citation_number=citation_number,
                source_type=result.source_type,
                chunk_id=result.chunk_id,
                metadata=result.metadata,
                report_id=result.report_id,
            )
            
            citation_number += 1

    context_text = "\n".join(context_parts)
    return context_text, citation_map
```

### 3.4 Result Formatting

Each result is formatted with source metadata:

```python
def _format_result(self, result: RAGResult) -> str:
    """Format a RAG result for context inclusion."""
    if result.source_type == "report":
        section_path = result.metadata.get("section_path", [])
        section_str = " > ".join(section_path) if section_path else "Report"
        return f"[Report > {section_str}]\n{result.chunk_text}"
    
    elif result.source_type in ["ifrs_s1", "ifrs_s2"]:
        paragraph_id = result.metadata.get("paragraph_id", "")
        pillar = result.metadata.get("pillar", "")
        section = result.metadata.get("section", "")
        return f"[IFRS {result.metadata.get('standard', '')} > {pillar} > {section} > {paragraph_id}]\n{result.chunk_text}"
    
    elif result.source_type == "finding":
        agent_name = result.metadata.get("agent_name", "")
        claim_id = result.metadata.get("claim_id", "")
        return f"[{agent_name.title()} Agent Finding | Claim: {claim_id}]\n{result.chunk_text}"
    
    elif result.source_type == "verdict":
        claim_id = result.metadata.get("claim_id", "")
        verdict = result.metadata.get("verdict", "")
        return f"[Judge Verdict: {verdict} | Claim: {claim_id}]\n{result.chunk_text}"
    
    elif result.source_type == "gap":
        paragraph_id = result.metadata.get("paragraph_id", "")
        gap_status = result.metadata.get("gap_status", "")
        return f"[Disclosure Gap: {paragraph_id} | Status: {gap_status}]\n{result.chunk_text}"
    
    return result.chunk_text
```

### 3.5 Context Length Management

The system manages context length to stay within Gemini 3 Flash's 1M token context window:

1. **Prioritize high-scoring results:** Sort by `score` and take top results first.
2. **Truncate long chunks:** If a chunk exceeds 500 tokens, truncate to first 500 tokens with `[...]` indicator.
3. **Limit total context:** Cap total context at 50,000 tokens (leaving room for system prompt, user message, conversation history, and response).
4. **Source type balancing:** Ensure at least one result from each relevant source type (if available).

---

## 4. LLM Integration

### 4.1 Overview

The chatbot uses Gemini 3 Flash via OpenRouter for response generation. Gemini 3 Flash is selected for its 1M token context window (handling large context), fast response times (conversational Q&A), and cost-effectiveness (PRD Section 4.12).

### 4.2 Model Configuration

| Parameter | Value | Rationale |
|---|---|---|
| Model | `google/gemini-3-flash` (`Models.GEMINI_FLASH`) | Fast conversational Q&A with good context handling (PRD Section 4.12) |
| Temperature | `0.3` | Balanced between creativity and accuracy for factual Q&A |
| Max output tokens | `4096` | Sufficient for detailed answers with citations |
| Response format | Streaming (SSE) | Real-time progressive text appearance |

### 4.3 Prompt Construction

The system constructs a prompt with:

1. **System prompt:** Instructions for the chatbot (see Appendix A).
2. **Context section:** Assembled RAG context with citation markers.
3. **Conversation history:** Previous messages (user + assistant) for multi-turn context.
4. **User message:** Current question.

```python
def build_chat_prompt(
    self,
    user_message: str,
    context_text: str,
    conversation_history: list[dict],
    citation_map: dict[int, CitationMetadata]
) -> list[dict]:
    """Build the full prompt for Gemini 3 Flash."""
    
    system_prompt = self._get_system_prompt(citation_map)
    
    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]
    
    # Add conversation history (last 5 turns to manage token usage)
    for msg in conversation_history[-10:]:  # Last 10 messages (5 turns)
        messages.append({
            "role": msg["role"],  # "user" or "assistant"
            "content": msg["content"]
        })
    
    # Add context and current user message
    user_content = f"""## Context Sources

{context_text}

## User Question

{user_message}

Please provide a comprehensive answer based on the context sources above. Use inline citations [1], [2], etc. to reference specific sources."""
    
    messages.append({
        "role": "user",
        "content": user_content
    })
    
    return messages
```

### 4.4 Streaming Response Generation

The system streams responses via SSE:

```python
async def generate_response_stream(
    self,
    messages: list[dict]
) -> AsyncIterator[dict]:
    """Stream response from Gemini 3 Flash."""
    
    async for chunk in self.openrouter_client.stream_chat_completion(
        model=Models.GEMINI_FLASH,
        messages=messages,
        temperature=0.3,
        max_tokens=4096
    ):
        if chunk.get("choices") and chunk["choices"][0].get("delta"):
            delta = chunk["choices"][0]["delta"]
            content = delta.get("content", "")
            
            if content:
                yield {
                    "type": "token",
                    "data": content
                }
        
        if chunk.get("done"):
            yield {
                "type": "done",
                "data": {}
            }
```

### 4.5 Citation Extraction

After the response is generated, the system extracts citation markers:

```python
import re

def extract_citations(response_text: str) -> list[int]:
    """Extract citation numbers from response text.
    
    Returns list of citation numbers referenced in the response.
    """
    # Match [1], [2], [12], etc.
    pattern = r'\[(\d+)\]'
    matches = re.findall(pattern, response_text)
    
    # Convert to integers and deduplicate
    citations = sorted(set(int(m) for m in matches))
    return citations
```

---

## 5. Inline Citation System

### 5.1 Overview

Inline citations are reference markers (e.g., `[1]`, `[2]`) within chatbot response text that link to source entities. Citations are generated during response generation, extracted from the LLM output, and mapped to source entities for navigation.

### 5.2 Citation Format

Citations appear inline in the response text:

```
The report discloses Scope 3 emissions totaling 12.4 million tonnes CO2e [1]. 
However, the Legal Agent found that the disclosure does not meet the IFRS S2.29(a)(iii) 
requirement for category-level breakdown [2]. The Judge Agent verified this finding [3], 
and the report is flagged as having a disclosure gap [4].
```

### 5.3 Citation Metadata Schema

```python
class CitationMetadata(BaseModel):
    """Metadata for a citation linking to a source entity."""
    citation_number: int  # [1], [2], etc.
    source_type: str  # "claim" | "finding" | "ifrs_paragraph" | "verdict" | "gap"
    chunk_id: str  # UUID of the source entity
    metadata: dict  # Source-specific metadata (claim_id, paragraph_id, etc.)
    report_id: str  # Report UUID
    navigation_target: dict  # Navigation target for frontend (see Section 6)
```

### 5.4 Citation-to-Entity Mapping

The system maps citations to source entities:

```python
def map_citations_to_entities(
    self,
    citations: list[int],
    citation_map: dict[int, CitationMetadata],
    db: AsyncSession
) -> list[CitationEntity]:
    """Map citation numbers to full entity data for frontend navigation."""
    
    citation_entities = []
    
    for citation_num in citations:
        if citation_num not in citation_map:
            continue
        
        metadata = citation_map[citation_num]
        
        # Load full entity data based on source_type
        if metadata.source_type == "claim":
            claim = await db.get(Claim, metadata.metadata.get("claim_id"))
            citation_entities.append(CitationEntity(
                citation_number=citation_num,
                source_type="claim",
                entity_id=claim.claim_id,
                entity_data={
                    "claim_text": claim.claim_text,
                    "source_page": claim.source_page,
                    "claim_type": claim.claim_type,
                },
                navigation_target={
                    "type": "pdf_viewer",
                    "report_id": metadata.report_id,
                    "claim_id": claim.claim_id,
                    "page": claim.source_page,
                }
            ))
        
        elif metadata.source_type == "finding":
            finding = await db.get(Finding, metadata.chunk_id)
            citation_entities.append(CitationEntity(
                citation_number=citation_num,
                source_type="finding",
                entity_id=finding.finding_id,
                entity_data={
                    "agent_name": finding.agent_name,
                    "summary": finding.summary,
                    "claim_id": finding.claim_id,
                },
                navigation_target={
                    "type": "agent_finding",
                    "finding_id": finding.finding_id,
                    "agent_name": finding.agent_name,
                }
            ))
        
        # ... similar for ifrs_paragraph, verdict, gap
    
    return citation_entities
```

### 5.5 Citation Rendering in Frontend

Citations are rendered as clickable links in the chat message component (see Section 9).

---

## 6. Citation Types and Navigation Targets

### 6.1 Citation Type: Claim

**Source:** Original claim extracted from the report.

**Navigation Target:**
```typescript
{
  type: "pdf_viewer",
  report_id: string,
  claim_id: string,
  page: number
}
```

**Frontend Action:** Navigate to PDF viewer, highlight the claim on the specified page.

### 6.2 Citation Type: Finding

**Source:** Agent finding from investigation.

**Navigation Target:**
```typescript
{
  type: "agent_finding",
  finding_id: string,
  agent_name: string
}
```

**Frontend Action:** Navigate to Source of Truth report, expand the finding panel for the specified agent.

### 6.3 Citation Type: IFRS Paragraph

**Source:** IFRS S1/S2 standard paragraph.

**Navigation Target:**
```typescript
{
  type: "ifrs_paragraph",
  paragraph_id: string,
  standard: "S1" | "S2"
}
```

**Frontend Action:** Show IFRS paragraph viewer modal with the paragraph requirement text.

### 6.4 Citation Type: Verdict

**Source:** Judge Agent verdict for a claim.

**Navigation Target:**
```typescript
{
  type: "verdict",
  claim_id: string,
  verdict_id: string
}
```

**Frontend Action:** Navigate to Source of Truth report, expand the claim card showing the verdict.

### 6.5 Citation Type: Gap

**Source:** Disclosure gap from Legal Agent.

**Navigation Target:**
```typescript
{
  type: "disclosure_gap",
  paragraph_id: string,
  gap_id: string
}
```

**Frontend Action:** Navigate to Source of Truth report, scroll to Disclosure Gaps section, highlight the gap.

---

## 7. Conversation Persistence

### 7.1 Overview

Conversation persistence stores chat messages, citations, and timestamps in PostgreSQL, enabling conversation history to be retrieved when the chat panel is reopened or when navigating between pages.

### 7.2 Data Model

```python
# app/models/chat.py

class Conversation(Base):
    """A conversation thread for a report."""
    __tablename__ = "conversations"
    
    conversation_id = Column(UUID, primary_key=True, default=uuid7)
    report_id = Column(UUID, ForeignKey("reports.report_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatMessage(Base):
    """A single message in a conversation."""
    __tablename__ = "chat_messages"
    
    message_id = Column(UUID, primary_key=True, default=uuid7)
    conversation_id = Column(UUID, ForeignKey("conversations.conversation_id"), nullable=False)
    role = Column(String, nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Citations in this message (JSON array)
    citations = Column(JSONB, default=list)

class Citation(Base):
    """A citation linking a message to a source entity."""
    __tablename__ = "chat_citations"
    
    citation_id = Column(UUID, primary_key=True, default=uuid7)
    message_id = Column(UUID, ForeignKey("chat_messages.message_id"), nullable=False)
    citation_number = Column(Integer, nullable=False)  # [1], [2], etc.
    source_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)  # UUID of source entity
    navigation_target = Column(JSONB, nullable=False)
```

### 7.3 Conversation Retrieval

```python
async def get_conversation_history(
    self,
    report_id: str,
    limit: int = 50
) -> list[dict]:
    """Retrieve conversation history for a report."""
    
    # Get or create conversation
    stmt = select(Conversation).where(
        Conversation.report_id == report_id
    ).order_by(Conversation.created_at.desc()).limit(1)
    
    result = await self.db.execute(stmt)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        return []
    
    # Get messages
    stmt = select(ChatMessage).where(
        ChatMessage.conversation_id == conversation.conversation_id
    ).order_by(ChatMessage.created_at.asc()).limit(limit)
    
    messages_result = await self.db.execute(stmt)
    messages = messages_result.scalars().all()
    
    # Format for frontend
    history = []
    for msg in messages:
        # Load citations
        citations_stmt = select(Citation).where(
            Citation.message_id == msg.message_id
        )
        citations_result = await self.db.execute(citations_stmt)
        citations = citations_result.scalars().all()
        
        history.append({
            "message_id": str(msg.message_id),
            "role": msg.role,
            "content": msg.content,
            "citations": [
                {
                    "citation_number": c.citation_number,
                    "source_type": c.source_type,
                    "entity_id": c.entity_id,
                    "navigation_target": c.navigation_target,
                }
                for c in citations
            ],
            "created_at": msg.created_at.isoformat(),
        })
    
    return history
```

### 7.4 Message Persistence

```python
async def save_message(
    self,
    report_id: str,
    role: str,
    content: str,
    citations: list[CitationEntity]
) -> str:
    """Save a message and its citations to the database."""
    
    # Get or create conversation
    stmt = select(Conversation).where(
        Conversation.report_id == report_id
    ).order_by(Conversation.created_at.desc()).limit(1)
    
    result = await self.db.execute(stmt)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        conversation = Conversation(
            conversation_id=uuid7(),
            report_id=report_id
        )
        self.db.add(conversation)
        await self.db.flush()
    
    # Create message
    message = ChatMessage(
        message_id=uuid7(),
        conversation_id=conversation.conversation_id,
        role=role,
        content=content,
        citations=[c.citation_number for c in citations]
    )
    self.db.add(message)
    await self.db.flush()
    
    # Create citations
    for citation_entity in citations:
        citation = Citation(
            citation_id=uuid7(),
            message_id=message.message_id,
            citation_number=citation_entity.citation_number,
            source_type=citation_entity.source_type,
            entity_id=citation_entity.entity_id,
            navigation_target=citation_entity.navigation_target
        )
        self.db.add(citation)
    
    await self.db.commit()
    return str(message.message_id)
```

---

## 8. Chat Panel UI

### 8.1 Overview

The chat panel (`src/components/Chatbot/ChatPanel.tsx`) is a slide-out panel anchored to the right edge of the screen, accessible from any page via a floating button. The panel contains the message list, input area, and handles conversation state.

### 8.2 Component Structure

```typescript
// src/components/Chatbot/ChatPanel.tsx

interface ChatPanelProps {
  reportId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ChatPanel({ reportId, isOpen, onClose }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { sendMessage, streamResponse } = useChat(reportId);

  // Load conversation history on mount
  useEffect(() => {
    if (isOpen && reportId) {
      loadConversationHistory(reportId);
    }
  }, [isOpen, reportId]);

  return (
    <>
      {/* Floating button */}
      <FloatingChatButton onClick={() => setIsOpen(true)} />

      {/* Slide-out panel */}
      <SlideOutPanel isOpen={isOpen} onClose={onClose} side="right">
        <div className="flex flex-col h-full">
          {/* Header */}
          <ChatPanelHeader onClose={onClose} />

          {/* Message list */}
          <ChatMessageList messages={messages} />

          {/* Input area */}
          <ChatInput
            onSend={handleSendMessage}
            isLoading={isLoading}
          />
        </div>
      </SlideOutPanel>
    </>
  );
}
```

### 8.3 Floating Button

```typescript
// src/components/Chatbot/FloatingChatButton.tsx

export function FloatingChatButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 z-50 bg-primary text-primary-foreground rounded-full p-4 shadow-lg hover:shadow-xl transition-shadow"
      aria-label="Open chat"
    >
      <MessageCircle className="w-6 h-6" />
    </button>
  );
}
```

### 8.4 Slide-Out Panel Animation

The panel slides in from the right using CSS transitions:

```css
/* TailwindCSS classes */
.slide-out-panel {
  @apply fixed top-0 right-0 h-full w-96 bg-background border-l shadow-xl;
  transform: translateX(100%);
  transition: transform 0.3s ease-in-out;
}

.slide-out-panel.open {
  transform: translateX(0);
}
```

### 8.5 Panel Positioning

- **Position:** Fixed, right edge of viewport
- **Width:** 384px (24rem / `w-96`)
- **Height:** Full viewport height
- **Z-index:** 40 (above page content, below modals)
- **Overlay:** Semi-transparent backdrop when open (optional)

---

## 9. Chat Message Component

### 9.1 Overview

The chat message component (`src/components/Chatbot/ChatMessage.tsx`) renders individual message bubbles with citation rendering and markdown support.

### 9.2 Component Structure

```typescript
// src/components/Chatbot/ChatMessage.tsx

interface ChatMessageProps {
  message: ChatMessage;
  onCitationClick: (citation: Citation) => void;
}

export function ChatMessage({ message, onCitationClick }: ChatMessageProps) {
  const isUser = message.role === "user";
  
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div className={`max-w-[80%] rounded-lg p-3 ${
        isUser 
          ? "bg-primary text-primary-foreground" 
          : "bg-muted text-foreground"
      }`}>
        {/* Message content with markdown and citations */}
        <MessageContent
          content={message.content}
          citations={message.citations}
          onCitationClick={onCitationClick}
        />
        
        {/* Timestamp */}
        <div className="text-xs opacity-70 mt-2">
          {formatTimestamp(message.created_at)}
        </div>
      </div>
    </div>
  );
}
```

### 9.3 Citation Rendering

Citations are rendered as clickable links:

```typescript
// src/components/Chatbot/MessageContent.tsx

function MessageContent({
  content,
  citations,
  onCitationClick
}: {
  content: string;
  citations: Citation[];
  onCitationClick: (citation: Citation) => void;
}) {
  // Parse content and replace [1], [2] with clickable citations
  const parts = parseContentWithCitations(content, citations);
  
  return (
    <div className="prose prose-sm max-w-none">
      {parts.map((part, idx) => {
        if (part.type === "citation") {
          const citation = citations.find(c => c.citation_number === part.number);
          return (
            <button
              key={idx}
              onClick={() => citation && onCitationClick(citation)}
              className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-primary/20 text-primary hover:bg-primary/30 transition-colors text-xs font-medium"
            >
              {part.number}
            </button>
          );
        }
        return <span key={idx}>{part.text}</span>;
      })}
    </div>
  );
}

function parseContentWithCitations(
  content: string,
  citations: Citation[]
): Array<{ type: "text" | "citation"; text?: string; number?: number }> {
  const parts: Array<{ type: "text" | "citation"; text?: string; number?: number }> = [];
  const pattern = /\[(\d+)\]/g;
  let lastIndex = 0;
  let match;
  
  while ((match = pattern.exec(content)) !== null) {
    // Add text before citation
    if (match.index > lastIndex) {
      parts.push({
        type: "text",
        text: content.slice(lastIndex, match.index)
      });
    }
    
    // Add citation
    const citationNumber = parseInt(match[1], 10);
    parts.push({
      type: "citation",
      number: citationNumber
    });
    
    lastIndex = match.index + match[0].length;
  }
  
  // Add remaining text
  if (lastIndex < content.length) {
    parts.push({
      type: "text",
      text: content.slice(lastIndex)
    });
  }
  
  return parts;
}
```

### 9.4 Markdown Support

Message content supports markdown for formatting:

```typescript
import ReactMarkdown from "react-markdown";

function MessageContent({ content, citations, onCitationClick }: Props) {
  // Replace citation markers with React components before markdown rendering
  const processedContent = replaceCitationsWithComponents(content, citations);
  
  return (
    <ReactMarkdown
      components={{
        // Custom components for citations, links, etc.
      }}
    >
      {processedContent}
    </ReactMarkdown>
  );
}
```

### 9.5 Citation Click Handler

```typescript
function handleCitationClick(citation: Citation) {
  const { navigation_target } = citation;
  
  switch (navigation_target.type) {
    case "pdf_viewer":
      navigate(`/analysis/${navigation_target.report_id}`, {
        state: { highlightClaim: navigation_target.claim_id, page: navigation_target.page }
      });
      break;
    
    case "agent_finding":
      navigate(`/report/${navigation_target.report_id}`, {
        state: { expandFinding: navigation_target.finding_id }
      });
      break;
    
    case "ifrs_paragraph":
      openIFRSParagraphModal(navigation_target.paragraph_id, navigation_target.standard);
      break;
    
    case "verdict":
      navigate(`/report/${navigation_target.report_id}`, {
        state: { expandClaim: navigation_target.claim_id }
      });
      break;
    
    case "disclosure_gap":
      navigate(`/report/${navigation_target.report_id}`, {
        state: { scrollToGap: navigation_target.gap_id }
      });
      break;
  }
}
```

---

## 10. Chat Input Component

### 10.1 Overview

The chat input component (`src/components/Chatbot/ChatInput.tsx`) provides a text field and send button for user input, with loading state during response generation.

### 10.2 Component Structure

```typescript
// src/components/Chatbot/ChatInput.tsx

interface ChatInputProps {
  onSend: (message: string) => Promise<void>;
  isLoading: boolean;
}

export function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    
    const message = input.trim();
    setInput("");
    await onSend(message);
  };
  
  return (
    <form onSubmit={handleSubmit} className="border-t p-4">
      <div className="flex gap-2">
        <Textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about the analysis..."
          disabled={isLoading}
          className="resize-none"
          rows={1}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <Button
          type="submit"
          disabled={!input.trim() || isLoading}
          size="icon"
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </div>
    </form>
  );
}
```

### 10.3 Auto-Resize Textarea

The textarea auto-resizes based on content:

```typescript
useEffect(() => {
  if (textareaRef.current) {
    textareaRef.current.style.height = "auto";
    textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
  }
}, [input]);
```

### 10.4 Loading State

During response generation:
- Input field is disabled
- Send button shows spinner
- Placeholder text indicates "Generating response..."

---

## 11. Streaming Response Display

### 11.1 Overview

Response streaming delivers chatbot responses progressively via SSE, with text appearing word-by-word in real-time (similar to ChatGPT).

### 11.2 SSE Connection

```typescript
// src/hooks/useChat.ts

export function useChat(reportId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  
  const streamResponse = async (userMessage: string) => {
    setIsStreaming(true);
    
    // Add user message immediately
    const userMsg: ChatMessage = {
      message_id: uuid(),
      role: "user",
      content: userMessage,
      citations: [],
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    
    // Create assistant message placeholder
    const assistantMsg: ChatMessage = {
      message_id: uuid(),
      role: "assistant",
      content: "",
      citations: [],
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, assistantMsg]);
    
    // Connect to SSE endpoint
    const eventSource = new EventSource(
      `${API_BASE_URL}/chat/${reportId}/message?message=${encodeURIComponent(userMessage)}&stream=true`
    );
    
    let accumulatedContent = "";
    const citations: Citation[] = [];
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === "token") {
        accumulatedContent += data.data;
        // Update assistant message content
        setMessages(prev => prev.map(msg =>
          msg.message_id === assistantMsg.message_id
            ? { ...msg, content: accumulatedContent }
            : msg
        ));
      } else if (data.type === "citation") {
        citations.push(data.data);
        // Update citations
        setMessages(prev => prev.map(msg =>
          msg.message_id === assistantMsg.message_id
            ? { ...msg, citations: [...citations] }
            : msg
        ));
      } else if (data.type === "done") {
        eventSource.close();
        setIsStreaming(false);
      }
    };
    
    eventSource.onerror = () => {
      eventSource.close();
      setIsStreaming(false);
    };
  };
  
  return { messages, streamResponse, isStreaming };
}
```

### 11.3 Progressive Text Rendering

The message content updates in real-time as tokens arrive:

```typescript
// ChatMessage component re-renders as content updates
function ChatMessage({ message }: ChatMessageProps) {
  // Content updates progressively as tokens stream in
  return <MessageContent content={message.content} citations={message.citations} />;
}
```

### 11.4 Citation Streaming

Citations are streamed as they are extracted:

```typescript
// Backend streams citations as they are identified
yield {
    "type": "citation",
    "data": {
        "citation_number": 1,
        "source_type": "claim",
        "entity_id": "claim-123",
        "navigation_target": {...}
    }
}
```

---

## 12. Cross-Page Persistence

### 12.1 Overview

Conversation history persists across page navigation. When the user navigates between Home, Analysis, and Report pages, the chat panel remains accessible and conversation history is maintained.

### 12.2 Global Chat State

```typescript
// src/contexts/ChatContext.tsx

interface ChatContextValue {
  conversations: Record<string, ChatMessage[]>;  // report_id -> messages
  openChat: (reportId: string) => void;
  closeChat: () => void;
  currentReportId: string | null;
}

export const ChatContext = createContext<ChatContextValue | null>(null);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [conversations, setConversations] = useState<Record<string, ChatMessage[]>>({});
  const [currentReportId, setCurrentReportId] = useState<string | null>(null);
  
  // Load conversation history when report changes
  useEffect(() => {
    if (currentReportId) {
      loadConversationHistory(currentReportId).then(history => {
        setConversations(prev => ({
          ...prev,
          [currentReportId]: history
        }));
      });
    }
  }, [currentReportId]);
  
  return (
    <ChatContext.Provider value={{
      conversations,
      openChat: setCurrentReportId,
      closeChat: () => setCurrentReportId(null),
      currentReportId
    }}>
      {children}
    </ChatContext.Provider>
  );
}
```

### 12.3 Chat Panel in Layout

The chat panel is rendered at the layout level (not page level):

```typescript
// src/components/Layout/AppShell.tsx

export function AppShell({ children }: { children: React.ReactNode }) {
  const { currentReportId, openChat, closeChat } = useChatContext();
  
  return (
    <div className="min-h-screen">
      {children}
      
      {/* Chat panel available on all pages */}
      {currentReportId && (
        <ChatPanel
          reportId={currentReportId}
          isOpen={!!currentReportId}
          onClose={closeChat}
        />
      )}
    </div>
  );
}
```

### 12.4 Conversation Restoration

When the chat panel is reopened, conversation history is restored from the database:

```typescript
async function loadConversationHistory(reportId: string) {
  const response = await fetch(`${API_BASE_URL}/chat/${reportId}/history`);
  const history = await response.json();
  return history.messages;
}
```

---

## 13. Backend Chat Endpoint

### 13.1 POST /api/v1/chat/{reportId}/message

**Purpose:** Send a user message and receive a chatbot response (streaming or complete).

**Request:**
```
POST /api/v1/chat/{reportId}/message

Query Parameters:
  - stream: boolean (default: true) -- Whether to stream response via SSE

Request Body:
{
  "message": "What evidence supports the company's Scope 3 emission reduction claim?"
}
```

**Response (SSE stream):**
```
event: token
data: {"type": "token", "data": "The"}

event: token
data: {"type": "token", "data": " report"}

event: citation
data: {"type": "citation", "data": {"citation_number": 1, "source_type": "claim", ...}}

event: token
data: {"type": "token", "data": " discloses"}

...

event: done
data: {"type": "done", "data": {}}
```

**Response (non-streaming):**
```json
{
  "message_id": "uuid-...",
  "content": "The report discloses Scope 3 emissions...",
  "citations": [
    {
      "citation_number": 1,
      "source_type": "claim",
      "entity_id": "claim-123",
      "navigation_target": {...}
    }
  ],
  "created_at": "2026-02-09T15:30:00Z"
}
```

### 13.2 GET /api/v1/chat/{reportId}/history

**Purpose:** Retrieve conversation history for a report.

**Request:**
```
GET /api/v1/chat/{reportId}/history

Query Parameters:
  - limit: int (default: 50) -- Maximum number of messages to return
```

**Response:**
```json
{
  "conversation_id": "uuid-...",
  "messages": [
    {
      "message_id": "uuid-...",
      "role": "user",
      "content": "What did the Geography Agent find?",
      "citations": [],
      "created_at": "2026-02-09T15:25:00Z"
    },
    {
      "message_id": "uuid-...",
      "role": "assistant",
      "content": "The Geography Agent found...",
      "citations": [
        {
          "citation_number": 1,
          "source_type": "finding",
          "entity_id": "finding-456",
          "navigation_target": {...}
        }
      ],
      "created_at": "2026-02-09T15:25:05Z"
    }
  ],
  "total_messages": 2
}
```

### 13.3 Endpoint Implementation

```python
# app/api/routes/chat.py

router = APIRouter(prefix="/chat", tags=["Chatbot"])

@router.post("/{report_id}/message")
async def send_message(
    report_id: str,
    request: ChatMessageRequest,
    stream: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
    openrouter_client: OpenRouterClient = Depends(get_openrouter_client)
):
    """Send a message and receive a chatbot response."""
    
    # Verify report exists
    report = await get_report_or_404(report_id, db)
    
    # Load conversation history
    chat_service = ChatService(db, rag_service, openrouter_client)
    history = await chat_service.get_conversation_history(report_id)
    
    if stream:
        # Stream response via SSE
        return StreamingResponse(
            chat_service.generate_response_stream(
                report_id, request.message, history
            ),
            media_type="text/event-stream"
        )
    else:
        # Return complete response
        response = await chat_service.generate_response(
            report_id, request.message, history, stream=False
        )
        return response

@router.get("/{report_id}/history")
async def get_history(
    report_id: str,
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
    openrouter_client: OpenRouterClient = Depends(get_openrouter_client)
):
    """Get conversation history for a report."""
    
    chat_service = ChatService(db, rag_service, openrouter_client)
    history = await chat_service.get_conversation_history(report_id, limit)
    
    return {
        "messages": history,
        "total_messages": len(history)
    }
```

---

## 14. Chat Data Model

### 14.1 Database Schema

```python
# app/models/chat.py

class Conversation(Base):
    """A conversation thread for a report."""
    __tablename__ = "conversations"
    
    conversation_id = Column(UUID, primary_key=True, default=uuid7)
    report_id = Column(UUID, ForeignKey("reports.report_id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")

class ChatMessage(Base):
    """A single message in a conversation."""
    __tablename__ = "chat_messages"
    
    message_id = Column(UUID, primary_key=True, default=uuid7)
    conversation_id = Column(UUID, ForeignKey("conversations.conversation_id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    citations = Column(JSONB, default=list)  # Array of citation numbers [1, 2, 3]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    citation_entities = relationship("Citation", back_populates="message", cascade="all, delete-orphan")

class Citation(Base):
    """A citation linking a message to a source entity."""
    __tablename__ = "chat_citations"
    
    citation_id = Column(UUID, primary_key=True, default=uuid7)
    message_id = Column(UUID, ForeignKey("chat_messages.message_id"), nullable=False, index=True)
    citation_number = Column(Integer, nullable=False)  # [1], [2], etc.
    source_type = Column(String, nullable=False)  # "claim" | "finding" | "ifrs_paragraph" | "verdict" | "gap"
    entity_id = Column(String, nullable=False)  # UUID of source entity
    navigation_target = Column(JSONB, nullable=False)  # Frontend navigation target
    
    # Relationships
    message = relationship("ChatMessage", back_populates="citation_entities")
```

### 14.2 Alembic Migration

```python
# alembic/versions/xxxx_add_chat_tables.py

def upgrade():
    op.create_table(
        "conversations",
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("report_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["reports.report_id"]),
        sa.PrimaryKeyConstraint("conversation_id")
    )
    op.create_index("ix_conversations_report_id", "conversations", ["report_id"])
    
    op.create_table(
        "chat_messages",
        sa.Column("message_id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.conversation_id"]),
        sa.PrimaryKeyConstraint("message_id")
    )
    op.create_index("ix_chat_messages_conversation_id", "chat_messages", ["conversation_id"])
    op.create_index("ix_chat_messages_created_at", "chat_messages", ["created_at"])
    
    op.create_table(
        "chat_citations",
        sa.Column("citation_id", sa.UUID(), nullable=False),
        sa.Column("message_id", sa.UUID(), nullable=False),
        sa.Column("citation_number", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("navigation_target", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["chat_messages.message_id"]),
        sa.PrimaryKeyConstraint("citation_id")
    )
    op.create_index("ix_chat_citations_message_id", "chat_citations", ["message_id"])
```

---

## 15. Error Handling

### 15.1 RAG Retrieval Errors

| Error | Trigger | Handling |
|---|---|---|
| RAG service unavailable | Database connection failure | Return error message: "Unable to retrieve context. Please try again." |
| No results found | Query returns zero results | Generate response explaining that no relevant information was found, suggest rephrasing the question |
| Embedding API failure | OpenRouter embedding endpoint error | Retry up to 3 times; on failure, use keyword-only search as fallback |

### 15.2 LLM Generation Errors

| Error | Trigger | Handling |
|---|---|---|
| LLM timeout | Gemini 3 Flash exceeds 30 seconds | Return partial response if any tokens were generated; otherwise return error message |
| LLM rate limit | OpenRouter returns 429 | Exponential backoff retry (handled by OpenRouter client); propagate error after 3 retries |
| LLM returns non-text | Malformed response | Log error; return fallback message: "I encountered an error generating a response. Please try again." |

### 15.3 Database Errors

| Error | Trigger | Handling |
|---|---|---|
| Conversation save failure | Database constraint violation | Log error; continue without saving (response still delivered to user) |
| History retrieval failure | Database query error | Return empty history; user can start a new conversation |

### 15.4 Frontend Errors

| Error | Trigger | Handling |
|---|---|---|
| SSE connection failure | Network error or server disconnect | Show error message; allow user to retry |
| Citation navigation failure | Invalid navigation target | Log error; show toast notification: "Unable to navigate to citation source" |

### 15.5 Graceful Degradation

If RAG retrieval fails:
1. Attempt keyword-only search as fallback.
2. If that fails, generate a response explaining the limitation.
3. Never crash or return empty responses without explanation.

---

## 16. Exit Criteria

FRD 14 is complete when ALL of the following are satisfied:

| # | Criterion | Verification |
|---|---|---|
| 1 | Chat endpoint accepts messages | `POST /api/v1/chat/{reportId}/message` responds with 200 or SSE stream |
| 2 | Multi-source RAG retrieval works | Chatbot retrieves from report, findings, IFRS, verdicts, and gaps |
| 3 | Context assembly includes citations | Assembled context contains citation markers [1], [2], etc. |
| 4 | Gemini 3 Flash generates responses | LLM calls succeed and produce coherent answers |
| 5 | Inline citations are extracted | Response text contains citation markers that are parsed and mapped to entities |
| 6 | Citations link to correct sources | Citation metadata maps to correct claim/finding/IFRS paragraph/verdict/gap |
| 7 | Conversation history is stored | Messages and citations are persisted to the database |
| 8 | Conversation history is retrievable | `GET /api/v1/chat/{reportId}/history` returns stored messages |
| 9 | Chat panel UI renders | `ChatPanel.tsx` displays messages and input field |
| 10 | Floating button is visible | Floating chat button appears on all pages |
| 11 | Chat panel slides out | Panel animates in from the right when button is clicked |
| 12 | Message bubbles render correctly | User messages right-aligned, assistant messages left-aligned |
| 13 | Citations are clickable | Citation buttons are rendered and clickable in message content |
| 14 | Citation navigation works | Clicking a citation navigates to the correct source (PDF viewer, finding panel, etc.) |
| 15 | Response streaming works | Response text appears progressively via SSE |
| 16 | Conversation persists across navigation | Navigating between pages maintains chat history |
| 17 | Multi-turn conversation works | Follow-up questions maintain context from previous messages |
| 18 | Error handling is graceful | RAG failures, LLM errors, and database errors are handled without crashing |
| 19 | Example queries from PRD work | Test queries from PRD Section 4.12 produce relevant, cited responses |
| 20 | Performance is acceptable | Response generation completes within 5 seconds for typical queries |

---

## Appendix A: Chatbot System Prompt

### A.1 System Prompt Template

```
You are the Sibyl Chatbot, an AI assistant that helps users understand sustainability report analysis results. Your role is to answer questions about the analyzed report, agent findings, IFRS compliance, and disclosure gaps.

## Your Capabilities

1. **Answer questions about the analysis:** Explain what agents found, what claims were verified, and what compliance gaps exist.

2. **Reference specific sources:** Use inline citations [1], [2], etc. to reference the context sources provided. Always cite your sources when making factual claims.

3. **Understand the analysis structure:** You can reference:
   - Specific agents (Claims Agent, Geography Agent, Legal Agent, etc.)
   - Specific claims (by claim ID or description)
   - IFRS paragraphs (e.g., S2.14(a)(iv))
   - Agent findings and evidence
   - Judge verdicts (Verified, Unverified, Contradicted, Insufficient Evidence)
   - Disclosure gaps

4. **Provide contextual answers:** Ground your answers in the actual analysis results, not generic information. If information is not available in the context, say so clearly.

## Response Guidelines

- Be concise but comprehensive
- Use inline citations [1], [2], etc. for all factual claims
- Explain technical terms (IFRS paragraphs, agent names) when helpful
- If asked about something not in the context, explain that the information is not available
- For multi-part questions, address each part systematically
- Maintain a helpful, professional tone

## Citation Format

When referencing sources, use inline citations:
- "The report discloses Scope 3 emissions [1]."
- "The Legal Agent found that this claim does not meet S2.14(a)(iv) requirements [2]."
- "The Judge Agent verified this claim [3]."

The context sources are numbered [1], [2], [3], etc. Use these numbers to cite specific sources.
```

### A.2 Context Section Format

The context section in the prompt includes:

```
## Context Sources

### Report Content
[1] [Report > Environmental Performance > GHG Emissions > Scope 3]
Our Scope 3 emissions totaled 12.4 million tonnes CO2e in FY2024...

### IFRS Standards
[2] [IFRS S2 > Strategy > Decision-Making > S2.14(a)(iv)]
An entity shall disclose its transition plan, including information about...

### Agent Findings
[3] [Legal Agent Finding | Claim: claim-123]
Claim about transition plan maps to S2.14(a)(iv). Compliance status: partially_addressed...

### Judge Verdicts
[4] [Judge Verdict: Verified | Claim: claim-123]
Verdict: Verified. Multiple sources corroborate the transition plan claim...

### Disclosure Gaps
[5] [Disclosure Gap: S2.29(a)(iii) | Status: fully_unaddressed]
IFRS S2.29(a)(iii) requirement (Scope 3 emissions by category) is fully_unaddressed...
```

---

## Appendix B: RAG Query Construction Examples

### B.1 Query: "What did the Geography Agent find about the Borneo facility?"

**RAG Queries:**
```python
# Finding retrieval
query = "Geography Agent Borneo facility"
source_types = ["finding"]  # Filter to findings
# Database query: Finding.agent_name == "geography" AND Finding.summary.contains("Borneo")

# Report content retrieval
query = "Borneo facility"
source_types = ["report"]
report_id = current_report_id
```

### B.2 Query: "Does the report meet S2.14(a)(iv) transition plan requirements?"

**RAG Queries:**
```python
# IFRS paragraph lookup
paragraph_id = "S2.14(a)(iv)"
# Direct paragraph retrieval via RAGService.get_paragraph()

# Related claims
query = "transition plan S2.14"
source_types = ["report"]
# Find claims mentioning transition plans

# Legal Agent findings
query = "S2.14(a)(iv) transition plan compliance"
source_types = ["finding"]
# Filter: Finding.agent_name == "legal" AND Finding.details.contains("S2.14")

# Verdicts
query = "transition plan verdict"
# Database query: Verdict.reasoning.contains("transition plan")
```

### B.3 Query: "What are the main compliance gaps in the Governance pillar?"

**RAG Queries:**
```python
# Disclosure gaps
query = "Governance pillar disclosure gap"
# Database query: Finding.evidence_type == "disclosure_gap" AND Finding.details.pillar == "governance"

# IFRS Governance paragraphs
query = "IFRS S1 S2 Governance requirements"
source_types = ["ifrs_s1", "ifrs_s2"]
# Filter: chunk_metadata.pillar == "governance"
```

---

## Appendix C: Citation Format Specification

### C.1 Citation Marker Format

Citations appear as `[N]` where N is a positive integer:
- `[1]`, `[2]`, `[3]`, etc.
- Sequential numbering within a single response
- Citations can appear multiple times in the response (e.g., `[1]` referenced twice)

### C.2 Citation Extraction Regex

```python
CITATION_PATTERN = re.compile(r'\[(\d+)\]')
```

### C.3 Citation Metadata JSON

```json
{
  "citation_number": 1,
  "source_type": "claim",
  "entity_id": "claim-123",
  "metadata": {
    "claim_text": "Our Scope 3 emissions totaled 12.4 million tonnes CO2e...",
    "source_page": 45,
    "claim_type": "quantitative"
  },
  "report_id": "report-uuid",
  "navigation_target": {
    "type": "pdf_viewer",
    "report_id": "report-uuid",
    "claim_id": "claim-123",
    "page": 45
  }
}
```

---

## Appendix D: Example Conversations

### D.1 Example 1: Agent Finding Query

**User:** "What did the Geography Agent find about the Borneo facility?"

**Chatbot:** "The Geography Agent investigated claims related to the Borneo facility and found satellite imagery evidence supporting the reforestation claim [1]. NDVI analysis showed a significant increase in vegetation density from 2020 to 2024, with approximately 4,200 hectares showing reforestation [1]. The analysis used Sentinel-2 imagery with low cloud cover (<10%) and high confidence [1]."

**Citations:**
- `[1]` → Geography Agent Finding (finding-456) → Navigate to Source of Truth, expand Geography Agent finding

### D.2 Example 2: IFRS Compliance Query

**User:** "Does the report meet S2.14(a)(iv) transition plan requirements?"

**Chatbot:** "The report mentions a transition plan [1], but the Legal Agent found that it does not fully meet S2.14(a)(iv) requirements [2]. Specifically, S2.14(a)(iv) requires disclosure of key assumptions, dependencies, and timeline [3]. The report includes a timeline [1] but omits key assumptions and dependencies [2]. The Judge Agent verified this finding, resulting in a 'Partially Addressed' compliance status [4]."

**Citations:**
- `[1]` → Report Content (chunk-789) → Navigate to PDF viewer, page 23
- `[2]` → Legal Agent Finding (finding-123) → Navigate to Source of Truth, expand Legal Agent finding
- `[3]` → IFRS S2 Paragraph S2.14(a)(iv) → Show IFRS paragraph modal
- `[4]` → Judge Verdict (verdict-456) → Navigate to Source of Truth, expand claim card

### D.3 Example 3: Disclosure Gap Query

**User:** "What are the main compliance gaps in the Governance pillar?"

**Chatbot:** "The Legal Agent identified several disclosure gaps in the Governance pillar. The most significant gaps are:

1. **S2.6 - Climate competencies:** The report does not disclose how board members' competencies for climate strategies are ensured [1].

2. **S1.27(a)(v) - Remuneration links:** The report mentions governance oversight but does not link sustainability performance to executive remuneration [2].

3. **S2.7 - Climate-linked remuneration:** No disclosure of whether climate performance affects remuneration [3].

These gaps indicate incomplete governance disclosure, which is critical for assessing board accountability for climate risks [1][2][3]."

**Citations:**
- `[1]` → Disclosure Gap S2.6 → Navigate to Source of Truth, Disclosure Gaps section
- `[2]` → Disclosure Gap S1.27(a)(v) → Navigate to Source of Truth, Disclosure Gaps section
- `[3]` → Disclosure Gap S2.7 → Navigate to Source of Truth, Disclosure Gaps section

### D.4 Example 4: Evidence Chain Query

**User:** "What evidence supports the company's Scope 3 emission reduction claim?"

**Chatbot:** "Multiple agents investigated the Scope 3 emission reduction claim and found supporting evidence:

**Claim:** The report states that Scope 3 emissions decreased by 3.2% from FY2023 to FY2024 [1].

**Evidence:**
- **Data/Metrics Agent:** Verified mathematical consistency of the reported figures and confirmed the calculation methodology aligns with GHG Protocol [2].
- **Academic/Research Agent:** Validated that the reduction percentage is plausible for the company's industry sector based on benchmark data [3].
- **News/Media Agent:** Found public reporting corroborating the company's emission reduction initiatives [4].

**Judge Verdict:** Verified [5]. Multiple independent sources corroborate the claim with no contradictions found."

**Citations:**
- `[1]` → Claim (claim-789) → Navigate to PDF viewer, highlight claim
- `[2]` → Data/Metrics Agent Finding → Navigate to Source of Truth, expand Data/Metrics finding
- `[3]` → Academic/Research Agent Finding → Navigate to Source of Truth, expand Academic finding
- `[4]` → News/Media Agent Finding → Navigate to Source of Truth, expand News/Media finding
- `[5]` → Judge Verdict → Navigate to Source of Truth, expand claim card

---

## Appendix E: Chat API Response Schemas

### E.1 ChatMessageRequest

```python
class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
```

### E.2 ChatMessageResponse (Non-Streaming)

```python
class ChatMessageResponse(BaseModel):
    message_id: str
    content: str
    citations: list[CitationEntity]
    created_at: str
```

### E.3 CitationEntity

```python
class CitationEntity(BaseModel):
    citation_number: int
    source_type: str  # "claim" | "finding" | "ifrs_paragraph" | "verdict" | "gap"
    entity_id: str
    navigation_target: dict
```

### E.4 SSE Event Types

```python
# Token event
{
    "type": "token",
    "data": "The"
}

# Citation event
{
    "type": "citation",
    "data": {
        "citation_number": 1,
        "source_type": "claim",
        "entity_id": "claim-123",
        "navigation_target": {...}
    }
}

# Done event
{
    "type": "done",
    "data": {}
}
```

### E.5 ConversationHistoryResponse

```python
class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    messages: list[ChatMessageResponse]
    total_messages: int
```

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| Gemini 3 Flash over Claude Sonnet 4.5 for chatbot | PRD Section 4.12 specifies Gemini 3 Flash for cost-effectiveness and fast conversational Q&A. Claude Sonnet 4.5 is used for complex reasoning (agents), but chatbot needs speed and large context (1M tokens). |
| Multi-source RAG retrieval over single-source | Chatbot questions span multiple domains (report content, agent findings, IFRS standards, verdicts, gaps). Single-source retrieval would miss relevant information. Multi-source ensures comprehensive answers. |
| Inline citations over separate reference list | Inline citations (like academic papers) are more readable and allow direct source verification. Separate reference lists require users to match numbers, reducing usability. |
| Citation markers [1], [2] over hyperlinks | Citation markers are LLM-friendly (easy to generate) and can be rendered as clickable buttons in the frontend. Hyperlinks in LLM output are less reliable and harder to parse. |
| Conversation persistence in database over localStorage | Database persistence enables conversation history across devices and sessions. localStorage is browser-specific and lost on clear. Database also enables future features (conversation search, analytics). |
| SSE streaming over complete response | Progressive text appearance (like ChatGPT) provides better UX and perceived performance. Users see responses immediately rather than waiting for complete generation. |
| Slide-out panel over modal | Slide-out panel allows users to reference the chat while viewing other content. Modal blocks the entire screen, reducing usability. Panel can remain open during navigation. |
| Floating button on all pages over page-specific | Chatbot is a global feature accessible from any page. Floating button ensures consistent access regardless of current page. |
| Citation navigation targets as JSON over hardcoded routes | JSON navigation targets are flexible and can evolve without frontend changes. Hardcoded routes would require frontend updates for each new navigation type. |
| Context length management (50K tokens) over unlimited | Gemini 3 Flash has 1M token context, but we reserve space for system prompt, user message, conversation history, and response. 50K tokens for context ensures we don't exceed limits. |
| Multi-turn conversation (last 10 messages) over full history | Including full conversation history would exceed token limits for long conversations. Last 10 messages (5 turns) provides sufficient context while managing token usage. |
| RAG retrieval parallelization over sequential | Parallel retrieval reduces latency. All source types are queried simultaneously, then results are merged. Sequential queries would add unnecessary delay. |
| Citation extraction via regex over LLM parsing | Regex extraction is fast and reliable. LLM parsing would add latency and cost. Citation markers [1], [2] are simple patterns that regex handles well. |
| Chat panel in layout (global) over page-specific | Global placement ensures chat is available on all pages without duplication. Page-specific placement would require chat component on every page. |
| Conversation history limit (50 messages) over unlimited | Unlimited history retrieval could be slow for very long conversations. 50 messages is sufficient for typical use cases and keeps response times fast. |
| Error handling with fallback responses over exceptions | Users should always receive a response, even if RAG or LLM fails. Fallback responses explain limitations rather than showing errors. Exceptions would break the UX. |
| Temperature 0.3 over 0.1 or 0.5 | 0.3 balances accuracy (factual Q&A) with natural language generation. 0.1 would be too rigid; 0.5 would introduce too much creativity for factual answers. |
| Citation metadata includes navigation_target | Frontend needs to know where to navigate when citations are clicked. Including navigation_target in metadata avoids frontend logic to construct routes. |
| Stream response by default over complete | Streaming provides better UX (progressive appearance). Complete responses require users to wait for full generation. Streaming is the default; complete is available as fallback. |
