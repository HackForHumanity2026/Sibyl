"""Sample SibylState fixtures for testing.

Provides pre-configured state objects for testing the Legal Agent
in various scenarios.
"""

from typing import Any

from app.agents.state import (
    Claim,
    ReinvestigationRequest,
    RoutingAssignment,
    SibylState,
    InfoRequest,
    InfoResponse,
)
from tests.fixtures.sample_claims import (
    GOVERNANCE_CLAIM,
    STRATEGIC_CLAIM_TRANSITION_PLAN,
    STRATEGIC_CLAIM_INCOMPLETE,
    METRICS_CLAIM_SCOPE_3,
    RISK_MANAGEMENT_CLAIM,
    ROUTING_GOVERNANCE,
    ROUTING_STRATEGIC,
    ROUTING_STRATEGIC_INCOMPLETE,
    ROUTING_METRICS,
    ROUTING_RISK_MANAGEMENT,
    ROUTING_NO_LEGAL,
    # Data Metrics imports
    DATA_METRICS_CLAIM_SCOPE_TOTALS,
    DATA_METRICS_CLAIM_SCOPE_MISMATCH,
    DATA_METRICS_CLAIM_YOY_CHANGE,
    DATA_METRICS_CLAIM_TARGET,
    DATA_METRICS_CLAIM_TARGET_AGGRESSIVE,
    DATA_METRICS_CLAIM_INTENSITY,
    DATA_METRICS_CLAIM_MULTIPLE_SCOPES,
    ROUTING_DATA_METRICS_SCOPE,
    ROUTING_DATA_METRICS_SCOPE_MISMATCH,
    ROUTING_DATA_METRICS_YOY,
    ROUTING_DATA_METRICS_TARGET,
    ROUTING_DATA_METRICS_TARGET_AGGRESSIVE,
    ROUTING_DATA_METRICS_INTENSITY,
    ROUTING_DATA_METRICS_MULTIPLE,
    # News/Media imports
    NEWS_CLAIM_EMISSIONS_REDUCTION,
    NEWS_CLAIM_CERTIFICATION,
    NEWS_CLAIM_CONTROVERSY,
    NEWS_CLAIM_NET_ZERO_TARGET,
    NEWS_CLAIM_REFORESTATION,
    NEWS_CLAIM_SUPPLY_CHAIN,
    ROUTING_NEWS_EMISSIONS,
    ROUTING_NEWS_CERTIFICATION,
    ROUTING_NEWS_CONTROVERSY,
    ROUTING_NEWS_NET_ZERO,
    ROUTING_NEWS_REFORESTATION,
    ROUTING_NEWS_SUPPLY_CHAIN,
    ROUTING_NO_NEWS,
    # Academic/Research imports
    ACADEMIC_CLAIM_METHODOLOGY,
    ACADEMIC_CLAIM_CERTIFICATION,
    ACADEMIC_CLAIM_SBTI,
    ACADEMIC_CLAIM_BENCHMARK,
    ACADEMIC_CLAIM_RESEARCH,
    ACADEMIC_CLAIM_OFFSET,
    ROUTING_ACADEMIC_METHODOLOGY,
    ROUTING_ACADEMIC_CERTIFICATION,
    ROUTING_ACADEMIC_SBTI,
    ROUTING_ACADEMIC_BENCHMARK,
    ROUTING_ACADEMIC_RESEARCH,
    ROUTING_ACADEMIC_OFFSET,
    ROUTING_NO_ACADEMIC,
    # Geography imports
    GEOGRAPHY_CLAIM_REFORESTATION,
    GEOGRAPHY_CLAIM_FACILITY,
    GEOGRAPHY_CLAIM_DEFORESTATION,
    GEOGRAPHY_CLAIM_SOLAR,
    ROUTING_GEO_REFORESTATION,
    ROUTING_GEO_FACILITY,
    ROUTING_GEO_DEFORESTATION,
    ROUTING_GEO_SOLAR,
    ROUTING_NO_GEO,
)


def create_base_state(**overrides: Any) -> SibylState:
    """Create a base SibylState with common defaults.
    
    Args:
        **overrides: Key-value pairs to override default state values.
        
    Returns:
        SibylState with defaults and any provided overrides.
    """
    base: SibylState = {
        "report_id": "test-report-001",
        "document_content": "Sample sustainability report content for testing.",
        "document_chunks": [],
        "claims": [],
        "routing_plan": [],
        "agent_status": {},
        "findings": [],
        "info_requests": [],
        "info_responses": [],
        "verdicts": [],
        "reinvestigation_requests": [],
        "iteration_count": 0,
        "max_iterations": 3,
        "disclosure_gaps": [],
        "events": [],
    }
    base.update(overrides)
    return base


