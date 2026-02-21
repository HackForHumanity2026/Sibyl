"""Legal Agent - validates compliance and governance claims against IFRS/SASB.

Implements FRD 6.

Model: Claude Sonnet 4.5 (excellent legal and compliance reasoning)
Knowledge Base: IFRS S1/S2, SASB standards

The Legal Agent performs:
- Paragraph-level IFRS compliance mapping
- Governance structure assessment (S1.26-27, S2.5-7)
- Risk management disclosure validation (S1.38-42, S2.24-26)
- Strategic claims assessment (S2.14)
- Metrics claims assessment (S2.27-37)
- Disclosure gap detection (omission analysis)
- Inter-agent communication for cross-domain verification
- Re-investigation handling for Judge-requested deeper analysis
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

# Maximum concurrent claim processing (rate limiting)
MAX_CONCURRENT_CLAIMS = 5

from pydantic import BaseModel, Field, field_validator

from app.agents.state import (
    AgentFinding,
    AgentStatus,
    Claim,
    InfoRequest,
    ReinvestigationRequest,
    SibylState,
    StreamEvent,
)
from app.core.database import generate_uuid7
from app.services.openrouter_client import Models, openrouter_client

logger = logging.getLogger(__name__)


# ============================================================================
# Response Schemas
# ============================================================================


class SubRequirementAssessment(BaseModel):
    """Assessment of a single sub-requirement within an IFRS paragraph."""

    requirement: str = Field(description="The sub-requirement identifier")
    addressed: bool = Field(description="Whether the requirement is addressed")
    evidence: str | None = Field(default=None, description="Evidence text if addressed")
    gap_reason: str | None = Field(default=None, description="Reason for gap if not addressed")


class IFRSMapping(BaseModel):
    """Mapping of a claim to a specific IFRS paragraph with compliance assessment."""

    paragraph_id: str = Field(description="IFRS paragraph identifier (e.g., S2.14(a)(iv))")
    pillar: str = Field(description="IFRS pillar (governance, strategy, risk_management, metrics_targets)")
    section: str = Field(description="Section name within the pillar")
    requirement_text: str = Field(description="Brief description of the requirement")
    sub_requirements: list[SubRequirementAssessment] = Field(default_factory=list)
    compliance_status: Literal["fully_addressed", "partially_addressed", "not_addressed", "unclear"] = Field(
        description="Overall compliance status for this paragraph"
    )
    s1_counterpart: str | None = Field(default=None, description="Corresponding S1 paragraph if applicable")


class LegalAssessmentResult(BaseModel):
    """Complete compliance assessment result from LLM."""

    ifrs_mappings: list[IFRSMapping] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list, description="Evidence text extracted from claim/report")
    gaps: list[str] = Field(default_factory=list, description="Identified compliance gaps")
    confidence: Literal["high", "medium", "low"] = Field(description="Assessment confidence level")

    @field_validator('evidence', 'gaps', mode='before')
    @classmethod
    def flatten_string_lists(cls, v):
        """Flatten nested lists and convert non-strings to strings."""
        if not isinstance(v, list):
            return [str(v)] if v else []
        result = []
        for item in v:
            if isinstance(item, list):
                result.extend(str(x) for x in item)
            else:
                result.append(str(item))
        return result


class GapCoverageResult(BaseModel):
    """Result of assessing whether report chunks cover an IFRS paragraph."""

    paragraph_id: str
    coverage_status: Literal["fully_addressed", "partially_addressed", "fully_unaddressed"]
    missing_sub_requirements: list[str] = Field(default_factory=list)
    evidence_found: str | None = None

    @field_validator('missing_sub_requirements', mode='before')
    @classmethod
    def flatten_sub_requirements(cls, v):
        """Flatten nested lists and convert non-strings to strings."""
        if not isinstance(v, list):
            return [str(v)] if v else []
        result = []
        for item in v:
            if isinstance(item, list):
                result.extend(str(x) for x in item)
            else:
                result.append(str(item))
        return result

    @field_validator('evidence_found', mode='before')
    @classmethod
    def stringify_evidence(cls, v):
        """Convert dict/list evidence to string."""
        if v is None:
            return None
        if isinstance(v, dict):
            return json.dumps(v)
        if isinstance(v, list):
            return "; ".join(str(x) for x in v)
        return str(v)


# ============================================================================
# LLM Response Normalization
# ============================================================================


def _normalize_sub_requirement(item: str | dict) -> dict:
    """Normalize a sub-requirement to match SubRequirementAssessment schema."""
    if isinstance(item, str):
        return {
            "requirement": item,
            "addressed": True,
            "evidence": None,
            "gap_reason": None,
        }
    if isinstance(item, dict):
        # Map common LLM field variations
        return {
            "requirement": item.get("requirement") or item.get("id") or item.get("text") or str(item),
            "addressed": item.get("addressed", item.get("met", True)),
            "evidence": item.get("evidence"),
            "gap_reason": item.get("gap_reason") or item.get("gap"),
        }
    return {"requirement": str(item), "addressed": False, "evidence": None, "gap_reason": None}


def _normalize_ifrs_mapping(mapping: dict) -> dict:
    """Normalize an IFRS mapping to match IFRSMapping schema."""
    # Normalize sub_requirements if present
    sub_reqs = mapping.get("sub_requirements", [])
    if isinstance(sub_reqs, list):
        mapping["sub_requirements"] = [_normalize_sub_requirement(sr) for sr in sub_reqs]
    
    # Normalize compliance_status variations
    status = mapping.get("compliance_status", "unclear")
    status_map = {
        "addressed": "fully_addressed",
        "full": "fully_addressed",
        "partial": "partially_addressed",
        "not": "not_addressed",
        "none": "not_addressed",
        "missing": "not_addressed",
    }
    for key, value in status_map.items():
        if key in str(status).lower():
            mapping["compliance_status"] = value
            break
    
    return mapping


def _normalize_evidence_item(item: str | dict) -> str:
    """Normalize an evidence item to a string."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        # Extract meaningful text from common LLM response structures
        return item.get("text") or item.get("evidence") or item.get("content") or json.dumps(item)
    return str(item)


