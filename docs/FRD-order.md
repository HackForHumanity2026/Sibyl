# Sibyl -- Feature Requirements Document Order

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.3](./PRD.md) |
| **Created** | 2026-02-08 |
| **Purpose** | Define the ordered sequence of FRDs for incremental implementation |

---

## Overview

Each FRD represents a single unit of full functionality that can be implemented, tested, and delivered independently. FRDs are ordered by dependency -- each assumes all prior FRDs are complete. A Setup Document (FRD 0) establishes the project foundation before any feature work begins.

### Ordering Principles

1. **Infrastructure before consumers** -- RAG before agents that query it; SSE before the dashboard that displays it.
2. **Data producers before data consumers** -- Claims Agent before PDF highlights; all specialist agents before the Judge; Judge before Source of Truth.
3. **Complexity deferred where possible** -- The Geography Agent (satellite API + vision model) is last among specialists; the Chatbot is last overall since it has no downstream dependents.

---

## Implementation Order

| # | FRD | PRD Section(s) | Depends On | Delivers |
|---|---|---|---|---|
| 0 | [Setup Document](#frd-0-setup-document) | 5.1, 5.3, 6 | -- | Project scaffolding, Docker, DB, app shells, state schema |
| 1 | [RAG Pipeline](#frd-1-rag-pipeline) | 5.5 | FRD 0 | Embedding, chunking, hybrid retrieval, IFRS/SASB corpus |
| 2 | [PDF Upload & Ingestion](#frd-2-pdf-upload--ingestion) | 4.1 | FRD 0, 1 | Upload UI, PDF parsing, content storage |
| 3 | [Claims Agent](#frd-3-claims-agent) | 4.2 | FRD 0, 1, 2 | Claim extraction and categorization |
| 4 | [PDF Viewer with Claim Highlights](#frd-4-pdf-viewer-with-claim-highlights) | 4.1, 4.2, 7.2 | FRD 2, 3 | Interactive PDF with clickable claim overlays |
| 5 | [Orchestrator Agent & LangGraph Pipeline](#frd-5-orchestrator-agent--langgraph-pipeline) | 4.3, 5.3, 5.4 | FRD 0, 3 | Pipeline graph, routing, SSE streaming, inter-agent protocol |
| 6 | [Legal Agent](#frd-6-legal-agent) | 4.5 | FRD 1, 5 | IFRS compliance mapping, disclosure gap detection |
| 7 | [Data/Metrics Agent](#frd-7-datametrics-agent) | 4.8 | FRD 5 | Quantitative validation and consistency checks |
| 8 | [News/Media Agent](#frd-8-newsmedia-agent) | 4.6 | FRD 5 | Public source verification with credibility tiering |
| 9 | [Academic/Research Agent](#frd-9-academicresearch-agent) | 4.7 | FRD 5, 8 | Technical validation against literature and benchmarks |
| 10 | [Geography Agent](#frd-10-geography-agent) | 4.4 | FRD 5 | Satellite imagery verification via MPC |
| 11 | [Judge Agent & Cyclic Validation](#frd-11-judge-agent--cyclic-validation) | 4.9 | FRD 5, 6-10 | Evidence evaluation, re-investigation loops, final verdicts |
| 12 | [Detective Dashboard](#frd-12-detective-dashboard) | 4.10, 7.2 | FRD 5, 6-11 | Real-time React Flow network graph visualization |
| 13 | [Source of Truth Report](#frd-13-source-of-truth-report) | 4.11, 7.2 | FRD 6, 11 | Interactive IFRS compliance report with disclosure gaps |
| 14 | [Chatbot](#frd-14-chatbot) | 4.12, 7.2 | FRD 1, 11, 13 | RAG-powered conversational Q&A |

---

## FRD Descriptions

### FRD 0: Setup Document

**Type:** Infrastructure scaffold (not a feature)

**Scope:**

- Docker Compose configuration (PostgreSQL 17 + pgvector, Redis, backend container, frontend container)
- FastAPI backend scaffold: app shell, `config.py`, `database.py`, dependency injection, Alembic setup
- React + Vite frontend scaffold: project init, shadcn/ui + TailwindCSS v4, dark-mode theme, layout shell (`AppShell.tsx`, `Sidebar.tsx`, `Header.tsx`), routing
- Database models and initial Alembic migration (Report, Claim, Finding, Verdict, Embedding)
- `SibylState` Pydantic schema (shared LangGraph state)
- OpenRouter client wrapper (`openrouter_client.py`)
- `.env.example` and environment variable structure
- README with setup instructions

**Exit criteria:** `docker-compose up` starts all services; backend responds to health check; frontend renders the layout shell.

---

### FRD 1: RAG Pipeline

**PRD Section:** 5.5

**Scope:**

- Embedding service using OpenAI `text-embedding-3-small` via OpenRouter
- Chunking strategies: hierarchical for reports, paragraph-level for IFRS standards
- pgvector storage with source text, metadata (paragraph number, page, section, document type), and foreign keys
- Hybrid retrieval: semantic search (cosine similarity) + keyword search (PostgreSQL `ts_vector` full-text search) with re-ranking
- Ingestion of IFRS S1 and S2 standard texts into the corpus (`data/ifrs/s1_full.md`, `s2_full.md`, `s1_s2_mapping.json`)
- Ingestion of SASB industry standards (`data/sasb/`)
- RAG service API (`rag_service.py`, `rag_lookup.py` tool)

**Exit criteria:** IFRS/SASB corpus is embedded and retrievable; hybrid search returns relevant paragraphs for test queries.

---

### FRD 2: PDF Upload & Ingestion

**PRD Section:** 4.1

**Scope:**

- Home page UI: hero section, drag-and-drop upload zone (`UploadZone.tsx`, `UploadProgress.tsx`, `ContentPreview.tsx`)
- Backend upload endpoint (`upload.py` route)
- PyMuPDF4LLM parsing: PDF to structured markdown preserving tables, headings, page numbers
- Content chunking and embedding into pgvector via the RAG pipeline (FRD 1)
- Upload progress indicator and content structure preview (sections, page count, detected tables)
- PDF binary storage for later rendering
- Redis task queue integration for background processing

**Exit criteria:** User uploads a PDF; system parses it; preview shows extracted structure; content is chunked and embedded in pgvector.

---

### FRD 3: Claims Agent

**PRD Section:** 4.2

**Scope:**

- Claims extraction logic from parsed document content
- Claim categorization: Geographic, Quantitative/Metrics, Legal/Governance, Strategic/Forward-looking, Environmental
- Claim tagging: source page number, text location, preliminary IFRS paragraph mapping (via RAG), claim type, priority
- LangGraph node: `extract_claims` (`claims_agent.py`)
- Backend endpoint to trigger claims extraction and retrieve results
- Model: Gemini 3 Flash

**Exit criteria:** Given an uploaded document, the system extracts and returns a categorized set of verifiable claims with IFRS mappings.

---

### FRD 4: PDF Viewer with Claim Highlights

**PRD Sections:** 4.1 (highlighting), 4.2 (PDF highlighting), 7.2 (Analysis Page left panel)

**Scope:**

- Embedded PDF renderer using `@pdf-viewer/react`
- Claim highlight overlays positioned using page/location data from Claims Agent
- Highlight tooltips: click to see claim text, category, preliminary IFRS mapping, Claims Agent reasoning
- Page navigation and zoom controls
- Analysis Page left panel layout

**Exit criteria:** User views uploaded PDF with claims highlighted; clicking a highlight shows claim details in a tooltip.

---

### FRD 5: Orchestrator Agent & LangGraph Pipeline

**PRD Sections:** 4.3, 5.3, 5.4

**Scope:**

- LangGraph `StateGraph` definition and compilation (`graph.py`)
- Orchestrator routing logic: claim type to specialist agent(s) assignment
- Execution management: priorities, failure handling, timeouts, agent status tracking
- Inter-agent communication protocol: `InfoRequest`/`InfoResponse` through shared state
- Re-investigation handling: receiving Judge requests and re-routing to specialist agents
- Conditional edges: fan-out to specialists, conditional cycle back from Judge
- SSE streaming infrastructure: `StreamEvent` emission, FastAPI SSE endpoint (`stream.py`), LangGraph callback handler
- LangGraph PostgreSQL checkpointing for fault tolerance
- Analysis Page right panel: agent reasoning stream (real-time SSE text, agent tabs)
- Model: Claude Sonnet 4.5

**Exit criteria:** Claims flow into the Orchestrator; routing plans are created; SSE events stream to the frontend; the reasoning panel displays real-time agent activity. Specialist agent nodes exist as stubs that accept routed claims.

---

### FRD 6: Legal Agent

**PRD Section:** 4.5

**Scope:**

- RAG retrieval against IFRS S1/S2 and SASB knowledge base
- Investigation of governance (S1.26-27, S2.5-7), risk management (S1.38-42, S2.24-26), strategy (S2.14), and metrics (S2.27-37) claims
- Paragraph-level IFRS mapping (e.g., S2.14(a)(iv))
- Disclosure gap detection: systematic coverage analysis comparing full IFRS requirements against report content; flags fully unaddressed and partially addressed paragraphs
- Inter-agent communication participation (InfoRequest/InfoResponse)
- LangGraph node: `investigate_legal` (`legal_agent.py`)
- Model: Claude Sonnet 4.5

**Exit criteria:** Given routed claims, the Legal Agent produces paragraph-level IFRS compliance mappings and a disclosure gap analysis distinguishing fully unaddressed and partially addressed requirements.

---

### FRD 7: Data/Metrics Agent

**PRD Section:** 4.8

**Scope:**

- Internal consistency checks (e.g., Scope 1 + 2 + 3 = Total, year-over-year percentage validation)
- Unit and methodology validation (tCO2e, GHG Protocol alignment)
- Benchmark comparison for plausibility
- Target assessment: mathematical achievability of reduction targets given baselines and timelines
- Historical consistency checks
- IFRS S2.27-37 metrics compliance assessment
- Inter-agent communication participation
- LangGraph node: `investigate_data` (`data_metrics_agent.py`)
- Model: Claude Sonnet 4.5

**Exit criteria:** Given routed quantitative claims, the agent validates mathematical consistency, methodology alignment, and benchmark plausibility.

---

### FRD 8: News/Media Agent

**PRD Section:** 4.6

**Scope:**

- Web search tool integration (`search_web.py`)
- Source credibility tiering (Tier 1 through 4)
- Investigation of company-specific and industry-wide news coverage
- Evidence output: source URL, publication date, credibility tier, relevance summary
- Contradiction detection: flagging when public reporting contradicts report claims
- Inter-agent communication participation
- LangGraph node: `investigate_news` (`news_media_agent.py`)
- Model: Claude Sonnet 4.5

**Exit criteria:** Given routed claims, the agent searches public news sources and returns credibility-weighted evidence with contradiction flags.

---

### FRD 9: Academic/Research Agent

**PRD Section:** 4.7

**Scope:**

- Web search for academic papers, industry benchmarks, CDP disclosures, SBTi frameworks, GHG Protocol standards
- Methodology validation: emissions methodologies, renewable energy certifications, carbon offsets, science-based targets
- Benchmark comparison against peer-reviewed research and industry standards
- Reuses web search tool from FRD 8
- Inter-agent communication participation
- LangGraph node: `investigate_academic` (`academic_agent.py`)
- Model: DeepSeek V3.2

**Exit criteria:** Given routed technical claims, the agent validates against academic literature and industry benchmarks, returning referenced findings.

---

### FRD 10: Geography Agent

**PRD Section:** 4.4

**Scope:**

- Microsoft Planetary Computer integration via `pystac-client` (`satellite_service.py`, `query_mpc.py`)
- Sentinel-2 multispectral imagery queries by coordinates, time range, collection
- Geocoding: location names to geographic coordinates
- Analysis capabilities: NDVI vegetation change detection, land cover classification, temporal comparison (before/after), environmental impact indicators
- Satellite image processing and evidence output with image references, analysis results, temporal comparisons
- Inter-agent communication participation
- LangGraph node: `investigate_geography` (`geography_agent.py`)
- Model: Gemini 2.5 Pro

**Exit criteria:** Given routed geographic claims, the agent queries satellite imagery from MPC and produces visual evidence supporting or contradicting the claims.

---

### FRD 11: Judge Agent & Cyclic Validation

**PRD Section:** 4.9

**Scope:**

- Evidence evaluation across all specialist findings: sufficiency, consistency, quality, completeness
- Cyclic re-investigation: generating `ReinvestigationRequest` objects with refined queries, specific agent targets, evidence gap descriptions
- Iteration depth control (configurable max, default 3 cycles)
- Final verdict production: Verified, Unverified, Contradicted, Insufficient Evidence
- Verdict-to-IFRS paragraph mapping
- Conditional edge logic: route back to Orchestrator or forward to `compile_report`
- LangGraph node: `judge_evidence` (`judge_agent.py`)
- Model: Claude Opus 4.5

**Exit criteria:** The complete agent pipeline runs end-to-end. Claims are extracted, routed, investigated, judged (with re-investigation if needed), and final verdicts with IFRS mappings are produced and persisted.

---

### FRD 12: Detective Dashboard

**PRD Section:** 4.10, 7.2 (Analysis Page center panel)

**Scope:**

- React Flow (`@xyflow/react`) network graph with agent nodes and claim/evidence edges
- Custom `AgentNode.tsx` with unique agent colors, status indicators (pulsing active, solid idle, checkmark complete, warning error)
- Custom `ClaimEdge.tsx` with animated particles showing data flow direction and volume
- Real-time updates driven by SSE events from the LangGraph pipeline
- Node interaction: expand to see status, reasoning stream, findings summary, claim count
- Edge interaction: click to see the message or data being passed
- Agent-specific displays:
  - Geography Agent: satellite image tile with location caption and coordinates
  - Legal Agent: IFRS coverage progress bars per pillar (green/orange/grey)
  - Data/Metrics Agent: running consistency check list with pass/fail indicators
  - Judge Agent: verdict cards with color-coded badges and cycle counts
- Cyclic validation visualization: re-investigation loop animation
- Inter-agent communication visualization: InfoRequest/Response edges through Orchestrator

**Exit criteria:** Users watch the full investigation in real time through an animated, interactive network graph with agent-specific displays and clickable nodes/edges.

---

### FRD 13: Source of Truth Report

**PRD Section:** 4.11, 7.2 (Source of Truth Page)

**Scope:**

- Report compilation backend (`report_compiler.py`, `compile_report` LangGraph node)
- Report page organized by four IFRS pillars (Governance, Strategy, Risk Management, Metrics & Targets)
- Claim cards: original text with PDF link, IFRS paragraph tags, expandable evidence chain, full agent reasoning, Judge verdict, color-coded compliance status (green/yellow/red)
- S1/S2 cross-mapping sidebar
- Disclosure Gaps section: per-pillar listing of fully unaddressed (grey) and partially addressed (orange) IFRS requirements with materiality context
- Filter bar: pillar, claim type, verdict status, investigating agent, IFRS paragraph search, disclosure gap status
- Backend report endpoints (`report.py` routes)

**Exit criteria:** A complete, interactive compliance report renders with all claims mapped to IFRS requirements, verdicts, evidence chains, and a disclosure gaps section organized by pillar.

---

### FRD 14: Chatbot

**PRD Section:** 4.12, 7.2 (Chatbot Panel)

**Scope:**

- Slide-out chat panel UI (`ChatPanel.tsx`, `ChatMessage.tsx`, `ChatInput.tsx`) accessible via floating button from any page
- RAG-powered retrieval across: original report content, agent findings, IFRS/SASB standards, Source of Truth verdicts and disclosure gaps
- Contextual awareness: references specific agents, claims, IFRS paragraphs, evidence, and gaps
- Inline citations linking to claims, agent findings, or IFRS paragraphs
- Persistent conversation across page navigation
- Backend chat endpoint (`chat.py` route)
- Model: Gemini 3 Flash

**Exit criteria:** Users ask natural-language questions about the analysis and receive contextual, evidence-backed answers with inline citations from any page in the application.

---

## Dependency Graph

```
FRD 0 (Setup)
├── FRD 1 (RAG Pipeline)
│   ├── FRD 2 (PDF Upload & Ingestion)
│   │   ├── FRD 3 (Claims Agent)
│   │   │   ├── FRD 4 (PDF Viewer with Highlights)
│   │   │   └── FRD 5 (Orchestrator & LangGraph Pipeline)
│   │   │       ├── FRD 6 (Legal Agent)
│   │   │       ├── FRD 7 (Data/Metrics Agent)
│   │   │       ├── FRD 8 (News/Media Agent)
│   │   │       │   └── FRD 9 (Academic/Research Agent)
│   │   │       └── FRD 10 (Geography Agent)
│   │   │       └───── FRD 11 (Judge Agent) ← requires FRDs 6-10
│   │   │               ├── FRD 12 (Detective Dashboard)
│   │   │               └── FRD 13 (Source of Truth Report)
│   │   │                   └── FRD 14 (Chatbot)
```