def create_state_with_single_governance_claim() -> SibylState:
    """Create a state with a single governance claim routed to legal agent."""
    return create_base_state(
        claims=[GOVERNANCE_CLAIM],
        routing_plan=[ROUTING_GOVERNANCE],
    )


def create_state_with_strategic_claim() -> SibylState:
    """Create a state with a strategic transition plan claim."""
    return create_base_state(
        claims=[STRATEGIC_CLAIM_TRANSITION_PLAN],
        routing_plan=[ROUTING_STRATEGIC],
    )


def create_state_with_incomplete_strategic_claim() -> SibylState:
    """Create a state with an incomplete strategic claim (missing details)."""
    return create_base_state(
        claims=[STRATEGIC_CLAIM_INCOMPLETE],
        routing_plan=[ROUTING_STRATEGIC_INCOMPLETE],
    )


def create_state_with_metrics_claim() -> SibylState:
    """Create a state with a metrics claim about Scope 3 emissions."""
    return create_base_state(
        claims=[METRICS_CLAIM_SCOPE_3],
        routing_plan=[ROUTING_METRICS],
    )


def create_state_with_risk_management_claim() -> SibylState:
    """Create a state with a risk management claim."""
    return create_base_state(
        claims=[RISK_MANAGEMENT_CLAIM],
        routing_plan=[ROUTING_RISK_MANAGEMENT],
    )


def create_state_with_multiple_claims() -> SibylState:
    """Create a state with multiple claims of different types."""
    return create_base_state(
        claims=[
            GOVERNANCE_CLAIM,
            STRATEGIC_CLAIM_TRANSITION_PLAN,
            METRICS_CLAIM_SCOPE_3,
            RISK_MANAGEMENT_CLAIM,
        ],
        routing_plan=[
            ROUTING_GOVERNANCE,
            ROUTING_STRATEGIC,
            ROUTING_METRICS,
            ROUTING_RISK_MANAGEMENT,
        ],
    )


def create_state_with_no_legal_claims() -> SibylState:
    """Create a state where no claims are routed to the legal agent."""
    geographic_claim = Claim(
        claim_id="claim-geo-001",
        text="Our main manufacturing facility is located in Singapore.",
        page_number=15,
        claim_type="geographic",
        ifrs_paragraphs=[],
        priority="medium",
        source_location={"source_context": "Operations Overview"},
        agent_reasoning="Geographic claim about facility location."
    )
    return create_base_state(
        claims=[geographic_claim],
        routing_plan=[ROUTING_NO_LEGAL],
    )


def create_state_with_reinvestigation_request() -> SibylState:
    """Create a state with a re-investigation request from the Judge agent."""
    reinvestigation = ReinvestigationRequest(
        claim_id=STRATEGIC_CLAIM_INCOMPLETE.claim_id,
        target_agents=["legal"],
        evidence_gap="Transition plan lacks key assumptions required by S2.14(a)(iv)",
        refined_queries=[
            "Does the report disclose key assumptions for the transition plan anywhere?",
            "Search report content for 'transition plan assumptions' or 'carbon price assumptions'",
        ],
        required_evidence="Specific assumptions (e.g., carbon price, GDP growth) used in developing the transition plan",
    )
    return create_base_state(
        claims=[STRATEGIC_CLAIM_INCOMPLETE],
        routing_plan=[ROUTING_STRATEGIC_INCOMPLETE],
        reinvestigation_requests=[reinvestigation],
        iteration_count=1,
    )


def create_state_with_info_request() -> SibylState:
    """Create a state where legal agent needs to request cross-domain info."""
    # This represents a state where the legal agent might need geographic verification
    claim_needing_verification = Claim(
        claim_id="claim-gov-002",
        text="Our Sustainability Committee oversees operations at our Singapore facility, which has achieved ISO 14001 certification.",
        page_number=14,
        claim_type="legal_governance",
        ifrs_paragraphs=["S2.6"],
        priority="medium",
        source_location={"source_context": "Section 3.2 Governance"},
        agent_reasoning="Governance claim mentioning specific facility and certification."
    )
    routing = RoutingAssignment(
        claim_id="claim-gov-002",
        assigned_agents=["legal"],
        reasoning="Governance claim with geographic and certification elements."
    )
    return create_base_state(
        claims=[claim_needing_verification],
        routing_plan=[routing],
    )


