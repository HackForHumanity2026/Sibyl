"""Data/Metrics Agent - validates quantitative claims for consistency.

Implements FRD 7.

Model: Claude Sonnet 4.5 (strong numerical reasoning)

The Data/Metrics Agent performs:
- Internal consistency checks (Scope 1+2+3 totals, year-over-year changes)
- Unit and methodology validation (GHG Protocol alignment)
- Benchmark comparison (industry sector plausibility)
- Target achievability assessment (mathematical validation)
- Historical consistency with prior reports
- IFRS S2.27-37 compliance assessment
- Inter-agent communication for benchmark data
- Re-investigation handling for Judge-requested deeper analysis

Uses a calculator tool for guaranteed arithmetic accuracy via SimpleEval.
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from app.agents.state import (
    AgentFinding,
    AgentStatus,
    Claim,
    InfoRequest,
    ReinvestigationRequest,
    SibylState,
    StreamEvent,
)
from app.agents.tools.calculator import calculator, get_calculator_tool
from app.core.database import generate_uuid7
from app.services.openrouter_client import Models, openrouter_client

logger = logging.getLogger(__name__)


# ============================================================================
# Response Schemas
# ============================================================================


class ConsistencyCheckResult(BaseModel):
    """Result of a single consistency check."""

    check_name: str = Field(
        description="Type of check: scope_addition, yoy_percentage, baseline_consistency, etc."
    )
    claim_id: str = Field(description="ID of the claim being checked")
    result: Literal["pass", "fail", "inconclusive"] = Field(
        description="Check result"
    )
    details: dict = Field(
        default_factory=dict,
        description="Calculation details including values and formulas used",
    )
    severity: Literal["critical", "warning", "info"] = Field(
        description="Severity of failed checks"
    )
    message: str = Field(description="Human-readable explanation of the result")


class UnitValidationResult(BaseModel):
    """Result of unit and methodology validation."""

    units_valid: bool = Field(description="Whether units are correctly used")
    methodology_aligned: bool = Field(
        description="Whether methodology aligns with GHG Protocol/IFRS"
    )
    conversion_factors_appropriate: bool = Field(
        description="Whether conversion factors are appropriate"
    )
    issues: list[str] = Field(
        default_factory=list, description="List of identified issues"
    )


class BenchmarkComparison(BaseModel):
    """Comparison of a metric against industry benchmarks."""

    metric_name: str = Field(description="Name of the metric being compared")
    reported_value: float = Field(description="Value reported in the claim")
    reported_unit: str = Field(description="Unit of the reported value")
    sector_average: float | None = Field(
        default=None, description="Sector average if available"
    )
    sector_unit: str | None = Field(default=None, description="Unit of sector average")
    benchmark_source: str | None = Field(
        default=None, description="Source of benchmark data"
    )
    assessment: Literal["plausible", "outlier_high", "outlier_low", "inconclusive"] = (
        Field(description="Assessment of plausibility")
    )
    reasoning: str = Field(description="Explanation of the assessment")


class TargetAchievabilityResult(BaseModel):
    """Assessment of target achievability."""

    claim_id: str = Field(description="ID of the target claim")
    target_type: Literal["absolute_reduction", "intensity_reduction", "net_zero"] = (
        Field(description="Type of emissions target")
    )
    baseline_year: int | None = Field(default=None, description="Baseline year")
    baseline_value: float | None = Field(
        default=None, description="Baseline emissions value"
    )
    target_year: int | None = Field(default=None, description="Target year")
    target_value: float | None = Field(
        default=None, description="Target emissions value if absolute"
    )
    target_percentage: float | None = Field(
        default=None, description="Target reduction percentage"
    )
    required_annual_reduction_rate: float | None = Field(
        default=None, description="Required CAGR to achieve target"
    )
    achievability_assessment: Literal[
        "achievable", "challenging", "questionable", "inconclusive"
    ] = Field(description="Assessment of target achievability")
    interim_targets_consistent: bool | None = Field(
        default=None, description="Whether interim targets are consistent with final"
    )
    ifrs_s2_33_36_compliant: bool = Field(
        description="Whether target disclosures comply with IFRS S2.33-36"
    )
    missing_ifrs_requirements: list[str] = Field(
        default_factory=list, description="Missing IFRS requirements"
    )
    reasoning: str = Field(description="Explanation of the assessment")


class HistoricalConsistencyResult(BaseModel):
    """Assessment of historical consistency."""

    claim_id: str = Field(description="ID of the claim")
    current_year: int | None = Field(default=None, description="Current reporting year")
    current_value: float | None = Field(default=None, description="Current year value")
    prior_years: list[dict] = Field(
        default_factory=list, description="Prior year values for comparison"
    )
    yoy_change_consistent: bool | None = Field(
        default=None, description="Whether YoY change matches reported percentage"
    )
    trend_consistent: bool | None = Field(
        default=None, description="Whether trend is consistent with prior years"
    )
    methodology_changes: list[str] = Field(
        default_factory=list, description="Identified methodology changes"
    )
    unexplained_deviations: list[str] = Field(
        default_factory=list, description="Unexplained deviations from trend"
    )
    assessment: Literal[
        "consistent", "inconsistent", "partially_consistent", "inconclusive"
    ] = Field(description="Overall consistency assessment")
    reasoning: str = Field(description="Explanation of the assessment")


class IFRSComplianceResult(BaseModel):
    """IFRS S2.27-37 compliance assessment result."""

    claim_id: str = Field(description="ID of the claim")
    ifrs_paragraphs: list[str] = Field(
        default_factory=list, description="Relevant IFRS paragraphs"
    )
    compliance_status: Literal[
        "compliant", "partially_compliant", "non_compliant", "not_applicable"
    ] = Field(description="Compliance status")
    missing_requirements: list[str] = Field(
        default_factory=list, description="Missing IFRS requirements"
    )
    compliance_details: dict = Field(
        default_factory=dict, description="Detailed compliance breakdown"
    )
    reasoning: str = Field(description="Explanation of compliance assessment")


class QuantitativeValidationResult(BaseModel):
    """Complete validation result for a quantitative claim."""

    claim_id: str = Field(description="ID of the claim")
    consistency_checks: list[ConsistencyCheckResult] = Field(
        default_factory=list, description="Results of all consistency checks"
    )
    unit_validation: UnitValidationResult = Field(
        description="Unit and methodology validation"
    )
    benchmark_comparison: BenchmarkComparison | None = Field(
        default=None, description="Benchmark comparison if applicable"
    )
    target_achievability: TargetAchievabilityResult | None = Field(
        default=None, description="Target achievability if this is a target claim"
    )
    historical_consistency: HistoricalConsistencyResult | None = Field(
        default=None, description="Historical consistency assessment"
    )
    ifrs_compliance: IFRSComplianceResult = Field(
        description="IFRS S2.27-37 compliance assessment"
    )
    summary: str = Field(description="Brief summary of validation results")
    supports_claim: bool | None = Field(
        default=None, description="Whether evidence supports the claim"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence in the assessment"
    )
    missing_data: list[str] = Field(
        default_factory=list, description="Data that was missing for full assessment"
    )
    calculation_trace: list[dict] = Field(
        default_factory=list,
        description="Trace of calculator tool invocations for transparency",
    )


# ============================================================================
# LLM Response Normalization
# ============================================================================


def _normalize_result_value(value: str) -> str:
    """Normalize result values to match expected Literal values."""
    value_lower = str(value).lower()
    if value_lower in ("pass", "passed", "verified", "consistent", "valid", "true", "yes"):
        return "pass"
    if value_lower in ("fail", "failed", "invalid", "inconsistent", "false", "no"):
        return "fail"
    return "inconclusive"


def _normalize_consistency_check(item: dict) -> dict:
    """Normalize a consistency check to match ConsistencyCheckResult schema."""
    return {
        "check_name": item.get("check_name") or item.get("check") or item.get("name") or "unknown",
        "claim_id": item.get("claim_id") or item.get("id") or "unknown",
        "result": _normalize_result_value(item.get("result") or item.get("status") or "inconclusive"),
        "details": item.get("details") if isinstance(item.get("details"), dict) else {},
        "severity": item.get("severity") or "info",
        "message": item.get("message") or item.get("description") or item.get("note") or "",
    }


def _normalize_unit_validation(data: dict | None) -> dict:
    """Normalize unit validation to match UnitValidationResult schema."""
    if not data or not isinstance(data, dict):
        return {
            "units_valid": True,
            "methodology_aligned": True,
            "conversion_factors_appropriate": True,
            "issues": [],
        }
    return {
        "units_valid": data.get("units_valid", data.get("valid", True)),
        "methodology_aligned": data.get("methodology_aligned", data.get("aligned", True)),
        "conversion_factors_appropriate": data.get("conversion_factors_appropriate", True),
        "issues": data.get("issues", []) if isinstance(data.get("issues"), list) else [],
    }


def _normalize_benchmark_comparison(data: dict | None) -> dict | None:
    """Normalize benchmark comparison to match BenchmarkComparison schema."""
    if not data or not isinstance(data, dict):
        return None
    
    # Check if it's a "not available" response
    status = data.get("status", "")
    if "unavailable" in str(status).lower() or "unable" in str(status).lower():
        return None
    
    assessment = data.get("assessment", "inconclusive")
    if assessment not in ("plausible", "outlier_high", "outlier_low", "inconclusive"):
        assessment = "inconclusive"
    
    return {
        "metric_name": data.get("metric_name") or data.get("metric") or "unknown",
        "reported_value": float(data.get("reported_value", 0)),
        "reported_unit": data.get("reported_unit") or data.get("unit") or "unknown",
        "sector_average": data.get("sector_average"),
        "sector_unit": data.get("sector_unit"),
        "benchmark_source": data.get("benchmark_source") or data.get("source"),
        "assessment": assessment,
        "reasoning": data.get("reasoning") or data.get("note") or "",
    }


def _normalize_target_achievability(data: dict | None) -> dict | None:
    """Normalize target achievability to match TargetAchievabilityResult schema."""
    if not data or not isinstance(data, dict):
        return None
    
    # Check if it's a "not applicable" response
    status = data.get("status", "")
    if "not_applicabl" in str(status).lower() or "n/a" in str(status).lower():
        return None
    
    assessment = data.get("achievability_assessment") or data.get("assessment") or "inconclusive"
    if assessment not in ("achievable", "challenging", "questionable", "inconclusive"):
        assessment = "inconclusive"
    
    target_type = data.get("target_type") or "absolute_reduction"
    if target_type not in ("absolute_reduction", "intensity_reduction", "net_zero"):
        target_type = "absolute_reduction"
    
    return {
        "claim_id": data.get("claim_id") or "unknown",
        "target_type": target_type,
        "baseline_year": data.get("baseline_year"),
        "baseline_value": data.get("baseline_value"),
        "target_year": data.get("target_year"),
        "target_value": data.get("target_value"),
        "target_percentage": data.get("target_percentage"),
        "required_annual_reduction_rate": data.get("required_annual_reduction_rate"),
        "achievability_assessment": assessment,
        "interim_targets_consistent": data.get("interim_targets_consistent"),
        "ifrs_s2_33_36_compliant": data.get("ifrs_s2_33_36_compliant", False),
        "missing_ifrs_requirements": data.get("missing_ifrs_requirements", []),
        "reasoning": data.get("reasoning") or "",
    }


def _normalize_historical_consistency(data: dict | None) -> dict | None:
    """Normalize historical consistency to match HistoricalConsistencyResult schema."""
    if not data or not isinstance(data, dict):
        return None
    
    # Check if it's a "not available" response
    status = data.get("status", "")
    if "unavailable" in str(status).lower() or "unable" in str(status).lower():
        return None
    
    assessment = data.get("assessment") or "inconclusive"
    if assessment not in ("consistent", "inconsistent", "partially_consistent", "inconclusive"):
        assessment = "inconclusive"
    
    return {
        "claim_id": data.get("claim_id") or "unknown",
        "current_year": data.get("current_year"),
        "current_value": data.get("current_value"),
        "prior_years": data.get("prior_years", []),
        "yoy_change_consistent": data.get("yoy_change_consistent"),
        "trend_consistent": data.get("trend_consistent"),
        "methodology_changes": data.get("methodology_changes", []),
        "unexplained_deviations": data.get("unexplained_deviations", []),
        "assessment": assessment,
        "reasoning": data.get("reasoning") or data.get("details") or "",
    }


def _normalize_ifrs_compliance(data: dict | None, claim_id: str = "unknown") -> dict:
    """Normalize IFRS compliance to match IFRSComplianceResult schema."""
    if not data or not isinstance(data, dict):
        return {
            "claim_id": claim_id,
            "ifrs_paragraphs": [],
            "compliance_status": "not_applicable",
            "missing_requirements": [],
            "compliance_details": {},
            "reasoning": "No IFRS compliance data available",
        }
    
    status = data.get("compliance_status") or data.get("status") or "not_applicable"
    status_map = {
        "compliant": "compliant",
        "partial": "partially_compliant",
        "partially": "partially_compliant",
        "non": "non_compliant",
        "not_compliant": "non_compliant",
        "n/a": "not_applicable",
    }
    for key, value in status_map.items():
        if key in str(status).lower():
            status = value
            break
    if status not in ("compliant", "partially_compliant", "non_compliant", "not_applicable"):
        status = "not_applicable"
    
    return {
        "claim_id": data.get("claim_id") or claim_id,
        "ifrs_paragraphs": data.get("ifrs_paragraphs", []),
        "compliance_status": status,
        "missing_requirements": data.get("missing_requirements", []),
        "compliance_details": data.get("compliance_details", {}),
        "reasoning": data.get("reasoning") or "",
    }


def _normalize_quantitative_validation_response(data: dict, claim_id: str = "unknown") -> dict:
    """Normalize LLM response to match QuantitativeValidationResult schema."""
    # Normalize consistency_checks
    checks = data.get("consistency_checks", [])
    if isinstance(checks, list):
        data["consistency_checks"] = [_normalize_consistency_check(c) for c in checks if isinstance(c, dict)]
    else:
        data["consistency_checks"] = []
    
    # Normalize unit_validation
    data["unit_validation"] = _normalize_unit_validation(data.get("unit_validation"))
    
    # Normalize optional fields
    data["benchmark_comparison"] = _normalize_benchmark_comparison(data.get("benchmark_comparison"))
    data["target_achievability"] = _normalize_target_achievability(data.get("target_achievability"))
    data["historical_consistency"] = _normalize_historical_consistency(data.get("historical_consistency"))
    data["ifrs_compliance"] = _normalize_ifrs_compliance(data.get("ifrs_compliance"), claim_id)
    
    # Ensure required fields
    data["claim_id"] = data.get("claim_id") or claim_id
    data["summary"] = data.get("summary") or "Validation completed"
    data["confidence"] = data.get("confidence") or "medium"
    if data["confidence"] not in ("high", "medium", "low"):
        data["confidence"] = "medium"
    
    return data


# ============================================================================
# Constants and Prompts
# ============================================================================

# Claim type to validation focus mapping
CLAIM_TYPE_VALIDATION_FOCUS = {
    "quantitative": {
        "checks": ["scope_addition", "yoy_percentage", "unit_validation"],
        "ifrs_paragraphs": ["S2.29", "S2.29(a)(i)", "S2.29(a)(ii)", "S2.29(a)(iii)"],
        "query_suffix": "GHG emissions Scope 1 2 3 tCO2e methodology",
    },
    "target": {
        "checks": ["target_achievability", "interim_consistency", "baseline_validation"],
        "ifrs_paragraphs": ["S2.33", "S2.34", "S2.35", "S2.36"],
        "query_suffix": "emissions target reduction baseline net zero SBTi",
    },
    "intensity": {
        "checks": ["benchmark_comparison", "unit_validation", "calculation_accuracy"],
        "ifrs_paragraphs": ["S2.29(e)", "S2.30", "S2.31"],
        "query_suffix": "emission intensity carbon intensity revenue production",
    },
}

# System prompt with calculator tool instructions
DATA_METRICS_SYSTEM_PROMPT = """You are the Data/Metrics Agent in Sibyl, an AI system that verifies sustainability reports against IFRS S2 disclosure standards. Your task is to validate quantitative claims for mathematical consistency, methodological alignment, and benchmark plausibility.

