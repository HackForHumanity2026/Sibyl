"""Academic/Research Agent - validates technical claims against research.

Implements FRD 9.

Model: DeepSeek V3.2 (fast and cost-effective for research synthesis)

The Academic/Research Agent performs:
- Academic search query construction (Google Scholar-style, benchmarks, standards)
- Web search via Tavily API (reuses search_web tool from FRD 8)
- Methodology validation against GHG Protocol, ISO 14064, SBTi frameworks
- Certification and carbon offset legitimacy assessment
- Science-based target alignment validation
- Benchmark comparison (emission intensities, sector metrics)
- Technology/practice research support validation
- Inter-agent communication for cross-domain verification
- Re-investigation handling for Judge-requested deeper analysis
"""

import json
import logging
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from app.agents.state import (
    AgentFinding,
    AgentStatus,
    Claim,
    InfoRequest,
    InfoResponse,
    ReinvestigationRequest,
    RoutingAssignment,
    SibylState,
    StreamEvent,
)
from app.agents.tools.search_web import SearchAPIError, search_web_async
from app.core.database import generate_uuid7
from app.services.openrouter_client import Models, openrouter_client

logger = logging.getLogger(__name__)


# ============================================================================
# Investigation Types
# ============================================================================

INVESTIGATION_TYPES = Literal[
    "methodology_validation",
    "certification_validation",
    "sbti_validation",
    "benchmark_comparison",
    "research_support",
]

# Keywords for classifying investigation types
METHODOLOGY_KEYWORDS = [
    "methodology", "calculation method", "accounting standard", "ghg protocol",
    "iso 14064", "emission factor", "spend-based", "activity-based",
    "life-cycle analysis", "measurement", "reporting framework",
]

CERTIFICATION_KEYWORDS = [
    "renewable energy certificate", "rec", "i-rec", "carbon offset",
    "carbon credit", "vcs", "gold standard", "certified", "certification",
    "verified carbon standard", "cdm", "redd+",
]

SBTI_KEYWORDS = [
    "science-based target", "sbti", "net-zero", "1.5°c pathway",
    "1.5 degree", "sbti validated", "science based targets",
    "net zero", "paris-aligned",
]

BENCHMARK_KEYWORDS = [
    "emission intensity", "sector benchmark", "industry average",
    "per revenue", "per unit", "peer comparison", "top quartile",
    "cdp disclosure", "sector average",
]

RESEARCH_KEYWORDS = [
    "technology reduces", "innovation", "pilot", "carbon capture",
    "efficiency", "practice reduces", "circular economy",
    "renewable energy technology", "hydrogen",
]


# ============================================================================
# Response Schemas
# ============================================================================


class AcademicSearchQuerySet(BaseModel):
    """Set of targeted academic search queries."""

    queries: list[str] = Field(
        description="List of 2-4 targeted academic search queries"
    )


class AcademicAnalysisResult(BaseModel):
    """Structured analysis result from LLM."""

    investigation_type: str = Field(description="Type of investigation performed")
    supports_claim: bool | None = Field(
        default=None,
        description="True = supports, False = contradicts, None = inconclusive"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score"
    )
    standard_alignment: str | None = Field(
        default=None,
        description="aligned | partially_aligned | not_aligned | unknown"
    )
    legitimacy_assessment: str | None = Field(
        default=None,
        description="legitimate | questionable | not_recognized | unknown"
    )
    sbti_validation_status: str | None = Field(
        default=None,
        description="validated | not_validated | status_unclear"
    )
    plausibility: str | None = Field(
        default=None,
        description="plausible | high | low | outlier | unknown"
    )
    benchmark_range: dict | None = Field(
        default=None,
        description="Benchmark range with min, max, median, reported, unit"
    )
    research_consensus: str | None = Field(
        default=None,
        description="Summary of peer-reviewed research findings"
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Identified limitations or concerns"
    )
    references: list[dict] = Field(
        default_factory=list,
        description="Academic references, benchmark sources, standard documents"
    )
    summary: str = Field(
        default="",
        description="Plain-language assessment summary"
    )