def create_state_with_info_response() -> SibylState:
    """Create a state with a pending InfoResponse for the legal agent."""
    claim = Claim(
        claim_id="claim-gov-003",
        text="Our Singapore facility operates under ISO 14001 certification with quarterly environmental audits.",
        page_number=16,
        claim_type="legal_governance",
        ifrs_paragraphs=["S2.6"],
        priority="medium",
        source_location={"source_context": "Section 3.2 Governance"},
        agent_reasoning="Governance claim about facility certification."
    )
    routing = RoutingAssignment(
        claim_id="claim-gov-003",
        assigned_agents=["legal"],
        reasoning="Governance claim with certification verification needed."
    )
    # Simulate an InfoRequest the legal agent posted previously
    info_request = InfoRequest(
        request_id="req-001",
        requesting_agent="legal",
        description="Verify ISO 14001 certification for Singapore facility.",
        context={"claim_id": "claim-gov-003", "certification": "ISO 14001"},
        status="responded",
    )
    # Simulate an InfoResponse from the news/academic agent
    info_response = InfoResponse(
        request_id="req-001",
        responding_agent="news_media",
        response="Verified: Singapore facility received ISO 14001 certification in 2022, renewed in 2024.",
        details={"source": "ISO certification database", "verification_date": "2024-03-15"},
    )
    return create_base_state(
        claims=[claim],
        routing_plan=[routing],
        info_requests=[info_request],
        info_responses=[info_response],
    )


def create_state_for_gap_detection() -> SibylState:
    """Create a state specifically for testing gap detection.
    
    Contains claims that cover some IFRS requirements but leave gaps.
    """
    # This state has governance claim but no transition plan claim
    return create_base_state(
        report_id="test-report-gaps",
        claims=[GOVERNANCE_CLAIM, RISK_MANAGEMENT_CLAIM],
        routing_plan=[ROUTING_GOVERNANCE, ROUTING_RISK_MANAGEMENT],
    )


# ============================================================================
# Data Metrics Agent State Factories
# ============================================================================


def create_state_with_emissions_claim() -> SibylState:
    """Create a state with a scope emissions claim routed to data_metrics agent."""
    return create_base_state(
        claims=[DATA_METRICS_CLAIM_SCOPE_TOTALS],
        routing_plan=[ROUTING_DATA_METRICS_SCOPE],
    )


def create_state_with_scope_mismatch_claim() -> SibylState:
    """Create a state with a scope claim that has incorrect totals."""
    return create_base_state(
        claims=[DATA_METRICS_CLAIM_SCOPE_MISMATCH],
        routing_plan=[ROUTING_DATA_METRICS_SCOPE_MISMATCH],
    )


def create_state_with_yoy_claim() -> SibylState:
    """Create a state with a YoY percentage change claim."""
    return create_base_state(
        claims=[DATA_METRICS_CLAIM_YOY_CHANGE],
        routing_plan=[ROUTING_DATA_METRICS_YOY],
    )


def create_state_with_target_claim() -> SibylState:
    """Create a state with a target achievability claim."""
    return create_base_state(
        claims=[DATA_METRICS_CLAIM_TARGET],
        routing_plan=[ROUTING_DATA_METRICS_TARGET],
    )


def create_state_with_aggressive_target_claim() -> SibylState:
    """Create a state with an aggressive target that may be questionable."""
    return create_base_state(
        claims=[DATA_METRICS_CLAIM_TARGET_AGGRESSIVE],
        routing_plan=[ROUTING_DATA_METRICS_TARGET_AGGRESSIVE],
    )


def create_state_with_intensity_claim() -> SibylState:
    """Create a state with an intensity metric claim needing benchmark data."""
    return create_base_state(
        claims=[DATA_METRICS_CLAIM_INTENSITY],
        routing_plan=[ROUTING_DATA_METRICS_INTENSITY],
    )


def create_state_with_multiple_quantitative_claims() -> SibylState:
    """Create a state with multiple quantitative claims of different types."""
    return create_base_state(
        claims=[
            DATA_METRICS_CLAIM_SCOPE_TOTALS,
            DATA_METRICS_CLAIM_YOY_CHANGE,
            DATA_METRICS_CLAIM_TARGET,
            DATA_METRICS_CLAIM_INTENSITY,
        ],
        routing_plan=[
            ROUTING_DATA_METRICS_SCOPE,
            ROUTING_DATA_METRICS_YOY,
            ROUTING_DATA_METRICS_TARGET,
            ROUTING_DATA_METRICS_INTENSITY,
        ],
    )