## CRITICAL: Calculator Tool Usage

You have access to a `calculator` tool. You MUST use this tool for ALL arithmetic calculations. NEVER calculate numbers mentally - always use the calculator tool to ensure 100% accuracy.

Examples of when to use the calculator:
- Adding scope emissions: calculator("2300000 + 1100000 + 8500000")
- Calculating percentage change: calculator("((2450000 - 2300000) / 2450000) * 100")
- Checking discrepancy: calculator("abs(11900000 - 12000000) / 12000000 * 100")
- Annual reduction rate: calculator("(1 - 0.42) ** (1/11)")
- Compound growth: calculator("2500000 * (1 - 0.042) ** 11")

## Your Responsibilities

1. **Internal Consistency Checks:**
   - Scope Addition: Verify Scope 1 + Scope 2 + Scope 3 = Total (within 1% tolerance)
   - Year-over-Year Percentages: Verify reported % changes match actual calculations (0.1pp tolerance)
   - Baseline Consistency: Verify baseline values are used consistently across targets
   - Recalculation Consistency: Verify recalculations are applied uniformly

2. **Unit and Methodology Validation:**
   - Units are appropriate (tCO2e, MtCO2e, etc.)
   - Methodology aligns with GHG Protocol
   - Conversion factors are reasonable
   - Scope 2 location/market-based distinction

