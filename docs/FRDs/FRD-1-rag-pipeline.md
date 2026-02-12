# Feature Requirements Document: FRD 1 -- RAG Pipeline (v1.0)

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.3](../PRD.md) |
| **FRD Order** | [FRD Order](../FRD-order.md) |
| **PRD Sections** | 5.5 (RAG Pipeline Architecture) |
| **Type** | Core infrastructure feature |
| **Depends On** | FRD 0 (Setup Document) |
| **Delivers** | Embedding service, chunking, hybrid retrieval, IFRS/SASB corpus ingestion |
| **Created** | 2026-02-08 |

---

## Summary

FRD 1 builds the Retrieval-Augmented Generation (RAG) pipeline that underpins Sibyl's ability to ground agent reasoning in authoritative source material. The pipeline consists of three layers: an embedding service that converts text into 1536-dimensional vectors via OpenAI `text-embedding-3-small` (through OpenRouter), a set of chunking strategies tailored to each corpus type (paragraph-level for IFRS standards, topic-level for SASB standards, hierarchical for uploaded reports), and a hybrid retrieval engine that combines semantic search (pgvector cosine similarity) with keyword search (PostgreSQL full-text search) and re-ranks the merged results using Reciprocal Rank Fusion (RRF). FRD 1 also delivers the initial knowledge base -- the IFRS S1 and S2 standard texts and the SASB industry standards are parsed, chunked, embedded, and stored during a one-time corpus ingestion step. The entire RAG pipeline is exposed through a `RAGService` class consumed by agents (via the `rag_lookup` LangGraph tool) and the chatbot.

---

## Given Context (Preconditions)

The following are assumed to be in place from FRD 0:

| Prerequisite | FRD 0 Deliverable |
|---|---|
| PostgreSQL 17 with pgvector running | Docker Compose `db` service |
| `embeddings` table with `Vector(1536)` column, HNSW index, GIN index on `ts_content` | Alembic initial migration |
| `Embedding` SQLAlchemy model | `app/models/embedding.py` |
| Async database engine and session factory | `app/core/database.py` |
| OpenRouter client wrapper with retry logic | `app/services/openrouter_client.py` |
| Model constants including `Models.EMBEDDING` | `app/services/openrouter_client.py` |
| Stub files for `rag_service.py` and `rag_lookup.py` | `app/services/` and `app/agents/tools/` |
| Empty `data/ifrs/` and `data/sasb/` directories | Backend file structure |

### Terms

| Term | Definition |
|---|---|
| Chunk | A self-contained segment of text with associated metadata, stored as a single embedding row |
| Corpus | A collection of documents loaded into the RAG knowledge base (IFRS S1, IFRS S2, SASB, or report content) |
| Hybrid search | Retrieval combining semantic similarity (vector) and keyword matching (full-text) into a single ranked result set |
| Re-ranking | The process of merging, de-duplicating, and re-scoring results from multiple retrieval methods into a final ordered list. Implemented via RRF. |
| RRF (Reciprocal Rank Fusion) | The re-ranking algorithm used in hybrid search -- a rank-based score combination method that does not require score normalization across retrieval methods |
| Ingestion | The process of parsing a source document, chunking it, embedding the chunks, and storing them in the database |
| Paragraph ID | An IFRS standard identifier like `S1.26`, `S2.14(a)(iv)`, or `S2.29(a)(iii)` that uniquely identifies a disclosure requirement |

---

## Executive Summary (Gherkin-Style)

```gherkin
Feature: RAG Pipeline

  Background:
    Given  FRD 0 is complete
    And    PostgreSQL with pgvector is running
    And    the embeddings table exists with HNSW and GIN indexes

  Scenario: Embed a single text chunk
    When   the embedding service receives a text string
    Then   it calls OpenAI text-embedding-3-small via OpenRouter
    And    returns a 1536-dimensional float vector
    And    the call includes retry logic for transient failures

  Scenario: Embed a batch of text chunks
    When   the embedding service receives a list of text strings
    Then   it batches them into groups respecting the token limit
    And    calls the embedding API once per batch
    And    returns a list of 1536-dimensional vectors in the same order

  Scenario: Ingest IFRS S1 standard text
    When   the corpus ingestion command runs for IFRS S1
    Then   the system parses data/ifrs/s1_full.md
    And    splits it into paragraph-level chunks
    And    each chunk has metadata: paragraph_id, section, pillar, sub_requirements
    And    each chunk is embedded and stored with source_type = "ifrs_s1"
    And    full-text search vectors (ts_content) are generated

  Scenario: Ingest IFRS S2 standard text
    When   the corpus ingestion command runs for IFRS S2
    Then   the system parses data/ifrs/s2_full.md
    And    splits it into paragraph-level chunks with S2-specific metadata
    And    each chunk includes the corresponding S1 pillar mapping
    And    each chunk is embedded and stored with source_type = "ifrs_s2"

  Scenario: Ingest SASB standards
    When   the corpus ingestion command runs for SASB
    Then   the system parses files from data/sasb/
    And    splits them into topic-level chunks with industry sector metadata
    And    each chunk is embedded and stored with source_type = "sasb"

  Scenario: Ingest report content (used by FRD 2)
    When   the RAG service receives parsed report markdown and a report_id
    Then   it splits the content using hierarchical chunking
    And    preserves section headers and page numbers as metadata
    And    each chunk is embedded and stored with source_type = "report"
    And    each chunk links to the parent report via report_id

  Scenario: Semantic search
    Given  the IFRS corpus has been ingested
    When   a consumer searches for "transition plan requirements"
    Then   the system embeds the query
    And    performs cosine similarity search against pgvector
    And    returns the top-k most semantically similar chunks with scores

  Scenario: Keyword search
    Given  the IFRS corpus has been ingested
    When   a consumer searches for "S2.14(a)(iv)"
    Then   the system performs PostgreSQL full-text search using ts_query
    And    returns chunks containing the exact paragraph identifier

  Scenario: Hybrid search with re-ranking
    Given  the IFRS corpus has been ingested
    When   a consumer performs a hybrid search for "Scope 3 emissions S2.29"
    Then   the system runs both semantic and keyword searches
    And    re-ranks and merges results using Reciprocal Rank Fusion (RRF)
    And    de-duplicates by chunk ID
    And    returns a single ranked result list

  Scenario: RAG lookup tool for agents
    Given  the RAG pipeline is operational
    When   a LangGraph agent calls the rag_lookup tool with a query
    Then   the tool performs a hybrid search
    And    returns formatted context text with source metadata
    And    the agent can use the context in its reasoning
```