# ============================================================================
# System Prompts
# ============================================================================

QUERY_CONSTRUCTION_PROMPT = """You are the Academic/Research Agent in Sibyl, an AI system that validates technical sustainability claims against peer-reviewed research, industry benchmarks, and recognized standards.

Your task is to construct 2-4 targeted search queries to find academic evidence for a sustainability claim.

Investigation type: {investigation_type}

Guidelines by investigation type:
- methodology_validation: Search for GHG Protocol, ISO 14064 standards, peer-reviewed methodology evaluations
- certification_validation: Search for certification registry standards, additionality research, greenwashing studies
- sbti_validation: Search for SBTi methodology documents, validation criteria, company validation status
- benchmark_comparison: Search for CDP disclosures, industry emission intensity benchmarks, sector averages
- research_support: Search for peer-reviewed papers on the specific technology/practice effectiveness

Include relevant keywords from the claim. Add domain-specific modifiers like "peer-reviewed", "research", "benchmark", "standard".

Return ONLY valid JSON matching this schema:
{{"queries": ["query1", "query2", "query3"]}}"""


ANALYSIS_PROMPT = """You are the Academic/Research Agent in Sibyl, an AI system that validates technical sustainability claims against peer-reviewed research, industry benchmarks, and recognized standards.

Analyze the following search results and produce a structured finding.

CLAIM: {claim_text}
INVESTIGATION TYPE: {investigation_type}

SEARCH RESULTS:
{search_results}

Produce a structured JSON assessment with these fields:
- investigation_type: "{investigation_type}"
- supports_claim: true/false/null (null if inconclusive)
- confidence: 0.0-1.0
- standard_alignment: "aligned" | "partially_aligned" | "not_aligned" | "unknown" (for methodology)
- legitimacy_assessment: "legitimate" | "questionable" | "not_recognized" | "unknown" (for certification/offset)
- sbti_validation_status: "validated" | "not_validated" | "status_unclear" (for SBTi)
- plausibility: "plausible" | "high" | "low" | "outlier" | "unknown" (for benchmark)
- benchmark_range: {{"min": float, "max": float, "median": float, "reported": float, "unit": str}} or null
- research_consensus: summary of peer-reviewed findings
- limitations: [list of limitations or concerns]
- references: [list of {{type, title, authors, publication_date, url, snippet, source_credibility}}]
- summary: plain-language assessment (2-3 sentences)

Return ONLY valid JSON."""


# ============================================================================
# Helper Functions - Investigation Type Classification
# ============================================================================


def _classify_investigation_type(claim: Claim) -> str:
    """Classify the investigation type based on claim content.

    Args:
        claim: The claim to classify

    Returns:
        Investigation type string
    """
    claim_lower = claim.text.lower()

    # Check keywords in priority order
    if any(kw in claim_lower for kw in SBTI_KEYWORDS):
        return "sbti_validation"

    if any(kw in claim_lower for kw in CERTIFICATION_KEYWORDS):
        return "certification_validation"

    if any(kw in claim_lower for kw in BENCHMARK_KEYWORDS):
        return "benchmark_comparison"

    if any(kw in claim_lower for kw in METHODOLOGY_KEYWORDS):
        return "methodology_validation"

    if any(kw in claim_lower for kw in RESEARCH_KEYWORDS):
        return "research_support"

    # Fallback: quantitative claims → benchmark, strategic → methodology
    if claim.claim_type == "quantitative":
        return "benchmark_comparison"
    if claim.claim_type == "strategic":
        return "methodology_validation"

    return "research_support"


# ============================================================================
# Helper Functions - Query Construction
# ============================================================================


