# Feature Requirements Document: FRD 8 -- News/Media Agent (v1.0)

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.3](../PRD.md) |
| **FRD Order** | [FRD Order](../FRD-order.md) |
| **PRD Sections** | 4.6 (News/Media Agent -- Public Source Verification) |
| **Type** | Feature |
| **Depends On** | FRD 5 (Orchestrator Agent & LangGraph Pipeline) |
| **Delivers** | Web search tool integration (`search_web.py`), source credibility tiering (Tier 1-4), investigation of company-specific and industry-wide news coverage, evidence output with source URLs, publication dates, credibility tiers, relevance summaries, contradiction detection, inter-agent communication participation, LangGraph node `investigate_news` (`news_media_agent.py`), StreamEvent emissions, re-investigation handling |
| **Created** | 2026-02-09 |

---

## Summary

FRD 8 delivers the News/Media Agent -- a specialist investigation agent in the Sibyl multi-agent pipeline that scours public news sources, press releases, and investigative journalism for corroboration or contradiction of specific sustainability claims. The agent replaces the `investigate_news` stub defined in FRD 5 Section 6 with a fully functional LangGraph node (`app/agents/news_media_agent.py`) that receives routed claims from the Orchestrator, constructs targeted search queries (company-specific, industry-wide, controversy-focused), executes web searches via a shared web search tool (`app/agents/tools/search_web.py`), evaluates source credibility using a four-tier classification system (Tier 1: major investigative journalism and regulatory actions; Tier 2: established news organizations and government reports; Tier 3: company press releases and wire services; Tier 4: blogs and unverified sources), analyzes search results for relevance and contradiction, and produces structured evidence findings with source URLs, publication dates, credibility tiers, relevance summaries, and contradiction flags. The agent participates in the inter-agent communication protocol (InfoRequest/InfoResponse) and handles re-investigation requests from the Judge Agent with refined queries. The web search tool (`search_web.py`) is fully defined in this FRD and will be reused by FRD 9 (Academic/Research Agent). The agent uses Claude Sonnet 4.5 for source analysis, credibility assessment, and nuanced reasoning about corroboration versus contradiction. After FRD 8, given routed claims, the agent searches public news sources and returns credibility-weighted evidence with contradiction flags.

---

## Given Context (Preconditions)

The following are assumed to be in place from prior FRDs:

| Prerequisite | Source FRD | Deliverable |
|---|---|---|
| Docker Compose with PostgreSQL 17 + pgvector, Redis, backend, frontend | FRD 0 | `docker-compose.yml` |
| `SibylState` Pydantic schema with `Claim`, `RoutingAssignment`, `AgentFinding`, `InfoRequest`, `InfoResponse`, `ReinvestigationRequest`, `StreamEvent` | FRD 0 | `app/agents/state.py` |
| LangGraph StateGraph compiled with all nodes including `investigate_news` stub | FRD 5 | `app/agents/graph.py` |
| Orchestrator Agent routing claims to specialist agents | FRD 5 | `app/agents/orchestrator_agent.py` |
| Inter-agent communication protocol (InfoRequest/InfoResponse) | FRD 5 | Shared state mechanism |
| Re-investigation handling in Orchestrator | FRD 5 | `ReinvestigationRequest` processing |
| SSE streaming infrastructure | FRD 5 | `app/api/routes/stream.py`, callback handler |
| OpenRouter client wrapper with retry logic and `Models.CLAUDE_SONNET` constant | FRD 0 | `app/services/openrouter_client.py` |
| `investigate_news` stub that accepts routed claims and returns placeholder findings | FRD 5 | `app/agents/news_media_agent.py` |
| `AgentFinding` schema with `agent_name`, `claim_id`, `evidence_type`, `summary`, `details`, `supports_claim`, `confidence`, `iteration` | FRD 0 | `app/agents/state.py` |
| Frontend agent reasoning panel displaying SSE events | FRD 5 | `src/components/Analysis/AgentReasoningPanel.tsx` |
| Claims extracted with `claim_text`, `claim_type`, `source_page`, `ifrs_paragraphs` | FRD 3 | `claims` database table |
| Report record with company name and metadata | FRD 2 | `reports` database table |

### Terms

| Term | Definition |
|---|---|
| Web search tool | A LangChain tool (`search_web.py`) that executes web searches via a search API (Tavily, Brave Search, or SerpAPI) and returns structured results |
| Source credibility tier | A four-tier classification (Tier 1-4) ranking the reliability and weight of a news source for verification purposes |
| Contradiction detection | The process of identifying when public reporting directly contradicts or challenges a claim made in the sustainability report |
| Company-specific search | A search query targeting news coverage specifically about the reporting company and its sustainability claims |
| Industry-wide search | A search query targeting broader industry trends, incidents, or regulatory patterns relevant to the claim |
| Controversy-focused search | A search query designed to surface negative coverage, whistleblower reports, or enforcement actions related to the claim |
| Evidence finding | An `AgentFinding` object produced by the News/Media Agent containing source URLs, dates, tiers, summaries, and contradiction flags |
| Relevance summary | A plain-language explanation of how a search result relates to the specific claim being investigated |
| Publication date | The date when a news article or press release was published, used for temporal relevance assessment |

---

## Executive Summary (Gherkin-Style)