def _normalize_gap_item(item: str | dict) -> str:
    """Normalize a gap item to a string."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        # Extract meaningful text from common LLM response structures
        return item.get("gap") or item.get("description") or item.get("missing") or json.dumps(item)
    return str(item)


def _normalize_legal_assessment_response(data: dict) -> dict:
    """Normalize LLM response to match LegalAssessmentResult schema."""
    # Normalize ifrs_mappings
    if "ifrs_mappings" in data and isinstance(data["ifrs_mappings"], list):
        data["ifrs_mappings"] = [_normalize_ifrs_mapping(m) for m in data["ifrs_mappings"]]
    
    # Normalize evidence list
    if "evidence" in data and isinstance(data["evidence"], list):
        data["evidence"] = [_normalize_evidence_item(e) for e in data["evidence"]]
    
    # Normalize gaps list
    if "gaps" in data and isinstance(data["gaps"], list):
        data["gaps"] = [_normalize_gap_item(g) for g in data["gaps"]]
    
    # Ensure confidence has a valid value
    if "confidence" not in data:
        data["confidence"] = "medium"
    
    return data


# ============================================================================
# Constants and Prompts
# ============================================================================

# Path to IFRS paragraph registry
REGISTRY_PATH = Path(__file__).parent.parent.parent / "data" / "ifrs" / "paragraph_registry.json"

# IFRS paragraph ID pattern for validation
IFRS_PARAGRAPH_PATTERN = re.compile(
    r'^S[12]\.\d+(\([a-z]\))?(\([ivx]+\))?(\([0-9]+\))?$'
)

# Claim type to IFRS paragraph focus mapping
CLAIM_TYPE_IFRS_FOCUS = {
    "legal_governance": {
        "paragraphs": ["S1.26", "S1.27", "S2.5", "S2.6", "S2.7"],
        "query_suffix": "governance claim IFRS S1.26-27 S2.5-7 board oversight competencies",
        "source_types": ["ifrs_s1", "ifrs_s2"],
    },
    "strategic": {
        "paragraphs": ["S2.14", "S2.14(a)(iv)", "S1.33"],
        "query_suffix": "strategy claim transition plan IFRS S2.14 decision-making resource allocation",
        "source_types": ["ifrs_s2"],
    },
    "quantitative": {
        "paragraphs": ["S2.29", "S2.29(a)(iii)", "S2.30", "S2.31", "S2.33", "S2.34", "S2.35", "S2.36"],
        "query_suffix": "metrics claim GHG emissions Scope IFRS S2.27-37 S2.29",
        "source_types": ["ifrs_s2"],
    },
    "environmental": {
        "paragraphs": ["S2.24", "S2.25", "S2.26", "S1.38", "S1.41", "S1.42"],
        "query_suffix": "risk management claim IFRS S1.38-42 S2.24-26 risk identification assessment",
        "source_types": ["ifrs_s1", "ifrs_s2"],
    },
}

# System prompt for compliance assessment
LEGAL_AGENT_SYSTEM_PROMPT = """You are the Legal Agent in Sibyl, an AI system that verifies sustainability reports against IFRS S1/S2 disclosure standards. Your task is to investigate legal, regulatory, and governance-related claims and assess their compliance with IFRS S1/S2 requirements at the paragraph level.

## Your Responsibilities

1. **Paragraph-level IFRS mapping:** Map each claim to specific IFRS paragraph identifiers (e.g., S2.14(a)(iv)), not just pillar-level categories.

