# Feature Requirements Document: FRD 0 -- Setup Document (v1.0)

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.3](../PRD.md) |
| **FRD Order** | [FRD Order](../FRD-order.md) |
| **PRD Sections** | 5.1 (Tech Stack), 5.3 (LangGraph State Machine Design), 6 (High-Level File Structure) |
| **Type** | Infrastructure scaffold (not a feature) |
| **Depends On** | -- (no prior FRDs) |
| **Delivers** | Project scaffolding, Docker, database, app shells, state schema |
| **Created** | 2026-02-08 |

---

## Summary

FRD 0 establishes the complete project foundation for Sibyl. It produces a working monorepo with a Dockerized backend (FastAPI), frontend (React + Vite), PostgreSQL 17 with pgvector, and Redis -- all orchestrated by Docker Compose. The backend scaffold includes application configuration, database connectivity via SQLAlchemy 2.1, Alembic migrations, all five core database models, the shared LangGraph `SibylState` Pydantic schema, and an OpenRouter API client wrapper. The frontend scaffold includes a Vite + React + TypeScript project initialized with shadcn/ui, TailwindCSS v4, a dark-mode-first theme matching the detective aesthetic, a layout shell with sidebar and header, and client-side routing for all planned pages. No feature logic is implemented -- FRD 0 produces the skeleton that all subsequent FRDs build upon.

---

## Given Context (Preconditions)

The following terms and context are presupposed throughout this document:

| Term | Definition |
|---|---|
| Monorepo | A single repository containing both `frontend/` and `backend/` directories at the project root |
| Docker Compose | Container orchestration tool that defines and runs multi-container applications via a single `docker-compose.yml` |
| pgvector | PostgreSQL extension enabling vector similarity search; used for RAG embeddings |
| FastAPI | Async Python web framework for the backend API server |
| SQLAlchemy 2.1 | Python ORM used for database models and queries |
| Alembic | Database migration tool for SQLAlchemy |
| Pydantic v2 | Data validation library used for request/response schemas and the LangGraph state |
| shadcn/ui | React component library built on Radix UI primitives, styled with TailwindCSS |
| TailwindCSS v4 | Utility-first CSS framework; v4 uses CSS-first configuration (no `tailwind.config.ts`) |
| React Flow | `@xyflow/react` -- node-based graph visualization library for the detective dashboard |
| OpenRouter | Unified LLM gateway providing access to Claude, Gemini, DeepSeek, and other models through a single API |
| LangGraph | Graph-based AI orchestration framework supporting cyclic workflows and shared state |
| SSE | Server-Sent Events -- unidirectional server-to-client streaming protocol |

---

## Executive Summary (Gherkin-Style)

```gherkin
Feature: Project Setup and Infrastructure

  Background:
    Given  Docker and Docker Compose are installed on the host machine
    And    no prior Sibyl code exists

  Scenario: Start all services
    When   the developer runs `docker-compose up`
    Then   PostgreSQL 17 with pgvector starts and is accessible
    And    Redis starts and is accessible
    And    the FastAPI backend starts and binds to port 8000
    And    the React frontend starts and binds to port 5173
    And    all services are networked and can communicate

  Scenario: Backend health check
    Given  all services are running
    When   a GET request is sent to /api/v1/health
    Then   the backend responds with 200 OK and a JSON body containing service status

  Scenario: Frontend layout shell
    Given  all services are running
    When   a user navigates to http://localhost:5173
    Then   the browser renders the AppShell with a sidebar, header, and main content area
    And    the theme is dark mode by default
    And    navigation links for Home, Analysis, and Report pages are visible
    And    clicking a navigation link routes to the correct page shell (no feature content yet)

  Scenario: Database models and migrations
    Given  PostgreSQL is running
    When   Alembic migrations run (automatically on backend startup)
    Then   all five tables are created: reports, claims, findings, verdicts, embeddings
    And    the pgvector extension is enabled
    And    the embeddings table has a vector column

  Scenario: Environment configuration
    Given  a developer clones the repository
    When   they copy .env.example to .env and fill in the OpenRouter API key
    Then   all services can read their configuration from environment variables
    And    no secrets are hardcoded in source code
```

---

## Table of Contents