def create_state_with_benchmark_info_response() -> SibylState:
    """Create a state with a pending benchmark InfoResponse for data_metrics agent."""
    # Simulate an InfoRequest the data_metrics agent posted previously
    info_request = InfoRequest(
        request_id="req-dm-001",
        requesting_agent="data_metrics",
        description="Request sector benchmark data for emission_intensity to validate claim",
        context={
            "claim_id": "claim-dm-006",
            "metric_type": "emission_intensity",
            "target_agent": "academic",
        },
        status="responded",
    )
    # Simulate an InfoResponse from the academic agent
    info_response = InfoResponse(
        request_id="req-dm-001",
        responding_agent="academic",
        response="Manufacturing sector average emission intensity: 0.8 tCO2e per $1M revenue (source: industry benchmarks 2024).",
        details={
            "sector": "manufacturing",
            "average_intensity": 0.8,
            "unit": "tCO2e per $1M revenue",
            "source": "Industry Sector Benchmarks 2024",
            "sample_size": 150,
        },
    )
    return create_base_state(
        claims=[DATA_METRICS_CLAIM_INTENSITY],
        routing_plan=[ROUTING_DATA_METRICS_INTENSITY],
        info_requests=[info_request],
        info_responses=[info_response],
    )


def create_state_with_data_metrics_reinvestigation() -> SibylState:
    """Create a state with a re-investigation request from Judge targeting data_metrics."""
    reinvestigation = ReinvestigationRequest(
        claim_id=DATA_METRICS_CLAIM_TARGET.claim_id,
        target_agents=["data_metrics"],
        evidence_gap="Target achievability calculation needs verification with interim milestones",
        refined_queries=[
            "Search for interim emission targets between 2019 and 2030",
            "Find historical emission reduction rates for comparison",
        ],
        required_evidence="Interim targets and historical reduction rates to validate achievability",
    )
    return create_base_state(
        claims=[DATA_METRICS_CLAIM_TARGET],
        routing_plan=[ROUTING_DATA_METRICS_TARGET],
        reinvestigation_requests=[reinvestigation],
        iteration_count=1,
    )


def create_state_with_no_data_metrics_claims() -> SibylState:
    """Create a state where no claims are routed to the data_metrics agent."""
    return create_base_state(
        claims=[GOVERNANCE_CLAIM],
        routing_plan=[ROUTING_GOVERNANCE],
    )


# ============================================================================
# News/Media Agent State Factories
# ============================================================================


def create_state_with_news_claim() -> SibylState:
    """Create a state with a single emissions claim routed to news_media agent."""
    return create_base_state(
        claims=[NEWS_CLAIM_EMISSIONS_REDUCTION],
        routing_plan=[ROUTING_NEWS_EMISSIONS],
    )


def create_state_with_news_certification_claim() -> SibylState:
    """Create a state with a certification claim for news_media verification."""
    return create_base_state(
        claims=[NEWS_CLAIM_CERTIFICATION],
        routing_plan=[ROUTING_NEWS_CERTIFICATION],
    )


def create_state_with_news_controversy_claim() -> SibylState:
    """Create a state with a controversy claim likely to surface contradictions."""
    return create_base_state(
        claims=[NEWS_CLAIM_CONTROVERSY],
        routing_plan=[ROUTING_NEWS_CONTROVERSY],
    )


def create_state_with_news_multiple_claims() -> SibylState:
    """Create a state with multiple news-related claims."""
    return create_base_state(
        claims=[
            NEWS_CLAIM_EMISSIONS_REDUCTION,
            NEWS_CLAIM_CERTIFICATION,
            NEWS_CLAIM_NET_ZERO_TARGET,
        ],
        routing_plan=[
            ROUTING_NEWS_EMISSIONS,
            ROUTING_NEWS_CERTIFICATION,
            ROUTING_NEWS_NET_ZERO,
        ],
    )