3. **Benchmark Comparison:**
   - Compare metrics against industry sector averages when available
   - Flag outliers (values significantly above/below sector norms)
   - Note if benchmark data is unavailable

4. **Target Achievability:**
   - Calculate required annual reduction rate
   - Assess if rate is historically achievable
   - Check interim targets for consistency
   - Validate IFRS S2.33-36 compliance

5. **Historical Consistency:**
   - Compare with prior year values
   - Verify YoY changes match reported percentages
   - Identify unexplained trend deviations
   - Note methodology changes

6. **IFRS S2.27-37 Compliance:**
   - S2.29: GHG emissions disclosure (Scope 1, 2, 3)
   - S2.29(a)(i)-(iii): Scope breakdown requirements
   - S2.29(e): Emission intensity metrics
   - S2.33-36: Target disclosure requirements

## Output Format

After using the calculator for all necessary calculations, return a JSON object with:
- `claim_id`: The claim being validated
- `consistency_checks`: Array of check results
- `unit_validation`: Unit and methodology assessment
- `benchmark_comparison`: Benchmark analysis (if applicable)
- `target_achievability`: Target assessment (if applicable)
- `historical_consistency`: Historical analysis (if applicable)
- `ifrs_compliance`: IFRS compliance assessment
- `summary`: Brief overall summary
- `supports_claim`: true/false/null
- `confidence`: "high"/"medium"/"low"
- `missing_data`: Array of data that was unavailable
- `calculation_trace`: Array of calculations performed (expression and result)

