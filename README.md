# Sibyl — Hack for Humanity 2026

<div align="center">

<br />

![Group 213 (1)](https://github.com/user-attachments/assets/e80b83ac-ff83-47da-98f9-2e51d4cbf5bc)

</div>

<div align="center">
  <p align="center">
    <a href="https://devpost.com/software/sibyl-x8gpor">
      <strong>« Hack for Humanity 2026 — DevPost »</strong>
    </a>
  </p>
</div>

<p align="center">
Sibyl is a multi-agent AI orchestration system that ingests sustainability report PDFs, deploys eight specialized investigative agents to gather evidence from satellite imagery, legal databases, news archives, and academic research, and produces a paragraph-level IFRS S1/S2 compliance report — exposing both what companies claim and what they conspicuously choose not to disclose.
</p>

---

## The Problem

Corporate sustainability reports are dense, 100–200 page documents filled with claims that are nearly impossible to independently verify. The IFRS S1/S2 standards (effective January 2024) mandate specific disclosures across four pillars — Governance, Strategy, Risk Management, and Metrics & Targets — yet **no automated tooling exists to validate whether reported claims are actually supported by real-world evidence**.

Two primary manifestations of greenwashing exist in practice:

1. **Selective disclosure** — companies report favorable data while omitting unfavorable information
2. **Decoupling** — a measurable gap between what companies communicate and what they actually do

Existing solutions fail on both dimensions:
- Checklist tools only verify presence/absence of topics, not whether claims are evidence-based
- Keyword matchers extract sustainability language but cannot verify claims against external sources
- Human auditors can be thorough but are expensive, slow, and cannot scale

**The data is stark:** 56% of EU-examined green claims were completely unsubstantiated. KPMG found 69% of CEOs have adapted climate language to meet stakeholder expectations, while 66% admit they are not prepared to withstand shareholder scrutiny on those claims.

Sibyl exists because independent, evidence-based sustainability verification should be accessible to anyone.

<div align="center">
  <a href="https://www.youtube.com/watch?v=YWpDHMI29LM">
    <img src="https://img.shields.io/badge/▶️_View_Demo-FF0000?style=for-the-badge&logoColor=white" alt="Sibyl Demo"/>
  </a>
</div>

---

## How It Works

Sibyl operates through a sequential-then-parallel multi-agent pipeline. A document moves from ingestion through eight specialized agents, each investigating a different dimension of every claim, before a Judge agent evaluates the assembled evidence and produces a final verdict.

### Pipeline Overview

```mermaid
flowchart LR
    subgraph input [Document Ingestion]
        PDF[PDF Upload]
        PARSE[PyMuPDF4LLM Parser]
        CHUNK[Hierarchical Chunking]
        EMBED[pgvector Embeddings]
        PDF --> PARSE --> CHUNK --> EMBED
    end

    subgraph pipeline [LangGraph Agent Pipeline]
        CLAIMS[Claims Agent\nMenny · Gemini 3 Flash]
        ORCH[Orchestrator\nBron · Claude Sonnet 4.5]

        subgraph specialists [Specialist Agents — Pentagon Formation]
            GEO[Geography Agent\nColumbo · Gemini 2.5 Pro]
            LEGAL[Legal Agent\nMike · Claude Sonnet 4.5]
            NEWS[News/Media Agent\nIzzy · Claude Sonnet 4.5]
            ACAD[Academic Agent\nNewton · DeepSeek V3.2]
            DATA[Data/Metrics Agent\nRhea · Claude Sonnet 4.5]
        end

        MSGPOOL[(Message Pool\nShared LangGraph State)]
        JUDGE[Judge Agent\nJudy · Claude Opus 4.5]

        CLAIMS --> ORCH
        ORCH --> GEO & LEGAL & NEWS & ACAD & DATA
        GEO & LEGAL & NEWS & ACAD & DATA <-->|InfoRequest/InfoResponse| MSGPOOL
        MSGPOOL <-->|routed via Orchestrator| ORCH
        GEO & LEGAL & NEWS & ACAD & DATA --> JUDGE
        JUDGE -->|"Re-investigate (cyclic)"| ORCH
        JUDGE -->|Verdicts| COMPILE[compile_report]
    end

    subgraph output [Output]
        REPORT[Source of Truth Report\nIFRS S1/S2 Compliance Map]
        GAPS[Disclosure Gap Analysis\nWhat the report does NOT say]
        DASH[Detective Dashboard\nLive investigation visualization]
    end

    EMBED --> CLAIMS
    COMPILE --> REPORT & GAPS
    pipeline --> DASH
```

### Phase 1 — Claims Extraction

The **Claims Agent (Menny)** receives the full parsed document content (Gemini 3 Flash handles the 1M-token context window for 200-page reports in a single pass). It identifies every verifiable sustainability claim and categorizes each as:

- **Geographic:** Facility locations, land use, deforestation commitments
- **Quantitative/Metrics:** Emission figures, targets, year-over-year comparisons
- **Legal/Governance:** Board oversight structures, compliance assertions
- **Strategic/Forward-looking:** Transition plans, investment commitments
- **Environmental:** Biodiversity, waste management, renewable energy claims

Each claim is tagged with its source page number, preliminary IFRS S1/S2 paragraph mapping, and investigation priority.

### Phase 2 — Orchestration and Routing

The **Orchestrator (Bron)** receives all categorized claims and builds a routing plan that assigns each claim to one or more specialist agents based on claim type and content. A single claim may be routed to multiple agents — a geographic emissions claim might go to both the Geography Agent and the Data/Metrics Agent simultaneously.

The Orchestrator also handles all **inter-agent communication**: specialist agents never communicate directly. When any specialist agent needs cross-domain context, it posts an `InfoRequest` to the shared LangGraph state. The Orchestrator detects pending requests and routes them to the appropriate agent(s), which respond via `InfoResponse` objects. This architecture is fully dynamic — there are no hardcoded agent-to-agent channels.

### Phase 3 — Parallel Investigation

Five specialist agents investigate claims concurrently:

| Agent | Avatar | Model | Investigation Scope |
|-------|--------|-------|---------------------|
| Geography | Columbo | Gemini 2.5 Pro | Satellite imagery via Microsoft Planetary Computer; NDVI analysis; deforestation detection; physical risk exposure |
| Legal | Mike | Claude Sonnet 4.5 | IFRS S1/S2 paragraph-level compliance; SASB standards; governance structure validation; disclosure gap detection |
| News/Media | Izzy | Claude Sonnet 4.5 | Public news corroboration/contradiction; investigative journalism; regulatory enforcement actions; credibility-tiered sources |
| Academic | Newton | DeepSeek V3.2 | Peer-reviewed methodology validation; SBTi framework alignment; industry benchmark comparison; GHG Protocol compliance |
| Data/Metrics | Rhea | Claude Sonnet 4.5 | Mathematical consistency; unit/methodology validation; benchmark plausibility; target achievability |

### Phase 4 — Cyclic Validation

The **Judge Agent (Judy)** receives all specialist findings and evaluates each claim for evidence sufficiency, consistency, quality, and completeness. If evidence is insufficient or contradictory, Judy sends a specific re-investigation request back to the Orchestrator with:

- Which agent(s) should re-investigate
- What specific evidence gap needs to be addressed
- Refined search queries and investigation angles
- What would constitute sufficient evidence

This **cyclic loop** continues until findings are robust or a configurable maximum iteration depth (default: 3 cycles) is reached. The result is one of four verdicts:

- **Verified** — Multiple independent sources corroborate the claim
- **Unverified** — No external evidence found to support or contradict
- **Contradicted** — Evidence directly contradicts the claim
- **Insufficient Evidence** — Evidence exists but is not sufficient for a confident verdict

### Phase 5 — Disclosure Gap Analysis

Beyond claim verification, the **Legal Agent** performs a systematic coverage analysis: it compares the full set of IFRS S1/S2 disclosure requirements (at the paragraph level) against everything extracted from the report. Any IFRS paragraph with no corresponding content is flagged as a **disclosure gap** — detecting not just what companies say that is wrong, but what they chose not to say at all.

---

## System Architecture

```mermaid
flowchart TB
    subgraph client [Browser Client]
        REACT[React 18 + TypeScript]
        VITE[Vite Build]
        REACTFLOW[React Flow — Detective Dashboard]
        FRAMER[Framer Motion — Animations]
        PDFVIEW[PDF Viewer + Claim Highlights]
        CHATBOT[RAG Chatbot Panel]
    end

    subgraph server [Backend Server]
        FASTAPI[FastAPI — Async Python]
        subgraph agents [LangGraph Agent Pipeline]
            CLAIMS_A[Claims Agent]
            ORCH_A[Orchestrator Agent]
            SPECS[5 Specialist Agents]
            JUDGE_A[Judge Agent]
        end
        subgraph services [Service Layer]
            PARSER[PyMuPDF4LLM Parser]
            RAGSERV[RAG Service — pgvector]
            SATELLITE[Satellite Service — MPC]
            COMPILER[Report Compiler]
        end
        SSE_EP[SSE Streaming Endpoint]
    end

    subgraph external [External APIs]
        OPENROUTER[OpenRouter — Unified LLM Gateway]
        MPC[Microsoft Planetary Computer]
        WEBSOURCES[News + Academic Web Sources]
    end

    subgraph storage [Data Layer]
        PG[(PostgreSQL 17 + pgvector)]
        REDIS[(Redis — Task Queue)]
    end

    REACT <-->|REST + SSE| FASTAPI
    FASTAPI --> PARSER --> PG
    FASTAPI --> RAGSERV --> PG
    FASTAPI --> REDIS --> agents
    agents --> OPENROUTER
    SATELLITE --> MPC
    SPECS --> WEBSOURCES
    SSE_EP -->|StreamEvent objects| REACTFLOW
    COMPILER --> PG
```

### Frontend Architecture

The frontend is a React 18 + TypeScript SPA built with Vite. State management is divided between React hooks (`useSSE`, `useDashboard`, `useAnalysis`, `useChat`) and module-level JavaScript `Map` caches that persist data across navigation without triggering re-renders.

The **Detective Dashboard** is built on React Flow (`@xyflow/react`) with three custom node types (`EggAvatarNode`, `MessagePoolNode`) and one custom edge type (`ClaimEdge`). Agent nodes are animated egg-shaped SVG avatars using Framer Motion's `useMotionValue` + `useAnimationFrame` for continuous float animations that compose correctly with hover effects.

The **Analysis Page** is height-pinned to `calc(100vh - 56px)` and is deliberately non-scrollable — every UI element (graph, nav bar, reasoning panel) is always visible without scrolling.

### Backend Architecture

The backend follows a modular service architecture:

- **`app/api/routes/`** — FastAPI route handlers for upload, analysis, streaming, report, and chat endpoints
- **`app/agents/`** — LangGraph node implementations; `graph.py` compiles the full `StateGraph`
- **`app/services/`** — PDF parsing, RAG retrieval, satellite imagery, OpenRouter client, report compilation
- **`app/models/`** — SQLAlchemy ORM models (Report, Claim, Finding, Verdict, Embedding)
- **`app/schemas/`** — Pydantic request/response DTOs for all endpoints

### LangGraph State Machine

The pipeline is a `StateGraph` where each node reads from and writes to a shared `SibylState` Pydantic model:

```python
class SibylState(BaseModel):
    report_id: str
    document_content: str
    claims: list[Claim]                         # Claims Agent output
    routing_plan: list[RoutingAssignment]        # Orchestrator assignments
    agent_status: dict[str, AgentStatus]         # Per-agent execution state
    findings: list[AgentFinding]                 # Specialist agent results
    info_requests: list[InfoRequest]             # Cross-domain requests
    info_responses: list[InfoResponse]           # Cross-domain responses
    verdicts: list[ClaimVerdict]                 # Judge final verdicts
    reinvestigation_requests: list[ReinvestigationRequest]
    iteration_count: int                         # Current cycle (max: 3)
    events: list[StreamEvent]                    # Emitted to frontend via SSE
```

```mermaid
graph LR
    Parse["parse_document"] --> Extract["extract_claims"]
    Extract --> Orch["orchestrate"]
    Orch --> Specs["specialist agents\n(parallel fan-out)"]
    Specs --> Judge["judge_evidence"]
    Judge -->|"iteration < max AND reinvestigation needed"| Orch
    Judge -->|"iteration >= max OR all claims resolved"| Compile["compile_report"]
```

LangGraph's PostgreSQL checkpointer saves state after each node execution, enabling fault tolerance and pipeline replay from the last successful node.

### Real-Time Streaming (SSE)

Every node emits `StreamEvent` objects to the shared state. A LangGraph callback handler forwards these to a FastAPI `StreamingResponse` SSE endpoint. The frontend's `useSSE` hook maintains a live `EventSource` connection and updates the detective dashboard in real time. Module-level caches (`eventCache`, `graphStateCache`) keyed by `reportId` persist the full event history across navigation.

### RAG Pipeline

Three content corpora are embedded using `text-embedding-3-small` and stored in PostgreSQL with pgvector:

1. **IFRS Standards** — Full S1 and S2 text chunked at the paragraph level
2. **SASB Standards** — Industry-specific disclosure topics
3. **Report Content** — Uploaded document chunked with hierarchical structure preservation

Retrieval uses hybrid search: semantic (pgvector cosine similarity) + keyword (PostgreSQL full-text search with `ts_vector`), combined and re-ranked before delivery to agents or the chatbot.

---

## Detective Dashboard

The dashboard is the hero visual of Sibyl — a "detective village" where every AI agent is personified as an animated, egg-shaped avatar character.

### Agent Roster

| Agent | Avatar | Role | Color | Mark |
|-------|--------|------|-------|------|
| Claims Agent | Menny | Document analyst | `#7c9cbf` slate blue | document |
| Orchestrator | Bron | Pipeline supervisor | `#b8a99a` warm tan | network |
| Geography Agent | Columbo | Satellite investigator | `#6aaa64` forest green | globe |
| Legal Agent | Mike | Compliance mapper | `#9b6dd0` deep purple | scale |
| News/Media Agent | Izzy | Public source verifier | `#e8b84b` amber | wifi |
| Academic Agent | Newton | Research synthesizer | `#4db6ac` teal | flask |
| Data/Metrics Agent | Rhea | Quantitative validator | `#e8855a` coral | bar-chart |
| Judge Agent | Judy | Cyclic validator | `#c0392b` crimson | gavel |

### Graph Layout

```
Left                    Center                    Right
────────────────────────────────────────────────────────
                         Columbo
                        /       \
[Menny] → [Bron] → Data/Metrics  Legal  →  [Judy]
                        \  [MP]  /
                         Izzy Newton
                        Academic

MP = Message Pool (central table)
```

- **Pentagon formation:** Five specialist agents at pentagon vertices around the central Message Pool table
- **Left side:** Claims agent close to Orchestrator
- **Right side:** Judge agent
- **Message Pool:** Semi-transparent React Flow node (`z-index: -1`) showing live `InfoRequest`/`InfoResponse` messages

### Visual Features

- **Pulsating reasoning text** — Live agent reasoning appears below each avatar; pulses while agent is active; stops on completion
- **Village background** — Decorative SVG huts, trees, and a path at 11% opacity
- **Animated edges:**
  - **Claim edges:** Straight lines in source agent's color with particle animations
  - **InfoRequest edges:** Dashed lines in Orchestrator color
  - **Reinvestigation edges:** Dashed crimson quadratic bezier swooping wide below the pentagon
- **Bottom sheet** — Slides up from beneath the navigator bar on avatar click; shows full reasoning history, findings, and agent-specific content
- **Navigator bar** — Fixed at absolute bottom; 8 small clickable avatar icons; `z-index: 60`
- **Confetti** — Fires from both sides of screen on `pipeline_completed` event

---

## Source of Truth Report

The output is a comprehensive, interactive compliance report organized by IFRS S1/S2 pillars:

### Claim Cards

Each of the hundreds of extracted claims displays:
- Original claim text with link to PDF location
- IFRS S1/S2 paragraph tags (hoverable — shows full paragraph requirement on hover)
- Evidence from each investigating agent (expandable)
- Full agent reasoning chain
- Judge's final verdict with color-coded badge

### IFRS Paragraph Hover Tooltips

Every IFRS reference pill (e.g., `S2.14(a)(iv)`) has a popover showing paragraph ID, section name, and full requirement text. A 44-entry frontend registry (`paragraphRegistry.ts`) with prefix-match fallback ensures all references — including sub-paragraphs like `S2.14(a)(i)` — display correctly.

### Disclosure Gap Analysis

A dedicated "What this report does NOT disclose" section per pillar lists every IFRS requirement the report fails to address:

- **Fully unaddressed** — zero corresponding content (grey)
- **Partially addressed** — topic mentioned but specific sub-requirements missing (orange)

Each gap entry explains why the omission matters in plain language.

### S1/S2 Cross-Mapping Sidebar

A slide-out panel shows how each S2 climate disclosure fulfills its corresponding S1 general requirement, making the interconnection between the two standards explicit and traceable.

---

## Design System

Sibyl uses a distinctive warm cream design system — a deliberate departure from dark-mode dashboard aesthetics.

| Element | Value |
|---------|-------|
| Background | `#fff6e9` — warm cream; never `#ffffff` |
| Body text | `#4a3c2e` — warm dark brown |
| Label text | `#6b5344` — medium warm brown |
| Muted text | `#8b7355` — light warm brown |
| Muted surface | `#eddfc8` — pale cream |
| Borders | `#e0d4bf` — subtle warm border |
| Verified | `#10b981` emerald |
| Contradicted | `#f43f5e` rose |
| Unverified | `#f59e0b` amber |

**Strictly prohibited:** `text-slate-*`, `bg-slate-*`, `border-slate-200`, `rounded-xl` on content cards, emoji (Lucide React icons only).

Animations use Framer Motion throughout: blur-fade-in on page content, staggered list item entrance (50ms stagger, 220ms per item), continuous float on avatars, pulsating reasoning text, and bottom sheet slide-up.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 18 + TypeScript + Vite | SPA with fast HMR |
| Styling | TailwindCSS v4 | Warm cream utility-first design |
| Graph | React Flow (`@xyflow/react`) | Detective dashboard network graph |
| Animation | Framer Motion | Avatars, transitions, pulsating text |
| PDF Viewer | `@pdf-viewer/react` | Embedded PDF with claim highlight overlays |
| Backend | FastAPI + Python 3.11 | Async API server |
| Validation | Pydantic v2 | Request/response schema validation |
| ORM | SQLAlchemy 2.1 + Alembic | Database models and migrations |
| Database | PostgreSQL 17 + pgvector | Unified relational + vector store |
| AI Orchestration | LangGraph v1.0 | Graph-based state machine; cyclic workflows |
| LLM Integration | LangChain | RAG pipelines, tools, prompts |
| LLM Gateway | OpenRouter API | Unified access to Claude, Gemini, DeepSeek |
| PDF Parsing | PyMuPDF4LLM | Structured markdown extraction |
| Satellite Imagery | Microsoft Planetary Computer | Sentinel-2 imagery via pystac-client (no API key) |
| Embeddings | OpenAI text-embedding-3-small | pgvector RAG |
| Streaming | Server-Sent Events (SSE) | Real-time agent thought streaming |
| Task Queue | Redis | Background job processing |
| Confetti | canvas-confetti | Pipeline completion celebration |
| Deployment | Docker Compose | Single-command orchestration |

### Model Selection Rationale

| Agent | Model | Rationale | Cost (in/out per 1M tokens) |
|-------|-------|-----------|---------------------------|
| Claims Agent | Gemini 3 Flash | 1M context handles full 200-page PDFs in one pass | ~$0.50 / $3.00 |
| Orchestrator | Claude Sonnet 4.5 | Strong agentic routing and coordination reasoning | ~$3 / $15 |
| Geography | Gemini 2.5 Pro | Best multimodal/vision for satellite image analysis | ~$1.25 / $10 |
| Legal | Claude Sonnet 4.5 | Excellent legal and compliance interpretation | ~$3 / $15 |
| News/Media | Claude Sonnet 4.5 | Credibility assessment and nuanced source analysis | ~$3 / $15 |
| Academic | DeepSeek V3.2 | Fast, cost-effective research synthesis | ~$0.25 / $0.38 |
| Data/Metrics | Claude Sonnet 4.5 | Strong numerical reasoning and consistency checking | ~$3 / $15 |
| Judge | Claude Opus 4.5 | Highest reasoning quality for final judgment calls | ~$5 / $25 |
| Chatbot | Gemini 3 Flash | Fast conversational Q&A with RAG | ~$0.50 / $3.00 |
| Embeddings | text-embedding-3-small | Cost-effective, strong retrieval quality | ~$0.02 / N/A |

**Why LangGraph:** Native cyclic workflow support (critical for Judge re-investigation loop), explicit state machine architecture, built-in streaming callbacks for the dashboard, and PostgreSQL checkpointing for fault tolerance. CrewAI lacks cyclic control flow; AutoGen's event-driven model adds unnecessary complexity.

**Why pgvector over a separate vector DB:** Everything stays in one PostgreSQL database with ACID compliance. Vector search results can be joined with relational claim/finding data. At hackathon scale (hundreds of documents), pgvector v0.8.0 performance is more than sufficient.

**Why SSE over WebSockets:** Agent thought streaming is strictly unidirectional (server → client). SSE is simpler, auto-reconnects natively, and works directly with React's `EventSource` API.

---

## API Design

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/upload` | Upload PDF; triggers parsing pipeline |
| `GET` | `/api/v1/upload/{reportId}` | Get parsed document structure |
| `POST` | `/api/v1/analysis/{reportId}/start` | Enqueue analysis pipeline |
| `GET` | `/api/v1/analysis/{reportId}/status` | Get pipeline execution status |
| `GET` | `/api/v1/analysis/{reportId}/claims` | List extracted claims with IFRS mappings |
| `GET` | `/api/v1/stream/{reportId}` | **SSE endpoint** — streams `StreamEvent` objects |
| `GET` | `/api/v1/report/{reportId}` | Full Source of Truth report |
| `GET` | `/api/v1/report/{reportId}/summary` | Report summary with pillar stats |
| `POST` | `/api/v1/chat/{reportId}` | RAG chatbot query |

### SSE StreamEvent Types

```typescript
type StreamEventType =
  | 'agent_started'           // Agent begins working; node status → 'working'
  | 'agent_thinking'          // Reasoning message; updates pulsating text
  | 'claim_routed'            // Orchestrator assigns claim to agent; adds edge
  | 'evidence_found'          // Agent finds evidence; adds edge to Judge
  | 'reinvestigation'         // Judge requests re-investigation; swoop edge
  | 'info_request_routed'     // Cross-domain request; dashed edge
  | 'info_response_posted'    // InfoResponse stored in message pool
  | 'agent_completed'         // Agent finishes; node status → 'completed'
  | 'pipeline_completed'      // All done; triggers confetti + stops pulsing
  | 'error';                  // Agent error; node status → 'error'

interface StreamEvent {
  event_type: StreamEventType;
  agent: AgentName;
  message: string;
  timestamp: string;
  data?: Record<string, unknown>;
}
```

---

## Project Structure

```
sibyl/
├── frontend/
│   ├── public/
│   │   └── sibyl-favicon.png          # Leaf logo — browser tab favicon
│   ├── src/
│   │   ├── components/
│   │   │   ├── AgentVillage.tsx        # Agent definitions (AGENTS array), EggAvatar,
│   │   │   │                           # AgentMark SVG — used on landing page + dashboard
│   │   │   ├── Dashboard/
│   │   │   │   ├── DashboardGraph.tsx  # Main graph canvas, ReactFlowProvider, confetti
│   │   │   │   ├── DashboardGraph.css  # All graph/village/sheet/nav-bar styles
│   │   │   │   ├── EggAvatarNode.tsx   # Custom React Flow node: avatar + pulsating text
│   │   │   │   ├── MessagePoolNode.tsx # Custom React Flow node: message pool table
│   │   │   │   ├── ClaimEdge.tsx       # Animated edges (straight + swoop-under bezier)
│   │   │   │   ├── ParticleAnimation.tsx # SVG particles along edge paths
│   │   │   │   ├── AgentDetailSheet.tsx  # Bottom sheet: reasoning/findings/agent content
│   │   │   │   ├── VillageBackground.tsx # Decorative SVG huts/trees at 11% opacity
│   │   │   │   └── layout.ts           # AGENT_POSITIONS, AGENT_HEX_COLORS, LAYOUT_CONFIG
│   │   │   ├── Analysis/
│   │   │   │   ├── AgentReasoningPanel.tsx  # Right panel: live event log, agent tabs
│   │   │   │   └── AgentReasoningPanel.css
│   │   │   ├── PDFViewer/
│   │   │   │   ├── PDFViewer.tsx        # Embedded PDF renderer
│   │   │   │   ├── ClaimHighlight.tsx   # Overlay highlights on PDF pages
│   │   │   │   └── HighlightTooltip.tsx # Claim detail tooltip on highlight click
│   │   │   ├── SourceOfTruth/
│   │   │   │   ├── ComplianceReport.tsx # Main report view by IFRS pillars
│   │   │   │   ├── PillarSection.tsx    # Section for each pillar
│   │   │   │   ├── ClaimCard.tsx        # Individual claim with verdict + evidence
│   │   │   │   ├── EvidencePanel.tsx    # Expandable evidence chain viewer
│   │   │   │   ├── FilterBar.tsx        # Filter by pillar/status/paragraph
│   │   │   │   ├── S1S2MappingSidebar.tsx # Cross-mapping panel with flow arrows
│   │   │   │   └── IFRSParagraphTag.tsx   # Hover popover for IFRS references
│   │   │   ├── Chatbot/
│   │   │   │   ├── ChatPanel.tsx        # Slide-out chatbot panel
│   │   │   │   ├── ChatMessage.tsx      # Message bubble component
│   │   │   │   └── ChatInput.tsx        # User input with send button
│   │   │   ├── Upload/
│   │   │   │   ├── UploadZone.tsx       # Drag-and-drop upload
│   │   │   │   ├── UploadProgress.tsx   # Progress during parsing
│   │   │   │   └── ContentPreview.tsx   # Document structure preview
│   │   │   └── Layout/
│   │   │       ├── AppShell.tsx         # Main layout shell
│   │   │       └── Header.tsx           # Nav bar with leaf logo + links
│   │   ├── data/
│   │   │   └── paragraphRegistry.ts    # 44-entry IFRS paragraph registry;
│   │   │                               # getParagraphInfo() with prefix-match fallback
│   │   ├── hooks/
│   │   │   ├── useSSE.ts               # SSE hook; module-level eventCache by reportId
│   │   │   ├── useDashboard.ts         # Graph state hook; module-level graphStateCache
│   │   │   ├── useAnalysis.ts          # Analysis state management
│   │   │   └── useChat.ts              # Chatbot conversation state
│   │   ├── services/
│   │   │   ├── api.ts                  # REST API client
│   │   │   └── sse.ts                  # SSE client and StreamEvent types
│   │   ├── types/
│   │   │   ├── agent.ts                # AgentName union (includes "judge", "message_pool")
│   │   │   ├── claim.ts                # Claim, ClaimType, ClaimVerdict types
│   │   │   ├── dashboard.ts            # Verdict, IFRSCoverageContent types
│   │   │   ├── ifrs.ts                 # IFRS pillar and paragraph mapping types
│   │   │   └── report.ts               # Report, SourceOfTruth types
│   │   ├── pages/
│   │   │   ├── HomePage.tsx            # Upload landing page with AgentVillage
│   │   │   ├── AnalysisPage.tsx        # Split-panel analysis view (height-pinned)
│   │   │   ├── AnalysisPage.css        # Page layout, tab bar, back button styles
│   │   │   ├── AnalysisListPage.tsx    # List of past analyses; stagger fade-in
│   │   │   ├── ReportPage.tsx          # Source of Truth report + list view
│   │   │   └── DocsPage.tsx            # Comprehensive documentation page
│   │   ├── App.tsx                     # Routing (/, /analysis, /analysis/:id,
│   │   │                               #          /report, /report/:id, /docs)
│   │   ├── main.tsx                    # Entry point
│   │   └── index.css                   # Global styles; warm cream theme
│   ├── index.html                      # Favicon: sibyl-favicon.png
│   ├── package.json                    # Includes canvas-confetti
│   ├── vite.config.ts
│   └── Dockerfile
│
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   │   ├── upload.py               # PDF upload endpoint
│   │   │   ├── analysis.py             # Start/status analysis endpoints
│   │   │   ├── stream.py               # SSE streaming endpoint
│   │   │   ├── report.py               # Source of Truth report endpoints
│   │   │   └── chat.py                 # Chatbot conversation endpoint
│   │   ├── agents/
│   │   │   ├── state.py                # SibylState Pydantic schema
│   │   │   ├── graph.py                # LangGraph StateGraph compilation
│   │   │   ├── claims_agent.py         # Gemini 3 Flash — claims extraction
│   │   │   ├── orchestrator_agent.py   # Claude Sonnet 4.5 — routing + coordination
│   │   │   ├── geography_agent.py      # Gemini 2.5 Pro — satellite verification
│   │   │   ├── legal_agent.py          # Claude Sonnet 4.5 — compliance mapping
│   │   │   ├── news_media_agent.py     # Claude Sonnet 4.5 — news verification
│   │   │   ├── academic_agent.py       # DeepSeek V3.2 — research synthesis
│   │   │   ├── data_metrics_agent.py   # Claude Sonnet 4.5 — quantitative validation
│   │   │   ├── judge_agent.py          # Claude Opus 4.5 — cyclic validation
│   │   │   └── tools/
│   │   │       ├── search_web.py       # Web search for News/Academic agents
│   │   │       ├── query_mpc.py        # Microsoft Planetary Computer tool
│   │   │       └── rag_lookup.py       # RAG retrieval tool
│   │   ├── services/
│   │   │   ├── pdf_parser.py           # PyMuPDF4LLM integration
│   │   │   ├── rag_service.py          # Embedding, chunking, hybrid retrieval
│   │   │   ├── satellite_service.py    # MPC + Sentinel-2 image processing
│   │   │   ├── openrouter_client.py    # OpenRouter API wrapper with retry
│   │   │   └── report_compiler.py      # Source of Truth compilation
│   │   ├── models/                     # SQLAlchemy ORM models
│   │   ├── schemas/                    # Pydantic request/response DTOs
│   │   └── core/                       # Config, database, dependencies
│   ├── data/
│   │   ├── ifrs/
│   │   │   ├── s1_full.md              # IFRS S1 standard text (RAG corpus)
│   │   │   ├── s2_full.md              # IFRS S2 standard text (RAG corpus)
│   │   │   ├── s1_s2_mapping.json      # S1-S2 cross-reference map
│   │   │   └── paragraph_registry.json # 44-entry paragraph metadata
│   │   └── sasb/                       # SASB industry standards by sector
│   ├── alembic/                        # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
│
├── docs/
│   ├── PRD.md                          # Product Requirements Document (v0.4)
│   ├── FRD-order.md                    # FRD dependency and sequencing
│   └── FRDs/
│       ├── FRD-0-setup-document.md
│       ├── FRD-1-rag-pipeline.md
│       ├── FRD-2-pdf-upload-ingestion.md
│       ├── FRD-3-claims-agent.md
│       ├── FRD-4-pdf-viewer-claim-highlights.md
│       ├── FRD-5-orchestrator-agent-langgraph-pipeline.md
│       ├── FRD-6-legal-agent.md
│       ├── FRD-7-data-metrics-agent.md
│       ├── FRD-8-news-media-agent.md
│       ├── FRD-9-academic-research-agent.md
│       ├── FRD-10-geography-agent.md
│       ├── FRD-11-judge-agent-cyclic-validation.md
│       ├── FRD-12-detective-dashboard.md    # v2.0 — avatar village design
│       ├── FRD-13-source-of-truth-report.md
│       └── FRD-14-chatbot.md
│
├── docker-compose.yml                  # PostgreSQL + Redis + Backend + Frontend
└── .env.example                        # Environment variable template
```

---

## Key Engineering Decisions

### State Persistence Without a Database

When a user navigates away from the Analysis page and returns, both the SSE connection and the React component tree are destroyed. Rather than hitting the database to reconstruct state, module-level JavaScript `Map` caches (outside any React component) survive navigation:

```typescript
// Survives component unmount/remount for the browser session
const eventCache = new Map<string, StreamEvent[]>();      // in useSSE.ts
const graphStateCache = new Map<string, GraphState>();    // in useDashboard.ts
```

Both are keyed by `reportId`. On mount, hooks initialize from cache; on updates, they write back. A page reload clears both caches and reconnects SSE from scratch.

### Reinvestigation Edge Path

The reinvestigation edge from Judge (far right) to Orchestrator (left-center) would normally cut through the entire specialist pentagon. A custom quadratic bezier swoops wide below the cluster:

```typescript
const REINVESTIGATION_SWOOP_Y = CLUSTER_CY + 320; // Far below the pentagon
const d = `M ${sourceX},${sourceY} Q ${midX},${REINVESTIGATION_SWOOP_Y} ${targetX},${targetY}`;
```

### Avatar Float Animation Bug Fix

The original implementation combined float and hover into a single Framer Motion `animate` object, causing avatars to snap back to their float start position when hover ended. The fix separates concerns:

- **Float:** `useAnimationFrame` updates a `useMotionValue` at 60fps — no React re-renders
- **Hover:** `whileHover={{ scale: 1.08 }}` applies as a separate transform composition

When the user hovers off, the float continues from wherever the animation currently is.

### Analysis Page Height Pinning

The Analysis page needs to be non-scrollable while every other page in the app needs to scroll. The solution pins only the analysis page without touching the global layout:

```css
/* AnalysisPage.css — only affects this page */
.analysis-page {
  height: calc(100vh - 56px);   /* 56px = global header height */
  max-height: calc(100vh - 56px);
  overflow: hidden;
}
```

The global `<main>` element in `App.tsx` remains `overflow-auto`, so all other pages scroll normally.

### Dynamic Import for canvas-confetti

Vite's static import analysis fails if a package isn't in the container's `node_modules` at build time. The fix defers resolution to runtime:

```typescript
import('canvas-confetti').then(({ default: confetti }) => {
  confetti({ particleCount: 80, angle: 60, spread: 55, origin: { x: 0 } });
  confetti({ particleCount: 80, angle: 120, spread: 55, origin: { x: 1 } });
});
```

---

## IFRS S1/S2 Framework Reference

Sibyl maps every claim to specific IFRS paragraphs across the two standards:

| S1 Pillar | S1 Paragraphs | S2 Climate Paragraphs |
|-----------|--------------|----------------------|
| Governance | S1.26-27 | S2.5-7 |
| Strategy | S1.28-35 | S2.8-23 (risks, business model, decision-making, financial effects, resilience) |
| Risk Management | S1.38-42 | S2.24-26 |
| Metrics & Targets | S1.43-53 | S2.27-37 (GHG Scope 1/2/3, intensity, targets, carbon pricing) |

The **S1/S2 Cross-Reference:** S1 defines *how* to structure disclosures; S2 defines *what* to disclose for climate. Every S2 requirement fulfills a corresponding S1 pillar requirement — Sibyl's cross-mapping sidebar makes this relationship explicit for every claim.

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ and npm (for local frontend development)
- Python 3.11+ (for local backend development)
- OpenRouter API key with credits (for all LLM calls)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/sibyl.git
cd sibyl

# 2. Configure environment
cp .env.example .env
# Edit .env: set OPENROUTER_API_KEY, DATABASE_URL, REDIS_URL

# 3. Start all services with Docker Compose
docker-compose up --build

# Frontend:  http://localhost:5173
# Backend:   http://localhost:8000
# API docs:  http://localhost:8000/docs
```

### Environment Variables

```bash
# .env.example
OPENROUTER_API_KEY=sk-or-...        # Required for all LLM calls
DATABASE_URL=postgresql+asyncpg://sibyl:sibyl@localhost:5432/sibyl
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-in-production
```

### Local Development (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Non-Functional Requirements

| Metric | Target |
|--------|--------|
| PDF upload and parsing | < 30s for a 200-page document |
| Full agent pipeline | < 5 minutes (up to 3 Judge cycles) |
| Individual agent response | < 60s per claim investigation |
| SSE streaming latency | Agent thoughts visible within 500ms |
| Page load time | < 2s for any page |
| Chatbot response | < 5s per RAG query |
| Source of Truth render | < 3s for 100+ claims |
| Concurrent analyses | Up to 10 (limited by OpenRouter rate limits) |

**Error handling:** Individual agent failures do not stop the pipeline. The Judge evaluates available evidence and notes missing agents. OpenRouter calls retry up to 3 times with exponential backoff. LangGraph checkpointing enables recovery from the last successful node.

---

## Documentation

- [PRD v0.4](docs/PRD.md) — Full product specification with IFRS framework detail and architecture
- [FRD Order](docs/FRD-order.md) — Feature requirement dependency graph and implementation sequence
- [Detective Dashboard FRD (v2.0)](docs/FRDs/FRD-12-detective-dashboard.md) — Complete avatar village implementation spec
- [Source of Truth Report FRD](docs/FRDs/FRD-13-source-of-truth-report.md) — Compliance report design and IFRS mapping
- [Orchestrator & LangGraph Pipeline FRD](docs/FRDs/FRD-5-orchestrator-agent-langgraph-pipeline.md) — State machine design, SSE infrastructure
- [In-app Docs Page](/docs) — Interactive documentation page at `/docs` within the running application

**When the backend is running:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Team

Built for Hack for Humanity 2026 by the Sibyl team.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
