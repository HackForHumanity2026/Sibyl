"""News/Media Agent - verifies claims against public news sources.

Implements FRD 8.

Model: Claude Sonnet 4.5 (strong source analysis and credibility assessment)

The News/Media Agent performs:
- Web search via Tavily API (company-specific, industry-wide, controversy-focused)
- Source credibility tiering (Tier 1-4)
- Contradiction detection (direct, contextual, omission, timeline)
- Evidence synthesis with source URLs, publication dates, and relevance summaries
- Inter-agent communication for cross-domain verification
- Re-investigation handling for Judge-requested deeper analysis
"""

import asyncio
import json
import logging
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Maximum concurrent claim processing (rate limiting)
MAX_CONCURRENT_CLAIMS = 5

from app.agents.state import (
    AgentFinding,
    AgentStatus,
    Claim,
    InfoRequest,
    InfoResponse,
    ReinvestigationRequest,
    RoutingAssignment,
    SibylState,
)
from app.agents.stream_utils import (
    emit_agent_started,
    emit_agent_thinking,
    emit_agent_completed,
    emit_evidence_found,
    emit_search_executed,
    emit_source_evaluated,
    emit_contradiction_detected,
    emit_event,
    emit_error,
)
from app.agents.tools.search_web import SearchAPIError, search_web_async
from app.core.database import generate_uuid7
from app.services.openrouter_client import Models, openrouter_client

logger = logging.getLogger(__name__)


# ============================================================================
# Response Schemas
# ============================================================================


class SearchQuerySet(BaseModel):
    """Set of search queries for a claim."""

    company_specific: str = Field(description="Query targeting news about the specific company")
    industry_wide: str = Field(description="Query targeting industry trends and benchmarks")
    controversy: str = Field(description="Query targeting negative coverage or investigations")


class SourceCredibilityResult(BaseModel):
    """Result of credibility tier classification."""

    tier: Literal[1, 2, 3, 4] = Field(description="Credibility tier (1=highest, 4=lowest)")
    reasoning: str = Field(description="Brief explanation of tier assignment")


