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