async def _construct_academic_queries(
    claim: Claim,
    investigation_type: str,
) -> AcademicSearchQuerySet:
    """Use LLM to construct targeted academic search queries.

    Args:
        claim: The claim to construct queries for
        investigation_type: Type of investigation

    Returns:
        AcademicSearchQuerySet with search queries
    """
    user_prompt = f"""Construct search queries for this sustainability claim:

Claim: {claim.text}
Claim Type: {claim.claim_type}
IFRS Paragraphs: {', '.join(claim.ifrs_paragraphs) if claim.ifrs_paragraphs else 'None'}

Return the queries as JSON."""

    try:
        response = await openrouter_client.chat_completion(
            model=Models.DEEPSEEK,
            messages=[
                {
                    "role": "system",
                    "content": QUERY_CONSTRUCTION_PROMPT.format(
                        investigation_type=investigation_type
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=1024,
        )

        cleaned = _clean_json_response(response)
        result = json.loads(cleaned)
        return AcademicSearchQuerySet(**result)

    except Exception as e:
        logger.warning("LLM query construction failed, using fallback: %s", e)
        return _construct_fallback_queries(claim, investigation_type)


def _construct_fallback_queries(
    claim: Claim,
    investigation_type: str,
) -> AcademicSearchQuerySet:
    """Construct rule-based fallback queries when LLM fails.

    Args:
        claim: The claim to build queries for
        investigation_type: Type of investigation

    Returns:
        AcademicSearchQuerySet with rule-based queries
    """
    claim_snippet = claim.text[:150].replace('"', "").replace("'", "")

    queries = []

    if investigation_type == "methodology_validation":
        queries = [
            f"GHG Protocol {claim_snippet[:80]} calculation method",
            f"{claim_snippet[:80]} ISO 14064 alignment peer-reviewed",
            f"{claim_snippet[:80]} emission reduction methodology research",
        ]
    elif investigation_type == "certification_validation":
        queries = [
            f"{claim_snippet[:80]} certificate standard registry legitimacy",
            f"{claim_snippet[:80]} additionality peer-reviewed research",
            f"{claim_snippet[:80]} greenwashing certification study",
        ]
    elif investigation_type == "sbti_validation":
        queries = [
            f"SBTi methodology {claim_snippet[:80]} validation criteria",
            f"SBTi 1.5C pathway {claim.claim_type} sector targets",
            f"science based targets net-zero validation requirements",
        ]
    elif investigation_type == "benchmark_comparison":
        queries = [
            f"{claim_snippet[:80]} emission intensity benchmark",
            f"CDP {claim.claim_type} sector emission intensity average",
            f"{claim_snippet[:80]} peer-reviewed sector comparison",
        ]
    elif investigation_type == "research_support":
        queries = [
            f"{claim_snippet[:80]} emission reduction peer-reviewed",
            f"{claim_snippet[:80]} effectiveness study journal",
            f"{claim_snippet[:80]} carbon footprint research",
        ]
    else:
        queries = [
            f"{claim_snippet[:80]} sustainability peer-reviewed research",
            f"{claim_snippet[:80]} academic validation",
        ]

    return AcademicSearchQuerySet(queries=queries)


# ============================================================================
# Helper Functions - Web Search Execution
# ============================================================================


async def _execute_academic_searches(
    queries: AcademicSearchQuerySet,
) -> list[dict]:
    """Execute web searches for all academic queries and combine results.

    Args:
        queries: AcademicSearchQuerySet with queries

    Returns:
        Combined list of unique search results
    """
    all_results = []
    seen_urls: set[str] = set()

    for i, query in enumerate(queries.queries[:5]):  # Max 5 queries
        try:
            response = await search_web_async(
                query=query,
                max_results=10,
                search_depth="basic",
            )

            for result in response.get("results", []):
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    result["query_index"] = i
                    all_results.append(result)

        except SearchAPIError as e:
            logger.warning("Academic search failed for query %d: %s", i, e)

    return all_results


# ============================================================================
# Helper Functions - LLM Analysis
# ============================================================================


async def _analyze_search_results(
    claim: Claim,
    results: list[dict],
    investigation_type: str,
) -> AcademicAnalysisResult:
    """Use DeepSeek V3.2 to analyze search results and produce structured findings.

    Args:
        claim: The claim being investigated
        results: Search results to analyze
        investigation_type: Type of investigation

    Returns:
        AcademicAnalysisResult with structured assessment
    """
    # Format search results for the prompt
    results_text = ""
    for i, r in enumerate(results[:15], 1):  # Max 15 results
        results_text += f"\n[{i}] Title: {r.get('title', 'N/A')}\n"
        results_text += f"    URL: {r.get('url', 'N/A')}\n"
        results_text += f"    Snippet: {r.get('snippet', 'N/A')[:400]}\n"
        results_text += f"    Published: {r.get('published_date', 'N/A')}\n"

    if not results_text:
        results_text = "No search results found."

    prompt = ANALYSIS_PROMPT.format(
        claim_text=claim.text,
        investigation_type=investigation_type,
        search_results=results_text,
    )

    try:
        response = await openrouter_client.chat_completion(
            model=Models.DEEPSEEK,
            messages=[
                {
                    "role": "system",
                    "content": "You are an academic research analyst. Produce structured JSON assessments.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=8192,
        )

        cleaned = _clean_json_response(response)
        result = json.loads(cleaned)
        return AcademicAnalysisResult(**result)

    except Exception as e:
        logger.warning("LLM analysis failed: %s", e)
        return AcademicAnalysisResult(
            investigation_type=investigation_type,
            supports_claim=None,
            confidence=0.0,
            research_consensus=None,
            limitations=[f"Analysis failed: {str(e)}"],
            summary=f"Unable to complete {investigation_type} analysis due to error: {str(e)}",
        )


# ============================================================================
# Helper Functions - Finding Generation
# ============================================================================


def _create_academic_finding(
    claim: Claim,
    analysis: AcademicAnalysisResult,
    search_results: list[dict],
    iteration: int,
) -> AgentFinding:
    """Create an AgentFinding from academic analysis results.

    Args:
        claim: The claim being investigated
        analysis: Analysis result from LLM
        search_results: Raw search results for reference
        iteration: Current iteration count

    Returns:
        AgentFinding object
    """
    # Build details dict
    details = {
        "investigation_type": analysis.investigation_type,
        "research_consensus": analysis.research_consensus,
        "limitations": analysis.limitations,
        "academic_references": analysis.references,
    }

    # Add type-specific fields
    if analysis.standard_alignment:
        details["standard_alignment"] = analysis.standard_alignment
    if analysis.legitimacy_assessment:
        details["legitimacy_assessment"] = analysis.legitimacy_assessment
    if analysis.sbti_validation_status:
        details["sbti_validation_status"] = analysis.sbti_validation_status
    if analysis.plausibility:
        details["plausibility"] = analysis.plausibility
    if analysis.benchmark_range:
        details["benchmark_range"] = analysis.benchmark_range

    # Add search result URLs as references
    details["source_urls"] = [
        r.get("url", "") for r in search_results[:10] if r.get("url")
    ]

    # Map confidence float to string
    confidence_val = analysis.confidence
    if confidence_val >= 0.7:
        confidence_str = "high"
    elif confidence_val >= 0.4:
        confidence_str = "medium"
    else:
        confidence_str = "low"

    return AgentFinding(
        finding_id=str(generate_uuid7()),
        agent_name="academic",
        claim_id=claim.claim_id,
        evidence_type=analysis.investigation_type,
        summary=analysis.summary or f"Academic investigation ({analysis.investigation_type}) completed.",
        details=details,
        supports_claim=analysis.supports_claim,
        confidence=confidence_str,
        iteration=iteration,
    )


# ============================================================================
# Helper Functions - Inter-Agent Communication
# ============================================================================


def _should_request_cross_domain(
    claim: Claim,
    investigation_type: str,
    results: list[dict],
) -> tuple[str, str] | None:
    """Determine if cross-domain verification is needed.

    Returns:
        Tuple of (target_agent, description) if needed, None otherwise
    """
    claim_lower = claim.text.lower()

    # Request data_metrics for quantitative verification
    if investigation_type == "benchmark_comparison":
        if any(word in claim_lower for word in ["scope 1", "scope 2", "scope 3", "total emissions"]):
            return (
                "data_metrics",
                f"Verify reported emission figures for benchmark comparison in claim {claim.claim_id}",
            )

    # Request geography for location-specific claims
    if any(word in claim_lower for word in ["facility", "site", "plant", "reforestation"]):
        return (
            "geography",
            f"Verify geographic claims related to {claim.claim_id}",
        )

    return None


def _process_info_responses(state: SibylState, claim: Claim) -> list[dict]:
    """Find and process InfoResponses relevant to this claim."""
    responses = []
    info_responses = state.get("info_responses", [])
    info_requests = state.get("info_requests", [])

    our_requests = [
        req for req in info_requests
        if req.requesting_agent == "academic"
        and req.context.get("claim_id") == claim.claim_id
    ]

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
    """Get re-investigation request targeting academic agent for a claim."""
    reinvestigation_requests = state.get("reinvestigation_requests", [])

    for req in reinvestigation_requests:
        if req.claim_id == claim_id and "academic" in req.target_agents:
            return req

    return None


async def _process_reinvestigation(
    claim: Claim,
    reinvest_request: ReinvestigationRequest,
) -> list[dict]:
    """Execute re-investigation using Judge's refined queries."""
    all_results = []
    seen_urls: set[str] = set()

    for query in reinvest_request.refined_queries:
        try:
            response = await search_web_async(
                query=query,
                max_results=10,
                search_depth="advanced",
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
    """Extract company name from state/report metadata."""
    return "the company"


# ============================================================================
# Main Node Function
# ============================================================================


async def investigate_academic(state: SibylState) -> dict:
    """Academic/Research Agent: Validate technical claims against academic literature and benchmarks.

    Reads: state.routing_plan, state.claims, state.info_requests,
           state.reinvestigation_requests, state.iteration_count
    Writes: state.findings, state.agent_status, state.info_requests,
            state.info_responses, state.events

    Responsibilities:
    1. Receive routed technical claims from the Orchestrator.
    2. Classify investigation type for each claim.
    3. Construct academic search queries targeting peer-reviewed papers, benchmarks, standards.
    4. Execute web searches using the search_web tool from FRD 8.
    5. Analyze search results to validate methodologies, certifications, targets, benchmarks.
    6. Produce structured findings with academic references and assessments.
    7. Participate in inter-agent communication (InfoRequest/InfoResponse).
    8. Handle re-investigation requests with refined queries.

    Returns:
        Partial state update with findings, agent status, and events.
    """
    agent_name = "academic"
    events: list[StreamEvent] = []
    findings: list[AgentFinding] = []
    info_requests: list[InfoRequest] = []

    # 1. Emit start event
    events.append(
        StreamEvent(
            event_type="agent_started",
            agent_name=agent_name,
            data={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )

    # 2. Find claims assigned to this agent
    routing_plan = state.get("routing_plan", [])
    claims = list(state.get("claims", []))
    iteration_count = state.get("iteration_count", 0)

    assigned_assignments = [
        a for a in routing_plan
        if agent_name in a.assigned_agents
    ]

    assigned_claim_ids = {a.claim_id for a in assigned_assignments}
    assigned_claims = [c for c in claims if c.claim_id in assigned_claim_ids]

    logger.info(
        "Academic Agent processing %d claims (iteration %d)",
        len(assigned_claims),
        iteration_count,
    )

    if not assigned_claims:
        events.append(
            StreamEvent(
                event_type="agent_completed",
                agent_name=agent_name,
                data={
                    "claims_processed": 0,
                    "findings_count": 0,
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )
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
            "events": events,
        }

    # 3. Emit thinking event
    events.append(
        StreamEvent(
            event_type="agent_thinking",
            agent_name=agent_name,
            data={
                "message": f"Investigating {len(assigned_claims)} claims against academic literature and benchmarks..."
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )

    # 4. Process each assigned claim
    for claim in assigned_claims:
        try:
            # Classify investigation type
            investigation_type = _classify_investigation_type(claim)

            events.append(
                StreamEvent(
                    event_type="agent_thinking",
                    agent_name=agent_name,
                    data={
                        "message": f"Investigating claim {claim.claim_id} as {investigation_type}..."
                    },
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

            # Check for re-investigation context
            reinvest_request = _get_reinvestigation_context(state, claim.claim_id)

            if reinvest_request:
                events.append(
                    StreamEvent(
                        event_type="agent_thinking",
                        agent_name=agent_name,
                        data={
                            "message": f"Re-investigating claim {claim.claim_id}: {reinvest_request.evidence_gap}"
                        },
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                )
                search_results = await _process_reinvestigation(
                    claim, reinvest_request
                )
            else:
                # Construct search queries
                events.append(
                    StreamEvent(
                        event_type="agent_thinking",
                        agent_name=agent_name,
                        data={
                            "message": f"Constructing academic search queries ({investigation_type})..."
                        },
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                )

                queries = await _construct_academic_queries(
                    claim, investigation_type
                )

                # Execute searches
                search_results = await _execute_academic_searches(queries)

                events.append(
                    StreamEvent(
                        event_type="search_executed",
                        agent_name=agent_name,
                        data={
                            "claim_id": claim.claim_id,
                            "investigation_type": investigation_type,
                            "queries": queries.queries,
                            "results_count": len(search_results),
                        },
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                )

            # Analyze results with LLM
            analysis = await _analyze_search_results(
                claim, search_results, investigation_type
            )

            # Create finding
            finding = _create_academic_finding(
                claim=claim,
                analysis=analysis,
                search_results=search_results,
                iteration=iteration_count + 1,
            )
            findings.append(finding)

            # Emit evidence found event
            events.append(
                StreamEvent(
                    event_type="evidence_found",
                    agent_name=agent_name,
                    data={
                        "claim_id": claim.claim_id,
                        "evidence_type": analysis.investigation_type,
                        "supports_claim": analysis.supports_claim,
                        "confidence": analysis.confidence,
                        "summary": analysis.summary[:200],
                    },
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

            # Check if cross-domain verification is needed
            if not reinvest_request:
                cross_domain = _should_request_cross_domain(
                    claim, investigation_type, search_results
                )
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
                    info_requests.append(info_req)

                    events.append(
                        StreamEvent(
                            event_type="info_request_posted",
                            agent_name=agent_name,
                            data={
                                "request_id": info_req.request_id,
                                "target_agent": target_agent,
                                "description": description,
                            },
                            timestamp=datetime.now(timezone.utc).isoformat(),
                        )
                    )

            # Check for InfoResponses from other agents
            info_resp_data = _process_info_responses(state, claim)
            if info_resp_data:
                finding.details["cross_domain_evidence"] = info_resp_data

        except Exception as e:
            logger.error("Error processing claim %s: %s", claim.claim_id, e)
            error_finding = AgentFinding(
                finding_id=str(generate_uuid7()),
                agent_name=agent_name,
                claim_id=claim.claim_id,
                evidence_type="error",
                summary=f"Error during academic investigation: {str(e)}",
                details={"error": str(e)},
                supports_claim=None,
                confidence="low",
                iteration=iteration_count + 1,
            )
            findings.append(error_finding)

            events.append(
                StreamEvent(
                    event_type="error",
                    agent_name=agent_name,
                    data={
                        "claim_id": claim.claim_id,
                        "message": str(e),
                    },
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

    # 9. Process pending InfoRequests addressed to academic agent
    pending_info_requests = state.get("info_requests", [])
    info_responses: list[InfoResponse] = []

    for req in pending_info_requests:
        if (
            req.status in ("pending", "routed")
            and req.context.get("target_agent") == "academic"
            and req.requesting_agent != "academic"
        ):
            # Respond with a generic benchmark/research response
            info_resp = InfoResponse(
                request_id=req.request_id,
                responding_agent=agent_name,
                response=f"Academic agent processed request: {req.description}",
                details={"status": "processed"},
            )
            info_responses.append(info_resp)

    # 10. Emit completion event
    events.append(
        StreamEvent(
            event_type="agent_completed",
            agent_name=agent_name,
            data={
                "claims_processed": len(assigned_claims),
                "findings_count": len(findings),
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )

    # 11. Return partial state update
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
        "events": events,
    }

    if info_requests:
        result["info_requests"] = info_requests
    if info_responses:
        result["info_responses"] = info_responses

    return result