def create_state_with_news_reinvestigation() -> SibylState:
    """Create a state with a re-investigation request from Judge targeting news_media."""
    reinvestigation = ReinvestigationRequest(
        claim_id=NEWS_CLAIM_CONTROVERSY.claim_id,
        target_agents=["news_media"],
        evidence_gap="Need deeper investigation into compliance violations mentioned in initial search",
        refined_queries=[
            '"{company_name}" EPA enforcement action 2024',
            '"{company_name}" environmental violation settlement',
            '"{company_name}" whistleblower environmental',
        ],
        required_evidence="Official regulatory actions, court filings, or verified investigative reporting",
    )
    return create_base_state(
        claims=[NEWS_CLAIM_CONTROVERSY],
        routing_plan=[ROUTING_NEWS_CONTROVERSY],
        reinvestigation_requests=[reinvestigation],
        iteration_count=1,
    )


def create_state_with_news_info_request() -> SibylState:
    """Create a state with an InfoRequest from another agent to news_media."""
    info_request = InfoRequest(
        request_id="req-news-001",
        requesting_agent="legal",
        description="Need public news verification of compliance claims",
        context={
            "claim_id": NEWS_CLAIM_CERTIFICATION.claim_id,
            "question": "Has the company's ISO 14001 certification been publicly verified or questioned?",
        },
        status="pending",
    )
    return create_base_state(
        claims=[NEWS_CLAIM_CERTIFICATION],
        routing_plan=[ROUTING_NEWS_CERTIFICATION],
        info_requests=[info_request],
    )


def create_state_with_news_info_response() -> SibylState:
    """Create a state with an InfoResponse from another agent to news_media."""
    info_request = InfoRequest(
        request_id="req-news-002",
        requesting_agent="news_media",
        description="Request geographic verification of reforestation site",
        context={
            "claim_id": NEWS_CLAIM_REFORESTATION.claim_id,
            "target_agent": "geography",
        },
        status="completed",
    )
    info_response = InfoResponse(
        request_id="req-news-002",
        responding_agent="geography",
        response="Satellite imagery confirms reforestation activity in the specified region of Central Kalimantan.",
        details={
            "verification_source": "Sentinel-2 imagery analysis",
            "confidence": "high",
        },
    )
    return create_base_state(
        claims=[NEWS_CLAIM_REFORESTATION],
        routing_plan=[ROUTING_NEWS_REFORESTATION],
        info_requests=[info_request],
        info_responses=[info_response],
    )


def create_state_with_no_news_claims() -> SibylState:
    """Create a state where no claims are routed to the news_media agent."""
    return create_base_state(
        claims=[GOVERNANCE_CLAIM],
        routing_plan=[ROUTING_NO_NEWS],
    )


def create_state_with_news_supply_chain_claim() -> SibylState:
    """Create a state with a supply chain claim for investigative news verification."""
    return create_base_state(
        claims=[NEWS_CLAIM_SUPPLY_CHAIN],
        routing_plan=[ROUTING_NEWS_SUPPLY_CHAIN],
    )


# ============================================================================
# Academic/Research Agent State Factories (FRD 9)
# ============================================================================


def create_state_with_academic_methodology_claim() -> SibylState:
    """Create a state with a methodology claim routed to academic agent."""
    return create_base_state(
        claims=[ACADEMIC_CLAIM_METHODOLOGY],
        routing_plan=[ROUTING_ACADEMIC_METHODOLOGY],
    )


def create_state_with_academic_certification_claim() -> SibylState:
    """Create a state with a certification claim for academic validation."""
    return create_base_state(
        claims=[ACADEMIC_CLAIM_CERTIFICATION],
        routing_plan=[ROUTING_ACADEMIC_CERTIFICATION],
    )


def create_state_with_academic_sbti_claim() -> SibylState:
    """Create a state with an SBTi target claim for academic validation."""
    return create_base_state(
        claims=[ACADEMIC_CLAIM_SBTI],
        routing_plan=[ROUTING_ACADEMIC_SBTI],
    )


def create_state_with_academic_benchmark_claim() -> SibylState:
    """Create a state with a benchmark comparison claim for academic validation."""
    return create_base_state(
        claims=[ACADEMIC_CLAIM_BENCHMARK],
        routing_plan=[ROUTING_ACADEMIC_BENCHMARK],
    )


def create_state_with_academic_research_claim() -> SibylState:
    """Create a state with a research support claim for academic validation."""
    return create_base_state(
        claims=[ACADEMIC_CLAIM_RESEARCH],
        routing_plan=[ROUTING_ACADEMIC_RESEARCH],
    )