Always output valid JSON. No markdown, no code blocks, just the raw JSON object."""

DATA_METRICS_USER_PROMPT_TEMPLATE = """Validate the following quantitative claim for consistency and plausibility:

**Claim:** {claim_text}

**Claim Type:** {claim_type}

**Preliminary IFRS Mapping:** {preliminary_ifrs}

**Related Claims (for consistency checking):**
{related_claims_json}

**Document Context:**
{document_context}

**Benchmark Data (if available):**
{benchmark_data_json}

**Historical Data (if available):**
{historical_data_json}

**Retrieved IFRS Paragraphs:**
{rag_results}

Instructions:
1. Use the calculator tool for ALL arithmetic calculations
2. Perform all applicable consistency checks
3. Validate units and methodology
4. Compare against benchmarks if data is available
5. Assess target achievability for target claims
6. Check historical consistency
7. Assess IFRS S2.27-37 compliance

Return your assessment as a JSON object matching the specified schema."""


# ============================================================================
# Helper Functions - Claim Processing
# ============================================================================


def _group_claims_by_analysis_type(
    claims: list[Claim],
) -> dict[str, list[Claim]]:
    """Group claims into emissions, targets, intensity, and other categories.

    Args:
        claims: List of claims to group

    Returns:
        Dict mapping category to list of claims
    """
    groups: dict[str, list[Claim]] = {
        "emissions": [],
        "targets": [],
        "intensity": [],
        "other": [],
    }

    for claim in claims:
        text_lower = claim.text.lower()

        # Check for target claims
        if any(word in text_lower for word in ["target", "reduce", "reduction", "net zero", "2030", "2050"]):
            groups["targets"].append(claim)
        # Check for intensity claims
        elif any(word in text_lower for word in ["intensity", "per revenue", "per unit", "per employee"]):
            groups["intensity"].append(claim)
        # Check for emissions claims
        elif any(word in text_lower for word in ["scope 1", "scope 2", "scope 3", "emissions", "tco2e", "ghg"]):
            groups["emissions"].append(claim)
        else:
            groups["other"].append(claim)

    return groups


def _find_related_claims(claim: Claim, all_claims: list[Claim]) -> list[Claim]:
    """Find claims related by scope, timeframe, or metric for consistency checks.

    Args:
        claim: The claim to find related claims for
        all_claims: All claims in the state

    Returns:
        List of related claims
    """
    related: list[Claim] = []
    claim_text_lower = claim.text.lower()

    for other in all_claims:
        if other.claim_id == claim.claim_id:
            continue

        other_text_lower = other.text.lower()

        # Same scope family
        scope_terms = ["scope 1", "scope 2", "scope 3", "total emissions"]
        if any(term in claim_text_lower and term in other_text_lower for term in scope_terms):
            related.append(other)
            continue

        # Same year reference
        years = re.findall(r"20\d{2}", claim.text)
        for year in years:
            if year in other.text:
                related.append(other)
                break

    return related[:5]  # Limit to 5 most related claims


# ============================================================================
# Helper Functions - Unit Normalization
# ============================================================================

# Unit conversion factors to base unit (tCO2e)
UNIT_CONVERSIONS = {
    "tco2e": 1,
    "tco2": 1,
    "t co2e": 1,
    "tonnes co2e": 1,
    "metric tons co2e": 1,
    "mtco2e": 1_000_000,
    "mt co2e": 1_000_000,
    "million tonnes co2e": 1_000_000,
    "million tco2e": 1_000_000,
    "m tco2e": 1_000_000,
    "ktco2e": 1_000,
    "kt co2e": 1_000,
    "thousand tonnes co2e": 1_000,
    "gtco2e": 1_000_000_000,
    "gt co2e": 1_000_000_000,
    "billion tonnes co2e": 1_000_000_000,
}


def normalize_emissions(value: float, unit: str) -> float:
    """Convert emissions to tCO2e (handle Mt, kt, Gt prefixes).

    Args:
        value: The numeric value
        unit: The unit string

    Returns:
        Value in tCO2e
    """
    unit_lower = unit.lower().strip()

    # Try exact match first
    if unit_lower in UNIT_CONVERSIONS:
        return value * UNIT_CONVERSIONS[unit_lower]

    # Try partial match
    for known_unit, factor in UNIT_CONVERSIONS.items():
        if known_unit in unit_lower:
            return value * factor

    # Check for M/Mt prefix
    if unit_lower.startswith("m") and "co2" in unit_lower:
        return value * 1_000_000

    # Check for k/kt prefix
    if unit_lower.startswith("k") and "co2" in unit_lower:
        return value * 1_000

    # Default: assume already in tCO2e
    return value


# ============================================================================
# Helper Functions - RAG Retrieval
# ============================================================================


async def _retrieve_ifrs_metrics_paragraphs(
    claim: Claim,
    report_id: str,  # noqa: ARG001 - Will be used when RAG is properly integrated
) -> str:
    """Retrieve IFRS S2.27-37 and related paragraphs via RAG.

    Args:
        claim: The claim to retrieve paragraphs for
        report_id: The report ID for context (used for RAG filtering)

    Returns:
        Formatted RAG results as a string
    """
    # Import here to avoid circular imports
    try:
        from app.agents.tools.rag_lookup import rag_lookup
    except ImportError:
        logger.warning("RAG lookup not available, returning placeholder")
        return "--- RAG lookup not available ---"

    claim_type = claim.claim_type
    focus = CLAIM_TYPE_VALIDATION_FOCUS.get(claim_type, CLAIM_TYPE_VALIDATION_FOCUS["quantitative"])

    # Build query with claim text and type-specific suffix
    preliminary_ids = " ".join(claim.ifrs_paragraphs) if claim.ifrs_paragraphs else ""
    query = f"{claim.text[:500]} {focus['query_suffix']} {preliminary_ids}".strip()

    try:
        results = await rag_lookup.ainvoke({
            "query": query,
            "source_types": ["ifrs_s2"],
            "top_k": 5,
        })
        return results
    except Exception as e:
        logger.warning("RAG retrieval failed for claim %s: %s", claim.claim_id, e)
        return f"--- RAG retrieval failed: {e} ---"


# ============================================================================
# Helper Functions - Validation with Tool Loop
# ============================================================================


async def _validate_quantitative_claim(
    claim: Claim,
    related_claims: list[Claim],
    benchmark_data: dict | None,
    historical_data: dict | None,
    rag_results: str,
    document_context: str = "",
) -> QuantitativeValidationResult:
    """Main validation orchestrator with calculator tool binding.

    Uses a tool loop:
    1. Send prompt with claim data to LLM with calculator tool bound
    2. LLM may call calculator multiple times for different checks
    3. When LLM returns final JSON (no more tool calls), parse and return

    Args:
        claim: The claim to validate
        related_claims: Related claims for consistency checking
        benchmark_data: Benchmark data from other agents (if available)
        historical_data: Historical data (if available)
        rag_results: Retrieved IFRS paragraphs

    Returns:
        QuantitativeValidationResult with validation assessment
    """
    # Format related claims as JSON
    related_claims_json = json.dumps(
        [
            {"claim_id": c.claim_id, "text": c.text[:300], "type": c.claim_type}
            for c in related_claims
        ],
        indent=2,
    ) if related_claims else "No related claims found"

    # Format benchmark and historical data
    benchmark_json = json.dumps(benchmark_data, indent=2) if benchmark_data else "No benchmark data available"
    historical_json = json.dumps(historical_data, indent=2) if historical_data else "No historical data available"

    # Build user prompt
    preliminary_ifrs = ", ".join(claim.ifrs_paragraphs) if claim.ifrs_paragraphs else "None"
    user_prompt = DATA_METRICS_USER_PROMPT_TEMPLATE.format(
        claim_text=claim.text,
        claim_type=claim.claim_type,
        preliminary_ifrs=preliminary_ifrs,
        related_claims_json=related_claims_json,
        document_context=document_context or "No additional context",
        benchmark_data_json=benchmark_json,
        historical_data_json=historical_json,
        rag_results=rag_results,
    )

    # Get calculator tool schema for OpenRouter
    calc_tool = get_calculator_tool()
    tool_schema = {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": calc_tool.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        }
    }

    messages: list[dict] = [
        {"role": "system", "content": DATA_METRICS_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    calculation_trace: list[dict] = []
    max_iterations = 15

    for _iteration in range(max_iterations):
        try:
            # Build request payload with tools
            payload = {
                "model": Models.CLAUDE_SONNET,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 8192,
                "tools": [tool_schema],
            }

            # Make request through httpx client directly for tool support
            response = await openrouter_client._client.post(
                "/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            choice = data["choices"][0]
            message = choice["message"]
            _finish_reason = choice.get("finish_reason", "")  # noqa: F841

            # Check for tool calls
            if message.get("tool_calls"):
                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": message.get("content", ""),
                    "tool_calls": message["tool_calls"],
                })

                # Execute each tool call
                for tool_call in message["tool_calls"]:
                    if tool_call["function"]["name"] == "calculator":
                        try:
                            args = json.loads(tool_call["function"]["arguments"])
                            expression = args.get("expression", "")
                            result = calculator.invoke({"expression": expression})

                            calculation_trace.append({
                                "expression": expression,
                                "result": result,
                            })

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": result,
                            })
                        except Exception as e:
                            logger.warning("Calculator tool error: %s", e)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": f"Error: {str(e)}",
                            })
                continue

            # No tool calls - this is the final response
            content = message.get("content", "")
            if not content:
                logger.warning("Empty response from LLM")
                return _create_error_result(claim.claim_id, "Empty LLM response", calculation_trace)

            # Parse JSON response
            try:
                cleaned = content.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                cleaned = cleaned.strip()

                result_data = json.loads(cleaned)
                result_data = _normalize_quantitative_validation_response(result_data, claim.claim_id)
                result_data["calculation_trace"] = calculation_trace
                return QuantitativeValidationResult(**result_data)

            except (json.JSONDecodeError, Exception) as e:
                logger.warning("Failed to parse LLM response: %s", e)
                logger.debug("Response was: %s", content[:500])
                return _create_error_result(
                    claim.claim_id,
                    f"Failed to parse response: {e}",
                    calculation_trace,
                )

        except Exception as e:
            logger.error("LLM validation call failed: %s", e)
            return _create_error_result(claim.claim_id, str(e), calculation_trace)

    # Exceeded max iterations
    logger.warning("Tool loop exceeded max iterations for claim %s", claim.claim_id)
    return _create_error_result(
        claim.claim_id,
        "Tool loop exceeded maximum iterations",
        calculation_trace,
    )


def _create_error_result(
    claim_id: str,
    error_message: str,
    calculation_trace: list[dict],
) -> QuantitativeValidationResult:
    """Create an error result when validation fails.

    Args:
        claim_id: The claim ID
        error_message: Description of the error
        calculation_trace: Any calculations performed before error

    Returns:
        QuantitativeValidationResult with error information
    """
    return QuantitativeValidationResult(
        claim_id=claim_id,
        consistency_checks=[],
        unit_validation=UnitValidationResult(
            units_valid=False,
            methodology_aligned=False,
            conversion_factors_appropriate=False,
            issues=[f"Validation error: {error_message}"],
        ),
        benchmark_comparison=None,
        target_achievability=None,
        historical_consistency=None,
        ifrs_compliance=IFRSComplianceResult(
            claim_id=claim_id,
            ifrs_paragraphs=[],
            compliance_status="not_applicable",
            missing_requirements=[],
            compliance_details={},
            reasoning=f"Unable to assess due to error: {error_message}",
        ),
        summary=f"Validation failed: {error_message}",
        supports_claim=None,
        confidence="low",
        missing_data=["Full validation could not be performed"],
        calculation_trace=calculation_trace,
    )


# ============================================================================
# Helper Functions - Inter-Agent Communication
# ============================================================================


def _should_request_benchmark_data(claim: Claim) -> tuple[str, str] | None:
    """Determine if benchmark data should be requested from Academic/Research Agent.

    Args:
        claim: The claim to check

    Returns:
        Tuple of (agent_type, metric_type) if benchmark needed, None otherwise
    """
    claim_text_lower = claim.text.lower()

    # Intensity metrics need sector benchmarks
    if any(word in claim_text_lower for word in ["intensity", "per revenue", "per unit"]):
        if "emission" in claim_text_lower or "carbon" in claim_text_lower:
            return ("academic", "emission_intensity")

    # Water/energy intensity
    if any(word in claim_text_lower for word in ["water intensity", "energy intensity"]):
        return ("academic", "resource_intensity")

    return None


def _create_benchmark_info_request(
    claim: Claim,
    metric_type: str,
) -> InfoRequest:
    """Create InfoRequest for benchmark data.

    Args:
        claim: The claim needing benchmark data
        metric_type: Type of metric for benchmark

    Returns:
        InfoRequest object
    """
    return InfoRequest(
        request_id=str(generate_uuid7()),
        requesting_agent="data_metrics",
        description=f"Request sector benchmark data for {metric_type} to validate claim",
        context={
            "claim_id": claim.claim_id,
            "claim_text": claim.text[:200],
            "metric_type": metric_type,
            "target_agent": "academic",
        },
        status="pending",
    )


def _process_benchmark_responses(
    state: SibylState,
    claim: Claim,
) -> dict | None:
    """Extract benchmark data from InfoResponses.

    Args:
        state: Current pipeline state
        claim: The claim to find responses for

    Returns:
        Benchmark data dict or None
    """
    info_responses = state.get("info_responses", [])
    info_requests = state.get("info_requests", [])

    # Find requests from data_metrics for this claim
    our_requests = [
        req for req in info_requests
        if req.requesting_agent == "data_metrics"
        and req.context.get("claim_id") == claim.claim_id
    ]

    # Find matching responses
    for req in our_requests:
        for resp in info_responses:
            if resp.request_id == req.request_id:
                return {
                    "source": resp.responding_agent,
                    "data": resp.details,
                    "response": resp.response,
                }

    return None


# ============================================================================
# Helper Functions - Re-investigation
# ============================================================================


def _get_reinvestigation_context(
    state: SibylState,
    claim_id: str,
) -> ReinvestigationRequest | None:
    """Get re-investigation request targeting data_metrics agent for a claim.

    Args:
        state: Current pipeline state
        claim_id: The claim ID to check

    Returns:
        ReinvestigationRequest if found, None otherwise
    """
    reinvestigation_requests = state.get("reinvestigation_requests", [])

    for req in reinvestigation_requests:
        if req.claim_id == claim_id and "data_metrics" in req.target_agents:
            return req

    return None


async def _perform_reinvestigation(
    claim: Claim,
    reinvest_request: ReinvestigationRequest,
    report_id: str,
    state: SibylState,
) -> QuantitativeValidationResult:
    """Perform targeted re-investigation based on Judge guidance.

    Args:
        claim: The claim to re-investigate
        reinvest_request: The re-investigation request with guidance
        report_id: Report ID for RAG queries
        state: Current state for additional context

    Returns:
        Updated validation result
    """
    # Get standard IFRS retrieval
    rag_results = await _retrieve_ifrs_metrics_paragraphs(claim, report_id)

    # Add re-investigation context
    reinvest_context = f"""
