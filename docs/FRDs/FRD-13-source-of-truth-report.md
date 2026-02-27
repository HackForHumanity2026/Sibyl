# Feature Requirements Document: FRD 13 -- Source of Truth Report (v1.0)

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.4](../PRD.md) |
| **FRD Order** | [FRD Order](../FRD-order.md) |
| **PRD Sections** | 4.11 (Source of Truth Output), 7.2 (Source of Truth Page) |
| **Type** | Feature |
| **Depends On** | FRD 6 (Legal Agent), FRD 11 (Judge Agent & Cyclic Validation) |
| **Delivers** | Interactive IFRS compliance report with disclosure gaps, report compilation backend, report page UI, claim cards, evidence panels, S1/S2 cross-mapping sidebar, disclosure gaps section, filter bar, backend report endpoints; IFRS paragraph hover tooltips; cross-mapping UX redesign; report list page redesign |
| **Created** | 2026-02-09 |
| **Revised** | 2026-02-27 (implementation updates -- see Appendix F) |

---

## Summary

FRD 13 delivers the Source of Truth Report -- the primary output of Sibyl, a comprehensive, interactive IFRS S1/S2 compliance report that maps every extracted claim to IFRS requirements, displays evidence chains from all investigating agents, shows Judge verdicts, and surfaces disclosure gaps. The report compilation backend (`app/services/report_compiler.py`) replaces the FRD 5 stub `compile_report` LangGraph node with a functional implementation that reads all verdicts, findings, and disclosure gaps from the LangGraph state, organizes them by IFRS pillar (Governance, Strategy, Risk Management, Metrics & Targets), persists the compiled report to the database, and generates summary statistics. The report page (`src/pages/ReportPage.tsx`) is a full-width interactive dashboard organized by four IFRS pillar sections (`src/components/SourceOfTruth/PillarSection.tsx`), each containing claim cards (`src/components/SourceOfTruth/ClaimCard.tsx`) displaying original claim text with PDF links, IFRS paragraph tags, expandable evidence chains (`src/components/SourceOfTruth/EvidencePanel.tsx`), full agent reasoning, Judge verdict badges with color-coded compliance status (green=verified, yellow=unverified/insufficient evidence, red=contradicted), and a disclosure gaps section listing fully unaddressed (grey) and partially addressed (orange) IFRS requirements with materiality context. The S1/S2 cross-mapping sidebar (`src/components/SourceOfTruth/S1S2MappingSidebar.tsx`) shows how S2 climate paragraphs fulfill S1 general requirements. The filter bar (`src/components/SourceOfTruth/FilterBar.tsx`) enables filtering by pillar, claim type, verdict status, investigating agent, IFRS paragraph search, and disclosure gap status. Backend report endpoints (`app/api/routes/report.py`) serve report data via RESTful API: `GET /api/v1/report/{reportId}`, `GET /api/v1/report/{reportId}/claims`, `GET /api/v1/report/{reportId}/gaps`, `GET /api/v1/report/{reportId}/summary`. The frontend uses `useReport` hook (`src/hooks/useReport.ts`) for data fetching and filtering logic. After FRD 13, a complete, interactive compliance report renders with all claims mapped to IFRS requirements, verdicts, evidence chains, and a disclosure gaps section organized by pillar, serving as the definitive output of Sibyl's multi-agent investigation.

---

## Given Context (Preconditions)

The following are assumed to be in place from prior FRDs:

| Prerequisite | Source FRD | Deliverable |
|---|---|---|
| Docker Compose with PostgreSQL 17 + pgvector, Redis, backend, frontend | FRD 0 | `docker-compose.yml` |
| `SibylState` Pydantic schema with `Claim`, `AgentFinding`, `ClaimVerdict`, `ReinvestigationRequest`, `StreamEvent` types | FRD 0, FRD 5 | `app/agents/state.py` |
| LangGraph StateGraph with `compile_report` stub node | FRD 5 | `app/agents/graph.py` |
| `compile_report` stub that persists verdicts and findings | FRD 5 | `app/agents/graph.py` (stub) |
| Legal Agent producing IFRS compliance mappings and disclosure gap findings | FRD 6 | `app/agents/legal_agent.py` |
| Judge Agent producing final verdicts (Verified, Unverified, Contradicted, Insufficient Evidence) | FRD 11 | `app/agents/judge_agent.py` |
| All specialist agents producing findings | FRDs 6-10 | `app/agents/*.py` |
| `Claim`, `Finding`, `Verdict` SQLAlchemy models | FRD 0 | `app/models/claim.py`, `finding.py`, `verdict.py` |
| `Report` model with status tracking | FRD 0 | `app/models/report.py` |
| Frontend React + TypeScript + shadcn/ui + TailwindCSS v4 setup | FRD 0 | `frontend/` scaffold |
| PDF viewer with claim highlights | FRD 4 | `src/components/PDFViewer/` |
| Routing infrastructure | FRD 0 | `src/App.tsx` with React Router |
| Report route stub | FRD 0 | Placeholder route |
| OpenRouter client wrapper | FRD 0 | `app/services/openrouter_client.py` |
| IFRS paragraph registry with S1/S2 mapping | FRD 6 | `data/ifrs/paragraph_registry.json`, `s1_s2_mapping.json` |

### Terms

| Term | Definition |
|---|---|
| Source of Truth Report | The primary output of Sibyl -- a comprehensive, interactive IFRS compliance report mapping claims to requirements, evidence, and verdicts |
| Report compilation | The process of reading verdicts, findings, and gaps from LangGraph state, organizing by IFRS pillar, and persisting to the database |
| IFRS pillar | One of four S1 pillars: Governance, Strategy, Risk Management, Metrics & Targets |
| Claim card | A UI component displaying a single claim with its verdict, evidence chain, and compliance status |
| Evidence chain | The sequence of agent findings and reasoning that led to a verdict, displayed in an expandable panel |
| Disclosure gap | An IFRS S1/S2 requirement that is fully unaddressed (grey) or partially addressed (orange) in the report |
| S1/S2 cross-mapping | The relationship showing how S2 climate paragraphs fulfill S1 general requirements |
| Compliance status | Color-coded status: green (verified), yellow (unverified/insufficient evidence), red (contradicted) |
| Verdict badge | A visual indicator showing the Judge's final verdict for a claim |
| Filter bar | UI component enabling filtering by pillar, claim type, verdict, agent, IFRS paragraph, gap status |

---

## Executive Summary (Gherkin-Style)