def create_state_with_academic_multiple_claims() -> SibylState:
    """Create a state with multiple academic claims of different types."""
    return create_base_state(
        claims=[
            ACADEMIC_CLAIM_METHODOLOGY,
            ACADEMIC_CLAIM_CERTIFICATION,
            ACADEMIC_CLAIM_SBTI,
            ACADEMIC_CLAIM_BENCHMARK,
        ],
        routing_plan=[
            ROUTING_ACADEMIC_METHODOLOGY,
            ROUTING_ACADEMIC_CERTIFICATION,
            ROUTING_ACADEMIC_SBTI,
            ROUTING_ACADEMIC_BENCHMARK,
        ],
    )


def create_state_with_academic_reinvestigation() -> SibylState:
    """Create a state with a re-investigation request targeting academic agent."""
    reinvestigation = ReinvestigationRequest(
        claim_id=ACADEMIC_CLAIM_CERTIFICATION.claim_id,
        target_agents=["academic"],
        evidence_gap="Need peer-reviewed research on I-REC additionality in Southeast Asian markets",
        refined_queries=[
            "I-REC additionality Southeast Asia peer-reviewed research",
            "renewable energy certificate greenwashing Asia-Pacific study",
        ],
        required_evidence="Academic research on whether I-RECs drive additional renewable energy investment",
    )
    return create_base_state(
        claims=[ACADEMIC_CLAIM_CERTIFICATION],
        routing_plan=[ROUTING_ACADEMIC_CERTIFICATION],
        reinvestigation_requests=[reinvestigation],
        iteration_count=1,
    )


def create_state_with_no_academic_claims() -> SibylState:
    """Create a state where no claims are routed to the academic agent."""
    return create_base_state(
        claims=[GOVERNANCE_CLAIM],
        routing_plan=[ROUTING_NO_ACADEMIC],
    )


# ============================================================================
# Geography Agent State Factories (FRD 10)
# ============================================================================


def create_state_with_geo_reforestation_claim() -> SibylState:
    """Create a state with a reforestation claim routed to geography agent."""
    return create_base_state(
        claims=[GEOGRAPHY_CLAIM_REFORESTATION],
        routing_plan=[ROUTING_GEO_REFORESTATION],
    )


def create_state_with_geo_facility_claim() -> SibylState:
    """Create a state with a facility claim for geography agent."""
    return create_base_state(
        claims=[GEOGRAPHY_CLAIM_FACILITY],
        routing_plan=[ROUTING_GEO_FACILITY],
    )


def create_state_with_geo_deforestation_claim() -> SibylState:
    """Create a state with a deforestation claim for geography agent."""
    return create_base_state(
        claims=[GEOGRAPHY_CLAIM_DEFORESTATION],
        routing_plan=[ROUTING_GEO_DEFORESTATION],
    )


def create_state_with_geo_multiple_claims() -> SibylState:
    """Create a state with multiple geographic claims."""
    return create_base_state(
        claims=[
            GEOGRAPHY_CLAIM_REFORESTATION,
            GEOGRAPHY_CLAIM_FACILITY,
            GEOGRAPHY_CLAIM_DEFORESTATION,
        ],
        routing_plan=[
            ROUTING_GEO_REFORESTATION,
            ROUTING_GEO_FACILITY,
            ROUTING_GEO_DEFORESTATION,
        ],
    )


def create_state_with_geo_reinvestigation() -> SibylState:
    """Create a state with a re-investigation request targeting geography agent."""
    reinvestigation = ReinvestigationRequest(
        claim_id=GEOGRAPHY_CLAIM_REFORESTATION.claim_id,
        target_agents=["geography"],
        evidence_gap="Need higher temporal resolution comparison focusing on northern sector",
        refined_queries=[
            "Focus NDVI analysis on the northern sector of the Central Kalimantan site",
            "Compare 2020 baseline with 2022 and 2024 imagery for staged progress",
        ],
        required_evidence="Temporal comparison showing progressive reforestation across multiple years",
    )
    return create_base_state(
        claims=[GEOGRAPHY_CLAIM_REFORESTATION],
        routing_plan=[ROUTING_GEO_REFORESTATION],
        reinvestigation_requests=[reinvestigation],
        iteration_count=1,
    )


def create_state_with_no_geo_claims() -> SibylState:
    """Create a state where no claims are routed to the geography agent."""
    return create_base_state(
        claims=[GOVERNANCE_CLAIM],
        routing_plan=[ROUTING_NO_GEO],
    )