**Re-investigation focus:** {reinvest_request.evidence_gap}

**Required evidence:** {reinvest_request.required_evidence or 'Not specified'}

**Refined queries from Judge:** {', '.join(reinvest_request.refined_queries)}
"""

    combined_rag = f"{reinvest_context}\n\n{rag_results}"

    # Find related claims
    claims = list(state.get("claims", []))
    related_claims = _find_related_claims(claim, claims)

    # Check for benchmark responses
    benchmark_data = _process_benchmark_responses(state, claim)

    # Perform validation with reinvestigation context
    return await _validate_quantitative_claim(
        claim=claim,
        related_claims=related_claims,
        benchmark_data=benchmark_data,
        historical_data=None,
        rag_results=combined_rag,
        document_context=f"Re-investigation: {reinvest_request.evidence_gap}",
    )


# ============================================================================
# Helper Functions - Finding Generation
# ============================================================================


def _create_quantitative_finding(
    claim: Claim,
    validation_result: QuantitativeValidationResult,
    iteration: int,
    benchmark_responses: dict | None = None,
) -> AgentFinding:
    """Create AgentFinding from validation results.

    Args:
        claim: The validated claim
        validation_result: The validation result
        iteration: Current iteration count
        benchmark_responses: Any benchmark data incorporated

    Returns:
        AgentFinding object
    """
    # Build summary from consistency checks
    check_results = validation_result.consistency_checks
    passed = sum(1 for c in check_results if c.result == "pass")
    failed = sum(1 for c in check_results if c.result == "fail")

    if check_results:
        check_summary = f"{passed}/{len(check_results)} consistency checks passed"
        if failed > 0:
            failed_names = [c.check_name for c in check_results if c.result == "fail"]
            check_summary += f" (failed: {', '.join(failed_names)})"
    else:
        check_summary = "No consistency checks performed"

    summary = f"{check_summary}. {validation_result.summary}"

    # Build details
    details: dict = {
        "consistency_checks": [c.model_dump() for c in check_results],
        "unit_validation": validation_result.unit_validation.model_dump(),
        "ifrs_compliance": validation_result.ifrs_compliance.model_dump(),
        "calculation_trace": validation_result.calculation_trace,
        "missing_data": validation_result.missing_data,
    }

    if validation_result.benchmark_comparison:
        details["benchmark_comparison"] = validation_result.benchmark_comparison.model_dump()

    if validation_result.target_achievability:
        details["target_achievability"] = validation_result.target_achievability.model_dump()

    if validation_result.historical_consistency:
        details["historical_consistency"] = validation_result.historical_consistency.model_dump()

    if benchmark_responses:
        details["cross_domain_evidence"] = benchmark_responses

    return AgentFinding(
        finding_id=str(generate_uuid7()),
        agent_name="data_metrics",
        claim_id=claim.claim_id,
        evidence_type="quantitative_validation",
        summary=summary,
        details=details,
        supports_claim=validation_result.supports_claim,
        confidence=validation_result.confidence,
        iteration=iteration + 1,
    )


# ============================================================================
# Main Node Function
# ============================================================================


async def investigate_data(state: SibylState) -> dict:
    """Data/Metrics Agent: Validate quantitative claims for consistency and plausibility.

    Uses calculator tool for guaranteed arithmetic accuracy via tool-calling loop.

    Reads: state.routing_plan, state.claims, state.report_id,
           state.info_responses, state.reinvestigation_requests
    Writes: state.findings, state.events, state.info_requests, state.agent_status

    Processing steps:
    1. Emit agent_started StreamEvent
    2. Find assigned claims from routing_plan
    3. Group claims by analysis type
    4. For each claim:
       a. Check for re-investigation context
       b. Find related claims for consistency checks
       c. Retrieve IFRS paragraphs via RAG
       d. Check for InfoResponses (benchmark data)
       e. Perform validation (LLM with calculator tool binding)
       f. Emit consistency_check events for each check
       g. Create AgentFinding (includes calculation_trace)
       h. Emit evidence_found event
       i. Check if InfoRequest needed for benchmarks
    5. Update agent_status to completed
    6. Emit agent_completed StreamEvent
    7. Return partial state update

    Returns:
        Partial state update with findings, events, and info_requests.
    """
    agent_name = "data_metrics"
    events: list[StreamEvent] = []
    findings: list[AgentFinding] = []
    info_requests: list[InfoRequest] = []

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
        "Data/Metrics Agent processing %d claims (iteration %d)",
        len(assigned_claims),
        iteration_count,
    )

    consistency_checks_passed = 0
    consistency_checks_failed = 0

    if not assigned_claims:
        # No claims assigned to us
        events.append(
            StreamEvent(
                event_type="agent_completed",
                agent_name=agent_name,
                data={
                    "claims_processed": 0,
                    "findings_count": 0,
                    "consistency_checks_passed": 0,
                    "consistency_checks_failed": 0,
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
                "message": f"Processing {len(assigned_claims)} quantitative claims for consistency validation..."
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )

    # Process each assigned claim
    for claim in assigned_claims:
        try:
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
                validation_result = await _perform_reinvestigation(
                    claim, reinvest_request, report_id, state
                )
            else:
                # Standard investigation
                events.append(
                    StreamEvent(
                        event_type="agent_thinking",
                        agent_name=agent_name,
                        data={
                            "message": f"Validating {claim.claim_type} claim: retrieving IFRS paragraphs..."
                        },
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                )

                # Find related claims
                related_claims = _find_related_claims(claim, claims)

                # RAG retrieval
                rag_results = await _retrieve_ifrs_metrics_paragraphs(claim, report_id)

                # Check for benchmark responses from other agents
                benchmark_data = _process_benchmark_responses(state, claim)

                # Perform validation with calculator tool
                validation_result = await _validate_quantitative_claim(
                    claim=claim,
                    related_claims=related_claims,
                    benchmark_data=benchmark_data,
                    historical_data=None,
                    rag_results=rag_results,
                )

            # Emit consistency_check events for each check
            for check in validation_result.consistency_checks:
                if check.result == "pass":
                    consistency_checks_passed += 1
                elif check.result == "fail":
                    consistency_checks_failed += 1

                events.append(
                    StreamEvent(
                        event_type="consistency_check",
                        agent_name=agent_name,
                        data={
                            "check_name": check.check_name,
                            "claim_id": check.claim_id,
                            "result": check.result,
                            "severity": check.severity,
                            "details": check.details,
                            "message": check.message,
                        },
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                )

            # Create finding
            finding = _create_quantitative_finding(
                claim,
                validation_result,
                iteration_count,
                benchmark_data if not reinvest_request else None,
            )
            findings.append(finding)

            # Emit evidence found event
            events.append(
                StreamEvent(
                    event_type="evidence_found",
                    agent_name=agent_name,
                    data={
                        "claim_id": claim.claim_id,
                        "summary": validation_result.summary,
                        "supports_claim": validation_result.supports_claim,
                        "confidence": validation_result.confidence,
                        "checks_passed": sum(
                            1 for c in validation_result.consistency_checks
                            if c.result == "pass"
                        ),
                        "checks_failed": sum(
                            1 for c in validation_result.consistency_checks
                            if c.result == "fail"
                        ),
                    },
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

            # Check if cross-domain benchmark data is needed
            if not reinvest_request:
                benchmark_needed = _should_request_benchmark_data(claim)
                if benchmark_needed and not benchmark_data:
                    benchmark_target_agent, metric_type = benchmark_needed
                    info_req = _create_benchmark_info_request(claim, metric_type)
                    info_requests.append(info_req)

                    events.append(
                        StreamEvent(
                            event_type="info_request_posted",
                            agent_name=agent_name,
                            data={
                                "request_id": info_req.request_id,
                                "description": info_req.description,
                                "request_type": metric_type,
                                "target_agent": benchmark_target_agent,
                            },
                            timestamp=datetime.now(timezone.utc).isoformat(),
                        )
                    )

        except Exception as e:
            logger.error("Error processing claim %s: %s", claim.claim_id, e)
            # Create error finding
            finding = AgentFinding(
                finding_id=str(generate_uuid7()),
                agent_name=agent_name,
                claim_id=claim.claim_id,
                evidence_type="quantitative_validation",
                summary=f"Error during quantitative validation: {str(e)}",
                details={"error": str(e)},
                supports_claim=None,
                confidence="low",
                iteration=iteration_count + 1,
            )
            findings.append(finding)

            events.append(
                StreamEvent(
                    event_type="error",
                    agent_name=agent_name,
                    data={
                        "claim_id": claim.claim_id,
                        "message": f"Validation error: {str(e)}",
                    },
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

    # Emit completion event
    events.append(
        StreamEvent(
            event_type="agent_completed",
            agent_name=agent_name,
            data={
                "claims_processed": len(assigned_claims),
                "findings_count": len(findings),
                "consistency_checks_passed": consistency_checks_passed,
                "consistency_checks_failed": consistency_checks_failed,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )

    # Build result
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

    return result