```gherkin
Feature: Source of Truth Report

  Background:
    Given  FRD 0, FRD 1, FRD 2, FRD 3, FRD 4, FRD 5, FRD 6, FRD 7, FRD 8, FRD 9, FRD 10, and FRD 11 are complete
    And    all services are running (backend, frontend, PostgreSQL, Redis)
    And    a sustainability report has been analyzed through the full pipeline
    And    all claims have been investigated, judged, and verdicts issued
    And    disclosure gaps have been identified by the Legal Agent

  Scenario: Compile report from LangGraph state
    Given  the LangGraph pipeline has completed with verdicts and findings in state
    When   the compile_report node executes
    Then   it reads all verdicts, findings, and disclosure gaps from state
    And    it organizes claims by IFRS pillar (Governance, Strategy, Risk Management, Metrics & Targets)
    And    it groups disclosure gaps by pillar
    And    it computes summary statistics (total claims, verdicts by type, disclosure gaps)
    And    it persists the compiled report to the database
    And    it sets the report status to "completed"

  Scenario: Report page renders with pillar sections
    Given  a compiled report exists in the database
    When   the user navigates to the Report Page
    Then   the page displays four pillar sections (Governance, Strategy, Risk Management, Metrics & Targets)
    And    each pillar section shows the count of claims and gaps
    And    each pillar section displays claim cards for claims mapped to that pillar
    And    each pillar section displays disclosure gaps below the claim cards

  Scenario: Claim card displays full information
    Given  a claim card is rendered
    When   the user views the card
    Then   it shows the original claim text with a link to the PDF viewer
    And    it displays IFRS paragraph tags (e.g., "S2.14(a)(iv)")
    And    it shows the Judge verdict badge with color-coded status
    And    it provides an expand button to reveal the evidence chain
    And    expanding shows evidence from each investigating agent with agent colors
    And    expanding shows full agent reasoning and findings
    And    expanding shows whether re-investigation was requested

  Scenario: Evidence panel shows agent contributions
    Given  a claim card is expanded
    When   the user views the evidence panel
    Then   it displays findings from each investigating agent
    And    each agent's section uses the agent's color identity
    And    each finding shows evidence type, summary, and details
    And    findings are ordered chronologically (first investigation → re-investigations)
    And    the Judge's reasoning is displayed at the end

  Scenario: Disclosure gaps section surfaces omissions
    Given  the report page is displayed
    When   the user views a pillar section
    Then   below the claim cards, a "Disclosure Gaps" section is shown
    And    fully unaddressed gaps are displayed with grey color coding
    And    partially addressed gaps are displayed with orange color coding
    And    each gap shows the IFRS paragraph identifier and requirement description
    And    each gap shows missing sub-requirements (for partially addressed)
    And    each gap includes materiality context explaining why the omission matters

  Scenario: S1/S2 cross-mapping sidebar
    Given  the report page is displayed
    When   the user opens the S1/S2 cross-mapping sidebar
    Then   it shows how S2 climate paragraphs fulfill S1 general requirements
    And    it highlights which S2 paragraphs are covered by claims (green)
    And    it highlights which S2 paragraphs are disclosure gaps (grey/orange)
    And    clicking a paragraph navigates to the relevant claim or gap

  Scenario: Filter bar enables filtering
    Given  the report page is displayed
    When   the user applies filters
    Then   filtering by pillar shows only claims and gaps for that pillar
    And    filtering by claim type shows only claims of that type
    And    filtering by verdict status shows only claims with that verdict
    And    filtering by investigating agent shows only claims investigated by that agent
    And    searching by IFRS paragraph filters to claims/gaps mapped to that paragraph
    And    filtering by gap status shows only fully unaddressed or partially addressed gaps
    And    multiple filters can be combined

  Scenario: Compliance summary statistics
    Given  the report page is displayed
    When   the user views the summary section
    Then   it shows total claims count
    And    it shows verdicts by type (Verified, Unverified, Contradicted, Insufficient Evidence)
    And    it shows coverage percentage by pillar
    And    it shows total disclosure gaps count
    And    it shows gaps by status (fully unaddressed, partially addressed)

  Scenario: Backend report endpoints serve data
    Given  a compiled report exists
    When   the frontend requests report data
    Then   GET /api/v1/report/{reportId} returns the full report structure
    And    GET /api/v1/report/{reportId}/claims returns claims organized by pillar
    And    GET /api/v1/report/{reportId}/gaps returns disclosure gaps organized by pillar
    And    GET /api/v1/report/{reportId}/summary returns summary statistics
    And    responses include proper pagination for large reports

  Scenario: PDF link navigation
    Given  a claim card displays a PDF link
    When   the user clicks the link
    Then   it navigates to the PDF viewer with the claim highlighted
    And    the PDF viewer scrolls to the claim's page and location

  Scenario: Report is comprehensive
    Given  the full pipeline has completed
    When   the report is compiled
    Then   every verifiable claim is present in the report
    And    every claim is mapped to IFRS paragraphs
    And    every claim has a verdict
    And    every IFRS requirement is accounted for (either mapped to a claim or flagged as a gap)
    And    the report does not degrade the complexity of the underlying document
```

---

## Table of Contents