2. **Compliance assessment:** For each mapped paragraph, assess whether the claim meets the paragraph's specific sub-requirements. Check for:
   - Presence: Is the required topic/content present?
   - Completeness: Are all sub-requirements addressed?
   - Specificity: Is the disclosure specific enough?
   - Methodology alignment: For metrics, does methodology align with IFRS?
   - Granularity: Does disclosure meet required level of detail?

3. **Sub-requirement extraction:** For each IFRS paragraph, identify its sub-requirements from the paragraph text. For example, S2.14(a)(iv) requires: key assumptions, dependencies, timeline.

4. **Evidence extraction:** Extract specific evidence from the claim text (or surrounding report content) that addresses each sub-requirement.

5. **Gap identification:** If a sub-requirement is not addressed, describe what is missing.

## IFRS Structure

### S1 Pillars:
- Governance (S1.26-27): Board oversight, competencies, reporting frequency, remuneration
- Strategy (S1.28-35): Risks/opportunities, business model effects, strategy response, financial effects
- Risk Management (S1.38-42): Risk identification, assessment, prioritization, monitoring, integration
- Metrics & Targets (S1.43-53): Performance metrics, targets, baseline, progress

### S2 Climate Paragraphs:
- Governance: S2.5-7 (climate-specific governance)
- Strategy: S2.8-12 (climate risks/opportunities), S2.13 (business model), S2.14 (decision-making/transition plan), S2.15-21 (financial effects), S2.22 (climate resilience)
- Risk Management: S2.24-26 (climate risk management)
- Metrics: S2.27-31 (GHG emissions), S2.33-36 (climate targets)

## Output Format

Return a JSON object with:
- `ifrs_mappings`: Array of paragraph mappings, each with paragraph_id, pillar, section, requirement_text, sub_requirements assessment, compliance_status
- `evidence`: Array of extracted evidence text for each sub-requirement
- `gaps`: Array of missing sub-requirements if compliance_status is "partially_addressed" or "not_addressed"
- `confidence`: "high" | "medium" | "low"

Always output valid JSON. No markdown, no code blocks, just the raw JSON object."""


LEGAL_AGENT_USER_PROMPT_TEMPLATE = """Investigate the following claim against IFRS S1/S2 requirements:

**Claim:** {claim_text}

**Claim Type:** {claim_type}

**Preliminary IFRS Mapping:** {preliminary_ifrs}

**Retrieved IFRS Paragraphs:**
{rag_results}

Assess:
1. Which specific IFRS paragraphs does this claim map to? (paragraph-level precision)
2. For each mapped paragraph, does the claim meet all sub-requirements?
3. Extract evidence for each addressed sub-requirement.
4. Identify any missing sub-requirements.

Return your assessment as a JSON object matching the specified schema."""


GAP_COVERAGE_PROMPT = """Assess whether the following report content addresses the requirements of IFRS paragraph {paragraph_id}.

**Paragraph Requirement:** {requirement_text}

**Sub-requirements to check:**
{sub_requirements}

**Report content chunks:**
{chunk_texts}

Assess:
1. Which sub-requirements are addressed by the report content?
2. Which sub-requirements are missing?
3. What is the overall coverage status: "fully_addressed", "partially_addressed", or "fully_unaddressed"?