```gherkin
Feature: News/Media Agent

  Background:
    Given  FRD 0, FRD 1, FRD 2, FRD 3, and FRD 5 are complete
    And    all services are running (backend, frontend, PostgreSQL, Redis)
    And    a sustainability report has been uploaded, parsed, and claims extracted
    And    the Orchestrator has routed claims to the News/Media Agent
    And    the web search tool is configured with a search API key

  Scenario: News/Media Agent investigates a routed claim
    Given  the Orchestrator routes a claim to the News/Media Agent
    When   the investigate_news node executes
    Then   it receives the assigned claim(s) from the routing plan
    And    it constructs targeted search queries (company-specific, industry-wide, controversy-focused)
    And    it executes web searches via the search_web tool
    And    it evaluates source credibility and assigns tiers (Tier 1-4)
    And    it analyzes search results for relevance and contradiction
    And    it produces structured evidence findings with URLs, dates, tiers, summaries, and contradiction flags
    And    it emits StreamEvent objects during investigation
    And    it returns findings to the shared state

  Scenario: Web search tool executes searches
    Given  the News/Media Agent calls the search_web tool
    When   it provides a search query and optional filters
    Then   the tool constructs an API request to the search provider
    And    it executes the search and retrieves results
    And    it returns structured results with: title, URL, snippet, publication date, source domain
    And    it handles API errors gracefully with retry logic

  Scenario: Source credibility tiering
    Given  the News/Media Agent receives search results
    When   it evaluates each source
    Then   Tier 1 sources are identified: major investigative journalism (ProPublica, Reuters Investigates), regulatory enforcement actions, court filings
    And    Tier 2 sources are identified: established news organizations (NYT, WSJ, BBC), industry trade publications, government reports
    And    Tier 3 sources are identified: company press releases, wire services (PR Newswire, Business Wire), analyst reports
    And    Tier 4 sources are identified: blogs, social media, unverified sources
    And    each source is assigned exactly one tier

  Scenario: Contradiction detection
    Given  the News/Media Agent analyzes search results for a claim
    When   it finds evidence that contradicts the claim
    Then   it flags the finding with `supports_claim = false` and `contradiction_detected = true`
    And    it provides a clear explanation of the contradiction in the summary
    And    the evidence includes the contradicting source URL and date
    And    higher-tier contradictions are weighted more heavily than lower-tier contradictions

  Scenario: Company-specific investigation
    Given  a claim mentions the reporting company by name
    When   the agent constructs search queries
    Then   it includes queries with the company name and claim keywords
    And    it searches for recent news (last 2 years) and historical coverage (last 5 years)
    And    it prioritizes sources that directly reference the company

  Scenario: Industry-wide investigation
    Given  a claim relates to industry trends or sector-wide issues
    When   the agent constructs search queries
    Then   it includes queries with industry keywords and claim topics
    And    it searches for regulatory actions, enforcement patterns, and benchmark comparisons
    And    it identifies whether the company's claim aligns with or deviates from industry norms

  Scenario: Inter-agent communication
    Given  the News/Media Agent needs cross-domain context
    When   it posts an InfoRequest to the shared state
    Then   the Orchestrator routes the request to the appropriate agent(s)
    And    the target agent(s) respond with InfoResponse objects
    And    the News/Media Agent incorporates the response into its investigation
    And    all communication is visible in the SSE stream

  Scenario: Re-investigation handling
    Given  the Judge Agent requests re-investigation with refined queries
    When   the Orchestrator routes the request back to the News/Media Agent
    Then   the agent receives the refined queries and evidence gap description
    And    it focuses its search on the specific gaps identified by the Judge
    And    it produces additional findings addressing the Judge's concerns
    And    the iteration count is incremented in the findings

  Scenario: Error handling
    Given  the web search API is unavailable or returns an error
    When   the agent attempts to search
    Then   it retries up to 3 times with exponential backoff
    And    if all retries fail, it returns findings with `evidence_type = "error"` and a descriptive message
    And    the pipeline continues with other agents
    And    an error StreamEvent is emitted
```

---

## Table of Contents