1. [Docker Compose Infrastructure](#1-docker-compose-infrastructure)
2. [Backend Scaffold](#2-backend-scaffold)
3. [Database Models and Migrations](#3-database-models-and-migrations)
4. [LangGraph State Schema](#4-langgraph-state-schema)
5. [OpenRouter Client Wrapper](#5-openrouter-client-wrapper)
6. [Frontend Scaffold](#6-frontend-scaffold)
7. [Environment Configuration](#7-environment-configuration)
8. [Exit Criteria](#8-exit-criteria)
9. [Appendix A: Complete File Manifest](#appendix-a-complete-file-manifest)
10. [Appendix B: Database Schema Diagram](#appendix-b-database-schema-diagram)
11. [Appendix C: SibylState Full Schema](#appendix-c-sibylstate-full-schema)
12. [Design Decisions Log](#design-decisions-log)

---

## 1. Docker Compose Infrastructure

### 1.1 Services

Docker Compose orchestrates four services on a shared network:

| Service | Image / Build | Port | Purpose |
|---|---|---|---|
| `db` | `pgvector/pgvector:pg17` | 5432 | PostgreSQL 17 with pgvector extension pre-installed |
| `redis` | `redis:7-alpine` | 6379 | Task queue for background PDF pipeline processing |
| `backend` | Build from `backend/Dockerfile` | 8000 | FastAPI application server |
| `frontend` | Build from `frontend/Dockerfile` | 5173 | Vite dev server serving the React SPA |

### 1.2 Service Dependencies

```
frontend ──depends_on──► backend ──depends_on──► db
                                 ──depends_on──► redis
```

- `backend` waits for `db` and `redis` to be healthy before starting.
- `frontend` waits for `backend` to be healthy before starting.
- Health checks: `db` uses `pg_isready`, `redis` uses `redis-cli ping`, `backend` uses the `/api/v1/health` endpoint.

### 1.3 Volumes

| Volume | Mount | Purpose |
|---|---|---|
| `pgdata` | `/var/lib/postgresql/data` on `db` | Persist database data across container restarts |
| `./backend` | `/app` on `backend` | Live code reload during development |
| `./frontend` | `/app` on `frontend` | Live code reload with Vite HMR |

### 1.4 Network

All services join a single Docker bridge network (`sibyl-network`). Services reference each other by service name (e.g., the backend connects to PostgreSQL at `db:5432`).

### 1.5 PostgreSQL Configuration

The system shall:

1. Use the `pgvector/pgvector:pg17` image, which includes the pgvector extension pre-installed.
2. Create the default database `sibyl` on first run via the `POSTGRES_DB` environment variable.
3. Enable the pgvector extension via the initial Alembic migration (`CREATE EXTENSION IF NOT EXISTS vector`).
4. Set `POSTGRES_USER` and `POSTGRES_PASSWORD` from environment variables.

### 1.6 Redis Configuration

The system shall:

1. Use `redis:7-alpine` with no authentication for MVP (no password, no TLS).
2. Expose port 6379 within the Docker network.
3. Redis is used only as a task queue broker. No persistent data is stored in Redis.

---

## 2. Backend Scaffold

### 2.1 Dockerfile

The backend Dockerfile shall:

1. Use `python:3.12-slim` as the base image.
2. Install system dependencies required by `psycopg[binary]` and PyMuPDF.
3. Copy `requirements.txt` and install Python dependencies.
4. Copy the application code.
5. Expose port 8000.
6. Run the FastAPI application using `uvicorn` with `--reload` for development.

### 2.2 Application Shell

The FastAPI application entry point (`app/main.py`) shall:

1. Create the FastAPI application instance with title `"Sibyl API"`, version `"0.1.0"`, and a description.
2. Configure CORS middleware to allow the frontend origin (`http://localhost:5173`).
3. Include the API router with a `/api/v1` prefix.
4. Register a startup event that runs Alembic migrations programmatically (using `alembic upgrade head`).
5. Register a shutdown event that disposes of the database engine.

### 2.3 Configuration (`app/core/config.py`)

The system shall define a `Settings` class using Pydantic `BaseSettings` with the following fields:

| Setting | Type | Default | Source |
|---|---|---|---|
| `DATABASE_URL` | `str` | `postgresql+psycopg://sibyl:sibyl@db:5432/sibyl` | `DATABASE_URL` env var |
| `REDIS_URL` | `str` | `redis://redis:6379/0` | `REDIS_URL` env var |
| `OPENROUTER_API_KEY` | `str` | *(required, no default)* | `OPENROUTER_API_KEY` env var |
| `OPENROUTER_BASE_URL` | `str` | `https://openrouter.ai/api/v1` | `OPENROUTER_BASE_URL` env var |
| `CORS_ORIGINS` | `list[str]` | `["http://localhost:5173"]` | `CORS_ORIGINS` env var |
| `MAX_UPLOAD_SIZE_MB` | `int` | `50` | `MAX_UPLOAD_SIZE_MB` env var |
| `MAX_JUDGE_ITERATIONS` | `int` | `3` | `MAX_JUDGE_ITERATIONS` env var |

A singleton `settings` instance is created at module level and imported by other modules.

### 2.4 Database Engine (`app/core/database.py`)

The system shall:

1. Create an async SQLAlchemy engine using `create_async_engine` with the `DATABASE_URL`.
2. Create an `async_sessionmaker` for dependency injection.
3. Define a `Base` declarative base class for all ORM models.
4. Provide an async context manager / FastAPI dependency (`get_db`) that yields a database session and handles commit/rollback.

### 2.5 Dependencies (`app/core/dependencies.py`)

The system shall define shared FastAPI dependencies:

1. `get_db` -- yields an async SQLAlchemy session (from `database.py`).
2. `get_settings` -- returns the `Settings` singleton.

### 2.6 API Router and Health Check

The system shall:

1. Define a root API router in `app/api/routes/__init__.py` that aggregates all route modules.
2. Implement a health check endpoint:

```
GET /api/v1/health

Response 200:
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "0.1.0"
}
```

3. The health check shall verify database connectivity (execute a simple query) and Redis connectivity (execute a PING). If either fails, the corresponding field shows `"disconnected"` and the overall status shows `"degraded"`.

### 2.7 Route Module Stubs

The following route modules shall be created as empty stubs (routers with no endpoints) to establish the file structure for subsequent FRDs:

| Module | File | Future FRD |
|---|---|---|
| Upload | `app/api/routes/upload.py` | FRD 2 |
| Analysis | `app/api/routes/analysis.py` | FRD 5 |
| Stream | `app/api/routes/stream.py` | FRD 5 |
| Report | `app/api/routes/report.py` | FRD 13 |
| Chat | `app/api/routes/chat.py` | FRD 14 |

Each stub creates an `APIRouter` with the appropriate prefix and tags but registers no endpoints.

### 2.8 Requirements

The `requirements.txt` shall include the following core dependencies (pinned to major.minor versions):

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn[standard]` | ASGI server |
| `pydantic` | Data validation (v2) |
| `pydantic-settings` | Environment-based settings |
| `sqlalchemy[asyncio]` | ORM with async support (2.1) |
| `psycopg[binary]` | PostgreSQL async driver |
| `alembic` | Database migrations |
| `pgvector` | pgvector SQLAlchemy integration |
| `redis` | Redis client |
| `httpx` | Async HTTP client (for OpenRouter) |
| `langgraph` | AI orchestration framework |
| `langchain-core` | LangChain core abstractions |
| `pymupdf4llm` | PDF parsing (for future FRDs) |
| `pystac-client` | Satellite data access (for future FRDs) |

---

## 3. Database Models and Migrations

### 3.1 Model Overview

Five SQLAlchemy ORM models form the core data layer. All models inherit from `Base` and share common patterns:

- `id`: UUID primary key, server-default `gen_random_uuid()`
- `created_at`: Timestamp with timezone, server-default `now()`
- `updated_at`: Timestamp with timezone, server-default `now()`, updated on modification

### 3.2 Report Model (`app/models/report.py`)

Represents an uploaded sustainability report.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | PK, default `gen_random_uuid()` | Unique report identifier |
| `filename` | `String(255)` | NOT NULL | Original uploaded filename |
| `file_size_bytes` | `BigInteger` | NOT NULL | Size of the uploaded PDF in bytes |
| `page_count` | `Integer` | nullable | Number of pages detected during parsing |
| `status` | `String(50)` | NOT NULL, default `"uploaded"` | Processing status (see below) |
| `parsed_content` | `Text` | nullable | Full markdown text extracted by PyMuPDF4LLM |
| `pdf_binary` | `LargeBinary` | nullable | Original PDF file for rendering in the viewer |
| `content_structure` | `JSONB` | nullable | Extracted structure metadata (sections, table count) |
| `error_message` | `Text` | nullable | Error details if processing fails |
| `created_at` | `DateTime(tz)` | NOT NULL, default `now()` | Upload timestamp |
| `updated_at` | `DateTime(tz)` | NOT NULL, default `now()` | Last modification timestamp |

**Report status values:**

| Status | Meaning |
|---|---|
| `uploaded` | PDF received, not yet parsed |
| `parsing` | PyMuPDF4LLM extraction in progress |
| `parsed` | Content extracted, ready for analysis |
| `analyzing` | Agent pipeline running |
| `completed` | Full pipeline complete, Source of Truth available |
| `error` | Processing failed (see `error_message`) |

**Relationships:**
- `claims`: One-to-many with `Claim`
- `embeddings`: One-to-many with `Embedding`

### 3.3 Claim Model (`app/models/claim.py`)

Represents a verifiable sustainability claim extracted from a report.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | PK, default `gen_random_uuid()` | Unique claim identifier |
| `report_id` | `UUID` | FK → `reports.id`, NOT NULL | Parent report |
| `claim_text` | `Text` | NOT NULL | Full text of the extracted claim |
| `claim_type` | `String(50)` | NOT NULL | Category: `geographic`, `quantitative`, `legal_governance`, `strategic`, `environmental` |
| `source_page` | `Integer` | NOT NULL | Page number in the original PDF |
| `source_location` | `JSONB` | nullable | Positional data for PDF highlighting (bounding box coordinates) |
| `ifrs_paragraphs` | `JSONB` | nullable | Preliminary IFRS S1/S2 paragraph mapping (array of paragraph identifiers) |
| `priority` | `String(20)` | NOT NULL, default `"medium"` | `high`, `medium`, `low` |
| `agent_reasoning` | `Text` | nullable | Claims Agent's reasoning for flagging this claim |
| `created_at` | `DateTime(tz)` | NOT NULL, default `now()` | Creation timestamp |
| `updated_at` | `DateTime(tz)` | NOT NULL, default `now()` | Last modification timestamp |

**Claim type enum values:**

| Value | PRD Mapping |
|---|---|
| `geographic` | Facility locations, land use, deforestation, water usage |
| `quantitative` | Emission figures, percentage targets, financial impacts, Scope 1/2/3 |
| `legal_governance` | Board oversight, committee responsibilities, compliance assertions |
| `strategic` | Transition plans, future targets, investment commitments |
| `environmental` | Biodiversity, waste management, resource efficiency, renewables |

**Relationships:**
- `report`: Many-to-one with `Report`
- `findings`: One-to-many with `Finding`
- `verdict`: One-to-one with `Verdict`

**Indexes:**
- Index on `report_id`
- Index on `claim_type`

### 3.4 Finding Model (`app/models/finding.py`)

Represents evidence gathered by a specialist agent during claim investigation.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | PK, default `gen_random_uuid()` | Unique finding identifier |
| `claim_id` | `UUID` | FK → `claims.id`, NOT NULL | Claim being investigated |
| `agent_name` | `String(50)` | NOT NULL | Agent that produced this finding: `geography`, `legal`, `news_media`, `academic`, `data_metrics` |
| `evidence_type` | `String(50)` | NOT NULL | Type of evidence: `satellite_imagery`, `legal_analysis`, `news_article`, `academic_paper`, `quantitative_check`, `benchmark_comparison` |
| `summary` | `Text` | NOT NULL | Plain-language summary of the finding |
| `details` | `JSONB` | nullable | Structured evidence details (agent-specific: source URLs, image refs, calculations, etc.) |
| `supports_claim` | `Boolean` | nullable | `true` = supports, `false` = contradicts, `null` = neutral/informational |
| `confidence` | `String(20)` | nullable | Agent's confidence: `high`, `medium`, `low` |
| `iteration` | `Integer` | NOT NULL, default `1` | Which investigation cycle produced this finding (1 = first pass, 2+ = re-investigation) |
| `created_at` | `DateTime(tz)` | NOT NULL, default `now()` | Creation timestamp |

**Relationships:**
- `claim`: Many-to-one with `Claim`

**Indexes:**
- Index on `claim_id`
- Index on `agent_name`
- Composite index on `(claim_id, agent_name)`

### 3.5 Verdict Model (`app/models/verdict.py`)

Represents the Judge Agent's final verdict on a claim.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | PK, default `gen_random_uuid()` | Unique verdict identifier |
| `claim_id` | `UUID` | FK → `claims.id`, UNIQUE, NOT NULL | One verdict per claim |
| `verdict` | `String(30)` | NOT NULL | `verified`, `unverified`, `contradicted`, `insufficient_evidence` |
| `reasoning` | `Text` | NOT NULL | Judge's full reasoning for the verdict |
| `ifrs_mapping` | `JSONB` | NOT NULL | Final paragraph-level IFRS mapping (array of objects with paragraph ID and compliance status) |
| `evidence_summary` | `JSONB` | nullable | Summary of evidence considered (which agents, finding counts, key factors) |
| `iteration_count` | `Integer` | NOT NULL, default `1` | Number of investigation cycles completed |
| `created_at` | `DateTime(tz)` | NOT NULL, default `now()` | Creation timestamp |

**Verdict enum values:**

| Value | Meaning (from PRD 4.9) |
|---|---|
| `verified` | Multiple independent sources corroborate; no contradictions |
| `unverified` | No external evidence found to support or contradict |
| `contradicted` | Evidence from one or more sources directly contradicts |
| `insufficient_evidence` | Some evidence exists but not enough for confident verdict |

**Relationships:**
- `claim`: One-to-one with `Claim`

**Indexes:**
- Unique index on `claim_id`

### 3.6 Embedding Model (`app/models/embedding.py`)

Represents a text chunk with its vector embedding for RAG retrieval.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | PK, default `gen_random_uuid()` | Unique embedding identifier |
| `report_id` | `UUID` | FK → `reports.id`, nullable | Parent report (null for IFRS/SASB standard text) |
| `source_type` | `String(30)` | NOT NULL | `report`, `ifrs_s1`, `ifrs_s2`, `sasb` |
| `chunk_text` | `Text` | NOT NULL | The source text content of this chunk |
| `chunk_metadata` | `JSONB` | nullable | Metadata: page number, section header, paragraph ID, document type, pillar |
| `embedding` | `Vector(1536)` | NOT NULL | 1536-dimensional vector from `text-embedding-3-small` |
| `ts_content` | `TSVector` | nullable | Full-text search index generated from `chunk_text` |
| `created_at` | `DateTime(tz)` | NOT NULL, default `now()` | Creation timestamp |

**Source type values:**

| Value | Description |
|---|---|
| `report` | Chunk from an uploaded sustainability report |
| `ifrs_s1` | Chunk from the IFRS S1 standard text |
| `ifrs_s2` | Chunk from the IFRS S2 standard text |
| `sasb` | Chunk from SASB industry standards |

**Relationships:**
- `report`: Many-to-one with `Report` (nullable for standard text)

**Indexes:**
- HNSW index on `embedding` column for approximate nearest-neighbor search (using pgvector `vector_cosine_ops`)
- GIN index on `ts_content` for full-text search
- Index on `report_id`
- Index on `source_type`

### 3.7 Initial Alembic Migration

The initial migration shall:

1. Enable the `vector` extension: `CREATE EXTENSION IF NOT EXISTS vector`
2. Enable the `uuid-ossp` extension: `CREATE EXTENSION IF NOT EXISTS "uuid-ossp"` (for `gen_random_uuid()`)
3. Create all five tables with the columns, constraints, and indexes defined above
4. The migration must be idempotent (safe to run multiple times)

### 3.8 Alembic Configuration

The system shall:

1. Configure Alembic in `alembic.ini` with the database URL sourced from the `DATABASE_URL` environment variable.
2. Configure `alembic/env.py` to use the async engine and import all models so autogenerate works correctly.
3. Store migration files in `alembic/versions/`.

---

## 4. LangGraph State Schema

### 4.1 Overview

The `SibylState` Pydantic model is the single shared state object for the entire LangGraph pipeline. It is defined in `app/agents/state.py` and referenced by all agent nodes. FRD 0 defines the schema only -- agent node implementations are deferred to subsequent FRDs.

### 4.2 Supporting Types

The following Pydantic models compose into `SibylState`:

```python
class DocumentChunk(BaseModel):
    """A chunk of parsed document content."""
    chunk_id: str
    text: str
    page_number: int | None = None
    section_header: str | None = None
    metadata: dict = {}

class Claim(BaseModel):
    """A verifiable sustainability claim extracted from the report."""
    claim_id: str
    text: str
    page_number: int
    claim_type: str          # geographic | quantitative | legal_governance | strategic | environmental
    ifrs_paragraphs: list[str] = []
    priority: str = "medium"  # high | medium | low
    source_location: dict | None = None
    agent_reasoning: str | None = None

class RoutingAssignment(BaseModel):
    """Maps a claim to one or more specialist agents."""
    claim_id: str
    assigned_agents: list[str]   # agent names
    reasoning: str | None = None

class AgentStatus(BaseModel):
    """Current status of a specialist agent."""
    agent_name: str
    status: str = "idle"  # idle | working | completed | error
    claims_assigned: int = 0
    claims_completed: int = 0
    error_message: str | None = None

class AgentFinding(BaseModel):
    """Evidence gathered by a specialist agent."""
    finding_id: str
    agent_name: str
    claim_id: str
    evidence_type: str
    summary: str
    details: dict = {}
    supports_claim: bool | None = None
    confidence: str | None = None  # high | medium | low
    iteration: int = 1

class InfoRequest(BaseModel):
    """Cross-domain information request from one agent."""
    request_id: str
    requesting_agent: str
    description: str
    context: dict = {}
    status: str = "pending"  # pending | routed | responded

class InfoResponse(BaseModel):
    """Response to a cross-domain information request."""
    request_id: str
    responding_agent: str
    response: str
    details: dict = {}

class ClaimVerdict(BaseModel):
    """Judge Agent's final verdict on a claim."""
    claim_id: str
    verdict: str           # verified | unverified | contradicted | insufficient_evidence
    reasoning: str
    ifrs_mapping: list[dict]  # [{paragraph: "S2.14(a)(iv)", status: "compliant"}]
    evidence_summary: dict = {}
    iteration_count: int = 1

class ReinvestigationRequest(BaseModel):
    """Judge Agent's request for deeper investigation."""
    claim_id: str
    target_agents: list[str]
    evidence_gap: str
    refined_queries: list[str] = []
    required_evidence: str | None = None

class StreamEvent(BaseModel):
    """Event emitted to the frontend via SSE."""
    event_type: str        # agent_started | agent_thinking | agent_completed | claim_routed |
                           # evidence_found | verdict_issued | reinvestigation | pipeline_completed | error
    agent_name: str | None = None
    data: dict = {}
    timestamp: str         # ISO 8601
```

### 4.3 SibylState Schema

```python
class SibylState(BaseModel):
    """Shared state for the entire LangGraph pipeline."""

    # --- Input ---
    report_id: str
    document_content: str = ""
    document_chunks: list[DocumentChunk] = []

    # --- Claims Agent output ---
    claims: list[Claim] = []

    # --- Orchestrator tracking ---
    routing_plan: list[RoutingAssignment] = []
    agent_status: dict[str, AgentStatus] = {}

    # --- Specialist agent findings ---
    findings: list[AgentFinding] = []

    # --- Inter-agent communication ---
    info_requests: list[InfoRequest] = []
    info_responses: list[InfoResponse] = []

    # --- Judge Agent ---
    verdicts: list[ClaimVerdict] = []
    reinvestigation_requests: list[ReinvestigationRequest] = []
    iteration_count: int = 0
    max_iterations: int = 3

    # --- Disclosure gaps (Legal Agent) ---
    disclosure_gaps: list[dict] = []

    # --- Streaming ---
    events: list[StreamEvent] = []
```

### 4.4 Graph Definition Stub (`app/agents/graph.py`)

The system shall create a stub LangGraph `StateGraph` definition that:

1. Imports `SibylState` as the state schema.
2. Defines placeholder node names (no implementations): `parse_document`, `extract_claims`, `orchestrate`, `investigate_geography`, `investigate_legal`, `investigate_news`, `investigate_academic`, `investigate_data`, `judge_evidence`, `compile_report`.
3. Does NOT compile or execute the graph -- subsequent FRDs implement nodes and edges.
4. Includes a comment block mapping each node name to its implementing FRD.

### 4.5 Agent Node Stubs

The following stub files shall be created under `app/agents/`, each containing only docstrings and function signatures (no implementation logic):

| File | Node Function | FRD |
|---|---|---|
| `claims_agent.py` | `extract_claims(state: SibylState) -> dict` | FRD 3 |
| `orchestrator_agent.py` | `orchestrate(state: SibylState) -> dict` | FRD 5 |
| `geography_agent.py` | `investigate_geography(state: SibylState) -> dict` | FRD 10 |
| `legal_agent.py` | `investigate_legal(state: SibylState) -> dict` | FRD 6 |
| `news_media_agent.py` | `investigate_news(state: SibylState) -> dict` | FRD 8 |
| `academic_agent.py` | `investigate_academic(state: SibylState) -> dict` | FRD 9 |
| `data_metrics_agent.py` | `investigate_data(state: SibylState) -> dict` | FRD 7 |
| `judge_agent.py` | `judge_evidence(state: SibylState) -> dict` | FRD 11 |

---

## 5. OpenRouter Client Wrapper

### 5.1 Purpose

The OpenRouter client (`app/services/openrouter_client.py`) provides a unified interface for all LLM calls in Sibyl. All agents use this single client to communicate with LLMs through the OpenRouter gateway.

### 5.2 Functional Requirements

The system shall:

1. Initialize an async HTTP client (`httpx.AsyncClient`) with the OpenRouter base URL and API key from settings.
2. Provide a `chat_completion` method accepting:
   - `model: str` -- the OpenRouter model identifier (e.g., `"anthropic/claude-sonnet-4-5"`)
   - `messages: list[dict]` -- chat messages in OpenAI-compatible format
   - `temperature: float` -- defaults to `0.0`
   - `max_tokens: int | None` -- optional max output tokens
   - `response_format: dict | None` -- optional structured output format
3. Implement retry logic: 3 retries with exponential backoff (1s, 2s, 4s) for transient failures (HTTP 429, 500, 502, 503, 504).
4. Return the response content as a string, or raise a descriptive exception on non-transient failure.
5. Include request headers: `Authorization: Bearer {api_key}`, `Content-Type: application/json`, `HTTP-Referer: https://sibyl.dev` (required by OpenRouter), `X-Title: Sibyl`.
6. Log all requests (model, token counts) and errors for debugging.

### 5.3 Model Constants

The system shall define model identifier constants:

```python
class Models:
    GEMINI_FLASH = "google/gemini-2.5-flash-preview"
    GEMINI_PRO = "google/gemini-2.5-pro-preview"
    CLAUDE_SONNET = "anthropic/claude-sonnet-4-5"
    CLAUDE_OPUS = "anthropic/claude-opus-4-5"
    DEEPSEEK = "deepseek/deepseek-chat"
    EMBEDDING = "openai/text-embedding-3-small"
```

Note: Exact model identifiers should be verified against the OpenRouter API at implementation time.

---

## 6. Frontend Scaffold

### 6.1 Project Initialization

The system shall:

1. Initialize a Vite + React + TypeScript project in the `frontend/` directory.
2. Configure TypeScript with strict mode enabled.
3. Install and configure shadcn/ui (following the shadcn/ui CLI initialization for Vite).
4. Install TailwindCSS v4 using the CSS-first configuration approach (no `tailwind.config.ts` file; all configuration via CSS `@theme` directives).
5. Install React Router for client-side routing.
6. Install `@xyflow/react` (React Flow) as a dependency (used in FRD 12, but installed now to validate the dependency tree).
7. Install `@pdf-viewer/react` as a dependency (used in FRD 4, but installed now to validate the dependency tree).

### 6.2 Dockerfile

The frontend Dockerfile shall:

1. Use `node:20-alpine` as the base image.
2. Copy `package.json` and `package-lock.json`, then run `npm install`.
3. Copy the application source code.
4. Expose port 5173.
5. Run the Vite dev server with `--host 0.0.0.0` so it is accessible from outside the container.

### 6.3 Dark-Mode Theme

The system shall configure a dark-mode-first theme matching the detective/investigation aesthetic described in PRD 7.1:

| Design Token | Value | Description |
|---|---|---|
| Background (primary) | Deep charcoal (`hsl(224, 20%, 10%)` or similar) | Main app background |
| Background (secondary) | Slightly lighter charcoal | Card/panel backgrounds |
| Foreground | High-contrast off-white | Primary text |
| Muted foreground | Medium grey | Secondary/metadata text |
| Border | Dark grey | Subtle borders and dividers |
| Accent (primary) | Slate blue | Primary interactive elements |
| Accent (destructive) | Crimson red | Error states, Judge agent |

**Agent color identity** (defined as CSS custom properties for consistent use across dashboard and report):

| Agent | CSS Variable | Color |
|---|---|---|
| Claims Agent | `--agent-claims` | Slate blue |
| Orchestrator | `--agent-orchestrator` | White/silver |
| Geography Agent | `--agent-geography` | Forest green |
| Legal Agent | `--agent-legal` | Deep purple |
| News/Media Agent | `--agent-news` | Amber/gold |
| Academic/Research Agent | `--agent-academic` | Teal |
| Data/Metrics Agent | `--agent-data` | Coral/orange |
| Judge Agent | `--agent-judge` | Crimson red |

### 6.4 Layout Shell

The layout shell consists of three components that wrap all page content:

**AppShell (`src/components/Layout/AppShell.tsx`)**

The root layout component. It shall:

1. Render the `Sidebar` on the left and `Header` at the top.
2. Render the active page content in a main content area that fills the remaining viewport.
3. Use a CSS Grid or Flexbox layout.
4. Apply the dark theme globally.

**Sidebar (`src/components/Layout/Sidebar.tsx`)**

The navigation sidebar. It shall:

1. Display the Sibyl project name/logo at the top.
2. Render navigation links for three pages:
   - **Home** (`/`) -- Upload landing page
   - **Analysis** (`/analysis`) -- 3-panel analysis view (detective dashboard)
   - **Report** (`/report`) -- Source of Truth report view
3. Highlight the currently active route.
4. Be collapsible (toggle between icon-only and full-width modes).

**Header (`src/components/Layout/Header.tsx`)**

The top header bar. It shall:

1. Display the current page title (derived from the active route).
2. Reserve space on the right for a future chatbot toggle button (FRD 14).

### 6.5 Client-Side Routing

The system shall configure React Router with the following routes:

| Path | Page Component | Description |
|---|---|---|
| `/` | `HomePage` | Upload landing page |
| `/analysis` | `AnalysisPage` | 3-panel analysis view |
| `/analysis/:reportId` | `AnalysisPage` | Analysis for a specific report |
| `/report` | `ReportPage` | Source of Truth report view |
| `/report/:reportId` | `ReportPage` | Report for a specific report |

Each page component is a stub that renders the page title and a placeholder message (e.g., "Upload page coming in FRD 2").

### 6.6 Page Stubs

The following page components shall be created in `src/pages/`:

| Component | File | Content |
|---|---|---|
| `HomePage` | `src/pages/HomePage.tsx` | Renders a centered placeholder with the text "Sibyl -- Upload a sustainability report to begin analysis" |
| `AnalysisPage` | `src/pages/AnalysisPage.tsx` | Renders a 3-panel layout placeholder (left, center, right panels with labels) |
| `ReportPage` | `src/pages/ReportPage.tsx` | Renders a full-width placeholder with the text "Source of Truth report will appear here" |

### 6.7 Component Directory Structure

The following component directories shall be created with empty `index.ts` barrel files (no component implementations):

- `src/components/Dashboard/`
- `src/components/PDFViewer/`
- `src/components/SourceOfTruth/`
- `src/components/Chatbot/`
- `src/components/Upload/`

### 6.8 Type Definitions

The following TypeScript type definition files shall be created in `src/types/` with the type definitions matching the backend schemas:

| File | Types |
|---|---|
| `claim.ts` | `Claim`, `ClaimType`, `ClaimVerdict`, `ClaimPriority` |
| `agent.ts` | `AgentName`, `AgentStatus`, `AgentFinding`, `InfoRequest`, `InfoResponse` |
| `ifrs.ts` | `IFRSPillar`, `IFRSParagraph`, `DisclosureGap`, `ComplianceStatus` |
| `report.ts` | `Report`, `ReportStatus`, `SourceOfTruthReport` |

These types mirror the backend Pydantic schemas and database models to maintain type safety across the stack.

### 6.9 API Client Stub

The system shall create `src/services/api.ts` with:

1. A base URL constant pointing to the backend API (`http://localhost:8000/api/v1`).
2. A configured `fetch` wrapper or axios instance with default headers.
3. A `healthCheck()` function that calls `GET /api/v1/health` and returns the response.
4. Stub functions (returning `TODO` comments) for future endpoints: `uploadReport()`, `getAnalysisStatus()`, `getReport()`, `sendChatMessage()`.

---

## 7. Environment Configuration

### 7.1 `.env.example`

The system shall provide a `.env.example` file at the project root with all required environment variables:

```env
# === Database ===
POSTGRES_USER=sibyl
POSTGRES_PASSWORD=sibyl
POSTGRES_DB=sibyl
DATABASE_URL=postgresql+psycopg://sibyl:sibyl@db:5432/sibyl

# === Redis ===
REDIS_URL=redis://redis:6379/0

# === OpenRouter ===
OPENROUTER_API_KEY=your-openrouter-api-key-here

# === Application ===
CORS_ORIGINS=["http://localhost:5173"]
MAX_UPLOAD_SIZE_MB=50
MAX_JUDGE_ITERATIONS=3
```

### 7.2 `.gitignore`

The `.gitignore` shall exclude:

- `.env` (but NOT `.env.example`)
- `__pycache__/`, `*.pyc`
- `node_modules/`
- `dist/`, `build/`
- `.vite/`
- `pgdata/` (Docker volume data)
- IDE files (`.vscode/`, `.idea/`)

---

## 8. Exit Criteria

FRD 0 is complete when ALL of the following are satisfied:

| # | Criterion | Verification |
|---|---|---|
| 1 | `docker-compose up` starts all four services without errors | Run `docker-compose up` and observe all containers reach healthy state |
| 2 | PostgreSQL is accessible and pgvector is enabled | Connect to db and run `SELECT * FROM pg_extension WHERE extname = 'vector'` |
| 3 | Redis is accessible | Run `redis-cli ping` and receive `PONG` |
| 4 | Backend health check responds | `curl http://localhost:8000/api/v1/health` returns 200 with `{"status": "healthy", ...}` |
| 5 | All five database tables exist | Run Alembic migration check; inspect tables in PostgreSQL |
| 6 | Frontend renders the layout shell | Navigate to `http://localhost:5173` and see the AppShell with sidebar, header, and placeholder content |
| 7 | Client-side routing works | Click sidebar links and observe URL changes and page stub content |
| 8 | Dark mode theme is applied | Visual inspection: deep charcoal background, high-contrast text |
| 9 | `SibylState` schema is importable | `from app.agents.state import SibylState` succeeds in a Python shell |
| 10 | OpenRouter client is importable | `from app.services.openrouter_client import OpenRouterClient` succeeds |

---

## Appendix A: Complete File Manifest

```
sibyl/
    docker-compose.yml
    .env.example
    .gitignore
    README.md

    backend/
        Dockerfile
        requirements.txt
        alembic.ini
        alembic/
            env.py
            versions/
                001_initial_schema.py
        app/
            __init__.py
            main.py
            api/
                __init__.py
                routes/
                    __init__.py          # Root router aggregating all route modules
                    health.py            # GET /api/v1/health
                    upload.py            # Stub
                    analysis.py          # Stub
                    stream.py            # Stub
                    report.py            # Stub
                    chat.py              # Stub
            agents/
                __init__.py
                state.py                 # SibylState + all supporting Pydantic models
                graph.py                 # LangGraph StateGraph stub
                claims_agent.py          # Stub
                orchestrator_agent.py    # Stub
                geography_agent.py       # Stub
                legal_agent.py           # Stub
                news_media_agent.py      # Stub
                academic_agent.py        # Stub
                data_metrics_agent.py    # Stub
                judge_agent.py           # Stub
                tools/
                    __init__.py
                    search_web.py        # Stub
                    query_mpc.py         # Stub
                    rag_lookup.py        # Stub
            services/
                __init__.py
                openrouter_client.py     # OpenRouter API wrapper
                pdf_parser.py            # Stub
                rag_service.py           # Stub
                satellite_service.py     # Stub
                report_compiler.py       # Stub
            models/
                __init__.py
                report.py
                claim.py
                finding.py
                verdict.py
                embedding.py
            schemas/
                __init__.py
                upload.py                # Stub
                analysis.py              # Stub
                report.py                # Stub
                chat.py                  # Stub
            core/
                __init__.py
                config.py
                database.py
                dependencies.py
        data/
            ifrs/                        # Empty dir; populated in FRD 1
            sasb/                        # Empty dir; populated in FRD 1

    frontend/
        Dockerfile
        package.json
        tsconfig.json
        vite.config.ts
        index.html
        src/
            App.tsx
            main.tsx
            app.css                      # TailwindCSS v4 entry with @theme config
            components/
                Layout/
                    AppShell.tsx
                    Sidebar.tsx
                    Header.tsx
                Dashboard/
                    index.ts             # Empty barrel
                PDFViewer/
                    index.ts             # Empty barrel
                SourceOfTruth/
                    index.ts             # Empty barrel
                Chatbot/
                    index.ts             # Empty barrel
                Upload/
                    index.ts             # Empty barrel
            hooks/
                index.ts                 # Empty barrel
            services/
                api.ts
            types/
                claim.ts
                agent.ts
                ifrs.ts
                report.ts
            pages/
                HomePage.tsx
                AnalysisPage.tsx
                ReportPage.tsx
```

---

## Appendix B: Database Schema Diagram

```
┌─────────────────────────┐
│        reports           │
├─────────────────────────┤
│ id           UUID    PK │
│ filename     VARCHAR    │
│ file_size    BIGINT     │
│ page_count   INT        │
│ status       VARCHAR    │
│ parsed_content TEXT     │
│ pdf_binary   BYTEA      │
│ content_structure JSONB │
│ error_message TEXT      │
│ created_at   TIMESTAMPTZ│
│ updated_at   TIMESTAMPTZ│
└────────┬────────────────┘
         │ 1
         │
         ├──────────────────────────┐
         │ *                        │ *
┌────────▼────────────────┐ ┌──────▼──────────────────┐
│        claims            │ │      embeddings          │
├─────────────────────────┤ ├─────────────────────────┤
│ id           UUID    PK │ │ id           UUID    PK │
│ report_id    UUID    FK │ │ report_id    UUID FK(N) │
│ claim_text   TEXT       │ │ source_type  VARCHAR    │
│ claim_type   VARCHAR    │ │ chunk_text   TEXT       │
│ source_page  INT        │ │ chunk_metadata JSONB   │
│ source_location JSONB   │ │ embedding    VECTOR    │
│ ifrs_paragraphs JSONB   │ │ ts_content   TSVECTOR  │
│ priority     VARCHAR    │ │ created_at   TIMESTAMPTZ│
│ agent_reasoning TEXT    │ └─────────────────────────┘
│ created_at   TIMESTAMPTZ│
│ updated_at   TIMESTAMPTZ│
└────────┬───────┬────────┘
         │ 1     │ 1
         │       │
         │ *     │ 0..1
┌────────▼───────┐ ┌──────▼──────────────────┐
│    findings     │ │       verdicts           │
├────────────────┤ ├─────────────────────────┤
│ id       UUID PK│ │ id           UUID    PK │
│ claim_id UUID FK│ │ claim_id     UUID FK UQ │
│ agent_name VARCHAR│ │ verdict      VARCHAR    │
│ evidence_type VARCHAR│ │ reasoning    TEXT       │
│ summary    TEXT  │ │ ifrs_mapping JSONB     │
│ details    JSONB │ │ evidence_summary JSONB │
│ supports   BOOL  │ │ iteration_count INT    │
│ confidence VARCHAR│ │ created_at   TIMESTAMPTZ│
│ iteration  INT   │ └─────────────────────────┘
│ created_at TIMESTAMPTZ│
└──────────────────┘
```

---

## Appendix C: SibylState Full Schema

See [Section 4](#4-langgraph-state-schema) for the complete field-by-field definition.

The state follows LangGraph conventions:
- All fields have defaults so the state can be initialized incrementally.
- Agent nodes return partial state updates (dicts) that are merged into the full state by LangGraph.
- The `events` list is append-only and streamed to the frontend via SSE.
- The `iteration_count` is incremented by the Judge Agent each cycle and checked against `max_iterations` by the conditional edge.

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| `pgvector/pgvector:pg17` Docker image over manual extension install | Guarantees pgvector is available without custom Dockerfile; matches PRD spec for PostgreSQL 17 |
| Async SQLAlchemy (`create_async_engine`) over sync | FastAPI is async; async DB access prevents blocking the event loop during I/O-heavy agent operations |
| `psycopg[binary]` over `asyncpg` | psycopg3 (binary) is the recommended async driver for SQLAlchemy 2.x; supports both sync and async |
| Alembic migrations run on backend startup | Ensures database schema is always current in development; avoids manual migration steps for hackathon workflow |
| Single `SibylState` Pydantic model over multiple state objects | LangGraph requires a single state schema; all agent nodes operate on the same state; matches PRD Section 5.3 |
| HNSW index for vector search over IVFFlat | HNSW provides better recall at the scale of a hackathon project (hundreds of documents, not millions) |
| Frontend stubs render placeholder text | Validates routing and layout without implementing feature logic; subsequent FRDs replace placeholders |
| Agent color identity as CSS custom properties | Enables consistent agent theming across dashboard, report, and evidence panels; easy to reference in components |
| `httpx.AsyncClient` for OpenRouter over `requests` | Async-native; supports connection pooling; consistent with FastAPI's async architecture |
| TailwindCSS v4 CSS-first config over v3 JS config | PRD specifies TailwindCSS v4; v4 uses CSS `@theme` directives, eliminating `tailwind.config.ts` |
| All dependencies installed in FRD 0 (including future ones like PyMuPDF4LLM, pystac-client) | Validates the full dependency tree early; prevents incompatibility surprises in later FRDs |
| Route module stubs with empty routers | Establishes file structure and import patterns; subsequent FRDs add endpoints without restructuring |
| `Vector(1536)` dimension for embeddings | Matches `text-embedding-3-small` output dimensions (1536) as specified in PRD Section 5.5 |
| UUID primary keys with `gen_random_uuid()` | Database-generated UUIDs; no application-level UUID generation needed; globally unique across tables |
| JSONB for flexible metadata columns | Allows agent-specific data structures (satellite image refs, source URLs, calculations) without schema changes |