Return a JSON object with:
- `paragraph_id`: "{paragraph_id}"
- `coverage_status`: "fully_addressed" | "partially_addressed" | "fully_unaddressed"
- `missing_sub_requirements`: array of missing requirement names
- `evidence_found`: brief summary of evidence found (or null if none)"""


# ============================================================================
# Helper Functions - RAG Retrieval
# ============================================================================


def _build_rag_query(claim: Claim) -> tuple[str, list[str]]:
    """Build a RAG query optimized for the claim type.
    
    Args:
        claim: The claim to build a query for
        
    Returns:
        Tuple of (query_string, source_types)
    """
    claim_type = claim.claim_type
    focus = CLAIM_TYPE_IFRS_FOCUS.get(claim_type, CLAIM_TYPE_IFRS_FOCUS["legal_governance"])
    
    # Build query with claim text and type-specific suffix
    preliminary_ids = " ".join(claim.ifrs_paragraphs) if claim.ifrs_paragraphs else ""
    query = f"{claim.text[:500]} {focus['query_suffix']} {preliminary_ids}".strip()
    
    return query, focus["source_types"]


async def _retrieve_ifrs_paragraphs(
    claim: Claim,
    report_id: str,
) -> str:
    """Retrieve relevant IFRS paragraphs for a claim using RAG.
    
    Args:
        claim: The claim to retrieve paragraphs for
        report_id: The report ID for context
        
    Returns:
        Formatted RAG results as a string
    """
    from app.agents.tools.rag_lookup import rag_lookup
    
    query, source_types = _build_rag_query(claim)
    
    try:
        results = await rag_lookup.ainvoke({
            "query": query,
            "source_types": source_types,
            "top_k": 5,
        })
        return results
    except Exception as e:
        logger.warning("RAG retrieval failed for claim %s: %s", claim.claim_id, e)
        # Return placeholder indicating retrieval failed
        return f"--- RAG retrieval failed: {e} ---"


async def _retrieve_report_content(
    query: str,
    report_id: str,
) -> str:
    """Retrieve report content chunks for gap detection.
    
    Args:
        query: The search query
        report_id: The report ID to search within
        
    Returns:
        Formatted RAG results from report content
    """
    from app.agents.tools.rag_lookup import rag_lookup_report
    
    try:
        results = await rag_lookup_report.ainvoke({
            "query": query,
            "report_id": report_id,
            "top_k": 3,
        })
        return results
    except Exception as e:
        logger.warning("Report content retrieval failed: %s", e)
        return "--- No report content found ---"


# ============================================================================
# Helper Functions - Compliance Assessment
# ============================================================================


async def _assess_compliance(
    claim: Claim,
    rag_results: str,
) -> LegalAssessmentResult:
    """Use Claude Sonnet to assess claim compliance against IFRS paragraphs.
    
    Args:
        claim: The claim to assess
        rag_results: Retrieved IFRS paragraphs as formatted text
        
    Returns:
        LegalAssessmentResult with compliance assessment
    """
    # Build user prompt
    preliminary_ifrs = ", ".join(claim.ifrs_paragraphs) if claim.ifrs_paragraphs else "None"
    user_prompt = LEGAL_AGENT_USER_PROMPT_TEMPLATE.format(
        claim_text=claim.text,
        claim_type=claim.claim_type,
        preliminary_ifrs=preliminary_ifrs,
        rag_results=rag_results,
    )
    
    try:
        response = await openrouter_client.chat_completion(
            model=Models.GPT4O_MINI,
            messages=[
                {"role": "system", "content": LEGAL_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=8192,
        )
        
        # Parse JSON response
        try:
            # Clean the response in case it has markdown formatting
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            cleaned = cleaned.strip()
            
            result_data = json.loads(cleaned)
            result_data = _normalize_legal_assessment_response(result_data)
            return LegalAssessmentResult(**result_data)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Failed to parse LLM response as JSON: %s", e)
            logger.debug("Response was: %s", response[:500])
            # Return low-confidence result
            return LegalAssessmentResult(
                ifrs_mappings=[],
                evidence=[],
                gaps=["Failed to parse LLM assessment response"],
                confidence="low",
            )
            
    except Exception as e:
        logger.error("LLM compliance assessment failed: %s", e)
        return LegalAssessmentResult(
            ifrs_mappings=[],
            evidence=[],
            gaps=[f"LLM assessment error: {str(e)}"],
            confidence="low",
        )


# ============================================================================
# Helper Functions - Gap Detection
# ============================================================================


def _load_paragraph_registry() -> dict | None:
    """Load the IFRS paragraph registry from JSON file.
    
    Returns:
        Registry dict or None if loading fails
    """
    try:
        if not REGISTRY_PATH.exists():
            logger.warning("Paragraph registry not found at %s", REGISTRY_PATH)
            return None
            
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.error("Failed to load paragraph registry: %s", e)
        return None


def _get_claims_by_paragraph(
    claims: list[Claim],
    findings: list[AgentFinding],
) -> dict[str, list[str]]:
    """Build a mapping of paragraph IDs to claim IDs that address them.
    
    Args:
        claims: List of claims
        findings: List of findings with IFRS mappings
        
    Returns:
        Dict mapping paragraph_id to list of claim_ids
    """
    mapping: dict[str, list[str]] = {}
    
    # From claim preliminary mappings
    for claim in claims:
        for para_id in claim.ifrs_paragraphs:
            if para_id not in mapping:
                mapping[para_id] = []
            if claim.claim_id not in mapping[para_id]:
                mapping[para_id].append(claim.claim_id)
    
    # From findings with IFRS mappings
    for finding in findings:
        if finding.details and "ifrs_mappings" in finding.details:
            for ifrs_mapping in finding.details["ifrs_mappings"]:
                para_id = ifrs_mapping.get("paragraph_id")
                claim_id = finding.claim_id
                if para_id and claim_id:
                    if para_id not in mapping:
                        mapping[para_id] = []
                    if claim_id not in mapping[para_id]:
                        mapping[para_id].append(claim_id)
    
    return mapping


async def _assess_paragraph_coverage(
    paragraph: dict,
    report_id: str,
) -> GapCoverageResult:
    """Assess whether a specific IFRS paragraph is covered in the report.
    
    Args:
        paragraph: Paragraph dict from registry
        report_id: Report ID to search
        
    Returns:
        GapCoverageResult with coverage status
    """
    paragraph_id = paragraph["paragraph_id"]
    
    # Build search query from paragraph requirement
    query = f"{paragraph.get('requirement_text', '')} {paragraph_id}"
    
    # Search report content
    report_content = await _retrieve_report_content(query, report_id)
    
    if "No results found" in report_content or "No report content" in report_content:
        return GapCoverageResult(
            paragraph_id=paragraph_id,
            coverage_status="fully_unaddressed",
            missing_sub_requirements=[
                sr["requirement"] for sr in paragraph.get("sub_requirements", [])
            ],
            evidence_found=None,
        )
    
    # Use LLM to assess coverage
    sub_reqs_text = "\n".join([
        f"- {sr['requirement']}: {sr.get('description', '')}"
        for sr in paragraph.get("sub_requirements", [])
    ])
    
    prompt = GAP_COVERAGE_PROMPT.format(
        paragraph_id=paragraph_id,
        requirement_text=paragraph.get("requirement_text", ""),
        sub_requirements=sub_reqs_text if sub_reqs_text else "No specific sub-requirements",
        chunk_texts=report_content,
    )
    
    try:
        response = await openrouter_client.chat_completion(
            model=Models.CLAUDE_HAIKU,  # Fast, cheap for coverage assessment
            messages=[
                {"role": "system", "content": "You assess IFRS compliance coverage. Output only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=2048,
        )
        
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()
        
        result = json.loads(cleaned)
        return GapCoverageResult(**result)
        
    except Exception as e:
        logger.warning("Coverage assessment failed for %s: %s", paragraph_id, e)
        return GapCoverageResult(
            paragraph_id=paragraph_id,
            coverage_status="fully_unaddressed",
            missing_sub_requirements=[],
            evidence_found=None,
        )


async def _detect_disclosure_gaps(
    state: SibylState,
    compliance_findings: list[AgentFinding],
) -> list[AgentFinding]:
    """Perform systematic gap detection against IFRS paragraph registry.
    
    Args:
        state: Current pipeline state
        compliance_findings: Findings from compliance assessment
        
    Returns:
        List of gap findings for unaddressed/partially addressed paragraphs
    """
    registry = _load_paragraph_registry()
    if not registry:
        logger.warning("Skipping gap detection - registry not available")
        return []
    
    gap_findings: list[AgentFinding] = []
    claims = list(state.get("claims", []))
    report_id = state.get("report_id", "")
    iteration_count = state.get("iteration_count", 0)
    
    # Build mapping of paragraphs to claims that address them
    paragraph_coverage = _get_claims_by_paragraph(claims, compliance_findings)
    
    # Check each paragraph in registry
    for paragraph in registry.get("paragraphs", []):
        paragraph_id = paragraph["paragraph_id"]
        
        # Skip if claims already map to this paragraph
        if paragraph_id in paragraph_coverage:
            continue
        
        # Check report content coverage
        coverage_result = await _assess_paragraph_coverage(paragraph, report_id)
        
        if coverage_result.coverage_status in ("fully_unaddressed", "partially_addressed"):
            # Create gap finding
            gap_finding = AgentFinding(
                finding_id=str(generate_uuid7()),
                agent_name="legal",
                claim_id="",  # Gap findings not tied to specific claim
                evidence_type="disclosure_gap",
                summary=f"IFRS {paragraph_id} requirement is {coverage_result.coverage_status}. {paragraph.get('materiality_note', '')}",
                details={
                    "paragraph_id": paragraph_id,
                    "pillar": paragraph.get("pillar"),
                    "section": paragraph.get("section"),
                    "requirement_text": paragraph.get("requirement_text"),
                    "gap_status": coverage_result.coverage_status,
                    "missing_sub_requirements": coverage_result.missing_sub_requirements,
                    "materiality_context": paragraph.get("materiality_note"),
                    "s1_counterpart": paragraph.get("s1_counterpart"),
                },
                supports_claim=False,
                confidence="high",
                iteration=iteration_count + 1,
            )
            gap_findings.append(gap_finding)
    
    return gap_findings


# ============================================================================
# Helper Functions - Inter-Agent Communication
# ============================================================================


def _should_request_cross_domain_verification(
    claim: Claim,
    assessment: LegalAssessmentResult,
) -> tuple[str, str] | None:
    """Determine if cross-domain verification is needed.
    
    Args:
        claim: The claim being assessed
        assessment: The compliance assessment result
        
    Returns:
        Tuple of (agent_type, description) if verification needed, None otherwise
    """
    claim_text_lower = claim.text.lower()
    
    # Geographic verification for facility/location claims
    if any(word in claim_text_lower for word in ["facility", "location", "site", "plant", "headquarters"]):
        if any(loc in claim_text_lower for loc in ["singapore", "china", "india", "europe", "usa", "uk"]):
            return ("geography", f"Verify facility location mentioned in claim {claim.claim_id}")
    
    # Quantitative validation for metrics claims
    if claim.claim_type == "quantitative":
        if assessment.confidence == "low":
            return ("data_metrics", f"Validate numerical consistency for claim {claim.claim_id}")
    
    # News verification for certification/award claims
    if any(word in claim_text_lower for word in ["certified", "certification", "iso", "award", "recognition"]):
        return ("news_media", f"Verify certification/award mentioned in claim {claim.claim_id}")
    
    return None


def _create_info_request(
    claim: Claim,
    target_agent: str,
    description: str,
) -> InfoRequest:
    """Create an InfoRequest for cross-domain verification.
    
    Args:
        claim: The claim needing verification
        target_agent: Target agent type
        description: Description of what to verify
        
    Returns:
        InfoRequest object
    """
    return InfoRequest(
        request_id=str(generate_uuid7()),
        requesting_agent="legal",
        description=description,
        context={
            "claim_id": claim.claim_id,
            "claim_text": claim.text[:200],
            "claim_type": claim.claim_type,
            "target_agent": target_agent,
        },
        status="pending",
    )


def _process_info_responses(
    state: SibylState,
    claim: Claim,
) -> list[dict]:
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
    
    # Find requests from legal agent for this claim
    our_requests = [
        req for req in info_requests
        if req.requesting_agent == "legal" 
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
    """Get re-investigation request targeting legal agent for a claim.
    
    Args:
        state: Current pipeline state
        claim_id: The claim ID to check
        
    Returns:
        ReinvestigationRequest if found, None otherwise
    """
    reinvestigation_requests = state.get("reinvestigation_requests", [])
    
    for req in reinvestigation_requests:
        if req.claim_id == claim_id and "legal" in req.target_agents:
            return req
    
    return None


async def _perform_reinvestigation(
    claim: Claim,
    reinvest_request: ReinvestigationRequest,
    report_id: str,
) -> LegalAssessmentResult:
    """Perform targeted re-investigation based on Judge guidance.
    
    Args:
        claim: The claim to re-investigate
        reinvest_request: The re-investigation request with guidance
        report_id: Report ID for RAG queries
        
    Returns:
        Updated compliance assessment
    """
    # Use refined queries from Judge
    all_results = []
    for query in reinvest_request.refined_queries:
        # Search report content directly
        report_results = await _retrieve_report_content(query, report_id)
        if "No results found" not in report_results:
            all_results.append(report_results)
    
    # Also do standard IFRS retrieval
    ifrs_results = await _retrieve_ifrs_paragraphs(claim, report_id)
    
    # Combine all results
    combined_results = f"""**Re-investigation focus:** {reinvest_request.evidence_gap}