---

## Table of Contents

1. [Embedding Service](#1-embedding-service)
2. [Chunking Strategies](#2-chunking-strategies)
3. [Corpus Ingestion](#3-corpus-ingestion)
4. [Hybrid Retrieval Engine](#4-hybrid-retrieval-engine)
5. [RAG Service API](#5-rag-service-api)
6. [RAG Lookup Tool (LangGraph)](#6-rag-lookup-tool-langgraph)
7. [Backend Endpoints](#7-backend-endpoints)
8. [IFRS and SASB Source Files](#8-ifrs-and-sasb-source-files)
9. [Exit Criteria](#9-exit-criteria)
10. [Appendix A: IFRS Chunk Metadata Schema](#appendix-a-ifrs-chunk-metadata-schema)
11. [Appendix B: Chunking Examples](#appendix-b-chunking-examples)
12. [Appendix C: Hybrid Search Worked Example](#appendix-c-hybrid-search-worked-example)
13. [Design Decisions Log](#design-decisions-log)

---

## 1. Embedding Service

### 1.1 Overview

The embedding service (`app/services/embedding_service.py`) converts text strings into 1536-dimensional float vectors using OpenAI `text-embedding-3-small` via the OpenRouter API. It is the sole embedding interface for the entire application -- all corpus ingestion and query embedding flows through this service.

### 1.2 Functional Requirements

The system shall:

1. Provide an `embed_text(text: str) -> list[float]` method that embeds a single text string and returns a 1536-dimensional vector.
2. Provide an `embed_batch(texts: list[str]) -> list[list[float]]` method that embeds multiple text strings in batches and returns vectors in the same order as the input.
3. Call the OpenRouter API at the embeddings endpoint (`POST /v1/embeddings`) with model `openai/text-embedding-3-small`.
4. Implement batching for `embed_batch`:
   - Group texts into batches of up to **100 texts** or **8,000 tokens total** per batch (whichever limit is reached first), respecting the `text-embedding-3-small` context window.
   - Process batches sequentially to avoid rate limit issues.
5. Implement retry logic consistent with the OpenRouter client: 3 retries with exponential backoff (1s, 2s, 4s) for transient HTTP failures (429, 500, 502, 503, 504).
6. Raise a descriptive `EmbeddingError` exception if embedding fails after all retries.
7. Log embedding requests with text count and total token count for monitoring.

### 1.3 Token Estimation

The system shall implement a lightweight token estimator for batching purposes:

1. Use a simple heuristic: `token_count ≈ len(text) / 4` (approximate for English text).
2. This is used only for batch sizing -- the exact token count is handled by the API.
3. If a single text exceeds 8,000 estimated tokens, it shall be truncated to approximately 8,000 tokens (32,000 characters) with a logged warning. This should be rare because chunks are sized well below this limit.

### 1.4 Request Format

Each embedding API call shall use the following request body:

```json
{
  "model": "openai/text-embedding-3-small",
  "input": ["text1", "text2", "..."]
}
```

The response provides an array of embedding objects, each containing a `float[]` vector of dimension 1536.

### 1.5 Caching

No embedding cache is implemented for MVP. Each call produces a fresh embedding. Corpus ingestion is a one-time operation, and query embedding is fast enough at runtime.

---

## 2. Chunking Strategies

### 2.1 Overview

Three distinct chunking strategies handle the different corpus types. Each strategy produces chunks that are self-contained (readable without surrounding context), preserve critical metadata, and fit within the embedding model's 8K token context window.

### 2.2 IFRS Paragraph-Level Chunking

**Applies to:** `data/ifrs/s1_full.md`, `data/ifrs/s2_full.md`

**Strategy:** Split on paragraph boundaries defined by the IFRS standard structure. Each paragraph (e.g., S1.26, S2.14, S2.14(a)(iv)) becomes a single chunk.

The system shall:

1. Parse the markdown file and identify paragraph boundaries using heading patterns.
2. Recognize paragraph identifiers in the following formats:
   - Top-level paragraphs: `S1.26`, `S2.14`
   - Sub-paragraphs: `S1.27(a)`, `S2.14(a)(iv)`
   - Paragraph ranges in section headings: `S2.5-7`, `S2.27-31`
3. When a paragraph range heading is encountered (e.g., "## Governance (S2.5-7)"), treat each individual paragraph within the range as a separate chunk if they are individually identifiable in the body text. If paragraphs within the range are not individually delineated, keep the range as a single chunk.
4. Prepend each chunk with a context header containing the section path:
   ```
   [IFRS S2 > Strategy > Decision-Making > S2.14(a)(iv)]
   ```
   This ensures the chunk is self-contained and the embedding captures the hierarchical context.
5. If a paragraph exceeds 1,500 tokens (approximately 6,000 characters), split it at sentence boundaries while keeping the context header on each sub-chunk and appending a part indicator (e.g., "[Part 1/2]").

**Metadata per chunk:**

| Field | Type | Description |
|---|---|---|
| `paragraph_id` | `string` | The IFRS paragraph identifier (e.g., `"S2.14(a)(iv)"`) |
| `standard` | `string` | `"S1"` or `"S2"` |
| `pillar` | `string` | `"governance"`, `"strategy"`, `"risk_management"`, or `"metrics_targets"` |
| `section` | `string` | Section name (e.g., `"Decision-Making"`, `"GHG Emissions"`) |
| `sub_requirements` | `string[]` | List of specific sub-requirement identifiers within this paragraph |
| `s1_counterpart` | `string \| null` | For S2 paragraphs, the corresponding S1 paragraph (from the cross-mapping) |

### 2.3 SASB Topic-Level Chunking

**Applies to:** Files in `data/sasb/`

**Strategy:** Split by disclosure topic within each industry standard. Each topic (e.g., "GHG Emissions", "Energy Management", "Water Management") becomes a single chunk.

The system shall:

1. Parse each SASB industry standard markdown file.
2. Split on topic headings (typically H2 or H3 level).
3. Prepend each chunk with a context header:
   ```
   [SASB > Oil & Gas > GHG Emissions]
   ```
4. If a topic section exceeds 1,500 tokens, split at sub-topic or metric boundaries.

**Metadata per chunk:**

| Field | Type | Description |
|---|---|---|
| `industry_sector` | `string` | SASB industry name (e.g., `"Oil & Gas"`, `"Banking"`) |
| `disclosure_topic` | `string` | Topic name (e.g., `"GHG Emissions"`, `"Energy Management"`) |
| `metric_codes` | `string[]` | SASB metric identifiers within this topic |
| `standard_code` | `string` | SASB industry standard code (e.g., `"EM-EP"` for Extractives & Minerals Processing -- Exploration & Production) |

### 2.4 Report Hierarchical Chunking

**Applies to:** Uploaded sustainability report content (parsed markdown from PyMuPDF4LLM, consumed via FRD 2)

**Strategy:** Hierarchical chunking that preserves the document's section structure. Section headers flow down as metadata so every chunk knows where it sits in the document.

The system shall:

1. Parse the report markdown and identify section hierarchy from headings (H1, H2, H3, etc.).
2. Split content into chunks of **approximately 500-800 tokens** (2,000-3,200 characters), splitting at:
   - Paragraph boundaries (preferred)
   - Sentence boundaries (fallback)
   - Never mid-sentence
3. Apply a **100-token overlap** between consecutive chunks within the same section to preserve context at boundaries.
4. Prepend each chunk with the section header path:
   ```
   [Report > Environmental Performance > GHG Emissions > Scope 3]
   ```
5. Preserve table content: If a table fits within the chunk size limit, keep it as a single chunk. If it exceeds the limit, split by row groups while preserving the table header on each sub-chunk.
6. Track page numbers: Each chunk records the page number(s) it spans from the original PDF.

**Metadata per chunk:**

| Field | Type | Description |
|---|---|---|
| `page_start` | `int` | Starting page number in the original PDF |
| `page_end` | `int` | Ending page number (may equal `page_start`) |
| `section_path` | `string[]` | Ordered list of section headers from root to this chunk's section |
| `has_table` | `bool` | Whether this chunk contains tabular data |
| `chunk_index` | `int` | Sequential index of this chunk within the report (for ordering) |

### 2.5 Chunking Configuration

The system shall define chunking parameters as constants (not hardcoded inline) so they can be tuned:

```python
class ChunkingConfig:
    # IFRS / SASB paragraph chunking
    PARAGRAPH_MAX_TOKENS: int = 1500
    
    # Report hierarchical chunking
    REPORT_CHUNK_TARGET_TOKENS: int = 600
    REPORT_CHUNK_MIN_TOKENS: int = 200
    REPORT_CHUNK_MAX_TOKENS: int = 800
    REPORT_CHUNK_OVERLAP_TOKENS: int = 100
    
    # Token estimation
    CHARS_PER_TOKEN: int = 4  # Approximate for English text
```

---

## 3. Corpus Ingestion

### 3.1 Overview

Corpus ingestion parses source documents, applies the appropriate chunking strategy, embeds all chunks, and stores them in the `embeddings` table. There are two ingestion paths:

1. **Static corpus ingestion** (IFRS and SASB) -- runs once during setup or via a CLI command. This populates the foundational knowledge base that agents rely on.
2. **Report ingestion** (uploaded PDFs) -- runs per upload, triggered by FRD 2. This is a method on `RAGService` called by the PDF upload pipeline.

### 3.2 Static Corpus Ingestion Command

The system shall provide a CLI entry point (callable via `python -m app.services.rag_service ingest` or a FastAPI startup hook) that:

1. Checks whether the IFRS/SASB corpus has already been ingested (by querying for existing `source_type = 'ifrs_s1'` embeddings). If the corpus already exists, skip ingestion and log a message. To force re-ingestion, the existing embeddings must be deleted first.
2. Parses and chunks `data/ifrs/s1_full.md` using IFRS paragraph-level chunking.
3. Parses and chunks `data/ifrs/s2_full.md` using IFRS paragraph-level chunking.
4. Loads and validates `data/ifrs/s1_s2_mapping.json` and enriches S2 chunks with their S1 counterpart mappings.
5. Parses and chunks all SASB standard files from `data/sasb/` using SASB topic-level chunking.
6. Embeds all chunks via the embedding service (using `embed_batch` for efficiency).
7. Stores all embeddings in the `embeddings` table with:
   - `source_type`: `"ifrs_s1"`, `"ifrs_s2"`, or `"sasb"`
   - `report_id`: `null` (these are not linked to any specific report)
   - `chunk_text`: The full chunk text including the context header
   - `chunk_metadata`: The metadata dict appropriate to the corpus type
   - `embedding`: The 1536-dimensional vector
   - `ts_content`: Generated by PostgreSQL `to_tsvector('english', chunk_text)` at insert time
8. Logs progress: total chunks per corpus, embedding batch progress, total time elapsed.

### 3.3 Report Ingestion Method

The system shall provide a `RAGService.ingest_report(report_id: str, markdown_content: str, page_metadata: list[dict]) -> int` method that:

1. Applies hierarchical chunking to the markdown content.
2. Maps page metadata (from PyMuPDF4LLM parsing) to chunks.
3. Embeds all chunks via the embedding service.
4. Stores all embeddings in the `embeddings` table with:
   - `source_type`: `"report"`
   - `report_id`: The provided report UUID
   - `chunk_text`: The chunk text with section header prefix
   - `chunk_metadata`: Report-specific metadata (page numbers, section path, table flag)
   - `embedding` and `ts_content`: As above
5. Returns the number of chunks created.

### 3.4 ts_content Generation

For full-text search support, the system shall generate the `ts_content` TSVector column at insert time using PostgreSQL's `to_tsvector`:

1. Use the `'english'` text search configuration for stemming and stop-word removal.
2. Set `ts_content` via a SQLAlchemy column default or explicit assignment:
   ```sql
   ts_content = to_tsvector('english', chunk_text)
   ```
3. This enables the GIN index (created in FRD 0) to accelerate full-text search queries.

### 3.5 Idempotency and Re-ingestion

The system shall:

1. For static corpus: Check for existing embeddings before ingesting. Provide a `delete_corpus(source_type: str)` method to clear a specific corpus for re-ingestion.
2. For reports: Delete all existing embeddings for a `report_id` before re-ingesting (in case of re-parsing). This is performed within a transaction.

---

## 4. Hybrid Retrieval Engine

### 4.1 Overview

The retrieval engine supports three search modes: semantic-only, keyword-only, and hybrid (the default). Hybrid search combines results from both methods using Reciprocal Rank Fusion (RRF) to produce a single ranked result list.

### 4.2 Semantic Search

The system shall:

1. Accept a query string and embed it using the embedding service.
2. Execute a pgvector cosine similarity search against the `embeddings` table:
   ```sql
   SELECT id, chunk_text, chunk_metadata, source_type, report_id,
          1 - (embedding <=> :query_vector) AS similarity_score
   FROM embeddings
   WHERE (:source_types IS NULL OR source_type = ANY(:source_types))
     AND (:report_id IS NULL OR report_id = :report_id)
   ORDER BY embedding <=> :query_vector
   LIMIT :top_k
   ```
3. Apply optional filters:
   - `source_types: list[str] | None` -- restrict to specific corpus types (e.g., `["ifrs_s1", "ifrs_s2"]`)
   - `report_id: str | None` -- restrict to a specific report's chunks
4. Return results with `similarity_score` (0 to 1, higher is more similar).

### 4.3 Keyword Search

The system shall:

1. Accept a query string and convert it to a `tsquery` using PostgreSQL's `plainto_tsquery` (for natural language queries) or `to_tsquery` (for structured queries with explicit operators).
2. Execute a full-text search against the `ts_content` column:
   ```sql
   SELECT id, chunk_text, chunk_metadata, source_type, report_id,
          ts_rank_cd(ts_content, query) AS rank_score
   FROM embeddings, plainto_tsquery('english', :query_text) AS query
   WHERE ts_content @@ query
     AND (:source_types IS NULL OR source_type = ANY(:source_types))
     AND (:report_id IS NULL OR report_id = :report_id)
   ORDER BY rank_score DESC
   LIMIT :top_k
   ```
3. Apply the same optional filters as semantic search.
4. Return results with `rank_score` (PostgreSQL text search rank, higher is more relevant).

### 4.4 Paragraph ID Search (Specialized Keyword)

The system shall provide a specialized search for IFRS paragraph identifiers:

1. Accept a paragraph ID string (e.g., `"S2.14(a)(iv)"`).
2. Search the `chunk_metadata` JSONB column:
   ```sql
   SELECT id, chunk_text, chunk_metadata, source_type
   FROM embeddings
   WHERE chunk_metadata->>'paragraph_id' = :paragraph_id
     AND source_type IN ('ifrs_s1', 'ifrs_s2')
   ```
3. Return exact matches. This is used by the Legal Agent when it needs a specific IFRS paragraph by its identifier.

### 4.5 Hybrid Search with Re-ranking (Reciprocal Rank Fusion)

When hybrid mode is selected (the default), the system shall merge and re-rank results from both retrieval methods using **Reciprocal Rank Fusion (RRF)**, the re-ranking algorithm:

1. Run semantic search and keyword search in parallel (using `asyncio.gather`).
2. Re-rank and merge the two result lists using **Reciprocal Rank Fusion (RRF)**:
   ```
   RRF_score(d) = Σ 1 / (k + rank_i(d))
   ```
   Where:
   - `d` is a document (chunk)
   - `rank_i(d)` is the rank of document `d` in result list `i` (1-indexed)
   - `k` is a constant (default: 60) that dampens the effect of high rankings
   - The sum is over all result lists where `d` appears
3. De-duplicate by chunk `id` (a chunk may appear in both result lists).
4. Sort by descending RRF score.
5. Return the top `top_k` results.

**Why RRF for re-ranking:** Semantic similarity scores and full-text search ranks are on incomparable scales. RRF operates on ranks rather than scores, making it a robust re-ranking method across retrieval methods without requiring score normalization.

### 4.6 Search Result Schema

Each search result shall be returned as a `RAGResult` Pydantic model:

```python
class RAGResult(BaseModel):
    """A single retrieval result from the RAG pipeline."""
    chunk_id: str               # UUID of the embedding row
    chunk_text: str             # Full chunk text
    metadata: dict              # chunk_metadata from the database
    source_type: str            # ifrs_s1 | ifrs_s2 | sasb | report
    report_id: str | None       # Report UUID (for report chunks) or None
    score: float                # Retrieval score (similarity, rank, or RRF)
    search_method: str          # "semantic" | "keyword" | "hybrid"
```

### 4.7 Search Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | *(required)* | The search query text |
| `top_k` | `int` | `10` | Maximum number of results to return |
| `mode` | `str` | `"hybrid"` | Search mode: `"semantic"`, `"keyword"`, or `"hybrid"` |
| `source_types` | `list[str] \| None` | `None` | Filter by corpus type(s); `None` = all |
| `report_id` | `str \| None` | `None` | Filter to a specific report's chunks |
| `rrf_k` | `int` | `60` | RRF constant for hybrid mode |

---

## 5. RAG Service API

### 5.1 Class Design

The `RAGService` class (`app/services/rag_service.py`) is the central API for all RAG operations. It is instantiated with a database session and the embedding service.

```python
class RAGService:
    def __init__(self, db: AsyncSession, embedding_service: EmbeddingService):
        ...

    # --- Ingestion ---
    async def ingest_ifrs_corpus(self) -> dict:
        """Ingest IFRS S1 and S2 standard texts. Returns stats."""

    async def ingest_sasb_corpus(self) -> dict:
        """Ingest SASB industry standards. Returns stats."""

    async def ingest_report(
        self, report_id: str, markdown_content: str,
        page_metadata: list[dict] | None = None
    ) -> int:
        """Chunk, embed, and store report content. Returns chunk count."""

    async def delete_corpus(self, source_type: str) -> int:
        """Delete all embeddings for a source type. Returns deleted count."""

    async def delete_report_embeddings(self, report_id: str) -> int:
        """Delete all embeddings for a specific report. Returns deleted count."""

    # --- Retrieval ---
    async def search(
        self, query: str, top_k: int = 10, mode: str = "hybrid",
        source_types: list[str] | None = None,
        report_id: str | None = None, rrf_k: int = 60
    ) -> list[RAGResult]:
        """Perform a search and return ranked results."""

    async def get_paragraph(self, paragraph_id: str) -> RAGResult | None:
        """Retrieve a specific IFRS paragraph by its identifier."""

    # --- Utilities ---
    async def corpus_stats(self) -> dict:
        """Return counts of embeddings by source type."""
```

### 5.2 Dependency Injection

The `RAGService` shall be available as a FastAPI dependency:

```python
async def get_rag_service(db: AsyncSession = Depends(get_db)) -> RAGService:
    embedding_service = EmbeddingService(settings)
    return RAGService(db, embedding_service)
```

### 5.3 Error Handling

The system shall:

1. Wrap embedding API failures in an `EmbeddingError` with the original exception as context.
2. Wrap database failures in a `RAGServiceError`.
3. Log all errors with sufficient context (query text, source types, chunk counts) for debugging.
4. Return empty result lists (not exceptions) when a search produces no matches.

---

## 6. RAG Lookup Tool (LangGraph)

### 6.1 Purpose

The `rag_lookup` tool (`app/agents/tools/rag_lookup.py`) wraps the `RAGService` as a LangGraph tool that agents can call during their investigation. It provides a simplified interface suitable for LLM tool calling.

### 6.2 Tool Definition

The system shall define a LangChain-compatible tool:

```python
@tool
async def rag_lookup(
    query: str,
    source_types: list[str] | None = None,
    top_k: int = 5,
    paragraph_id: str | None = None
) -> str:
    """Search the RAG knowledge base for relevant IFRS standards,
    SASB guidance, or report content.

    Args:
        query: Natural language search query describing what information
            you need (e.g., "transition plan requirements", "Scope 3 emissions
            disclosure").
        source_types: Optional filter for corpus type(s). Valid values:
            "ifrs_s1", "ifrs_s2", "sasb", "report". If omitted, searches all.
        top_k: Number of results to return (default: 5).
        paragraph_id: If provided, retrieves the exact IFRS paragraph by ID
            (e.g., "S2.14(a)(iv)"). When set, query and source_types are ignored.

    Returns:
        Formatted text with retrieved passages and their source metadata.
    """
```

### 6.3 Output Formatting

The tool shall format results as a structured text string for LLM consumption:

```
--- Result 1 (source: ifrs_s2, score: 0.87) ---
[Paragraph: S2.14(a)(iv) | Pillar: Strategy | Section: Decision-Making]

An entity shall disclose its transition plan, including key assumptions
and dependencies used in developing the plan...

--- Result 2 (source: ifrs_s1, score: 0.82) ---
[Paragraph: S1.33 | Pillar: Strategy | Section: Strategy Response]

An entity shall disclose how it has responded to sustainability-related
risks and opportunities...

--- No more results ---
```

This format gives the LLM clear context about each result's source, relevance score, and hierarchical position within the standards.

### 6.4 Report-Scoped Search

When an agent needs to search the uploaded report content (rather than the IFRS/SASB corpus), it passes `source_types=["report"]`. The `report_id` is injected from the `SibylState.report_id` at runtime -- the tool reads it from the LangGraph state context rather than requiring the agent to pass it explicitly.

---

## 7. Backend Endpoints

### 7.1 Corpus Ingestion Endpoint

```
POST /api/v1/rag/ingest

Request Body:
{
  "corpus": "all" | "ifrs" | "sasb"
}

Response 200:
{
  "status": "completed",
  "ifrs_s1_chunks": 87,
  "ifrs_s2_chunks": 124,
  "sasb_chunks": 156,
  "total_chunks": 367,
  "duration_seconds": 42.3
}

Response 409 (already ingested):
{
  "status": "already_ingested",
  "message": "Corpus already exists. Delete it first to re-ingest.",
  "existing_counts": { "ifrs_s1": 87, "ifrs_s2": 124, "sasb": 156 }
}
```

This endpoint is intended for manual triggering during setup. In production, the static corpus is ingested once and then persists across application restarts (data is in PostgreSQL).

### 7.2 Corpus Stats Endpoint

```
GET /api/v1/rag/stats

Response 200:
{
  "ifrs_s1": 87,
  "ifrs_s2": 124,
  "sasb": 156,
  "report": 0,
  "total": 367
}
```

### 7.3 Search Endpoint (Development/Debug)

```
POST /api/v1/rag/search

Request Body:
{
  "query": "transition plan requirements",
  "top_k": 5,
  "mode": "hybrid",
  "source_types": ["ifrs_s1", "ifrs_s2"]
}

Response 200:
{
  "results": [
    {
      "chunk_id": "uuid-...",
      "chunk_text": "[IFRS S2 > Strategy > ...] An entity shall...",
      "metadata": { "paragraph_id": "S2.14(a)(iv)", "pillar": "strategy", ... },
      "source_type": "ifrs_s2",
      "report_id": null,
      "score": 0.87,
      "search_method": "hybrid"
    },
    ...
  ],
  "total_results": 5,
  "search_mode": "hybrid"
}
```

This endpoint is for development testing and debugging. Agents use the `rag_lookup` tool, not this endpoint.

### 7.4 Delete Corpus Endpoint (Development/Debug)

```
DELETE /api/v1/rag/corpus/{source_type}

Response 200:
{
  "status": "deleted",
  "source_type": "ifrs_s1",
  "deleted_count": 87
}
```

### 7.5 Route Registration

All RAG endpoints shall be registered under a new `rag` router (`app/api/routes/rag.py`) with prefix `/rag` and tag `"RAG Pipeline"`.

---

## 8. IFRS and SASB Source Files

### 8.1 IFRS S1 (`data/ifrs/s1_full.md`)

The IFRS S1 standard text shall be stored as a markdown file structured with:

- H1: Standard title and metadata
- H2: Major sections (Governance, Strategy, Risk Management, Metrics and Targets, Appendices)
- H3: Paragraph groups (e.g., "Governance (S1.26-27)")
- Body text: Individual paragraphs with their identifiers

The file shall cover all paragraphs referenced in PRD Appendix A (S1.26-27, S1.28-35, S1.38-42, S1.43-53) plus appendices and application guidance.

### 8.2 IFRS S2 (`data/ifrs/s2_full.md`)

The IFRS S2 standard text shall be stored as a markdown file structured similarly, covering all paragraphs referenced in PRD Appendix B (S2.5-37) plus appendices and industry-based guidance.

### 8.3 S1/S2 Cross-Reference Mapping (`data/ifrs/s1_s2_mapping.json`)

The cross-reference mapping shall be stored as a JSON file matching PRD Appendix C:

```json
{
  "mappings": [
    {
      "s2_paragraphs": "S2.5-7",
      "s2_description": "Climate governance",
      "s1_paragraphs": "S1.26-27",
      "s1_description": "General governance",
      "s1_pillar": "governance"
    },
    {
      "s2_paragraphs": "S2.10-12",
      "s2_description": "Climate risks/opportunities",
      "s1_paragraphs": "S1.30",
      "s1_description": "General risks/opportunities",
      "s1_pillar": "strategy"
    },
    {
      "s2_paragraphs": "S2.13",
      "s2_description": "Business model effects",
      "s1_paragraphs": "S1.32",
      "s1_description": "General business model effects",
      "s1_pillar": "strategy"
    },
    {
      "s2_paragraphs": "S2.14",
      "s2_description": "Strategy/decision-making",
      "s1_paragraphs": "S1.33",
      "s1_description": "General strategy response",
      "s1_pillar": "strategy"
    },
    {
      "s2_paragraphs": "S2.15-21",
      "s2_description": "Financial effects",
      "s1_paragraphs": "S1.35",
      "s1_description": "General financial effects",
      "s1_pillar": "strategy"
    },
    {
      "s2_paragraphs": "S2.22",
      "s2_description": "Climate resilience",
      "s1_paragraphs": "S1.36-37",
      "s1_description": "General resilience",
      "s1_pillar": "strategy"
    },
    {
      "s2_paragraphs": "S2.24-26",
      "s2_description": "Climate risk management",
      "s1_paragraphs": "S1.38-42",
      "s1_description": "General risk management",
      "s1_pillar": "risk_management"
    },
    {
      "s2_paragraphs": "S2.27-31",
      "s2_description": "GHG emissions metrics",
      "s1_paragraphs": "S1.43-53",
      "s1_description": "General metrics",
      "s1_pillar": "metrics_targets"
    },
    {
      "s2_paragraphs": "S2.33-36",
      "s2_description": "Climate targets",
      "s1_paragraphs": "S1.51-53",
      "s1_description": "General targets",
      "s1_pillar": "metrics_targets"
    }
  ]
}
```

This file is loaded during S2 corpus ingestion to enrich S2 chunk metadata with the `s1_counterpart` field. It is also consumed by the Legal Agent (FRD 6) and Source of Truth report (FRD 13).

### 8.4 SASB Standards (`data/sasb/`)

SASB industry standards shall be stored as markdown files, one per industry sector:

- `data/sasb/oil_and_gas.md`
- `data/sasb/banking_and_finance.md`
- `data/sasb/utilities.md`
- `data/sasb/transportation.md`
- `data/sasb/materials_and_mining.md`
- Additional sectors as relevant to sustainability report coverage

Each file shall be structured with H2 headings for disclosure topics and body text containing the metric definitions and guidance.

**Note on sourcing:** The exact IFRS and SASB text files must be assembled from publicly available standard summaries and guidance. The files should contain the disclosure requirements at a level of detail sufficient for the Legal Agent's compliance assessment. Full verbatim standard text is subject to licensing -- the implementation should use publicly available summaries, application guidance, and requirement checklists where full text is not available under IFRS Foundation terms.

---

## 9. Exit Criteria

FRD 1 is complete when ALL of the following are satisfied:

| # | Criterion | Verification |
|---|---|---|
| 1 | Embedding service produces 1536-dimensional vectors | Call `embed_text("test")` and verify output shape |
| 2 | Batch embedding handles multiple texts | Call `embed_batch(["text1", "text2", ..., "text20"])` and verify 20 vectors returned in order |
| 3 | IFRS S1 corpus is chunked and ingested | `RAGService.corpus_stats()` returns non-zero count for `ifrs_s1` |
| 4 | IFRS S2 corpus is chunked and ingested | `RAGService.corpus_stats()` returns non-zero count for `ifrs_s2` |
| 5 | SASB corpus is chunked and ingested | `RAGService.corpus_stats()` returns non-zero count for `sasb` |
| 6 | S2 chunks have S1 counterpart metadata | Query an S2 embedding and verify `chunk_metadata.s1_counterpart` is populated |
| 7 | Semantic search returns relevant results | Search for "transition plan" and verify S2.14-related chunks rank highly |
| 8 | Keyword search returns exact matches | Search for "S2.14(a)(iv)" and verify the exact paragraph is returned |
| 9 | Hybrid search combines both methods | Hybrid search for "Scope 3 emissions S2.29" returns results from both semantic and keyword paths |
| 10 | Paragraph ID lookup works | `RAGService.get_paragraph("S2.14(a)(iv)")` returns the correct chunk |
| 11 | Report ingestion method is callable | `RAGService.ingest_report(report_id, markdown, metadata)` succeeds (with test data) and creates embeddings with `source_type = "report"` |
| 12 | `rag_lookup` tool returns formatted results | Call the tool with a test query and verify the formatted output includes source metadata |
| 13 | `/api/v1/rag/stats` endpoint responds | `GET /api/v1/rag/stats` returns corpus counts |
| 14 | Idempotent ingestion | Running ingestion twice does not create duplicate embeddings |

---

## Appendix A: IFRS Chunk Metadata Schema

### A.1 IFRS S1 Chunk Metadata Example

```json
{
  "paragraph_id": "S1.27(a)(ii)",
  "standard": "S1",
  "pillar": "governance",
  "section": "Governance",
  "sub_requirements": ["S1.27(a)(ii)(1)", "S1.27(a)(ii)(2)"],
  "s1_counterpart": null
}
```

### A.2 IFRS S2 Chunk Metadata Example

```json
{
  "paragraph_id": "S2.14(a)(iv)",
  "standard": "S2",
  "pillar": "strategy",
  "section": "Decision-Making",
  "sub_requirements": [],
  "s1_counterpart": "S1.33"
}
```

### A.3 SASB Chunk Metadata Example

```json
{
  "industry_sector": "Oil & Gas",
  "disclosure_topic": "GHG Emissions",
  "metric_codes": ["EM-EP-110a.1", "EM-EP-110a.2", "EM-EP-110a.3"],
  "standard_code": "EM-EP"
}
```

### A.4 Report Chunk Metadata Example

```json
{
  "page_start": 42,
  "page_end": 43,
  "section_path": ["Environmental Performance", "GHG Emissions", "Scope 3"],
  "has_table": false,
  "chunk_index": 87
}
```

---

## Appendix B: Chunking Examples

### B.1 IFRS Paragraph Chunk

**Source text (from S2):**

```markdown
### S2.14 Strategy and Decision-Making

(a) An entity shall disclose information about how it has responded to, and
plans to respond to, climate-related risks and opportunities in its strategy
and decision-making, including:

(iv) its transition plan, including information about:
- key assumptions used in developing its transition plan;
- dependencies on which the entity's transition plan relies;
...
```

**Resulting chunk:**

```
[IFRS S2 > Strategy > Decision-Making > S2.14(a)(iv)]

An entity shall disclose its transition plan, including information about:
- key assumptions used in developing its transition plan;
- dependencies on which the entity's transition plan relies;
...
```

**Metadata:**

```json
{
  "paragraph_id": "S2.14(a)(iv)",
  "standard": "S2",
  "pillar": "strategy",
  "section": "Decision-Making",
  "sub_requirements": [],
  "s1_counterpart": "S1.33"
}
```

### B.2 Report Hierarchical Chunk

**Source text (page 45 of a sustainability report):**

```markdown
## Environmental Performance

### GHG Emissions

#### Scope 3

Our Scope 3 emissions totaled 12.4 million tonnes CO2e in FY2024,
representing a 3.2% decrease from the prior year. Category 11 (Use of
Sold Products) accounts for approximately 78% of our total Scope 3
footprint...
```

**Resulting chunk:**

```
[Report > Environmental Performance > GHG Emissions > Scope 3]

Our Scope 3 emissions totaled 12.4 million tonnes CO2e in FY2024,
representing a 3.2% decrease from the prior year. Category 11 (Use of
Sold Products) accounts for approximately 78% of our total Scope 3
footprint...
```

**Metadata:**

```json
{
  "page_start": 45,
  "page_end": 45,
  "section_path": ["Environmental Performance", "GHG Emissions", "Scope 3"],
  "has_table": false,
  "chunk_index": 87
}
```

---

## Appendix C: Hybrid Search Worked Example

**Query:** `"Scope 3 emissions disclosure requirements S2.29"`

**Step 1 -- Semantic search (top 5):**

| Rank | Chunk | Similarity |
|---|---|---|
| 1 | S2.29(a)(iii) -- Scope 3 GHG emissions by category | 0.91 |
| 2 | S2.29(a)(i) -- Scope 1 GHG emissions | 0.84 |
| 3 | S2.27 -- Metrics overview | 0.81 |
| 4 | S1.46 -- General metrics requirements | 0.78 |
| 5 | S2.33 -- Emissions targets | 0.75 |

**Step 2 -- Keyword search (top 5):**

| Rank | Chunk | FTS Rank |
|---|---|---|
| 1 | S2.29(a)(iii) -- Scope 3 GHG emissions by category | 0.42 |
| 2 | S2.29(a)(i) -- Scope 1 GHG emissions | 0.38 |
| 3 | S2.29(a)(ii) -- Scope 2 GHG emissions | 0.35 |
| 4 | S2.29(b) -- Physical risk exposure | 0.31 |
| 5 | S2.29(c) -- Transition risk exposure | 0.28 |

**Step 3 -- Re-ranking with RRF (k=60):**

| Chunk | Semantic Rank | Keyword Rank | RRF Score | Final Rank |
|---|---|---|---|---|
| S2.29(a)(iii) | 1 | 1 | 1/61 + 1/61 = 0.0328 | **1** |
| S2.29(a)(i) | 2 | 2 | 1/62 + 1/62 = 0.0323 | **2** |
| S2.29(a)(ii) | -- | 3 | 1/63 = 0.0159 | **3** |
| S2.27 | 3 | -- | 1/63 = 0.0159 | **4** |
| S2.29(b) | -- | 4 | 1/64 = 0.0156 | **5** |
| S1.46 | 4 | -- | 1/64 = 0.0156 | **6** |
| S2.33 | 5 | -- | 1/65 = 0.0154 | **7** |
| S2.29(c) | -- | 5 | 1/65 = 0.0154 | **8** |

The RRF re-ranking correctly places S2.29(a)(iii) (Scope 3 emissions) at #1, boosted by appearing in both result lists. Chunks appearing in only one list still surface but with lower re-ranked scores.

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| Reciprocal Rank Fusion (RRF) for re-ranking over linear score combination | Semantic scores (0-1 cosine similarity) and FTS ranks are on incomparable scales. RRF operates on ordinal ranks, making it robust without score normalization. Widely used in production IR systems for re-ranking multiple result lists. |
| Context header prepended to every chunk | Ensures the embedding captures hierarchical context (e.g., which pillar, which section). Without this, a generic paragraph about "governance oversight" might not embed near queries about S2.5-7 specifically. Also makes retrieved chunks self-contained for LLM consumption. |
| `text-embedding-3-small` over `text-embedding-3-large` | PRD specifies `text-embedding-3-small` for cost-effectiveness (~$0.02/M tokens). At the scale of this project (hundreds of chunks, not millions), the quality difference is negligible. |
| Paragraph-level chunking for IFRS over fixed-size chunking | IFRS paragraphs are the atomic unit of compliance assessment. The Legal Agent and Source of Truth report need to map claims to specific paragraphs. Fixed-size chunks would split across paragraph boundaries, breaking this mapping. |
| Hierarchical chunking with overlap for reports | Sustainability reports have natural section structure. Preserving headings as metadata enables section-scoped searches. Overlap prevents context loss at chunk boundaries. |
| Token estimation via `len(text)/4` heuristic over tokenizer library | Avoids adding a tokenizer dependency (tiktoken) just for batch sizing. The heuristic is sufficient for batching -- the API enforces exact limits. Keeps the dependency tree lean for hackathon scope. |
| `plainto_tsquery` as default over `to_tsquery` | `plainto_tsquery` handles natural language input without requiring boolean operators. Agents and the chatbot send natural language queries. `to_tsquery` is available for structured queries but not the default path. |
| Single `RAGService` class over separate ingestion/retrieval services | All RAG operations share the same database session and embedding service. A unified class simplifies dependency injection and avoids splitting related logic across files. |
| Idempotent static corpus ingestion | Prevents accidental duplicate embeddings if ingestion runs twice (e.g., backend restarts). Delete-then-ingest is explicit and intentional. |
| RAG endpoints under `/api/v1/rag/` prefix | Cleanly separates RAG operations from report/analysis endpoints. Debug/test endpoints are grouped together for easy discovery. |
| IFRS/SASB files as markdown over JSON or database seeds | Markdown preserves the natural structure of the standards (headings, paragraphs, lists). It is human-readable, easy to edit, and straightforward to parse. JSON would lose the narrative structure; database seeds would be harder to review and update. |
| Report ingestion as a method (not an endpoint) | Report ingestion is triggered by the PDF upload pipeline (FRD 2), not by a user-facing API call. Exposing it as a `RAGService` method makes it callable from within the backend without an HTTP round-trip. |
| `ts_content` generated at insert time | Ensures the TSVector is always in sync with the chunk text. Using a database trigger or column default would also work, but explicit generation in the application layer provides more control and visibility. |