1. [Report Compilation Backend](#1-report-compilation-backend)
2. [Report Data Model](#2-report-data-model)
3. [Backend Report Endpoints](#3-backend-report-endpoints)
4. [Report Page Layout](#4-report-page-layout)
5. [IFRS Pillar Sections](#5-ifrs-pillar-sections)
6. [Claim Cards](#6-claim-cards)
7. [Evidence Chain Panel](#7-evidence-chain-panel)
8. [S1/S2 Cross-Mapping Sidebar](#8-s1s2-cross-mapping-sidebar)
9. [Disclosure Gaps Section](#9-disclosure-gaps-section)
10. [Filter Bar](#10-filter-bar)
11. [Compliance Summary Statistics](#11-compliance-summary-statistics)
12. [Frontend State Management](#12-frontend-state-management)
13. [Navigation and Routing](#13-navigation-and-routing)
14. [Error Handling](#14-error-handling)
15. [Exit Criteria](#15-exit-criteria)
16. [Appendix A: Report API Response Schemas](#appendix-a-report-api-response-schemas)
17. [Appendix B: Claim Card Layout Specification](#appendix-b-claim-card-layout-specification)
18. [Appendix C: Filter Bar Options Reference](#appendix-c-filter-bar-options-reference)
19. [Appendix D: Color Coding Reference](#appendix-d-color-coding-reference)
20. [Design Decisions Log](#design-decisions-log)

---

## 1. Report Compilation Backend

### 1.1 Overview

The report compilation backend (`app/services/report_compiler.py`) replaces the FRD 5 stub `compile_report` LangGraph node with a functional implementation that reads all verdicts, findings, and disclosure gaps from the LangGraph state, organizes them by IFRS pillar, computes summary statistics, and persists the compiled report to the database.

### 1.2 Compile Report Node Function

```python
async def compile_report(state: SibylState) -> dict:
    """Compile the Source of Truth report from LangGraph state.

    Reads: state.verdicts, state.findings, state.claims, state.report_id
    Writes: Database (Report, Claim, Finding, Verdict records), state.events

    Responsibilities:
    1. Read all verdicts, findings, and claims from state
    2. Organize claims by IFRS pillar based on verdict IFRS mappings
    3. Group disclosure gaps by pillar
    4. Compute summary statistics
    5. Persist compiled report to database
    6. Set report status to "completed"

    Returns:
        Partial state update with events.
    """
```

### 1.3 Compilation Process

The `compile_report` node shall execute the following steps:

1. **Emit start event:** Append a `StreamEvent` with `event_type = "pipeline_completed"`, `agent_name = None`, including compilation start.

2. **Load state data:**
   - Read all `ClaimVerdict` objects from `state.verdicts`
   - Read all `AgentFinding` objects from `state.findings`
   - Read all `Claim` objects from `state.claims`
   - Filter disclosure gap findings (`evidence_type = "disclosure_gap"`)

3. **Organize claims by IFRS pillar:**
   - For each verdict, extract IFRS paragraph mappings from `verdict.ifrs_mapping`
   - Map each paragraph to its pillar using the IFRS paragraph registry
   - Group claims by pillar (a claim may appear in multiple pillars if it maps to paragraphs across pillars)

4. **Organize disclosure gaps by pillar:**
   - For each gap finding, extract `paragraph_id` from `finding.details`
   - Map paragraph to pillar using the registry
   - Group gaps by pillar

5. **Compute summary statistics:**
   - Total claims count
   - Verdicts by type: `verified`, `unverified`, `contradicted`, `insufficient_evidence`
   - Coverage percentage by pillar: `(claims_in_pillar / total_ifrs_paragraphs_in_pillar) * 100`
   - Total disclosure gaps count
   - Gaps by status: `fully_unaddressed`, `partially_addressed`

6. **Persist to database:**
   - Update `Report` record: set `status = "completed"`, store summary statistics in `metadata` JSON field
   - Ensure all `Claim`, `Finding`, `Verdict` records are persisted (may already exist from earlier nodes)

7. **Emit completion event:** Append a `StreamEvent` with `event_type = "report_compiled"`, including summary statistics.

8. **Return partial state:** Return updated `events` and report status.

### 1.4 Report Compiler Service

The system shall implement a `ReportCompiler` service class:

```python
# app/services/report_compiler.py

class ReportCompiler:
    """Service for compiling Source of Truth reports from LangGraph state."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.paragraph_registry = self._load_paragraph_registry()

    async def compile_from_state(
        self,
        state: SibylState,
        report_id: str
    ) -> CompiledReport:
        """Compile report from LangGraph state.

        Returns:
            CompiledReport object with organized claims, gaps, and statistics.
        """
```

### 1.5 Pillar Organization Logic

Claims are organized by pillar based on their IFRS paragraph mappings:

```python
def organize_claims_by_pillar(
    verdicts: list[ClaimVerdict],
    claims: list[Claim]
) -> dict[str, list[ClaimWithVerdict]]:
    """Organize claims by IFRS pillar.

    Returns:
        Dictionary mapping pillar names to lists of claims with verdicts.
    """
    pillar_claims = {
        "governance": [],
        "strategy": [],
        "risk_management": [],
        "metrics_targets": [],
    }

    for verdict in verdicts:
        claim = find_claim_by_id(claims, verdict.claim_id)
        if not claim:
            continue

        # Extract IFRS paragraphs from verdict mapping
        paragraphs = extract_ifrs_paragraphs(verdict.ifrs_mapping)

        # Map paragraphs to pillars
        pillars = set()
        for para_id in paragraphs:
            pillar = map_paragraph_to_pillar(para_id)
            pillars.add(pillar)

        # Add claim to each relevant pillar
        claim_with_verdict = ClaimWithVerdict(claim=claim, verdict=verdict)
        for pillar in pillars:
            pillar_claims[pillar].append(claim_with_verdict)

    return pillar_claims
```

### 1.6 Summary Statistics Computation

```python
def compute_summary_statistics(
    verdicts: list[ClaimVerdict],
    gaps: list[AgentFinding],
    pillar_claims: dict[str, list]
) -> ReportSummary:
    """Compute summary statistics for the report."""

    total_claims = len(verdicts)

    verdicts_by_type = {
        "verified": sum(1 for v in verdicts if v.verdict == "verified"),
        "unverified": sum(1 for v in verdicts if v.verdict == "unverified"),
        "contradicted": sum(1 for v in verdicts if v.verdict == "contradicted"),
        "insufficient_evidence": sum(1 for v in verdicts if v.verdict == "insufficient_evidence"),
    }

    gaps_by_status = {
        "fully_unaddressed": sum(1 for g in gaps if g.details.get("gap_status") == "fully_unaddressed"),
        "partially_addressed": sum(1 for g in gaps if g.details.get("gap_status") == "partially_addressed"),
    }

    return ReportSummary(
        total_claims=total_claims,
        verdicts_by_type=verdicts_by_type,
        total_gaps=len(gaps),
        gaps_by_status=gaps_by_status,
    )
```

### 1.7 Database Persistence

The compiler persists the compiled report structure:

```python
async def persist_compiled_report(
    self,
    report_id: str,
    compiled_report: CompiledReport
) -> None:
    """Persist compiled report to database."""

    # Update Report record
    report = await self.db.get(Report, report_id)
    report.status = "completed"
    report.metadata = {
        "summary": compiled_report.summary.model_dump(),
        "compiled_at": datetime.utcnow().isoformat(),
    }
    await self.db.commit()

    # Ensure all claims, findings, verdicts are persisted
    # (They may already exist from earlier nodes, but ensure they're linked)
    for claim_with_verdict in compiled_report.pillar_claims.values():
        # Persist claim if not exists
        # Persist verdict if not exists
        # Link findings to claims
        pass
```

---

## 2. Report Data Model

### 2.1 Overview

The report data model defines how compiled report data is structured for frontend consumption. It includes organized claims, gaps, summary statistics, and metadata.

### 2.2 Compiled Report Structure

```python
class CompiledReport(BaseModel):
    """Compiled Source of Truth report structure."""

    report_id: str
    report_title: str | None
    compiled_at: datetime

    # Organized by pillar
    pillar_claims: dict[str, list[ClaimWithVerdict]]  # pillar -> claims
    pillar_gaps: dict[str, list[DisclosureGap]]  # pillar -> gaps

    # Summary statistics
    summary: ReportSummary

    # Metadata
    total_claims: int
    total_gaps: int
    pipeline_iterations: int
```

### 2.3 Claim with Verdict Structure

```python
class ClaimWithVerdict(BaseModel):
    """Claim paired with its verdict and findings."""

    claim: Claim
    verdict: ClaimVerdict
    findings: list[AgentFinding]  # All findings from investigating agents
    evidence_chain: list[EvidenceChainEntry]  # Chronological evidence flow
```

### 2.4 Evidence Chain Entry

```python
class EvidenceChainEntry(BaseModel):
    """Single entry in the evidence chain."""

    agent_name: str
    agent_color: str  # Hex color for UI
    finding: AgentFinding
    iteration: int  # Investigation cycle number
    timestamp: datetime
    reasoning: str  # Agent's reasoning text
```

### 2.5 Disclosure Gap Structure

```python
class DisclosureGap(BaseModel):
    """Disclosure gap finding."""

    gap_id: str
    paragraph_id: str
    pillar: str
    section: str
    requirement_text: str
    gap_status: str  # "fully_unaddressed" | "partially_addressed"
    missing_sub_requirements: list[str] | None
    materiality_context: str
    s1_counterpart: str | None
```

### 2.6 Report Summary Structure

```python
class ReportSummary(BaseModel):
    """Summary statistics for the report."""

    total_claims: int
    verdicts_by_type: dict[str, int]
    total_gaps: int
    gaps_by_status: dict[str, int]
```

---

## 3. Backend Report Endpoints

### 3.1 Overview

Backend report endpoints (`app/api/routes/report.py`) serve compiled report data via RESTful API. Endpoints support filtering, pagination, and efficient data retrieval.

### 3.2 Endpoint: Get Full Report

```
GET /api/v1/report/{reportId}

Response 200:
{
  "report_id": "uuid-...",
  "report_title": "Sustainability Report 2024",
  "compiled_at": "2026-02-09T15:30:00Z",
  "summary": {
    "total_claims": 87,
    "verdicts_by_type": {
      "verified": 45,
      "unverified": 20,
      "contradicted": 5,
      "insufficient_evidence": 17
    },
    "total_gaps": 23,
    "gaps_by_status": {
      "fully_unaddressed": 15,
      "partially_addressed": 8
    }
  },
  "pillars": {
    "governance": {
      "claims": [...],
      "gaps": [...]
    },
    ...
  }
}
```

### 3.3 Endpoint: Get Claims by Pillar

```
GET /api/v1/report/{reportId}/claims

Query Parameters:
  - pillar: string (optional) -- Filter by pillar
  - verdict: string (optional) -- Filter by verdict type
  - agent: string (optional) -- Filter by investigating agent
  - ifrs_paragraph: string (optional) -- Filter by IFRS paragraph ID
  - page: int (default: 1)
  - page_size: int (default: 50)

Response 200:
{
  "claims": [
    {
      "claim_id": "uuid-...",
      "claim_text": "...",
      "claim_type": "legal_governance",
      "source_page": 23,
      "source_location": {...},
      "ifrs_paragraphs": ["S1.27(a)", "S2.5"],
      "verdict": {
        "verdict": "verified",
        "reasoning": "...",
        "confidence": "high"
      },
      "findings": [...],
      "evidence_chain": [...]
    },
    ...
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 87,
    "total_pages": 2
  }
}
```

### 3.4 Endpoint: Get Disclosure Gaps

```
GET /api/v1/report/{reportId}/gaps

Query Parameters:
  - pillar: string (optional) -- Filter by pillar
  - gap_status: string (optional) -- "fully_unaddressed" | "partially_addressed"
  - page: int (default: 1)
  - page_size: int (default: 50)

Response 200:
{
  "gaps": [
    {
      "gap_id": "uuid-...",
      "paragraph_id": "S2.29(a)(iii)",
      "pillar": "metrics_targets",
      "section": "GHG Emissions",
      "requirement_text": "...",
      "gap_status": "fully_unaddressed",
      "missing_sub_requirements": null,
      "materiality_context": "Scope 3 emissions typically represent...",
      "s1_counterpart": "S1.46"
    },
    ...
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 23,
    "total_pages": 1
  }
}
```

### 3.5 Endpoint: Get Report Summary

```
GET /api/v1/report/{reportId}/summary

Response 200:
{
  "report_id": "uuid-...",
  "summary": {
    "total_claims": 87,
    "verdicts_by_type": {...},
    "total_gaps": 23,
    "gaps_by_status": {...}
  },
  "compiled_at": "2026-02-09T15:30:00Z"
}
```

### 3.6 Endpoint Implementation

```python
# app/api/routes/report.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/report", tags=["Report"])

@router.get("/{report_id}")
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db)
) -> ReportResponse:
    """Get full compiled report."""

@router.get("/{report_id}/claims")
async def get_report_claims(
    report_id: str,
    pillar: str | None = Query(None),
    verdict: str | None = Query(None),
    agent: str | None = Query(None),
    ifrs_paragraph: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> ClaimsListResponse:
    """Get claims with optional filtering."""

@router.get("/{report_id}/gaps")
async def get_report_gaps(
    report_id: str,
    pillar: str | None = Query(None),
    gap_status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> GapsListResponse:
    """Get disclosure gaps with optional filtering."""

@router.get("/{report_id}/summary")
async def get_report_summary(
    report_id: str,
    db: AsyncSession = Depends(get_db)
) -> ReportSummaryResponse:
    """Get report summary statistics."""
```

---

## 4. Report Page Layout

### 4.1 Overview

The Report Page (`src/pages/ReportPage.tsx`) is a full-width interactive dashboard displaying the Source of Truth report. It is organized by IFRS pillars with claim cards, disclosure gaps, filter bar, and summary statistics.

### 4.2 Page Structure

```typescript
// src/pages/ReportPage.tsx

interface ReportPageProps {
  reportId: string;
}

export function ReportPage({ reportId }: ReportPageProps) {
  const { report, loading, error } = useReport(reportId);
  const [filters, setFilters] = useState<ReportFilters>({});

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <ReportHeader report={report} />

      {/* Filter Bar */}
      <FilterBar filters={filters} onFiltersChange={setFilters} />

      {/* Summary Statistics */}
      <ComplianceSummary summary={report?.summary} />

      {/* Pillar Sections */}
      <div className="container mx-auto px-4 py-8 space-y-8">
        <PillarSection
          pillar="governance"
          claims={filteredClaims.governance}
          gaps={filteredGaps.governance}
          filters={filters}
        />
        <PillarSection
          pillar="strategy"
          claims={filteredClaims.strategy}
          gaps={filteredGaps.strategy}
          filters={filters}
        />
        <PillarSection
          pillar="risk_management"
          claims={filteredClaims.risk_management}
          gaps={filteredGaps.risk_management}
          filters={filters}
        />
        <PillarSection
          pillar="metrics_targets"
          claims={filteredClaims.metrics_targets}
          gaps={filteredGaps.metrics_targets}
          filters={filters}
        />
      </div>

      {/* S1/S2 Cross-Mapping Sidebar */}
      <S1S2MappingSidebar report={report} />
    </div>
  );
}
```

### 4.3 Layout Specifications

| Element | Specification |
|---|---|
| **Page width** | Full-width (no max-width container for main content) |
| **Background** | Dark mode background (`bg-background`) |
| **Spacing** | Generous whitespace between sections (py-8, space-y-8) |
| **Container** | Main content in container with horizontal padding (px-4) |
| **Responsive** | Stack sections vertically on mobile, side-by-side on desktop |

---

## 5. IFRS Pillar Sections

### 5.1 Overview

Pillar sections (`src/components/SourceOfTruth/PillarSection.tsx`) display claims and gaps organized by IFRS pillar. Each section shows a header with counts, claim cards, and disclosure gaps.

### 5.2 Pillar Section Component

```typescript
// src/components/SourceOfTruth/PillarSection.tsx

interface PillarSectionProps {
  pillar: "governance" | "strategy" | "risk_management" | "metrics_targets";
  claims: ClaimWithVerdict[];
  gaps: DisclosureGap[];
  filters: ReportFilters;
}

export function PillarSection({
  pillar,
  claims,
  gaps,
  filters,
}: PillarSectionProps) {
  const pillarInfo = PILLAR_INFO[pillar];

  return (
    <section className="space-y-6">
      {/* Pillar Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{pillarInfo.title}</h2>
          <p className="text-muted-foreground mt-1">
            {pillarInfo.description}
          </p>
        </div>
        <div className="text-right">
          <div className="text-sm text-muted-foreground">
            {claims.length} claims
          </div>
          <div className="text-sm text-muted-foreground">
            {gaps.length} gaps
          </div>
        </div>
      </div>

      {/* Claim Cards */}
      <div className="space-y-4">
        {claims.map((claimWithVerdict) => (
          <ClaimCard
            key={claimWithVerdict.claim.claim_id}
            claim={claimWithVerdict.claim}
            verdict={claimWithVerdict.verdict}
            findings={claimWithVerdict.findings}
            evidenceChain={claimWithVerdict.evidence_chain}
          />
        ))}
      </div>

      {/* Disclosure Gaps */}
      {gaps.length > 0 && (
        <DisclosureGapsSection gaps={gaps} pillar={pillar} />
      )}
    </section>
  );
}
```

### 5.3 Pillar Information

```typescript
const PILLAR_INFO = {
  governance: {
    title: "Governance",
    description: "S1.26-27, S2.5-7: Board oversight, competencies, reporting frequency, remuneration",
    s1_paragraphs: ["S1.26", "S1.27"],
    s2_paragraphs: ["S2.5", "S2.6", "S2.7"],
  },
  strategy: {
    title: "Strategy",
    description: "S1.28-35, S2.8-23: Risks and opportunities, business model effects, transition plans, financial effects",
    s1_paragraphs: ["S1.28", "S1.29", "S1.30", "S1.31", "S1.32", "S1.33", "S1.34", "S1.35"],
    s2_paragraphs: ["S2.8", "S2.9", "S2.10", "S2.11", "S2.12", "S2.13", "S2.14", "S2.15", "S2.16", "S2.17", "S2.18", "S2.19", "S2.20", "S2.21", "S2.22", "S2.23"],
  },
  risk_management: {
    title: "Risk Management",
    description: "S1.38-42, S2.24-26: Risk identification, assessment, prioritization, monitoring, integration",
    s1_paragraphs: ["S1.38", "S1.39", "S1.40", "S1.41", "S1.42"],
    s2_paragraphs: ["S2.24", "S2.25", "S2.26"],
  },
  metrics_targets: {
    title: "Metrics & Targets",
    description: "S1.43-53, S2.27-37: GHG emissions, intensity metrics, targets, internal carbon pricing",
    s1_paragraphs: ["S1.43", "S1.44", "S1.45", "S1.46", "S1.47", "S1.48", "S1.49", "S1.50", "S1.51", "S1.52", "S1.53"],
    s2_paragraphs: ["S2.27", "S2.28", "S2.29", "S2.30", "S2.31", "S2.32", "S2.33", "S2.34", "S2.35", "S2.36", "S2.37"],
  },
};
```

---

## 6. Claim Cards

### 6.1 Overview

Claim cards (`src/components/SourceOfTruth/ClaimCard.tsx`) are the core UI element displaying individual claims with their verdicts, IFRS mappings, and evidence chains. Each card is expandable to reveal full agent reasoning.

### 6.2 Claim Card Component

```typescript
// src/components/SourceOfTruth/ClaimCard.tsx

interface ClaimCardProps {
  claim: Claim;
  verdict: ClaimVerdict;
  findings: AgentFinding[];
  evidenceChain: EvidenceChainEntry[];
}

export function ClaimCard({
  claim,
  verdict,
  findings,
  evidenceChain,
}: ClaimCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const complianceColor = getComplianceColor(verdict.verdict);

  return (
    <Card className={`border-l-4 ${complianceColor.border}`}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            {/* Claim Text */}
            <p className="text-sm leading-relaxed">{claim.claim_text}</p>

            {/* PDF Link */}
            <Link
              to={`/analysis/${claim.report_id}?page=${claim.source_page}&highlight=${claim.claim_id}`}
              className="text-xs text-muted-foreground hover:underline mt-2 inline-flex items-center gap-1"
            >
              <FileText className="h-3 w-3" />
              View in PDF (page {claim.source_page})
            </Link>
          </div>

          {/* Verdict Badge */}
          <VerdictBadge verdict={verdict.verdict} />
        </div>

        {/* IFRS Paragraph Tags */}
        <div className="flex flex-wrap gap-2 mt-4">
          {verdict.ifrs_mapping.map((paraId) => (
            <IFRSParagraphTag key={paraId} paragraphId={paraId} />
          ))}
        </div>
      </CardHeader>

      <CardContent>
        {/* Expandable Evidence Chain */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full"
        >
          {isExpanded ? "Hide" : "Show"} Evidence Chain ({evidenceChain.length} entries)
          <ChevronDown className={`ml-2 h-4 w-4 transition-transform ${isExpanded ? "rotate-180" : ""}`} />
        </Button>

        {isExpanded && (
          <EvidencePanel
            evidenceChain={evidenceChain}
            findings={findings}
            verdict={verdict}
          />
        )}
      </CardContent>
    </Card>
  );
}
```

### 6.3 Verdict Badge Component

```typescript
// src/components/SourceOfTruth/VerdictBadge.tsx

interface VerdictBadgeProps {
  verdict: "verified" | "unverified" | "contradicted" | "insufficient_evidence";
}

export function VerdictBadge({ verdict }: VerdictBadgeProps) {
  const config = VERDICT_CONFIG[verdict];

  return (
    <Badge className={`${config.bgColor} ${config.textColor} border-0`}>
      {config.icon && <config.icon className="h-3 w-3 mr-1" />}
      {config.label}
    </Badge>
  );
}

const VERDICT_CONFIG = {
  verified: {
    label: "Verified",
    bgColor: "bg-green-500/20",
    textColor: "text-green-400",
    icon: CheckCircle,
  },
  unverified: {
    label: "Unverified",
    bgColor: "bg-yellow-500/20",
    textColor: "text-yellow-400",
    icon: AlertCircle,
  },
  contradicted: {
    label: "Contradicted",
    bgColor: "bg-red-500/20",
    textColor: "text-red-400",
    icon: XCircle,
  },
  insufficient_evidence: {
    label: "Insufficient Evidence",
    bgColor: "bg-yellow-500/20",
    textColor: "text-yellow-400",
    icon: AlertTriangle,
  },
};
```

### 6.4 IFRS Paragraph Tag Component

```typescript
// src/components/SourceOfTruth/IFRSParagraphTag.tsx

interface IFRSParagraphTagProps {
  paragraphId: string;
}

export function IFRSParagraphTag({ paragraphId }: IFRSParagraphTagProps) {
  return (
    <Badge variant="outline" className="font-mono text-xs">
      {paragraphId}
    </Badge>
  );
}
```

### 6.5 Compliance Color Coding

```typescript
function getComplianceColor(verdict: string): { border: string } {
  switch (verdict) {
    case "verified":
      return { border: "border-l-green-500" };
    case "unverified":
    case "insufficient_evidence":
      return { border: "border-l-yellow-500" };
    case "contradicted":
      return { border: "border-l-red-500" };
    default:
      return { border: "border-l-gray-500" };
  }
}
```

---

## 7. Evidence Chain Panel

### 7.1 Overview

The evidence chain panel (`src/components/SourceOfTruth/EvidencePanel.tsx`) displays the chronological sequence of agent findings and reasoning that led to the verdict. It shows each agent's contribution with agent color identity.

### 7.2 Evidence Panel Component

```typescript
// src/components/SourceOfTruth/EvidencePanel.tsx

interface EvidencePanelProps {
  evidenceChain: EvidenceChainEntry[];
  findings: AgentFinding[];
  verdict: ClaimVerdict;
}

export function EvidencePanel({
  evidenceChain,
  findings,
  verdict,
}: EvidencePanelProps) {
  return (
    <div className="mt-4 space-y-4 border-t pt-4">
      <h4 className="text-sm font-semibold">Evidence Chain</h4>

      {/* Agent Findings */}
      {evidenceChain.map((entry, index) => (
        <div
          key={`${entry.agent_name}-${entry.iteration}-${index}`}
          className="pl-4 border-l-2"
          style={{ borderColor: entry.agent_color }}
        >
          <div className="flex items-center gap-2 mb-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: entry.agent_color }}
            />
            <span className="text-sm font-medium capitalize">
              {entry.agent_name.replace("_", " ")}
            </span>
            {entry.iteration > 1 && (
              <Badge variant="outline" className="text-xs">
                Cycle {entry.iteration}
              </Badge>
            )}
          </div>

          <div className="text-sm text-muted-foreground mb-2">
            {entry.reasoning}
          </div>

          <div className="text-xs space-y-1">
            <div>
              <span className="font-medium">Evidence Type:</span>{" "}
              {entry.finding.evidence_type}
            </div>
            <div>
              <span className="font-medium">Summary:</span>{" "}
              {entry.finding.summary}
            </div>
            {entry.finding.supports_claim !== null && (
              <div>
                <span className="font-medium">Supports Claim:</span>{" "}
                {entry.finding.supports_claim ? "Yes" : "No"}
              </div>
            )}
            {entry.finding.confidence && (
              <div>
                <span className="font-medium">Confidence:</span>{" "}
                {entry.finding.confidence}
              </div>
            )}
          </div>
        </div>
      ))}

      {/* Judge Verdict */}
      <div className="pl-4 border-l-2 border-red-500 mt-4 pt-4 border-t">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span className="text-sm font-medium">Judge</span>
        </div>
        <div className="text-sm text-muted-foreground mb-2">
          {verdict.reasoning}
        </div>
        <div className="text-xs">
          <span className="font-medium">Final Verdict:</span>{" "}
          <VerdictBadge verdict={verdict.verdict} />
        </div>
      </div>
    </div>
  );
}
```

### 7.3 Agent Color Identity

```typescript
const AGENT_COLORS: Record<string, string> = {
  claims: "#64748b", // Slate blue
  orchestrator: "#ffffff", // White/silver
  geography: "#16a34a", // Forest green
  legal: "#9333ea", // Deep purple
  news_media: "#f59e0b", // Amber/gold
  academic: "#14b8a6", // Teal
  data_metrics: "#f97316", // Coral/orange
  judge: "#dc2626", // Crimson red
};
```

---

## 8. S1/S2 Cross-Mapping Sidebar

### 8.1 Overview

The S1/S2 cross-mapping sidebar (`src/components/SourceOfTruth/S1S2MappingSidebar.tsx`) shows how S2 climate paragraphs fulfill S1 general requirements. It highlights which paragraphs are covered and which are gaps.

### 8.2 Sidebar Component

```typescript
// src/components/SourceOfTruth/S1S2MappingSidebar.tsx

interface S1S2MappingSidebarProps {
  report: CompiledReport;
}

export function S1S2MappingSidebar({ report }: S1S2MappingSidebarProps) {
  const [isOpen, setIsOpen] = useState(false);
  const mapping = useS1S2Mapping();

  return (
    <>
      {/* Toggle Button */}
      <Button
        variant="outline"
        className="fixed right-4 top-1/2 -translate-y-1/2 z-50"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Map className="h-4 w-4 mr-2" />
        S1/S2 Mapping
      </Button>

      {/* Sidebar */}
      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetContent side="right" className="w-[400px] overflow-y-auto">
          <SheetHeader>
            <SheetTitle>S1/S2 Cross-Mapping</SheetTitle>
            <SheetDescription>
              How S2 climate paragraphs fulfill S1 general requirements
            </SheetDescription>
          </SheetHeader>

          <div className="mt-6 space-y-4">
            {Object.entries(mapping).map(([s1Paragraph, s2Paragraphs]) => (
              <div key={s1Paragraph} className="border rounded-lg p-4">
                <div className="font-mono text-sm font-semibold mb-2">
                  {s1Paragraph}
                </div>
                <div className="space-y-2">
                  {s2Paragraphs.map((s2Para) => {
                    const status = getParagraphStatus(s2Para, report);
                    return (
                      <div
                        key={s2Para}
                        className={`flex items-center justify-between p-2 rounded ${
                          status === "covered"
                            ? "bg-green-500/20"
                            : status === "gap"
                            ? "bg-gray-500/20"
                            : "bg-yellow-500/20"
                        }`}
                      >
                        <span className="font-mono text-xs">{s2Para}</span>
                        <Badge variant="outline" className="text-xs">
                          {status === "covered" ? "Covered" : status === "gap" ? "Gap" : "Partial"}
                        </Badge>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
```

### 8.3 Paragraph Status Logic

```typescript
function getParagraphStatus(
  paragraphId: string,
  report: CompiledReport
): "covered" | "gap" | "partial" {
  // Check if paragraph is mapped to any claim
  const hasClaim = report.pillar_claims.some((claims) =>
    claims.some((c) => c.verdict.ifrs_mapping.includes(paragraphId))
  );

  // Check if paragraph is a gap
  const gap = report.pillar_gaps.find(
    (g) => g.paragraph_id === paragraphId
  );

  if (hasClaim && !gap) {
    return "covered";
  } else if (gap?.gap_status === "fully_unaddressed") {
    return "gap";
  } else {
    return "partial";
  }
}
```

---

## 9. Disclosure Gaps Section

### 9.1 Overview

The disclosure gaps section (`src/components/SourceOfTruth/DisclosureGapsSection.tsx`) displays IFRS requirements that are fully unaddressed (grey) or partially addressed (orange) in the report, organized by pillar.

### 9.2 Disclosure Gaps Component

```typescript
// src/components/SourceOfTruth/DisclosureGapsSection.tsx

interface DisclosureGapsSectionProps {
  gaps: DisclosureGap[];
  pillar: string;
}

export function DisclosureGapsSection({
  gaps,
  pillar,
}: DisclosureGapsSectionProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="mt-8 border-t pt-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">
            What this report does NOT disclose
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            IFRS requirements not addressed or partially addressed
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? "Collapse" : "Expand"} ({gaps.length})
        </Button>
      </div>

      {isExpanded && (
        <div className="space-y-3">
          {gaps.map((gap) => (
            <GapCard key={gap.gap_id} gap={gap} />
          ))}
        </div>
      )}
    </div>
  );
}
```

### 9.3 Gap Card Component

```typescript
// src/components/SourceOfTruth/GapCard.tsx

interface GapCardProps {
  gap: DisclosureGap;
}

export function GapCard({ gap }: GapCardProps) {
  const gapColor =
    gap.gap_status === "fully_unaddressed"
      ? "bg-gray-500/20 border-gray-500"
      : "bg-orange-500/20 border-orange-500";

  return (
    <Card className={`${gapColor} border-l-4`}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="outline" className="font-mono">
                {gap.paragraph_id}
              </Badge>
              <Badge
                variant={
                  gap.gap_status === "fully_unaddressed" ? "secondary" : "default"
                }
              >
                {gap.gap_status === "fully_unaddressed"
                  ? "Fully Unaddressed"
                  : "Partially Addressed"}
              </Badge>
            </div>
            <h4 className="text-sm font-semibold mb-1">{gap.requirement_text}</h4>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {gap.missing_sub_requirements && (
          <div className="mb-3">
            <p className="text-xs font-medium mb-1">Missing Sub-Requirements:</p>
            <ul className="text-xs text-muted-foreground list-disc list-inside space-y-1">
              {gap.missing_sub_requirements.map((req, idx) => (
                <li key={idx}>{req}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="text-xs text-muted-foreground">
          <p className="font-medium mb-1">Why this matters:</p>
          <p>{gap.materiality_context}</p>
        </div>

        {gap.s1_counterpart && (
          <div className="mt-3 text-xs">
            <span className="text-muted-foreground">S1 Counterpart: </span>
            <Badge variant="outline" className="font-mono text-xs">
              {gap.s1_counterpart}
            </Badge>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

---

## 10. Filter Bar

### 10.1 Overview

The filter bar (`src/components/SourceOfTruth/FilterBar.tsx`) enables filtering claims and gaps by pillar, claim type, verdict status, investigating agent, IFRS paragraph search, and disclosure gap status.

### 10.2 Filter Bar Component

```typescript
// src/components/SourceOfTruth/FilterBar.tsx

interface FilterBarProps {
  filters: ReportFilters;
  onFiltersChange: (filters: ReportFilters) => void;
}

export function FilterBar({ filters, onFiltersChange }: FilterBarProps) {
  return (
    <div className="border-b bg-card sticky top-0 z-40">
      <div className="container mx-auto px-4 py-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* Pillar Filter */}
          <Select
            value={filters.pillar || "all"}
            onValueChange={(value) =>
              onFiltersChange({ ...filters, pillar: value === "all" ? undefined : value })
            }
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All Pillars" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Pillars</SelectItem>
              <SelectItem value="governance">Governance</SelectItem>
              <SelectItem value="strategy">Strategy</SelectItem>
              <SelectItem value="risk_management">Risk Management</SelectItem>
              <SelectItem value="metrics_targets">Metrics & Targets</SelectItem>
            </SelectContent>
          </Select>

          {/* Claim Type Filter */}
          <Select
            value={filters.claim_type || "all"}
            onValueChange={(value) =>
              onFiltersChange({ ...filters, claim_type: value === "all" ? undefined : value })
            }
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="geographic">Geographic</SelectItem>
              <SelectItem value="quantitative">Quantitative</SelectItem>
              <SelectItem value="legal_governance">Legal/Governance</SelectItem>
              <SelectItem value="strategic">Strategic</SelectItem>
              <SelectItem value="environmental">Environmental</SelectItem>
            </SelectContent>
          </Select>

          {/* Verdict Filter */}
          <Select
            value={filters.verdict || "all"}
            onValueChange={(value) =>
              onFiltersChange({ ...filters, verdict: value === "all" ? undefined : value })
            }
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All Verdicts" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Verdicts</SelectItem>
              <SelectItem value="verified">Verified</SelectItem>
              <SelectItem value="unverified">Unverified</SelectItem>
              <SelectItem value="contradicted">Contradicted</SelectItem>
              <SelectItem value="insufficient_evidence">Insufficient Evidence</SelectItem>
            </SelectContent>
          </Select>

          {/* Agent Filter */}
          <Select
            value={filters.agent || "all"}
            onValueChange={(value) =>
              onFiltersChange({ ...filters, agent: value === "all" ? undefined : value })
            }
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All Agents" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Agents</SelectItem>
              <SelectItem value="geography">Geography</SelectItem>
              <SelectItem value="legal">Legal</SelectItem>
              <SelectItem value="news_media">News/Media</SelectItem>
              <SelectItem value="academic">Academic</SelectItem>
              <SelectItem value="data_metrics">Data/Metrics</SelectItem>
            </SelectContent>
          </Select>

          {/* IFRS Paragraph Search */}
          <Input
            placeholder="Search IFRS paragraph (e.g., S2.14(a)(iv))"
            value={filters.ifrs_paragraph || ""}
            onChange={(e) =>
              onFiltersChange({ ...filters, ifrs_paragraph: e.target.value || undefined })
            }
            className="w-[250px]"
          />

          {/* Gap Status Filter */}
          <Select
            value={filters.gap_status || "all"}
            onValueChange={(value) =>
              onFiltersChange({ ...filters, gap_status: value === "all" ? undefined : value })
            }
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All Gaps" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Gaps</SelectItem>
              <SelectItem value="fully_unaddressed">Fully Unaddressed</SelectItem>
              <SelectItem value="partially_addressed">Partially Addressed</SelectItem>
            </SelectContent>
          </Select>

          {/* Clear Filters */}
          {(filters.pillar || filters.claim_type || filters.verdict || filters.agent || filters.ifrs_paragraph || filters.gap_status) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onFiltersChange({})}
            >
              Clear Filters
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
```

### 10.3 Filter Type Definition

```typescript
interface ReportFilters {
  pillar?: "governance" | "strategy" | "risk_management" | "metrics_targets";
  claim_type?: string;
  verdict?: "verified" | "unverified" | "contradicted" | "insufficient_evidence";
  agent?: string;
  ifrs_paragraph?: string;
  gap_status?: "fully_unaddressed" | "partially_addressed";
}
```

---

## 11. Compliance Summary Statistics

### 11.1 Overview

The compliance summary (`src/components/SourceOfTruth/ComplianceSummary.tsx`) displays overview statistics: total claims, verdicts by type, coverage percentage by pillar, and disclosure gap counts.

### 11.2 Summary Component

```typescript
// src/components/SourceOfTruth/ComplianceSummary.tsx

interface ComplianceSummaryProps {
  summary: ReportSummary;
}

export function ComplianceSummary({ summary }: ComplianceSummaryProps) {
  return (
    <div className="border-b bg-card">
      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Total Claims */}
          <StatCard
            label="Total Claims"
            value={summary.total_claims}
            icon={FileText}
          />

          {/* Verdicts Breakdown */}
          <StatCard
            label="Verified"
            value={summary.verdicts_by_type.verified}
            icon={CheckCircle}
            color="text-green-400"
          />
          <StatCard
            label="Unverified"
            value={summary.verdicts_by_type.unverified}
            icon={AlertCircle}
            color="text-yellow-400"
          />
          <StatCard
            label="Contradicted"
            value={summary.verdicts_by_type.contradicted}
            icon={XCircle}
            color="text-red-400"
          />

          {/* Disclosure Gaps */}
          <StatCard
            label="Total Gaps"
            value={summary.total_gaps}
            icon={AlertTriangle}
            color="text-orange-400"
          />
        </div>
      </div>
    </div>
  );
}
```

---

## 12. Frontend State Management

### 12.1 Overview

The `useReport` hook (`src/hooks/useReport.ts`) manages report data fetching, filtering logic, and state updates.

### 12.2 useReport Hook

```typescript
// src/hooks/useReport.ts

interface UseReportReturn {
  report: CompiledReport | null;
  loading: boolean;
  error: string | null;
  filteredClaims: Record<string, ClaimWithVerdict[]>;
  filteredGaps: Record<string, DisclosureGap[]>;
  refetch: () => Promise<void>;
}

export function useReport(
  reportId: string,
  filters?: ReportFilters
): UseReportReturn {
  const [report, setReport] = useState<CompiledReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchReport(reportId, filters).then(setReport).catch(setError).finally(() => setLoading(false));
  }, [reportId, filters]);

  const filteredClaims = useMemo(() => {
    if (!report) return {};
    return applyFiltersToClaims(report.pillar_claims, filters);
  }, [report, filters]);

  const filteredGaps = useMemo(() => {
    if (!report) return {};
    return applyFiltersToGaps(report.pillar_gaps, filters);
  }, [report, filters]);

  return { report, loading, error, filteredClaims, filteredGaps, refetch };
}
```

### 12.3 Filter Application Logic

```typescript
function applyFiltersToClaims(
  pillarClaims: Record<string, ClaimWithVerdict[]>,
  filters?: ReportFilters
): Record<string, ClaimWithVerdict[]> {
  if (!filters) return pillarClaims;

  const filtered: Record<string, ClaimWithVerdict[]> = {};

  for (const [pillar, claims] of Object.entries(pillarClaims)) {
    if (filters.pillar && filters.pillar !== pillar) continue;

    filtered[pillar] = claims.filter((c) => {
      if (filters.claim_type && c.claim.claim_type !== filters.claim_type) return false;
      if (filters.verdict && c.verdict.verdict !== filters.verdict) return false;
      if (filters.agent && !c.findings.some((f) => f.agent_name === filters.agent)) return false;
      if (filters.ifrs_paragraph && !c.verdict.ifrs_mapping.includes(filters.ifrs_paragraph)) return false;
      return true;
    });
  }

  return filtered;
}
```

---

## 13. Navigation and Routing

### 13.1 Overview

The Report Page is integrated into the application routing. Navigation from the Analysis Page or PDF viewer links to the report with proper state management.

### 13.2 Route Configuration

```typescript
// src/App.tsx

<Routes>
  <Route path="/" element={<HomePage />} />
  <Route path="/analysis/:reportId" element={<AnalysisPage />} />
  <Route path="/report/:reportId" element={<ReportPage />} />
</Routes>
```

### 13.3 PDF Link Navigation

When a user clicks a PDF link in a claim card:

```typescript
<Link
  to={`/analysis/${claim.report_id}?page=${claim.source_page}&highlight=${claim.claim_id}`}
>
  View in PDF (page {claim.source_page})
</Link>
```

The Analysis Page handles the `highlight` query parameter to scroll to and highlight the claim in the PDF viewer.

---

## 14. Error Handling

### 14.1 Backend Errors

| Error | Trigger | Handling |
|---|---|---|
| Report not found | Invalid report_id | Return 404 with error message |
| Report not compiled | Report status is not "completed" | Return 400 with message "Report compilation in progress" |
| Database query failure | PostgreSQL error | Return 500 with generic error message, log details |
| Pagination overflow | Page number exceeds total pages | Return empty results array, valid pagination metadata |

### 14.2 Frontend Errors

| Error | Trigger | Handling |
|---|---|---|
| API request failure | Network error, 500 response | Display error toast, show retry button |
| Report not found | 404 response | Navigate to 404 page or show "Report not found" message |
| Filter application error | Invalid filter combination | Reset filters, show error message |
| PDF link navigation failure | Invalid page number | Show error toast, fallback to PDF viewer without highlight |

---

## 15. Exit Criteria

FRD 13 is complete when ALL of the following are satisfied:

| # | Criterion | Verification |
|---|---|---|
| 1 | `compile_report` node replaces FRD 5 stub | `compile_report` function is implemented and functional |
| 2 | Report compilation reads state correctly | Verify all verdicts, findings, and gaps are read from state |
| 3 | Claims organized by pillar | Verify claims are grouped into four pillar sections |
| 4 | Disclosure gaps organized by pillar | Verify gaps are grouped by pillar |
| 5 | Summary statistics computed | Verify totals, verdicts by type, coverage percentages are calculated |
| 6 | Report persisted to database | Verify Report status is "completed", metadata stored |
| 7 | Backend endpoints serve data | Test GET /api/v1/report/{reportId} and sub-endpoints |
| 8 | Report page renders | Navigate to /report/{reportId}, verify page loads |
| 9 | Pillar sections display | Verify four pillar sections are rendered with correct claims and gaps |
| 10 | Claim cards render | Verify claim cards show claim text, IFRS tags, verdict badge |
| 11 | PDF links work | Click PDF link, verify navigation to PDF viewer with highlight |
| 12 | Evidence chain expands | Click "Show Evidence Chain", verify panel expands with agent findings |
| 13 | Evidence chain shows agent colors | Verify each agent's section uses correct color identity |
| 14 | Disclosure gaps section displays | Verify gaps section appears below claim cards in each pillar |
| 15 | Gap cards show correct colors | Verify fully unaddressed=grey, partially addressed=orange |
| 16 | Gap cards show materiality context | Verify each gap includes "Why this matters" explanation |
| 17 | S1/S2 sidebar opens | Click S1/S2 Mapping button, verify sidebar opens |
| 18 | S1/S2 mapping displays | Verify S1-S2 paragraph relationships are shown |
| 19 | Filter bar filters claims | Apply pillar filter, verify only that pillar's claims show |
| 20 | Filter bar filters gaps | Apply gap_status filter, verify only matching gaps show |
| 21 | IFRS paragraph search works | Search for "S2.14(a)(iv)", verify matching claims/gaps appear |
| 22 | Multiple filters combine | Apply pillar + verdict filters, verify both are applied |
| 23 | Summary statistics display | Verify total claims, verdicts, coverage percentages are shown |
| 24 | Report is comprehensive | Verify every claim is present, every IFRS requirement is accounted for |
| 25 | Error handling works | Simulate API error, verify graceful error display |

---

## Appendix A: Report API Response Schemas

### A.1 ReportResponse Schema

```python
class ReportResponse(BaseModel):
    report_id: str
    report_title: str | None
    compiled_at: datetime
    summary: ReportSummary
    pillars: dict[str, PillarData]

class PillarData(BaseModel):
    claims: list[ClaimWithVerdictResponse]
    gaps: list[DisclosureGapResponse]
```

### A.2 ClaimWithVerdictResponse Schema

```python
class ClaimWithVerdictResponse(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: str
    source_page: int
    source_location: dict
    ifrs_paragraphs: list[str]
    verdict: VerdictResponse
    findings: list[FindingResponse]
    evidence_chain: list[EvidenceChainEntryResponse]
```

---

## Appendix B: Claim Card Layout Specification

### B.1 Card Dimensions

| Element | Specification |
|---|---|
| **Card width** | Full width of container (responsive) |
| **Card padding** | p-4 (CardHeader), p-6 (CardContent) |
| **Border** | Left border 4px, color-coded by compliance status |
| **Spacing** | space-y-4 between cards |

### B.2 Typography

| Element | Font Size | Weight | Color |
|---|---|---|---|
| Claim text | text-sm | normal | foreground |
| PDF link | text-xs | normal | muted-foreground |
| IFRS tags | text-xs | normal | foreground (mono) |
| Verdict badge | text-xs | medium | Color-coded |

---

## Appendix C: Filter Bar Options Reference

| Filter | Options | Default |
|---|---|---|
| **Pillar** | All, Governance, Strategy, Risk Management, Metrics & Targets | All |
| **Claim Type** | All, Geographic, Quantitative, Legal/Governance, Strategic, Environmental | All |
| **Verdict** | All, Verified, Unverified, Contradicted, Insufficient Evidence | All |
| **Agent** | All, Geography, Legal, News/Media, Academic, Data/Metrics | All |
| **IFRS Paragraph** | Free text search (e.g., "S2.14(a)(iv)") | Empty |
| **Gap Status** | All, Fully Unaddressed, Partially Addressed | All |

---

## Appendix D: Color Coding Reference

### D.1 Verdict Colors

| Verdict | Background | Text | Border |
|---|---|---|---|
| Verified | bg-green-500/20 | text-green-400 | border-green-500 |
| Unverified | bg-yellow-500/20 | text-yellow-400 | border-yellow-500 |
| Contradicted | bg-red-500/20 | text-red-400 | border-red-500 |
| Insufficient Evidence | bg-yellow-500/20 | text-yellow-400 | border-yellow-500 |

### D.2 Gap Status Colors

| Status | Background | Border |
|---|---|---|
| Fully Unaddressed | bg-gray-500/20 | border-gray-500 |
| Partially Addressed | bg-orange-500/20 | border-orange-500 |

### D.3 Agent Colors

| Agent | Hex Color |
|---|---|
| Claims | #64748b (Slate blue) |
| Orchestrator | #ffffff (White/silver) |
| Geography | #16a34a (Forest green) |
| Legal | #9333ea (Deep purple) |
| News/Media | #f59e0b (Amber/gold) |
| Academic | #14b8a6 (Teal) |
| Data/Metrics | #f97316 (Coral/orange) |
| Judge | #dc2626 (Crimson red) |

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| Full-width report page over constrained width | The report contains dense information (claims, gaps, evidence chains). Full width maximizes screen real estate and reduces scrolling. |
| Pillar-based organization over flat list | PRD Section 4.11 specifies organization by IFRS pillars. Pillar organization aligns with IFRS structure and makes compliance assessment intuitive. |
| Expandable evidence chains over always-visible | Evidence chains can be lengthy (multiple agents, re-investigations). Expandable UI reduces visual clutter while preserving full transparency on demand. |
| Color-coded compliance status over text-only | Visual color coding (green/yellow/red) enables quick scanning of compliance status. Users can identify problematic claims at a glance. |
| Disclosure gaps as separate section over inline | PRD Section 4.11 specifies gaps as a "dedicated section". Separate section emphasizes selective disclosure detection, a core Sibyl value proposition. |
| S1/S2 cross-mapping in sidebar over inline | Cross-mapping is supplementary information. Sidebar keeps it accessible without cluttering the main report view. |
| Filter bar sticky at top over scrollable | Sticky filter bar ensures filters remain accessible while scrolling through long reports. Users can adjust filters without scrolling back to top. |
| Backend compilation over frontend-only organization | Backend compilation pre-organizes data, reducing frontend computation. Database queries with filters are more efficient than client-side filtering of large datasets. |
| Pagination on backend endpoints over load-all | Large reports may contain 100+ claims. Pagination prevents frontend performance issues and reduces initial load time. |
| PDF links navigate to Analysis Page over embedded viewer | Analysis Page already has PDF viewer infrastructure (FRD 4). Reusing existing viewer avoids duplication and maintains consistency. |
| Materiality context in gap cards over bare gap listing | PRD Section 4.11 requires materiality context. Explaining why gaps matter helps users understand significance and prioritize remediation. |
| Agent color identity in evidence chain over uniform styling | Agent colors (from PRD Section 7.1) provide visual continuity with the detective dashboard (FRD 12). Users can trace evidence back to specific agents. |
| Verdict badge with icon over text-only | Icons (checkmark, X, alert) provide immediate visual recognition of verdict type, complementing color coding. |
| IFRS paragraph tags as badges over plain text | Badge styling makes paragraph identifiers (e.g., "S2.14(a)(iv)") visually distinct and easy to scan. Monospace font improves readability of technical identifiers. |
| Summary statistics in header over bottom | Summary statistics provide context before users dive into details. Header placement ensures visibility without scrolling. |
| Filter combination (AND logic) over OR logic | AND logic (all filters must match) provides precise filtering. Users can narrow down to specific subsets (e.g., "Verified claims in Governance pillar"). OR logic would be less useful for compliance analysis. |
| Report compilation as LangGraph node over separate service | Compilation is the final step of the pipeline. Making it a LangGraph node ensures it runs automatically after Judge completes, maintains state consistency, and enables checkpointing. |
| Persist compiled structure over recompute on demand | Pre-computing pillar organization and statistics enables fast frontend rendering. Recomputing on every request would add latency and database load. |
| Gap status color coding (grey/orange) over single color | Distinguishing fully unaddressed (grey) from partially addressed (orange) helps users prioritize. Fully unaddressed gaps are more severe than partial gaps. |
| Evidence chain chronological order over grouped by agent | Chronological order shows the investigation flow (which agent worked when, re-investigation cycles). This provides transparency into the investigative process. |
| Judge reasoning at end of evidence chain over beginning | Judge reasoning synthesizes all agent findings. Placing it at the end follows the logical flow: evidence → synthesis → verdict. |
| Report comprehensiveness requirement | PRD Section 4.11 states the report "does not degrade the complexity of the underlying document". Every claim and every IFRS requirement must be accounted for, ensuring the report is a complete compliance analysis. |

---

## Appendix F: Implementation Updates (2026-02-27)

This appendix documents divergences from the v1.0 specification and new features added during implementation.

### F.1 Design System -- Warm Cream Theme

The v1.0 spec assumed a dark theme aligned with the planned dashboard design. The implemented design uses the warm cream design system throughout the report page:

- **Backgrounds:** `#fff6e9` (warm cream) -- no pure white containers
- **Text:** `#4a3c2e` (body), `#6b5344` (labels), `#8b7355` (muted)
- **Borders:** `#e0d4bf` -- no `slate-200`
- **Prohibited:** All `text-slate-*`, `bg-slate-*`, `border-slate-*` classes
- **Footer:** Bottom divider (`border-t`) removed from the report footer
- **Buttons:** All action buttons (including the report-level "View Analysis" button) styled consistently with the "Begin Analysis" button: warm cream background, `#4a3c2e` text, no bright colors

### F.2 IFRS Paragraph Hover Tooltips (IFRSParagraphTag)

**Planned (v1.0):** IFRS paragraph identifiers rendered as plain badge components.

**Implemented:** `IFRSParagraphTag.tsx` upgraded to a proper hover popover:

- **Frontend registry:** `src/data/paragraphRegistry.ts` contains all 44 IFRS paragraph entries from `backend/data/ifrs/paragraph_registry.json`
- **Data per entry:** paragraph ID, section name, full requirement text
- **Popover content:** Shows paragraph ID, section name, and full requirement excerpt on hover
- **Prefix-match fallback:** `getParagraphInfo()` performs an exact lookup first; if not found (e.g., `"S2.14(a)(i)"`), it tries progressively shorter prefixes (`"S2.14(a)"`, `"S2.14"`) to find a parent section. This ensures all IFRS section pills show tooltip information, including non-disclosure S-heading sections
- **Applies everywhere:** Tooltips work in the report view, the analysis dashboard, and the cross-mapping sidebar

### F.3 S1/S2 Cross-Mapping Sidebar Redesign

**Planned (v1.0):** Basic collapsible sidebar showing S1-S2 paragraph relationships.

**Implemented (`S1S2MappingSidebar.tsx`):** Full UX redesign with:

- **Introductory paragraph:** Plain-language explanation of how S1 and S2 relate, so users unfamiliar with the standards understand the panel
- **Visual flow arrows:** Horizontal arrows between S1 pillars and their S2 climate counterparts, making the structural relationship immediately visible
- **Expandable claim lists:** Claims mapped to each S1/S2 relationship are in collapsible accordion sections, preventing information overload
- **Toggle tab styling:** Updated toggle between "S1 Coverage" and "S2 Mapping" views uses warm cream active state
- **Close button:** Hover removes brown background box; only text color changes

### F.4 Report List Page Redesign

**Planned (v1.0):** Standard list page with basic report cards.

**Implemented (`ReportPage.tsx` list view):**

- **Heading:** Large centered heading (`2.75rem`, near-landing-page scale) with a subheading, both center-aligned, positioned near the vertical center of the viewport
- **No top/bottom dividers:** The main list container has no `borderTop` or `borderBottom`; individual list items have no `borderBottom` either
- **Stagger animation:** List items fade in one after another with `delay: i * 0.05s`, `duration: 0.22s` -- fast and subtle
- **Hover effect:** Items underline their filename text on hover instead of darkening the container background (`whileHover` uses `textDecoration: "underline"` on the filename element)
- **Blur-fade entrance:** The heading and subheading use Framer Motion blur-fade-in matching the landing page's animation style

### F.5 Report Page Footer

The footer `div` in `ReportPage.tsx` no longer has `border-t border-[#e0d4bf]` -- the top border was removed for a cleaner visual separation between the report content and the footer area.

### F.6 Close Button Hover Standardization

All close/dismiss buttons in the report section (cross-mapping sidebar, highlight tooltip, etc.) have the hover brown background box removed. Only the `color` transitions on hover, not the background. This applies to:

- `S1S2MappingSidebar.tsx` close button: removed `hover:bg-[#eddfc8] rounded`
- `HighlightTooltip.tsx` close button: `background: transparent` on hover (via `index.css` override)

### F.7 File Changes Summary

| File | Change |
|---|---|
| `src/data/paragraphRegistry.ts` | **New file.** 44-entry IFRS paragraph registry with `getParagraphInfo()` prefix-match fallback |
| `src/components/SourceOfTruth/IFRSParagraphTag.tsx` | Upgraded to hover popover using `paragraphRegistry` |
| `src/components/SourceOfTruth/S1S2MappingSidebar.tsx` | Full UX redesign: intro text, flow arrows, expandable claim lists, updated toggle tabs |
| `src/pages/ReportPage.tsx` | List view redesign: large centered heading, stagger fade-in, underline hover, no dividers; footer border removed |
| `src/index.css` | Added `.report-list-item__filename:hover { text-decoration: underline; }` |