**Required evidence:** {reinvest_request.required_evidence or 'Not specified'}

**Report content search results:**
{chr(10).join(all_results) if all_results else 'No additional report content found'}

**IFRS paragraph reference:**
{ifrs_results}"""
    
    # Perform assessment with combined context
    return await _assess_compliance(claim, combined_results)


# ============================================================================
# Helper Functions - Finding Generation
# ============================================================================


def _create_compliance_finding(
    claim: Claim,
    assessment: LegalAssessmentResult,
    iteration: int,
    info_responses: list[dict] | None = None,
) -> AgentFinding:
    """Create an AgentFinding for claim compliance assessment.
    
    Args:
        claim: The assessed claim
        assessment: The compliance assessment result
        iteration: Current iteration count
        info_responses: Any cross-domain responses incorporated
        
    Returns:
        AgentFinding object
    """
    # Determine supports_claim based on compliance status
    if not assessment.ifrs_mappings:
        supports_claim = None
        confidence = "low"
    else:
        statuses = [m.compliance_status for m in assessment.ifrs_mappings]
        if all(s == "fully_addressed" for s in statuses):
            supports_claim = True
            confidence = assessment.confidence
        elif all(s == "not_addressed" for s in statuses):
            supports_claim = False
            confidence = assessment.confidence
        else:
            supports_claim = None  # Mixed or partial
            confidence = "medium" if assessment.confidence == "high" else "low"
    
    # Build summary
    if assessment.ifrs_mappings:
        para_ids = ", ".join([m.paragraph_id for m in assessment.ifrs_mappings])
        main_status = assessment.ifrs_mappings[0].compliance_status
        summary = f"Claim maps to {para_ids}. Compliance: {main_status}."
        if assessment.gaps:
            summary += f" Gaps: {', '.join(assessment.gaps[:2])}."
    else:
        summary = "Unable to map claim to specific IFRS paragraphs."
    
    # Build details
    details = {
        "ifrs_mappings": [m.model_dump() for m in assessment.ifrs_mappings],
        "evidence": assessment.evidence,
        "gaps": assessment.gaps,
        "compliance_status": assessment.ifrs_mappings[0].compliance_status if assessment.ifrs_mappings else "unclear",
    }
    
    if info_responses:
        details["cross_domain_evidence"] = info_responses
    
    return AgentFinding(
        finding_id=str(generate_uuid7()),
        agent_name="legal",
        claim_id=claim.claim_id,
        evidence_type="ifrs_compliance",
        summary=summary,
        details=details,
        supports_claim=supports_claim,
        confidence=confidence,
        iteration=iteration + 1,
    )


# ============================================================================
# Main Node Function
# ============================================================================


async def investigate_legal(state: SibylState) -> dict:
    """Legal Agent: Investigate legal/governance claims against IFRS S1/S2.

    Reads: state.routing_plan, state.claims, state.report_id,
           state.info_responses, state.reinvestigation_requests
    Writes: state.findings, state.events, state.info_requests, state.disclosure_gaps

    Responsibilities:
    1. Identify claims assigned to the Legal Agent from routing_plan
    2. For each claim, perform RAG retrieval against IFRS/SASB corpus
    3. Map claims to specific IFRS paragraphs (paragraph-level precision)
    4. Assess compliance: does the claim meet the paragraph's requirements?
    5. Perform disclosure gap detection: compare full IFRS set against report content
    6. Generate findings with compliance verdicts and evidence
    7. Participate in inter-agent communication when cross-domain context is needed

    Returns:
        Partial state update with findings, events, and info_requests.
    """
    agent_name = "legal"
    events: list[StreamEvent] = []
    findings: list[AgentFinding] = []
    info_requests: list[InfoRequest] = []
    disclosure_gaps: list[dict] = []

    # Emit start event
    events.append(
        StreamEvent(
            event_type="agent_started",
            agent_name=agent_name,
            data={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )

    # Find claims assigned to this agent
    routing_plan = state.get("routing_plan", [])
    claims = list(state.get("claims", []))
    report_id = state.get("report_id", "")
    iteration_count = state.get("iteration_count", 0)

    assigned_assignments = [
        a for a in routing_plan
        if agent_name in a.assigned_agents
    ]
    
    # Get claim objects for assigned claim IDs
    assigned_claim_ids = {a.claim_id for a in assigned_assignments}
    assigned_claims = [c for c in claims if c.claim_id in assigned_claim_ids]

    logger.info(
        "Legal Agent processing %d claims (iteration %d)",
        len(assigned_claims),
        iteration_count,
    )

    if not assigned_claims:
        # No claims assigned to us
        events.append(
            StreamEvent(
                event_type="agent_completed",
                agent_name=agent_name,
                data={
                    "claims_processed": 0,
                    "findings_count": 0,
                    "gaps_found": 0,
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

    # Emit thinking event
    events.append(
        StreamEvent(
            event_type="agent_thinking",
            agent_name=agent_name,
            data={
                "message": f"Investigating {len(assigned_claims)} claims against IFRS S1/S2 requirements..."
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )

    # Process claims in parallel with rate limiting
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_CLAIMS)
    
    async def process_single_claim(claim: Claim) -> tuple[AgentFinding, list[StreamEvent], list[InfoRequest]]:
        """Process a single claim and return finding, events, and info requests."""
        claim_events: list[StreamEvent] = []
        claim_info_requests: list[InfoRequest] = []
        
        async with semaphore:
            try:
                # Check for re-investigation context
                reinvest_request = _get_reinvestigation_context(state, claim.claim_id)
                
                if reinvest_request:
                    claim_events.append(
                        StreamEvent(
                            event_type="agent_thinking",
                            agent_name=agent_name,
                            data={
                                "message": f"Re-investigating claim {claim.claim_id}: {reinvest_request.evidence_gap}"
                            },
                            timestamp=datetime.now(timezone.utc).isoformat(),
                        )
                    )
                    assessment = await _perform_reinvestigation(claim, reinvest_request, report_id)
                else:
                    # Standard investigation
                    claim_events.append(
                        StreamEvent(
                            event_type="agent_thinking",
                            agent_name=agent_name,
                            data={
                                "message": f"Retrieving IFRS paragraphs for {claim.claim_type} claim..."
                            },
                            timestamp=datetime.now(timezone.utc).isoformat(),
                        )
                    )
                    
                    # RAG retrieval
                    rag_results = await _retrieve_ifrs_paragraphs(claim, report_id)
                    
                    # Compliance assessment
                    assessment = await _assess_compliance(claim, rag_results)
                
                # Check for InfoResponses from other agents
                info_resp_data = _process_info_responses(state, claim)
                
                # Create finding
                finding = _create_compliance_finding(
                    claim,
                    assessment,
                    iteration_count,
                    info_resp_data if info_resp_data else None,
                )
                
                # Emit evidence found event
                claim_events.append(
                    StreamEvent(
                        event_type="evidence_found",
                        agent_name=agent_name,
                        data={
                            "claim_id": claim.claim_id,
                            "paragraph_ids": [m.paragraph_id for m in assessment.ifrs_mappings],
                            "compliance_status": assessment.ifrs_mappings[0].compliance_status if assessment.ifrs_mappings else "unclear",
                            "confidence": assessment.confidence,
                        },
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                )
                
                # Check if cross-domain verification is needed
                if not reinvest_request:  # Don't create new requests during re-investigation
                    verification_needed = _should_request_cross_domain_verification(claim, assessment)
                    if verification_needed:
                        target_agent, description = verification_needed
                        info_req = _create_info_request(claim, target_agent, description)
                        claim_info_requests.append(info_req)
                        
                        claim_events.append(
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
                
                return finding, claim_events, claim_info_requests
                        
            except Exception as e:
                logger.error("Error processing claim %s: %s", claim.claim_id, e)
                # Create error finding
                finding = AgentFinding(
                    finding_id=str(generate_uuid7()),
                    agent_name=agent_name,
                    claim_id=claim.claim_id,
                    evidence_type="ifrs_compliance",
                    summary=f"Error during compliance assessment: {str(e)}",
                    details={"error": str(e)},
                    supports_claim=None,
                    confidence="low",
                    iteration=iteration_count + 1,
                )
                return finding, claim_events, claim_info_requests
    
    # Run all claims in parallel
    results = await asyncio.gather(*[process_single_claim(c) for c in assigned_claims])
    
    # Aggregate results
    for finding, claim_events, claim_info_requests in results:
        findings.append(finding)
        events.extend(claim_events)
        info_requests.extend(claim_info_requests)

    # Perform disclosure gap detection (only on first iteration to avoid duplicate gaps)
    if iteration_count == 0:
        events.append(
            StreamEvent(
                event_type="agent_thinking",
                agent_name=agent_name,
                data={
                    "message": "Performing disclosure gap detection against IFRS paragraph registry..."
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )
        
        try:
            gap_findings = await _detect_disclosure_gaps(state, findings)
            findings.extend(gap_findings)
            
            for gap in gap_findings:
                events.append(
                    StreamEvent(
                        event_type="disclosure_gap_found",
                        agent_name=agent_name,
                        data={
                            "paragraph_id": gap.details.get("paragraph_id"),
                            "gap_status": gap.details.get("gap_status"),
                            "pillar": gap.details.get("pillar"),
                        },
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                )
                disclosure_gaps.append(gap.details)
                
        except Exception as e:
            logger.error("Gap detection failed: %s", e)
            events.append(
                StreamEvent(
                    event_type="error",
                    agent_name=agent_name,
                    data={"message": f"Gap detection error: {str(e)}"},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

    # Emit IFRS coverage progress
    if findings:
        pillar_counts: dict[str, dict[str, int]] = {}
        for f in findings:
            if f.evidence_type == "ifrs_compliance" and f.details.get("ifrs_mappings"):
                for mapping in f.details["ifrs_mappings"]:
                    pillar = mapping.get("pillar", "unknown")
                    if pillar not in pillar_counts:
                        pillar_counts[pillar] = {"covered": 0, "gaps": 0}
                    pillar_counts[pillar]["covered"] += 1
            elif f.evidence_type == "disclosure_gap":
                pillar = f.details.get("pillar", "unknown")
                if pillar not in pillar_counts:
                    pillar_counts[pillar] = {"covered": 0, "gaps": 0}
                pillar_counts[pillar]["gaps"] += 1
        
        for pillar, counts in pillar_counts.items():
            events.append(
                StreamEvent(
                    event_type="ifrs_coverage_update",
                    agent_name=agent_name,
                    data={
                        "pillar": pillar,
                        "paragraphs_covered": counts["covered"],
                        "paragraphs_gaps": counts["gaps"],
                    },
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

    # Emit completion event
    gap_count = len([f for f in findings if f.evidence_type == "disclosure_gap"])
    compliance_count = len([f for f in findings if f.evidence_type == "ifrs_compliance"])
    
    events.append(
        StreamEvent(
            event_type="agent_completed",
            agent_name=agent_name,
            data={
                "claims_processed": len(assigned_claims),
                "findings_count": compliance_count,
                "gaps_found": gap_count,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )

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
        "events": events,
    }
    
    if info_requests:
        result["info_requests"] = info_requests
    
    if disclosure_gaps:
        result["disclosure_gaps"] = disclosure_gaps
    
    return result