1. [Web Search Tool Implementation](#1-web-search-tool-implementation)
2. [News/Media Agent Node Implementation](#2-newsmedia-agent-node-implementation)
3. [Search Query Construction](#3-search-query-construction)
4. [Source Credibility Tiering](#4-source-credibility-tiering)
5. [Contradiction Detection](#5-contradiction-detection)
6. [Evidence Output Structure](#6-evidence-output-structure)
7. [Inter-Agent Communication](#7-inter-agent-communication)
8. [Re-Investigation Handling](#8-re-investigation-handling)
9. [StreamEvent Emissions](#9-streamevent-emissions)
10. [Error Handling](#10-error-handling)
11. [Exit Criteria](#11-exit-criteria)
12. [Appendix A: Web Search Tool Prompt](#appendix-a-web-search-tool-prompt)
13. [Appendix B: Source Credibility Tier Definitions](#appendix-b-source-credibility-tier-definitions)
14. [Appendix C: Search Query Construction Examples](#appendix-c-search-query-construction-examples)
15. [Appendix D: Contradiction Detection Algorithm](#appendix-d-contradiction-detection-algorithm)
16. [Design Decisions Log](#design-decisions-log)

---

## 1. Web Search Tool Implementation

### 1.1 Overview

The web search tool (`app/agents/tools/search_web.py`) is a LangChain tool that executes web searches via a search API and returns structured results. This tool is shared between the News/Media Agent (FRD 8) and the Academic/Research Agent (FRD 9). It is fully defined in FRD 8 since FRD 8 comes first in the implementation order.

### 1.2 Search API Selection

For the hackathon MVP, the system shall use **Tavily Search API** as the primary search provider:

| Provider | Rationale |
|---|---|
| **Tavily Search API** | Designed for AI agents; provides structured JSON responses with relevance scores; includes source metadata (domain, date); free tier with 1,000 searches/month; simple Python SDK; good for news and web content |
| Alternative: Brave Search API | Requires API key; paid tier; good coverage but more complex setup |
| Alternative: SerpAPI | Requires API key; paid tier; comprehensive but adds dependency |

**Configuration:**

```python
# app/core/config.py
TAVILY_API_KEY: str | None = None  # Set via environment variable
SEARCH_API_PROVIDER: str = "tavily"  # Options: "tavily", "brave", "serpapi"
SEARCH_MAX_RESULTS: int = 10  # Maximum results per query
SEARCH_TIMEOUT_SECONDS: int = 30  # API request timeout
```

### 1.3 Tool Function Signature

```python
# app/agents/tools/search_web.py

from langchain.tools import tool
from typing import Optional

@tool
def search_web(
    query: str,
    max_results: Optional[int] = None,
    include_domains: Optional[list[str]] = None,
    exclude_domains: Optional[list[str]] = None,
    time_range: Optional[str] = None,  # "day", "week", "month", "year", "all"
    search_depth: str = "basic"  # "basic" or "advanced"
) -> dict:
    """Search the web for news articles, press releases, and public sources.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: config.SEARCH_MAX_RESULTS)
        include_domains: Optional list of domains to restrict search to (e.g., ["reuters.com", "bloomberg.com"])
        exclude_domains: Optional list of domains to exclude (e.g., ["twitter.com", "facebook.com"])
        time_range: Optional time filter: "day", "week", "month", "year", or "all" (default: "all")
        search_depth: "basic" for fast results or "advanced" for deeper search (default: "basic")

    Returns:
        {
            "results": [
                {
                    "title": str,
                    "url": str,
                    "snippet": str,
                    "published_date": str | None,  # ISO format or None
                    "source_domain": str,
                    "relevance_score": float | None  # 0.0-1.0 if available
                },
                ...
            ],
            "total_results": int,
            "query": str,
            "search_provider": str
        }

    Raises:
        SearchAPIError: If the search API fails after retries
    """
```

### 1.4 Tavily API Integration

The system shall implement Tavily integration:

```python
from tavily import TavilyClient

class TavilySearchProvider:
    """Tavily Search API provider."""

    def __init__(self, api_key: str):
        self.client = TavilyClient(api_key=api_key)

    async def search(
        self,
        query: str,
        max_results: int = 10,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        time_range: str | None = None,
        search_depth: str = "basic"
    ) -> dict:
        """Execute a Tavily search."""
        search_kwargs = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
        }

        if include_domains:
            search_kwargs["include_domains"] = include_domains
        if exclude_domains:
            search_kwargs["exclude_domains"] = exclude_domains

        # Tavily doesn't support time_range directly; filter results post-query
        response = self.client.search(**search_kwargs)

        results = []
        for result in response.get("results", []):
            result_dict = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("content", ""),  # Tavily uses "content" for snippet
                "published_date": result.get("published_date"),  # ISO format or None
                "source_domain": self._extract_domain(result.get("url", "")),
                "relevance_score": result.get("score"),  # Tavily relevance score
            }
            results.append(result_dict)

        return {
            "results": results,
            "total_results": len(results),
            "query": query,
            "search_provider": "tavily"
        }
```

### 1.5 Error Handling and Retry Logic

The search tool shall implement retry logic:

1. **Retry on transient failures:** Network errors, timeouts, rate limits (429), server errors (5xx)
2. **Retry strategy:** Exponential backoff: 1s, 2s, 4s (3 attempts total)
3. **Rate limit handling:** If Tavily returns 429, wait for the `Retry-After` header before retrying
4. **Final failure:** After 3 retries, raise `SearchAPIError` with a descriptive message

```python
class SearchAPIError(Exception):
    """Raised when web search API fails after retries."""
    pass
```

### 1.6 Domain Extraction Helper

```python
def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.netloc or ""
```

### 1.7 Tool Registration

The tool shall be registered as a LangChain tool and made available to the News/Media Agent:

```python
# In news_media_agent.py
from app.agents.tools.search_web import search_web

# Agent has access to the tool via LangChain's tool binding
tools = [search_web]
```

---

## 2. News/Media Agent Node Implementation

### 2.1 Overview

The News/Media Agent (`app/agents/news_media_agent.py`) replaces the FRD 5 stub with a functional LangGraph node that investigates routed claims by searching public news sources, evaluating source credibility, detecting contradictions, and producing structured evidence findings.

### 2.2 Node Function

```python
async def investigate_news(state: SibylState) -> dict:
    """News/Media Agent: Investigate claims via public news sources.

    Reads: state.routing_plan, state.claims, state.info_requests,
           state.reinvestigation_requests, state.iteration_count
    Writes: state.findings, state.agent_status, state.info_requests,
            state.events

    Responsibilities:
    1. Find claims assigned to this agent in the routing plan.
    2. Construct targeted search queries for each claim.
    3. Execute web searches via search_web tool.
    4. Evaluate source credibility and assign tiers.
    5. Detect contradictions between sources and claims.
    6. Produce structured evidence findings.
    7. Handle InfoRequests and re-investigation requests.

    Returns:
        Partial state update with findings, agent status, and events.
    """
```

### 2.3 Model Configuration

| Parameter | Value | Rationale |
|---|---|---|
| Model | `anthropic/claude-sonnet-4-5` (`Models.CLAUDE_SONNET`) | Strong source analysis, credibility assessment, and nuanced reasoning about corroboration vs. contradiction (PRD Section 4.6) |
| Temperature | `0.2` | Slightly higher than routing (0.1) to allow nuanced interpretation of source content while maintaining consistency |
| Max output tokens | `8192` | Sufficient for analyzing multiple search results and producing detailed findings |
| Response format | JSON schema (structured output) | Ensures parseable findings output |

### 2.4 Processing Steps

The `investigate_news` node shall execute the following steps:

1. **Emit start event:** Append a `StreamEvent` with `event_type = "agent_started"`, `agent_name = "news_media"`.

2. **Find assigned claims:** Extract claims assigned to this agent from `state.routing_plan`:
   ```python
   assigned_claims = [
       claim for claim in state.claims
       if any(
           assignment.claim_id == claim.claim_id
           and "news_media" in assignment.assigned_agents
           for assignment in state.routing_plan
       )
   ]
   ```

3. **Update agent status:** Set `agent_status["news_media"] = AgentStatus(status="working", claims_assigned=len(assigned_claims))`.

4. **Process each claim:**
   a. Construct search queries (see Section 3).
   b. Execute web searches via `search_web` tool.
   c. Evaluate source credibility (see Section 4).
   d. Detect contradictions (see Section 5).
   e. Produce evidence findings (see Section 6).
   f. Emit `agent_thinking` events during processing.

5. **Handle InfoRequests:** Process any `InfoRequest` objects routed to this agent (see Section 7).

6. **Handle re-investigation:** If `state.reinvestigation_requests` contains requests targeting this agent, process them with refined queries (see Section 8).

7. **Update agent status:** Set `status = "completed"`, `claims_completed = len(assigned_claims)`.

8. **Emit completion event:** Append a `StreamEvent` with `event_type = "agent_completed"`, `agent_name = "news_media"`, including findings summary.

9. **Return partial state:** Return updated `findings`, `agent_status`, `info_requests`, and `events`.

---

## 3. Search Query Construction

### 3.1 Overview

The News/Media Agent constructs targeted search queries to maximize the likelihood of finding relevant, credible sources. Query construction considers the claim type, content, company name, and investigation context (initial vs. re-investigation).

### 3.2 Query Types

The agent constructs three types of queries per claim:

| Query Type | Purpose | Example |
|---|---|---|
| **Company-specific** | Find news coverage directly about the reporting company and its claim | "{Company Name} Scope 1 emissions 2024" |
| **Industry-wide** | Find industry trends, benchmarks, or sector-wide incidents relevant to the claim | "oil and gas Scope 1 emissions reduction 2024" |
| **Controversy-focused** | Surface negative coverage, whistleblower reports, or enforcement actions | "{Company Name} emissions violation OR greenwashing OR investigation" |

### 3.3 Query Construction Strategy

For each claim, the agent shall:

1. **Extract key terms:**
   - Company name (from report metadata)
   - Claim keywords (emission types, metrics, locations, dates)
   - IFRS-related terms (if applicable)

2. **Construct company-specific query:**
   ```
   "{company_name} {claim_keywords} {time_period}"
   ```
   Example: "ExxonMobil Scope 1 emissions reduction 2024"

3. **Construct industry-wide query:**
   ```
   "{industry_keywords} {claim_topic} {time_period}"
   ```
   Example: "oil and gas industry emissions reduction targets 2024"

4. **Construct controversy-focused query:**
   ```
   "{company_name} {claim_topic} (violation OR investigation OR lawsuit OR whistleblower OR controversy)"
   ```
   Example: "ExxonMobil emissions (violation OR investigation OR lawsuit)"

### 3.4 Time Range Selection

The agent selects appropriate time ranges based on claim context:

| Claim Context | Time Range | Rationale |
|---|---|---|
| Recent metrics (current year) | `"year"` | Focus on recent coverage |
| Historical claims (past years) | `"all"` | Include historical context |
| Strategic commitments (future targets) | `"year"` | Recent coverage of commitments |
| Re-investigation | `"all"` | Cast wider net for missed sources |

### 3.5 Domain Filtering

The agent may apply domain filters to focus on credible sources:

**Include domains (optional, for Tier 1-2 sources):**
- Major news: `["reuters.com", "bloomberg.com", "wsj.com", "ft.com", "nytimes.com", "bbc.com"]`
- Regulatory: `["sec.gov", "epa.gov", "justice.gov"]`
- Industry: Domain-specific trade publications

**Exclude domains (always):**
- Social media: `["twitter.com", "facebook.com", "linkedin.com"]`
- Aggregators: `["reddit.com", "news.google.com"]` (unless specifically needed)

### 3.6 LLM-Assisted Query Refinement

For complex claims, the agent uses Claude Sonnet 4.5 to refine queries:

```python
def construct_search_queries(claim: Claim, company_name: str) -> list[str]:
    """Construct targeted search queries for a claim.
    
    Uses LLM to generate nuanced queries that maximize search effectiveness.
    """
    prompt = f"""
    Given the following sustainability claim, construct 3 search queries:
    1. Company-specific query (targeting news about {company_name})
    2. Industry-wide query (targeting sector trends)
    3. Controversy-focused query (targeting negative coverage or investigations)
    
    Claim: {claim.claim_text}
    Claim Type: {claim.claim_type}
    IFRS Paragraphs: {claim.ifrs_paragraphs}
    
    Return JSON:
    {{
        "company_specific": "query string",
        "industry_wide": "query string",
        "controversy": "query string"
    }}
    """
    # Call Claude Sonnet 4.5 for query generation
    # Parse and return queries
```

---

## 4. Source Credibility Tiering

### 4.1 Overview

The News/Media Agent assigns each search result to one of four credibility tiers, matching PRD Section 4.6. Higher tiers carry more weight in evidence evaluation and contradiction detection.

### 4.2 Tier Definitions

| Tier | Description | Examples | Weight |
|---|---|---|---|
| **Tier 1** | Highest credibility: Major investigative journalism, regulatory enforcement actions, court filings | ProPublica, Reuters Investigates, SEC enforcement actions, DOJ filings, court documents | 4.0 |
| **Tier 2** | High credibility: Established news organizations, industry trade publications, government reports | NYT, WSJ, BBC, Financial Times, Bloomberg, industry trade journals, EPA reports, government studies | 3.0 |
| **Tier 3** | Medium credibility: Company press releases, wire services, analyst reports | Company press releases, PR Newswire, Business Wire, Reuters, analyst reports (Goldman Sachs, Morgan Stanley) | 2.0 |
| **Tier 4** | Lowest credibility: Blogs, social media, unverified sources | Personal blogs, Medium articles, social media posts, unverified websites | 1.0 |

### 4.3 Tier Assignment Algorithm

The agent assigns tiers using a combination of domain matching and LLM analysis:

**Step 1: Domain-based classification (fast path)**

```python
TIER_1_DOMAINS = [
    "propublica.org",
    "reuters.com/investigates",
    "sec.gov",
    "justice.gov",
    "courtlistener.com",
    # ... more Tier 1 domains
]

TIER_2_DOMAINS = [
    "nytimes.com",
    "wsj.com",
    "bloomberg.com",
    "ft.com",
    "bbc.com",
    "reuters.com",  # General Reuters (not investigates)
    "epa.gov",
    # ... more Tier 2 domains
]

TIER_3_DOMAINS = [
    "prnewswire.com",
    "businesswire.com",
    "globenewswire.com",
    # ... more Tier 3 domains
]

def assign_tier_by_domain(source_domain: str) -> int | None:
    """Assign tier based on domain matching. Returns None if domain not recognized."""
    domain_lower = source_domain.lower()
    
    if any(tier1 in domain_lower for tier1 in TIER_1_DOMAINS):
        return 1
    if any(tier2 in domain_lower for tier2 in TIER_2_DOMAINS):
        return 2
    if any(tier3 in domain_lower for tier3 in TIER_3_DOMAINS):
        return 3
    
    return None  # Unknown domain, use LLM classification
```

**Step 2: LLM-based classification (fallback)**

For sources not matching known domains, the agent uses Claude Sonnet 4.5 to classify:

```python
def classify_source_credibility(source: dict) -> int:
    """Classify source credibility tier using LLM."""
    prompt = f"""
    Classify the following news source into a credibility tier:
    
    Title: {source['title']}
    Domain: {source['source_domain']}
    Snippet: {source['snippet']}
    
    Tier 1: Major investigative journalism, regulatory actions, court filings
    Tier 2: Established news organizations, industry trade publications, government reports
    Tier 3: Company press releases, wire services, analyst reports
    Tier 4: Blogs, social media, unverified sources
    
    Return JSON: {{"tier": 1-4, "reasoning": "brief explanation"}}
    """
    # Call Claude Sonnet 4.5
    # Parse tier from response
```

### 4.4 Company Press Release Detection

The agent identifies company press releases (Tier 3) by:

1. **Domain matching:** Check if `source_domain` matches the company's domain or known PR distribution domains.
2. **Content analysis:** Look for press release indicators: "FOR IMMEDIATE RELEASE", "Company announces", "Press Release" in title/snippet.
3. **Author analysis:** Check if the author is listed as a company spokesperson or PR department.

### 4.5 Tier Weighting in Evidence

When producing findings, the agent weights evidence by tier:

- **Tier 1 contradiction:** Strong contradiction flag; high confidence
- **Tier 2 contradiction:** Moderate contradiction flag; medium-high confidence
- **Tier 3 contradiction:** Weak contradiction flag (company press releases rarely contradict their own reports); low confidence
- **Tier 4 contradiction:** Very weak contradiction flag; very low confidence

Tier information is included in the `AgentFinding.details` field for downstream evaluation by the Judge Agent.

---

## 5. Contradiction Detection

### 5.1 Overview

The News/Media Agent detects when public reporting contradicts claims made in the sustainability report. Contradiction detection is critical for identifying potential greenwashing or misleading statements.

### 5.2 Contradiction Types

| Contradiction Type | Description | Example |
|---|---|---|
| **Direct contradiction** | Source explicitly states the opposite of the claim | Claim: "Emissions decreased 12%"; Source: "Company emissions increased 5%" |
| **Contextual contradiction** | Source provides context that undermines the claim | Claim: "100% renewable energy"; Source: "Company uses renewable certificates but still relies on fossil fuel grid" |
| **Omission contradiction** | Source reveals information the report omits | Claim: "Strong governance"; Source: "Company faces SEC investigation for climate disclosure violations" |
| **Timeline contradiction** | Source contradicts the timeline or dates in the claim | Claim: "Target achieved in 2024"; Source: "Target delayed to 2026" |

### 5.3 Contradiction Detection Algorithm

The agent uses Claude Sonnet 4.5 to analyze each search result for contradiction:

```python
def detect_contradiction(claim: Claim, search_result: dict) -> dict:
    """Analyze a search result for contradiction with the claim.
    
    Returns:
        {
            "contradicts": bool,
            "contradiction_type": str | None,  # "direct", "contextual", "omission", "timeline"
            "confidence": float,  # 0.0-1.0
            "explanation": str
        }
    """
    prompt = f"""
    Analyze whether the following news source contradicts the sustainability claim.
    
    Claim: {claim.claim_text}
    Claim Type: {claim.claim_type}
    Claim Context: {claim.source_context}
    
    News Source:
    Title: {search_result['title']}
    Snippet: {search_result['snippet']}
    URL: {search_result['url']}
    Published: {search_result['published_date']}
    
    Determine if the source:
    1. Directly contradicts the claim (states the opposite)
    2. Provides contextual information that undermines the claim
    3. Reveals omitted information that contradicts the claim's implications
    4. Contradicts the timeline or dates in the claim
    5. Does not contradict (supports or is neutral)
    
    Return JSON:
    {{
        "contradicts": true/false,
        "contradiction_type": "direct" | "contextual" | "omission" | "timeline" | null,
        "confidence": 0.0-1.0,
        "explanation": "Brief explanation of the contradiction or lack thereof"
    }}
    """
    # Call Claude Sonnet 4.5
    # Parse and return contradiction analysis
```

### 5.4 Contradiction Aggregation

For each claim, the agent aggregates contradictions across all search results:

1. **Count contradictions by tier:** Track how many Tier 1, Tier 2, Tier 3, Tier 4 sources contradict the claim.
2. **Weight by tier:** Higher-tier contradictions carry more weight.
3. **Final contradiction flag:** Set `supports_claim = false` if:
   - Any Tier 1 source contradicts, OR
   - 2+ Tier 2 sources contradict, OR
   - 3+ Tier 3 sources contradict (with lower confidence)

### 5.5 Contradiction Evidence Structure

When a contradiction is detected, the finding includes:

```python
finding = AgentFinding(
    agent_name="news_media",
    claim_id=claim.claim_id,
    evidence_type="news_contradiction",
    summary=f"Public reporting contradicts the claim: {contradiction_explanation}",
    details={
        "source_url": search_result['url'],
        "source_title": search_result['title'],
        "source_tier": tier,
        "contradiction_type": contradiction_type,
        "published_date": search_result['published_date'],
        "explanation": contradiction_explanation,
    },
    supports_claim=False,
    confidence=contradiction_confidence * tier_weight,
    iteration=state.iteration_count + 1,
)
```

---

## 6. Evidence Output Structure

### 6.1 Overview

The News/Media Agent produces `AgentFinding` objects containing structured evidence from public sources. Each finding includes source metadata, credibility tier, relevance summary, and contradiction flags.

### 6.2 Finding Schema

```python
class NewsMediaFinding(AgentFinding):
    """News/Media Agent finding with source evidence."""
    
    # Inherited from AgentFinding:
    # finding_id: str
    # agent_name: str = "news_media"
    # claim_id: str
    # evidence_type: str = "news_source"
    # summary: str
    # details: dict
    # supports_claim: bool | None
    # confidence: float | None
    # iteration: int
    
    # details dict structure:
    details = {
        "source_url": str,              # Full URL of the source
        "source_title": str,            # Article/press release title
        "source_domain": str,           # Domain name
        "source_tier": int,             # 1-4 credibility tier
        "published_date": str | None,   # ISO format date or None
        "relevance_summary": str,       # How the source relates to the claim
        "contradicts_claim": bool,      # Whether this source contradicts
        "contradiction_type": str | None,  # "direct", "contextual", "omission", "timeline"
        "contradiction_explanation": str | None,  # Explanation if contradicts
        "snippet": str,                 # Relevant excerpt from the source
    }
```

### 6.3 Relevance Summary Generation

The agent generates a plain-language relevance summary for each finding:

```python
def generate_relevance_summary(claim: Claim, search_result: dict) -> str:
    """Generate a relevance summary explaining how the source relates to the claim."""
    prompt = f"""
    Explain how the following news source relates to the sustainability claim.
    Be concise (2-3 sentences) and focus on what the source says about the claim.
    
    Claim: {claim.claim_text}
    
    Source:
    Title: {search_result['title']}
    Snippet: {search_result['snippet']}
    
    Return a brief relevance summary.
    """
    # Call Claude Sonnet 4.5 (lightweight call, can batch)
    # Return summary
```

### 6.4 Finding Aggregation

For each claim, the agent may produce multiple findings (one per relevant search result). Findings are grouped by:

- **Supporting evidence:** Findings where `supports_claim = true` or `contradicts_claim = false`
- **Contradicting evidence:** Findings where `contradicts_claim = true`
- **Neutral evidence:** Findings where the source is relevant but neither supports nor contradicts

The agent produces a summary finding that aggregates all individual findings:

```python
summary_finding = AgentFinding(
    agent_name="news_media",
    claim_id=claim.claim_id,
    evidence_type="news_investigation_summary",
    summary=f"Found {supporting_count} supporting sources, {contradicting_count} contradicting sources across {total_sources} total sources. {contradiction_summary}",
    details={
        "total_sources": total_sources,
        "supporting_sources": supporting_count,
        "contradicting_sources": contradicting_count,
        "tier_distribution": {1: tier1_count, 2: tier2_count, 3: tier3_count, 4: tier4_count},
        "key_findings": [finding.details for finding in key_findings],
    },
    supports_claim=None,  # Aggregated: may be mixed
    confidence=aggregated_confidence,
    iteration=state.iteration_count + 1,
)
```

---

## 7. Inter-Agent Communication

### 7.1 Overview

The News/Media Agent participates in the inter-agent communication protocol defined in FRD 5 Section 4. It can post `InfoRequest` objects to request cross-domain context and respond to `InfoRequest` objects from other agents.

### 7.2 Posting InfoRequests

The agent posts `InfoRequest` objects when it needs:

- **Geographic context:** Location verification for incident reports (request Geography Agent)
- **Regulatory context:** IFRS compliance interpretation for governance claims (request Legal Agent)
- **Quantitative validation:** Mathematical consistency checks for reported metrics (request Data/Metrics Agent)
- **Academic validation:** Methodology validation for technical claims (request Academic/Research Agent)

Example:

```python
info_request = InfoRequest(
    requesting_agent="news_media",
    description=f"Need geographic verification for incident location mentioned in news source: {location_name}. Source claims incident occurred at {coordinates}.",
    context={"claim_id": claim.claim_id, "source_url": search_result['url']},
    status="pending",
)
state.info_requests.append(info_request)
```

### 7.3 Responding to InfoRequests

When the agent receives a routed `InfoRequest`, it:

1. Analyzes the request description.
2. Searches for relevant news coverage related to the request.
3. Posts an `InfoResponse` with findings:

```python
info_response = InfoResponse(
    requesting_agent=info_request.requesting_agent,
    responding_agent="news_media",
    summary=f"Found {count} news sources related to {request_topic}.",
    details={
        "sources": [source.details for source in relevant_sources],
        "key_findings": key_findings_summary,
    },
    status="completed",
)
state.info_responses.append(info_response)
```

### 7.4 InfoRequest Visibility

All InfoRequests and InfoResponses are emitted as `StreamEvent` objects (see Section 9) for visibility in the detective dashboard.

---

## 8. Re-Investigation Handling

### 8.1 Overview

When the Judge Agent requests re-investigation (FRD 11), the Orchestrator routes `ReinvestigationRequest` objects back to the News/Media Agent. The agent processes these requests with refined queries and focused investigation angles.

### 8.2 Re-Investigation Processing

When the agent receives a `ReinvestigationRequest`:

1. **Read the request:** Extract `evidence_gap`, `refined_queries`, `required_evidence`, and `target_agents`.

2. **Focus investigation:** Use the Judge's `refined_queries` instead of constructing new queries. The Judge's queries are more targeted based on evidence gaps.

3. **Address specific gaps:** The `evidence_gap` description guides what to search for:
   - "Need more recent sources" → Focus on recent time range
   - "Need Tier 1 sources" → Filter to Tier 1 domains
   - "Need contradiction evidence" → Focus on controversy-focused queries

4. **Produce additional findings:** Generate new findings addressing the Judge's concerns.

5. **Increment iteration:** Set `iteration = state.iteration_count + 1` in findings to track re-investigation cycles.

### 8.3 Re-Investigation Example

```python
# Judge's re-investigation request
reinvestigation = ReinvestigationRequest(
    claim_id=claim.claim_id,
    target_agents=["news_media"],
    evidence_gap="Need more recent sources (2024) to verify the 2024 emissions claim. Current sources are from 2023.",
    refined_queries=[
        "{company_name} Scope 1 emissions 2024",
        "{company_name} emissions report 2024",
    ],
    required_evidence="Recent news coverage (2024) discussing the company's 2024 emissions figures.",
)

# Agent processes with refined queries
for query in reinvestigation.refined_queries:
    results = await search_web(query, time_range="year", max_results=10)
    # Process results with focus on recent sources
```

---

## 9. StreamEvent Emissions

### 9.1 Overview

The News/Media Agent emits `StreamEvent` objects throughout its execution to provide real-time visibility into the investigation process. These events are streamed to the frontend via SSE (FRD 5) and displayed in the detective dashboard (FRD 12).

### 9.2 Event Types

| Event Type | Agent | Data Fields | When |
|---|---|---|---|
| `agent_started` | `news_media` | `{}` | Node begins execution |
| `agent_thinking` | `news_media` | `{"message": "..."}` | Progress updates during investigation |
| `claim_investigating` | `news_media` | `{"claim_id": "...", "claim_text": "..."}` | Agent begins investigating a specific claim |
| `search_executed` | `news_media` | `{"query": "...", "results_count": N}` | Web search completes |
| `source_evaluated` | `news_media` | `{"source_url": "...", "tier": N, "relevance": "..."}` | Source credibility tier assigned |
| `contradiction_detected` | `news_media` | `{"claim_id": "...", "source_url": "...", "contradiction_type": "..."}` | Contradiction found |
| `evidence_found` | `news_media` | `{"claim_id": "...", "findings_count": N, "supports_claim": bool}` | Evidence findings produced |
| `agent_completed` | `news_media` | `{"claims_processed": N, "findings_count": M, "contradictions_count": K}` | Investigation complete |
| `info_request_posted` | `news_media` | `{"requesting_agent": "...", "description": "..."}` | Agent posts cross-domain request |
| `info_response_posted` | `news_media` | `{"responding_agent": "...", "requesting_agent": "...", "summary": "..."}` | Agent responds to info request |
| `error` | `news_media` | `{"message": "...", "claim_id": "..."}` | Error during investigation |

### 9.3 Event Emission Examples

```python
# Start event
events.append(StreamEvent(
    event_type="agent_started",
    agent_name="news_media",
    data={},
    timestamp=datetime.utcnow().isoformat()
))

# Thinking event
events.append(StreamEvent(
    event_type="agent_thinking",
    agent_name="news_media",
    data={"message": f"Investigating {len(assigned_claims)} claims via public news sources..."},
    timestamp=datetime.utcnow().isoformat()
))

# Search execution
events.append(StreamEvent(
    event_type="search_executed",
    agent_name="news_media",
    data={
        "query": "ExxonMobil Scope 1 emissions 2024",
        "results_count": 8,
    },
    timestamp=datetime.utcnow().isoformat()
))

# Contradiction detection
events.append(StreamEvent(
    event_type="contradiction_detected",
    agent_name="news_media",
    data={
        "claim_id": claim.claim_id,
        "source_url": "https://reuters.com/...",
        "contradiction_type": "direct",
        "tier": 2,
    },
    timestamp=datetime.utcnow().isoformat()
))
```

---

## 10. Error Handling

### 10.1 Web Search API Errors

| Error | Trigger | Handling |
|---|---|---|
| API key missing | `TAVILY_API_KEY` not set | Return findings with `evidence_type = "error"`, `summary = "Web search unavailable: API key not configured"`; pipeline continues |
| API rate limit exceeded | Tavily returns 429 | Retry with exponential backoff (handled by tool); if all retries fail, return error finding |
| API timeout | Request exceeds 30 seconds | Retry once; if still timeout, return error finding with partial results if available |
| API server error | Tavily returns 5xx | Retry up to 3 times; on final failure, return error finding |
| Network error | Connection failure | Retry up to 3 times; on final failure, return error finding |

### 10.2 LLM Analysis Errors

| Error | Trigger | Handling |
|---|---|---|
| Query construction failure | Claude Sonnet 4.5 fails to generate queries | Fall back to rule-based query construction (Section 3.3) |
| Credibility classification failure | LLM fails to classify source tier | Fall back to domain-based classification; if domain unknown, assign Tier 4 (lowest) |
| Contradiction analysis failure | LLM fails to analyze contradiction | Mark as `contradicts_claim = None`; include source in findings with manual review flag |
| Structured output parsing failure | LLM returns non-JSON | Retry once with simplified prompt; if still fails, use fallback heuristics |

### 10.3 Graceful Degradation

If the web search tool is unavailable or returns errors:

1. The agent returns findings with `evidence_type = "error"` and a descriptive message.
2. The pipeline continues with other agents.
3. The Judge Agent (FRD 11) evaluates available evidence and may request re-investigation when the search tool is available.
4. An error `StreamEvent` is emitted for visibility.

### 10.4 Partial Results Handling

If a search returns partial results (some queries succeed, others fail):

1. Process successful queries and produce findings.
2. Include error findings for failed queries.
3. Aggregate all findings (successful + errors) in the summary.
4. The Judge evaluates whatever evidence is available.

---

## 11. Exit Criteria

FRD 8 is complete when ALL of the following are satisfied:

| # | Criterion | Verification |
|---|---|---|
| 1 | Web search tool is implemented | Verify `app/agents/tools/search_web.py` exists and can execute searches via Tavily API |
| 2 | Search tool returns structured results | Call `search_web("test query")` and verify it returns results with title, URL, snippet, date, domain |
| 3 | News/Media Agent node replaces stub | Verify `investigate_news` function in `app/agents/news_media_agent.py` is fully implemented (not stub) |
| 4 | Agent receives routed claims | After Orchestrator routes claims, verify the agent processes assigned claims |
| 5 | Agent constructs search queries | Verify the agent generates company-specific, industry-wide, and controversy-focused queries |
| 6 | Agent executes web searches | Verify search_web tool is called with appropriate queries and parameters |
| 7 | Source credibility tiering works | Verify sources are assigned to Tier 1-4 based on domain and content analysis |
| 8 | Tier 1 sources are identified correctly | Verify major investigative journalism and regulatory actions are classified as Tier 1 |
| 9 | Tier 2 sources are identified correctly | Verify established news organizations are classified as Tier 2 |
| 10 | Tier 3 sources are identified correctly | Verify company press releases and wire services are classified as Tier 3 |
| 11 | Tier 4 sources are identified correctly | Verify blogs and unverified sources are classified as Tier 4 |
| 12 | Contradiction detection works | Verify the agent detects when sources contradict claims |
| 13 | Direct contradictions are flagged | Verify explicit contradictions (e.g., "increased" vs. "decreased") are detected |
| 14 | Contradiction types are classified | Verify contradictions are classified as direct, contextual, omission, or timeline |
| 15 | Evidence findings are produced | Verify the agent returns `AgentFinding` objects with source URLs, dates, tiers, summaries |
| 16 | Findings include contradiction flags | Verify findings have `supports_claim = false` and `contradicts_claim = true` when contradictions are detected |
| 17 | Relevance summaries are generated | Verify each finding includes a plain-language relevance summary |
| 18 | Inter-agent communication works | Verify the agent can post InfoRequests and respond to InfoRequests from other agents |
| 19 | Re-investigation handling works | Verify the agent processes ReinvestigationRequests with refined queries |
| 20 | StreamEvents are emitted | Verify the agent emits start, thinking, search_executed, contradiction_detected, and completion events |
| 21 | Error handling works | Simulate search API failure; verify the agent returns error findings and pipeline continues |
| 22 | Agent completes in reasonable time | Verify investigation of 10 claims completes in under 2 minutes |
| 23 | Findings are persisted to state | Verify findings are added to `state.findings` and visible to the Judge Agent |

---

## Appendix A: Web Search Tool Prompt

### A.1 Tool Description (for LLM)

The `search_web` tool is described to the agent's LLM as follows:

```
Tool: search_web

Description: Search the web for news articles, press releases, and public sources related to sustainability claims. Returns structured results with source URLs, titles, snippets, publication dates, and domain information.

Parameters:
- query (required): Search query string
- max_results (optional): Maximum number of results (default: 10)
- include_domains (optional): Restrict search to specific domains
- exclude_domains (optional): Exclude specific domains
- time_range (optional): Filter by time ("day", "week", "month", "year", "all")
- search_depth (optional): "basic" for fast results or "advanced" for deeper search

Returns: Dictionary with "results" list containing source information.

Use this tool to find public sources that corroborate or contradict sustainability claims.
```

---

## Appendix B: Source Credibility Tier Definitions

### B.1 Tier 1: Highest Credibility

**Criteria:**
- Major investigative journalism outlets with established track records
- Regulatory enforcement actions (SEC, EPA, DOJ)
- Court filings and legal documents
- Government investigations and official reports

**Examples:**
- ProPublica
- Reuters Investigates
- SEC enforcement actions (`sec.gov/enforcement`)
- DOJ filings (`justice.gov`)
- Court documents (`courtlistener.com`, PACER)

**Weight:** 4.0

### B.2 Tier 2: High Credibility

**Criteria:**
- Established news organizations with editorial standards
- Industry trade publications with professional journalism
- Government reports and studies (non-enforcement)
- Academic institution news offices

**Examples:**
- New York Times (`nytimes.com`)
- Wall Street Journal (`wsj.com`)
- Bloomberg (`bloomberg.com`)
- Financial Times (`ft.com`)
- BBC (`bbc.com`)
- Reuters (general news, not investigates)
- Industry trade journals (sector-specific)
- EPA reports (`epa.gov/reports`)
- Government studies

**Weight:** 3.0

### B.3 Tier 3: Medium Credibility

**Criteria:**
- Company press releases (self-reported)
- Wire services distributing press releases
- Analyst reports from financial institutions
- Industry association publications

**Examples:**
- PR Newswire (`prnewswire.com`)
- Business Wire (`businesswire.com`)
- Globe Newswire (`globenewswire.com`)
- Company websites (press release sections)
- Analyst reports (Goldman Sachs, Morgan Stanley, etc.)
- Industry association news

**Weight:** 2.0

### B.4 Tier 4: Lowest Credibility

**Criteria:**
- Personal blogs
- Social media posts
- Unverified websites
- Aggregator sites without editorial oversight

**Examples:**
- Personal blogs (Medium, WordPress, etc.)
- Social media (Twitter, Facebook, LinkedIn)
- Unverified news sites
- Reddit posts
- Opinion pieces without editorial oversight

**Weight:** 1.0

---

## Appendix C: Search Query Construction Examples

### C.1 Quantitative Claim Example

**Claim:** "Our total Scope 1 emissions were 2.3 million tonnes CO2e in FY2024, a 6.1% decrease from 2.45 million tonnes in FY2023."

**Company:** ExxonMobil

**Queries:**

1. **Company-specific:**
   ```
   "ExxonMobil Scope 1 emissions 2024 2.3 million tonnes"
   ```

2. **Industry-wide:**
   ```
   "oil and gas Scope 1 emissions 2024 reduction"
   ```

3. **Controversy-focused:**
   ```
   "ExxonMobil emissions (violation OR investigation OR lawsuit OR greenwashing) 2024"
   ```

### C.2 Geographic Claim Example

**Claim:** "Our reforestation initiative in Central Kalimantan, Borneo has restored 5,000 hectares of degraded peatland forest since 2020."

**Company:** Palm Oil Corp

**Queries:**

1. **Company-specific:**
   ```
   "Palm Oil Corp reforestation Central Kalimantan Borneo 5000 hectares"
   ```

2. **Industry-wide:**
   ```
   "palm oil reforestation Borneo peatland restoration"
   ```

3. **Controversy-focused:**
   ```
   "Palm Oil Corp Borneo (deforestation OR violation OR investigation OR lawsuit)"
   ```

### C.3 Strategic Claim Example

**Claim:** "We have committed to achieving net-zero greenhouse gas emissions across our full value chain by 2050, with an interim target of a 42% absolute reduction in Scope 1 and 2 emissions by 2030 from a 2019 baseline."

**Company:** TechCorp

**Queries:**

1. **Company-specific:**
   ```
   "TechCorp net-zero 2050 42% reduction 2030"
   ```

2. **Industry-wide:**
   ```
   "technology companies net-zero commitments 2050 SBTi"
   ```

3. **Controversy-focused:**
   ```
   "TechCorp net-zero (greenwashing OR investigation OR lawsuit OR criticism)"
   ```

---

## Appendix D: Contradiction Detection Algorithm

### D.1 Pseudocode

```
function detect_contradiction(claim, search_result):
    // Step 1: Extract key assertions from claim
    claim_assertions = extract_assertions(claim.claim_text)
    // e.g., ["emissions decreased 12%", "2.3 million tonnes", "2024"]
    
    // Step 2: Analyze search result content
    source_content = search_result.snippet + " " + search_result.title
    
    // Step 3: Check for direct contradictions
    for assertion in claim_assertions:
        if assertion contains numeric_value:
            if source_content contains opposite_numeric_value:
                return {
                    contradicts: true,
                    type: "direct",
                    confidence: 0.9
                }
        
        if assertion contains directional_change:
            // e.g., "decreased", "increased", "reduced"
            if source_content contains opposite_direction:
                return {
                    contradicts: true,
                    type: "direct",
                    confidence: 0.85
                }
    
    // Step 4: Check for contextual contradictions
    if claim implies positive_outcome:
        if source_content reveals negative_context:
            return {
                contradicts: true,
                type: "contextual",
                confidence: 0.7
            }
    
    // Step 5: Check for omission contradictions
    if claim omits material_information:
        if source_content reveals omitted_information:
            return {
                contradicts: true,
                type: "omission",
                confidence: 0.75
            }
    
    // Step 6: Check for timeline contradictions
    if claim contains date_or_timeline:
        if source_content contradicts_date:
            return {
                contradicts: true,
                type: "timeline",
                confidence: 0.8
            }
    
    // Step 7: No contradiction found
    return {
        contradicts: false,
        type: null,
        confidence: 0.5  // Neutral
    }
```

### D.2 LLM-Enhanced Detection

The algorithm uses Claude Sonnet 4.5 to perform nuanced analysis beyond simple keyword matching:

1. **Semantic understanding:** LLM understands that "emissions rose" contradicts "emissions decreased" even if exact wording differs.
2. **Context awareness:** LLM considers the broader context of the source (e.g., an investigative report vs. a press release).
3. **Confidence scoring:** LLM provides confidence scores based on the strength of the contradiction evidence.

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| Tavily Search API over Brave Search or SerpAPI | Tavily is designed for AI agents with structured JSON responses, includes relevance scores, has a free tier suitable for hackathon, and provides simple Python SDK. Brave and SerpAPI require paid tiers and more complex setup. |
| Four-tier credibility system over continuous scoring | Discrete tiers (1-4) are easier to reason about, match PRD specification exactly, and enable clear weighting rules. Continuous scoring (0.0-1.0) would require arbitrary thresholds. |
| Domain-based tier classification with LLM fallback over LLM-only | Domain matching is fast and deterministic for known sources. LLM fallback handles unknown domains. LLM-only classification would be slower and more expensive for every source. |
| Three query types (company-specific, industry-wide, controversy) over single query | Multiple query types maximize coverage: company-specific finds direct coverage, industry-wide finds benchmarks, controversy-focused finds negative coverage. A single query would miss relevant angles. |
| LLM-assisted query construction over rule-based only | Rule-based queries work for simple cases, but LLM-assisted construction handles complex claims with nuanced keyword extraction and query phrasing. Hybrid approach balances speed and effectiveness. |
| Contradiction detection via LLM analysis over keyword matching | Keyword matching misses semantic contradictions (e.g., "rose" vs. "fell"). LLM analysis understands context and provides nuanced contradiction classification. Trade-off: higher cost but better accuracy. |
| Aggregated summary finding plus individual findings over summary only | Individual findings preserve source-level detail for the Judge Agent. Summary finding provides quick overview. Both are needed: summary for efficiency, individual for depth. |
| Error findings with `evidence_type = "error"` over raising exceptions | Error findings allow the pipeline to continue with other agents. Raising exceptions would crash the node. The Judge evaluates available evidence and can request re-investigation when errors are resolved. |
| Time range filtering via post-query filtering over API-level filtering | Tavily doesn't support time_range parameter directly. Post-query filtering by `published_date` is a workaround. If using a different API (Brave, SerpAPI) that supports time filtering, use API-level filtering for efficiency. |
| Re-investigation uses Judge's refined queries over agent re-constructing | The Judge's refined queries are more targeted based on evidence gaps. Re-using them focuses the investigation efficiently. Agent re-constructing queries might miss the Judge's specific concerns. |
| Web search tool shared with Academic/Research Agent over separate tools | Both agents need web search. Sharing the tool reduces code duplication and ensures consistent search behavior. FRD 9 will reuse `search_web.py` without modification. |
| StreamEvent for every search execution over batched events | Individual search events provide granular visibility into the investigation process. Users can see which queries were executed and how many results were found. Batched events would hide this detail. |
| Company press releases as Tier 3 over Tier 2 | Company press releases are self-reported and may be biased. They provide official statements but lack independent verification. Tier 3 reflects their medium credibility. Tier 2 would over-weight company statements. |
| Contradiction confidence weighted by tier over uniform confidence | Higher-tier contradictions are more credible and should carry more weight. A Tier 1 contradiction with 0.8 confidence is stronger than a Tier 4 contradiction with 0.8 confidence. Weighting: `final_confidence = base_confidence * (tier / 4.0)`. |
| Maximum 10 results per query over 20+ | 10 results per query balances coverage with processing time. Analyzing 20+ results per query would slow the agent significantly. Multiple query types (3 per claim) already provide broad coverage. |
| Search tool timeout of 30 seconds over 60 seconds | 30 seconds is sufficient for most searches. Longer timeouts risk blocking the pipeline. If a search takes >30 seconds, it's likely an API issue and should be retried rather than waited for. |