class ContradictionAnalysis(BaseModel):
    """Analysis of whether a source contradicts a claim."""

    contradicts: bool = Field(description="Whether the source contradicts the claim")
    contradiction_type: Literal["direct", "contextual", "omission", "timeline"] | None = Field(
        default=None, description="Type of contradiction if detected"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the analysis")
    explanation: str = Field(description="Explanation of the contradiction or lack thereof")

    @field_validator('contradiction_type', mode='before')
    @classmethod
    def lowercase_contradiction_type(cls, v):
        """LLM sometimes returns capitalized values like 'Timeline' instead of 'timeline'."""
        if isinstance(v, str):
            return v.lower()
        return v


class NewsMediaAssessmentResult(BaseModel):
    """Overall assessment result for a claim."""

    sources_analyzed: int = Field(default=0)
    contradictions_found: int = Field(default=0)
    tier_distribution: dict[str, int] = Field(default_factory=dict)
    summary: str = Field(default="")
    supports_claim: bool | None = Field(default=None)
    confidence: Literal["high", "medium", "low"] = Field(default="low")


# ============================================================================
# Credibility Tier Domain Constants
# ============================================================================

# Tier 1: Highest credibility - Major investigative journalism, regulatory actions, court filings
TIER_1_DOMAINS = [
    "propublica.org",
    "reuters.com/investigates",
    "sec.gov",
    "justice.gov",
    "courtlistener.com",
    "pacer.gov",
    "ftc.gov",
    "epa.gov/enforcement",
]

# Tier 2: High credibility - Established news organizations, industry publications, government reports
TIER_2_DOMAINS = [
    "nytimes.com",
    "wsj.com",
    "washingtonpost.com",
    "bloomberg.com",
    "ft.com",
    "bbc.com",
    "bbc.co.uk",
    "reuters.com",
    "apnews.com",
    "theguardian.com",
    "economist.com",
    "epa.gov",
    "energy.gov",
    "iea.org",
    "wri.org",
    "cdp.net",
    "spglobal.com",
]

# Tier 3: Medium credibility - Company press releases, wire services, analyst reports
TIER_3_DOMAINS = [
    "prnewswire.com",
    "businesswire.com",
    "globenewswire.com",
    "accesswire.com",
    "seekingalpha.com",
    "fool.com",
    "investopedia.com",
]

# Social media / low credibility domains to exclude or classify as Tier 4
SOCIAL_MEDIA_DOMAINS = [
    "twitter.com",
    "x.com",
    "facebook.com",
    "linkedin.com",
    "reddit.com",
    "instagram.com",
    "tiktok.com",
]

# Tier weights for confidence calculation
TIER_WEIGHTS = {1: 4.0, 2: 3.0, 3: 2.0, 4: 1.0}


# ============================================================================
# System Prompts
# ============================================================================

QUERY_CONSTRUCTION_PROMPT = """You are the News/Media Agent in Sibyl, an AI system that verifies sustainability reports. Your task is to construct targeted search queries to find public news coverage about a sustainability claim.

Given a claim and company name, generate three search queries:
1. **Company-specific**: Target news directly about this company and the claim topic
2. **Industry-wide**: Target broader industry trends, benchmarks, or regulatory patterns
3. **Controversy-focused**: Surface negative coverage, investigations, violations, or greenwashing allegations

Guidelines:
- Include the company name in company-specific and controversy queries
- Use relevant keywords from the claim (emissions, targets, certifications, etc.)
- Add temporal context if the claim mentions specific years
- For controversy queries, include terms like: violation, investigation, lawsuit, greenwashing, controversy, whistleblower

Return ONLY valid JSON matching this schema:
{
    "company_specific": "query string",
    "industry_wide": "query string",
    "controversy": "query string"
}"""


CREDIBILITY_CLASSIFICATION_PROMPT = """You are classifying the credibility tier of a news source for sustainability claim verification.

Tier definitions:
- **Tier 1 (Highest)**: Major investigative journalism (ProPublica, Reuters Investigates), regulatory enforcement actions (SEC, EPA, DOJ), court filings
- **Tier 2 (High)**: Established news organizations (NYT, WSJ, BBC, Bloomberg), industry trade publications, government reports
- **Tier 3 (Medium)**: Company press releases, wire services (PR Newswire, Business Wire), analyst reports
- **Tier 4 (Lowest)**: Blogs, social media, unverified sources, opinion pieces without editorial oversight

Analyze the source and classify it:

Source Title: {title}
Source Domain: {domain}
Source Snippet: {snippet}

Return ONLY valid JSON with fields: tier (integer 1-4), reasoning (string)."""


CONTRADICTION_DETECTION_PROMPT = """You are analyzing whether a news source contradicts a sustainability claim.

Contradiction types:
1. **Direct**: Source explicitly states the opposite (e.g., "emissions increased" vs claim "emissions decreased")
2. **Contextual**: Source provides context that undermines the claim (e.g., renewable certificates vs actual energy source)
3. **Omission**: Source reveals material information the claim omits (e.g., ongoing investigation not disclosed)
4. **Timeline**: Source contradicts dates or timelines in the claim

Claim to verify:
{claim_text}

News Source:
Title: {title}
URL: {url}
Snippet: {snippet}
Published: {published_date}

Analyze whether this source contradicts the claim. Consider:
- Does the source directly contradict any facts in the claim?
- Does it provide context that undermines the claim's implications?
- Does it reveal omitted information that changes the claim's meaning?
- Are there timeline inconsistencies?

Return ONLY valid JSON with fields: contradicts (boolean), contradiction_type (string or null), confidence (number 0-1), explanation (string)."""


RELEVANCE_SUMMARY_PROMPT = """Summarize how this news source relates to the sustainability claim in 2-3 sentences.

Claim: {claim_text}

Source Title: {title}
Source Snippet: {snippet}

Focus on what the source says that is relevant to verifying or contradicting the claim. Be concise and factual."""


# ============================================================================
# Helper Functions - Query Construction
# ============================================================================


async def _construct_search_queries(
    claim: Claim,
    company_name: str,
) -> SearchQuerySet:
    """Use LLM to construct targeted search queries for a claim.
    
    Args:
        claim: The claim to construct queries for
        company_name: The company name from report metadata
        
    Returns:
        SearchQuerySet with three query types
    """
    user_prompt = f"""Construct search queries for this sustainability claim:

Company: {company_name}
Claim: {claim.text}
Claim Type: {claim.claim_type}
IFRS Paragraphs: {', '.join(claim.ifrs_paragraphs) if claim.ifrs_paragraphs else 'None'}

Return the three queries as JSON."""

    try:
        response = await openrouter_client.chat_completion(
            model=Models.DEEPSEEK,  # Cheap model for simple query generation
            messages=[
                {"role": "system", "content": QUERY_CONSTRUCTION_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=1024,
        )

        # Parse JSON response
        cleaned = _clean_json_response(response)
        result = json.loads(cleaned)
        return SearchQuerySet(**result)

    except Exception as e:
        logger.warning("LLM query construction failed, using fallback: %s", e)
        # Fallback to rule-based queries
        return _construct_fallback_queries(claim, company_name)


def _construct_fallback_queries(claim: Claim, company_name: str) -> SearchQuerySet:
    """Construct rule-based fallback queries when LLM fails."""
    claim_keywords = claim.text[:200].replace('"', "").replace("'", "")
    
    return SearchQuerySet(
        company_specific=f'"{company_name}" {claim_keywords[:100]}',
        industry_wide=f'{claim.claim_type} sustainability {claim_keywords[:50]}',
        controversy=f'"{company_name}" (violation OR investigation OR lawsuit OR greenwashing)',
    )


# ============================================================================
# Helper Functions - Web Search Execution
# ============================================================================


async def _execute_web_searches(
    queries: SearchQuerySet,
    time_range: str | None = "year",
    exclude_social: bool = True,
) -> list[dict]:
    """Execute web searches for all query types and combine results.
    
    Args:
        queries: SearchQuerySet with three query types
        time_range: Time filter for searches
        exclude_social: Whether to exclude social media domains
        
    Returns:
        Combined list of unique search results
    """
    exclude_domains = SOCIAL_MEDIA_DOMAINS if exclude_social else None
    
    all_results = []
    seen_urls = set()
    
    for query_name, query in [
        ("company_specific", queries.company_specific),
        ("industry_wide", queries.industry_wide),
        ("controversy", queries.controversy),
    ]:
        try:
            response = await search_web_async(
                query=query,
                max_results=10,
                exclude_domains=exclude_domains,
                time_range=time_range,
                search_depth="basic",
            )
            
            for result in response.get("results", []):
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    result["query_type"] = query_name
                    all_results.append(result)
                    
        except SearchAPIError as e:
            logger.warning("Search failed for %s query: %s", query_name, e)
            # Continue with other queries
            
    return all_results


# ============================================================================
# Helper Functions - Credibility Tiering
# ============================================================================


def _assign_tier_by_domain(source_domain: str) -> int | None:
    """Assign credibility tier based on domain matching.
    
    Returns tier 1-4, or None if domain not recognized.
    """
    domain_lower = source_domain.lower()
    
    # Check Tier 1
    for tier1_domain in TIER_1_DOMAINS:
        if tier1_domain in domain_lower:
            return 1
    
    # Check Tier 2
    for tier2_domain in TIER_2_DOMAINS:
        if tier2_domain in domain_lower:
            return 2
    
    # Check Tier 3
    for tier3_domain in TIER_3_DOMAINS:
        if tier3_domain in domain_lower:
            return 3
    
    # Check social media (Tier 4)
    for social_domain in SOCIAL_MEDIA_DOMAINS:
        if social_domain in domain_lower:
            return 4
    
    return None  # Unknown domain


async def _assign_credibility_tier(source: dict) -> SourceCredibilityResult:
    """Assign credibility tier to a source using domain matching + LLM fallback.
    
    Args:
        source: Search result dict with title, url, snippet, source_domain
        
    Returns:
        SourceCredibilityResult with tier and reasoning
    """
    domain = source.get("source_domain", "")
    
    # Fast path: domain-based classification
    tier = _assign_tier_by_domain(domain)
    if tier is not None:
        reasoning_map = {
            1: "Major investigative journalism or regulatory source",
            2: "Established news organization or government source",
            3: "Press release service or wire service",
            4: "Social media or unverified source",
        }
        return SourceCredibilityResult(tier=tier, reasoning=reasoning_map[tier])
    
    # Fallback: LLM classification for unknown domains
    try:
        prompt = CREDIBILITY_CLASSIFICATION_PROMPT.format(
            title=source.get("title", ""),
            domain=domain,
            snippet=source.get("snippet", "")[:500],
        )
        
        response = await openrouter_client.chat_completion(
            model=Models.CLAUDE_HAIKU,  # Fast, cheap for classification
            messages=[
                {"role": "system", "content": "You classify news source credibility. Output only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=256,
        )
        
        cleaned = _clean_json_response(response)
        result = json.loads(cleaned)
        return SourceCredibilityResult(
            tier=result.get("tier", 4),
            reasoning=result.get("reasoning", "LLM classification"),
        )
        
    except Exception as e:
        logger.warning("LLM credibility classification failed: %s", e)
        # Default to Tier 4 for unknown sources
        return SourceCredibilityResult(
            tier=4,
            reasoning="Unknown source - defaulting to lowest tier",
        )


# ============================================================================
# Helper Functions - Contradiction Detection
# ============================================================================


async def _detect_contradiction(
    claim: Claim,
    source: dict,
) -> ContradictionAnalysis:
    """Analyze whether a source contradicts a claim using LLM.
    
    Args:
        claim: The claim being verified
        source: Search result dict
        
    Returns:
        ContradictionAnalysis with contradiction details
    """
    prompt = CONTRADICTION_DETECTION_PROMPT.format(
        claim_text=claim.text,
        title=source.get("title", ""),
        url=source.get("url", ""),
        snippet=source.get("snippet", "")[:1000],
        published_date=source.get("published_date", "Unknown"),
    )
    
    try:
        response = await openrouter_client.chat_completion(
            model=Models.CLAUDE_HAIKU,  # Fast, cheap for classification
            messages=[
                {"role": "system", "content": "You analyze news sources for contradictions. Output only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=512,
        )
        
        cleaned = _clean_json_response(response)
        result = json.loads(cleaned)
        return ContradictionAnalysis(
            contradicts=result.get("contradicts", False),
            contradiction_type=result.get("contradiction_type"),
            confidence=result.get("confidence", 0.5),
            explanation=result.get("explanation", ""),
        )
        
    except Exception as e:
        logger.warning("Contradiction detection failed: %s", e)
        return ContradictionAnalysis(
            contradicts=False,
            contradiction_type=None,
            confidence=0.0,
            explanation=f"Analysis failed: {str(e)}",
        )


# ============================================================================
# Helper Functions - Relevance Summary
# ============================================================================


async def _generate_relevance_summary(claim: Claim, source: dict) -> str:
    """Generate a plain-language relevance summary for a source.
    
    Args:
        claim: The claim being verified
        source: Search result dict
        
    Returns:
        2-3 sentence relevance summary
    """
    prompt = RELEVANCE_SUMMARY_PROMPT.format(
        claim_text=claim.text[:500],
        title=source.get("title", ""),
        snippet=source.get("snippet", "")[:500],
    )
    
    try:
        response = await openrouter_client.chat_completion(
            model=Models.CLAUDE_HAIKU,  # Fast, cheap for summarization
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=256,
        )
        return response.strip()
        
    except Exception as e:
        logger.warning("Relevance summary generation failed: %s", e)
        return f"Source discusses: {source.get('title', 'Unknown topic')}"


# ============================================================================
# Helper Functions - Finding Generation
# ============================================================================


def _create_source_finding(
    claim: Claim,
    source: dict,
    tier: int,
    contradiction: ContradictionAnalysis,
    relevance_summary: str,
    iteration: int,
) -> AgentFinding:
    """Create an AgentFinding for a single source.
    
    Args:
        claim: The claim being verified
        source: Search result dict
        tier: Credibility tier (1-4)
        contradiction: Contradiction analysis result
        relevance_summary: Plain-language relevance summary
        iteration: Current iteration count
        
    Returns:
        AgentFinding object
    """
    # Calculate weighted confidence
    base_confidence = contradiction.confidence
    tier_weight = TIER_WEIGHTS.get(tier, 1.0) / 4.0  # Normalize to 0-1
    weighted_confidence = base_confidence * tier_weight
    
    # Determine evidence type
    if contradiction.contradicts:
        evidence_type = "news_contradiction"
    else:
        evidence_type = "news_source"
    
    # Build summary
    if contradiction.contradicts:
        summary = f"Source contradicts claim ({contradiction.contradiction_type}): {contradiction.explanation[:200]}"
    else:
        summary = relevance_summary[:300]
    
    return AgentFinding(
        finding_id=str(generate_uuid7()),
        agent_name="news_media",
        claim_id=claim.claim_id,
        evidence_type=evidence_type,
        summary=summary,
        details={
            "source_url": source.get("url", ""),
            "source_title": source.get("title", ""),
            "source_domain": source.get("source_domain", ""),
            "source_tier": tier,
            "published_date": source.get("published_date"),
            "relevance_summary": relevance_summary,
            "contradicts_claim": contradiction.contradicts,
            "contradiction_type": contradiction.contradiction_type,
            "contradiction_explanation": contradiction.explanation if contradiction.contradicts else None,
            "snippet": source.get("snippet", "")[:500],
            "query_type": source.get("query_type"),
        },
        supports_claim=not contradiction.contradicts if contradiction.contradicts else None,
        confidence="high" if weighted_confidence > 0.7 else "medium" if weighted_confidence > 0.4 else "low",
        iteration=iteration,
    )


def _create_summary_finding(
    claim: Claim,
    source_findings: list[AgentFinding],
    iteration: int,
) -> AgentFinding:
    """Create a summary finding aggregating all sources for a claim.
    
    Args:
        claim: The claim being verified
        source_findings: List of individual source findings
        iteration: Current iteration count
        
    Returns:
        AgentFinding with aggregated summary
    """
    # Count stats
    total_sources = len(source_findings)
    contradicting = sum(1 for f in source_findings if f.details.get("contradicts_claim"))
    supporting = total_sources - contradicting
    
    # Tier distribution
    tier_dist = {1: 0, 2: 0, 3: 0, 4: 0}
    for f in source_findings:
        tier = f.details.get("source_tier", 4)
        tier_dist[tier] = tier_dist.get(tier, 0) + 1
    
    # Determine overall support
    # Strong contradiction if any Tier 1 contradicts or 2+ Tier 2 contradict
    tier_1_contradictions = sum(
        1 for f in source_findings
        if f.details.get("contradicts_claim") and f.details.get("source_tier") == 1
    )
    tier_2_contradictions = sum(
        1 for f in source_findings
        if f.details.get("contradicts_claim") and f.details.get("source_tier") == 2
    )
    
    if tier_1_contradictions > 0 or tier_2_contradictions >= 2:
        supports_claim = False
        confidence = "high"
    elif contradicting > supporting:
        supports_claim = False
        confidence = "medium"
    elif contradicting > 0:
        supports_claim = None  # Mixed evidence
        confidence = "medium"
    elif total_sources == 0:
        supports_claim = None
        confidence = "low"
    else:
        supports_claim = True
        confidence = "medium"
    
    # Build summary
    summary = (
        f"Found {total_sources} sources: {supporting} supporting, {contradicting} contradicting. "
        f"Tier distribution: T1={tier_dist[1]}, T2={tier_dist[2]}, T3={tier_dist[3]}, T4={tier_dist[4]}."
    )
    
    if tier_1_contradictions > 0:
        summary += f" High-credibility contradiction from {tier_1_contradictions} Tier 1 source(s)."
    
    return AgentFinding(
        finding_id=str(generate_uuid7()),
        agent_name="news_media",
        claim_id=claim.claim_id,
        evidence_type="news_investigation_summary",
        summary=summary,
        details={
            "total_sources": total_sources,
            "supporting_sources": supporting,
            "contradicting_sources": contradicting,
            "tier_distribution": tier_dist,
            "key_findings": [
                {
                    "url": f.details.get("source_url"),
                    "tier": f.details.get("source_tier"),
                    "contradicts": f.details.get("contradicts_claim"),
                }
                for f in source_findings[:5]  # Top 5
            ],
        },
        supports_claim=supports_claim,
        confidence=confidence,
        iteration=iteration,
    )


# ============================================================================
# Helper Functions - Inter-Agent Communication
# ============================================================================


def _should_request_cross_domain(claim: Claim, sources: list[dict]) -> tuple[str, str] | None:
    """Determine if cross-domain verification is needed.
    
    Args:
        claim: The claim being verified
        sources: Search results
        
    Returns:
        Tuple of (target_agent, description) if verification needed, None otherwise
    """
    claim_lower = claim.text.lower()
    
    # Geographic verification for location-specific claims
    location_keywords = ["facility", "site", "plant", "location", "headquarters", "operations in"]
    if any(kw in claim_lower for kw in location_keywords):
        # Check if sources mention geographic inconsistencies
        for source in sources:
            snippet = source.get("snippet", "").lower()
            if any(word in snippet for word in ["different location", "not located", "closed", "relocated"]):
                return ("geography", f"Verify facility locations mentioned in claim {claim.claim_id}")
    
    # Regulatory verification for legal claims
    if claim.claim_type == "legal_governance":
        if any(word in claim_lower for word in ["certified", "compliance", "audit", "iso"]):
            return ("legal", f"Verify regulatory compliance status for claim {claim.claim_id}")
    
    # Academic verification for methodology claims
    if "methodology" in claim_lower or "scientif" in claim_lower:
        return ("academic", f"Verify scientific methodology in claim {claim.claim_id}")
    
    return None


def _process_info_responses(state: SibylState, claim: Claim) -> list[dict]:
    """Find and process InfoResponses relevant to this claim.
    
    Args:
        state: Current pipeline state
        claim: The claim to find responses for
        
    Returns:
        List of response data dicts
    """
    responses = []
    info_responses = state.get("info_responses", [])
    info_requests = state.get("info_requests", [])
    
    # Find requests from news_media agent for this claim
    our_requests = [
        req for req in info_requests
        if req.requesting_agent == "news_media"
        and req.context.get("claim_id") == claim.claim_id
    ]
    
    # Find matching responses
    for req in our_requests:
        for resp in info_responses:
            if resp.request_id == req.request_id:
                responses.append({
                    "responding_agent": resp.responding_agent,
                    "response": resp.response,
                    "details": resp.details,
                })
    
    return responses


# ============================================================================
# Helper Functions - Re-investigation
# ============================================================================


def _get_reinvestigation_context(
    state: SibylState,
    claim_id: str,
) -> ReinvestigationRequest | None:
    """Get re-investigation request targeting news_media agent for a claim.
    
    Args:
        state: Current pipeline state
        claim_id: The claim ID to check
        
    Returns:
        ReinvestigationRequest if found, None otherwise
    """
    reinvestigation_requests = state.get("reinvestigation_requests", [])
    
    for req in reinvestigation_requests:
        if req.claim_id == claim_id and "news_media" in req.target_agents:
            return req
    
    return None


async def _process_reinvestigation(
    claim: Claim,
    reinvest_request: ReinvestigationRequest,
    company_name: str,
) -> list[dict]:
    """Execute re-investigation using Judge's refined queries.
    
    Args:
        claim: The claim to re-investigate
        reinvest_request: The re-investigation request with refined queries
        company_name: Company name for queries
        
    Returns:
        List of search results from refined queries
    """
    all_results = []
    seen_urls = set()
    
    for query in reinvest_request.refined_queries:
        # Substitute company name if placeholder present
        query = query.replace("{company_name}", company_name)
        
        try:
            response = await search_web_async(
                query=query,
                max_results=10,
                exclude_domains=SOCIAL_MEDIA_DOMAINS,
                time_range="all",  # Cast wider net for re-investigation
                search_depth="advanced",  # Deeper search for re-investigation
            )
            
            for result in response.get("results", []):
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    result["query_type"] = "reinvestigation"
                    all_results.append(result)
                    
        except SearchAPIError as e:
            logger.warning("Re-investigation search failed: %s", e)
    
    return all_results


# ============================================================================
# Helper Functions - Utilities
# ============================================================================


def _clean_json_response(response: str) -> str:
    """Clean LLM response to extract valid JSON."""
    cleaned = response.strip()
    if cleaned.startswith("```"):
        # Remove markdown code blocks
        lines = cleaned.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.startswith("```"):
                in_block = not in_block
                continue
            if in_block or not cleaned.startswith("```"):
                json_lines.append(line)
        cleaned = "\n".join(json_lines)
    return cleaned.strip()


def _get_company_name(state: SibylState) -> str:
    """Extract company name from state/report metadata.
    
    For now, returns a placeholder. In full implementation, would
    extract from report metadata stored in state.
    """
    # TODO: Extract from report metadata when available
    # For now, return a default that won't break queries
    return "the company"


# ============================================================================
# Main Node Function
# ============================================================================


async def investigate_news(state: SibylState) -> dict:
    """News/Media Agent: Investigate claims via public news sources.

    Reads: state.routing_plan, state.claims, state.info_requests,
           state.reinvestigation_requests, state.iteration_count
    Writes: state.findings, state.agent_status, state.info_requests

    Responsibilities:
    1. Find claims assigned to this agent in the routing plan.
    2. Construct targeted search queries for each claim.
    3. Execute web searches via search_web tool.
    4. Evaluate source credibility and assign tiers.
    5. Detect contradictions between sources and claims.
    6. Produce structured evidence findings.
    7. Handle InfoRequests and re-investigation requests.

    Returns:
        Partial state update with findings, agent status.
    """
    agent_name = "news_media"
    findings: list[AgentFinding] = []
    info_requests: list[InfoRequest] = []

    # Emit start event (immediately sent to frontend)
    emit_agent_started(agent_name)

    # Find claims assigned to this agent
    routing_plan = state.get("routing_plan", [])
    claims = list(state.get("claims", []))
    iteration_count = state.get("iteration_count", 0)
    company_name = _get_company_name(state)

    assigned_assignments = [
        a for a in routing_plan
        if agent_name in a.assigned_agents
    ]
    
    assigned_claim_ids = {a.claim_id for a in assigned_assignments}
    assigned_claims = [c for c in claims if c.claim_id in assigned_claim_ids]

    logger.info(
        "News/Media Agent processing %d claims (iteration %d)",
        len(assigned_claims),
        iteration_count,
    )

    if not assigned_claims:
        # No claims assigned
        emit_agent_completed(agent_name, claims_processed=0, findings_count=0)
        return {
            "findings": findings,
            "agent_status": {
                agent_name: AgentStatus(
                    agent_name=agent_name,
                    status="completed",
                    claims_assigned=0,
                    claims_completed=0,
                )
            },
        }

    # Emit thinking event
    emit_agent_thinking(agent_name, f"Investigating {len(assigned_claims)} claims via public news sources...")

    total_contradictions = 0

    # Process claims in parallel with rate limiting
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_CLAIMS)
    
    async def process_single_claim(claim: Claim) -> tuple[list[AgentFinding], list[InfoRequest], int]:
        """Process a single claim and return findings, info requests, and contradiction count.
        
        Events are emitted directly via stream_utils (context propagates in Python 3.12).
        """
        claim_findings: list[AgentFinding] = []
        claim_info_requests: list[InfoRequest] = []
        claim_contradictions = 0
        
        async with semaphore:
            try:
                # Emit claim investigation event
                emit_event("claim_investigating", agent_name, {
                    "claim_id": claim.claim_id,
                    "claim_text": claim.text[:200],
                })
                
                # Check for re-investigation context
                reinvest_request = _get_reinvestigation_context(state, claim.claim_id)
                
                if reinvest_request:
                    emit_agent_thinking(agent_name, f"Re-investigating claim {claim.claim_id}: {reinvest_request.evidence_gap}")
                    search_results = await _process_reinvestigation(
                        claim, reinvest_request, company_name
                    )
                else:
                    # Standard investigation
                    emit_agent_thinking(agent_name, "Constructing search queries for claim...")
                    
                    # Construct queries
                    queries = await _construct_search_queries(claim, company_name)
                    
                    # Execute searches
                    search_results = await _execute_web_searches(queries)
                    
                    # Emit search executed event
                    emit_search_executed(
                        agent_name=agent_name,
                        query=queries.company_specific,
                        results_count=len(search_results),
                        source="web",
                    )
                
                # Process each search result
                source_findings: list[AgentFinding] = []
                
                for source in search_results:
                    # Assign credibility tier
                    credibility = await _assign_credibility_tier(source)
                    
                    # Emit source evaluated event
                    emit_source_evaluated(
                        agent_name=agent_name,
                        source_name=source.get("source_domain", ""),
                        credibility_tier=credibility.tier,
                        url=source.get("url"),
                    )
                    
                    # Detect contradiction
                    contradiction = await _detect_contradiction(claim, source)
                    
                    if contradiction.contradicts:
                        claim_contradictions += 1
                        
                        # Emit contradiction detected event
                        emit_contradiction_detected(
                            agent_name=agent_name,
                            claim_id=claim.claim_id,
                            source1=source.get("source_domain", "source"),
                            source2="claim",
                            description=contradiction.explanation[:200] if contradiction.explanation else "",
                        )
                    
                    # Generate relevance summary
                    relevance_summary = await _generate_relevance_summary(claim, source)
                    
                    # Create finding for this source
                    source_finding = _create_source_finding(
                        claim=claim,
                        source=source,
                        tier=credibility.tier,
                        contradiction=contradiction,
                        relevance_summary=relevance_summary,
                        iteration=iteration_count + 1,
                    )
                    source_findings.append(source_finding)
                    claim_findings.append(source_finding)
                
                # Create summary finding for this claim
                if source_findings:
                    summary_finding = _create_summary_finding(
                        claim=claim,
                        source_findings=source_findings,
                        iteration=iteration_count + 1,
                    )
                    claim_findings.append(summary_finding)
                    
                    # Emit evidence found event
                    emit_evidence_found(
                        agent_name=agent_name,
                        claim_id=claim.claim_id,
                        evidence_type="news_investigation_summary",
                        summary=summary_finding.summary[:200] if summary_finding.summary else "",
                        supports_claim=summary_finding.supports_claim,
                        confidence=summary_finding.confidence,
                    )
                
                # Check if cross-domain verification is needed
                if not reinvest_request:
                    cross_domain = _should_request_cross_domain(claim, search_results)
                    if cross_domain:
                        target_agent, description = cross_domain
                        info_req = InfoRequest(
                            request_id=str(generate_uuid7()),
                            requesting_agent=agent_name,
                            description=description,
                            context={
                                "claim_id": claim.claim_id,
                                "claim_text": claim.text[:200],
                                "target_agent": target_agent,
                            },
                            status="pending",
                        )
                        claim_info_requests.append(info_req)
                        
                        emit_event("info_request_posted", agent_name, {
                            "request_id": info_req.request_id,
                            "target_agent": target_agent,
                            "description": description,
                        })
                
                # Check for InfoResponses from other agents
                info_resp_data = _process_info_responses(state, claim)
                if info_resp_data and source_findings:
                    # Incorporate into the last finding
                    source_findings[-1].details["cross_domain_evidence"] = info_resp_data
                
                return claim_findings, claim_info_requests, claim_contradictions
                    
            except Exception as e:
                logger.error("Error processing claim %s: %s", claim.claim_id, e)
                emit_error(agent_name, f"Claim {claim.claim_id}: {str(e)}")
                # Create error finding
                error_finding = AgentFinding(
                    finding_id=str(generate_uuid7()),
                    agent_name=agent_name,
                    claim_id=claim.claim_id,
                    evidence_type="error",
                    summary=f"Error during news investigation: {str(e)}",
                    details={"error": str(e)},
                    supports_claim=None,
                    confidence="low",
                    iteration=iteration_count + 1,
                )
                claim_findings.append(error_finding)
                return claim_findings, claim_info_requests, claim_contradictions
    
    # Run all claims in parallel
    results = await asyncio.gather(*[process_single_claim(c) for c in assigned_claims])
    
    # Aggregate results
    for claim_findings, claim_info_requests, claim_contradictions in results:
        findings.extend(claim_findings)
        info_requests.extend(claim_info_requests)
        total_contradictions += claim_contradictions

    # Emit completion event
    emit_agent_completed(agent_name, claims_processed=len(assigned_claims), findings_count=len(findings))

    # Return partial state update
    result: dict = {
        "findings": findings,
        "agent_status": {
            agent_name: AgentStatus(
                agent_name=agent_name,
                status="completed",
                claims_assigned=len(assigned_claims),
                claims_completed=len(assigned_claims),
            )
        },
    }
    
    if info_requests:
        result["info_requests"] = info_requests
    
    return result
