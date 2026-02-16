"""Sample claim data for testing.

Provides pre-defined claims of various types for testing the Legal Agent.
"""

from app.agents.state import Claim, RoutingAssignment


# ============================================================================
# Sample Claims by Type
# ============================================================================

GOVERNANCE_CLAIM = Claim(
    claim_id="claim-gov-001",
    text="The Board's Sustainability Committee, chaired by an independent director, has primary oversight responsibility for climate-related matters. Committee members include directors with energy sector experience and climate risk management expertise. The Committee meets quarterly and reports to the full Board on climate matters at each regular Board meeting. 15% of executive bonus is tied to achievement of annual GHG reduction targets.",
    page_number=12,
    claim_type="legal_governance",
    ifrs_paragraphs=["S2.6", "S1.27(a)"],
    priority="high",
    source_location={"source_context": "Section 3.1 Governance"},
    agent_reasoning="Governance claim about board oversight, competencies, reporting frequency, and remuneration link."
)

STRATEGIC_CLAIM_TRANSITION_PLAN = Claim(
    claim_id="claim-str-001",
    text="Our transition plan assumes a 2.5% annual GDP growth rate, carbon price of $75/tCO2e by 2030, and availability of carbon capture and storage technology by 2028. The plan relies on policy support for carbon pricing and deployment of renewable energy infrastructure. We target net-zero by 2050 with interim milestones: 20% reduction by 2025, 42% by 2030, 70% by 2040.",
    page_number=45,
    claim_type="strategic",
    ifrs_paragraphs=["S2.14(a)(iv)", "S1.33"],
    priority="high",
    source_location={"source_context": "Section 5.2 Transition Plan"},
    agent_reasoning="Strategic claim about transition plan with key assumptions, dependencies, and timeline."
)

STRATEGIC_CLAIM_INCOMPLETE = Claim(
    claim_id="claim-str-002",
    text="We have developed a transition plan to achieve net-zero emissions by 2050, with interim targets in 2030 and 2040.",
    page_number=48,
    claim_type="strategic",
    ifrs_paragraphs=["S2.14(a)(iv)"],
    priority="high",
    source_location={"source_context": "Section 5.3 Climate Strategy"},
    agent_reasoning="Strategic claim mentions transition plan but lacks key assumptions and dependencies."
)

METRICS_CLAIM_SCOPE_3 = Claim(
    claim_id="claim-met-001",
    text="Our total Scope 3 emissions were 12.4 million tonnes CO2e in FY2024, calculated using spend-based methodology for upstream categories and life-cycle analysis for downstream. Measurement follows GHG Protocol Corporate Value Chain Standard.",
    page_number=67,
    claim_type="quantitative",
    ifrs_paragraphs=["S2.29(a)(iii)", "S1.46"],
    priority="high",
    source_location={"source_context": "Section 7.2 GHG Emissions"},
    agent_reasoning="Metrics claim about Scope 3 emissions with methodology disclosure."
)

METRICS_CLAIM_COMPLETE = Claim(
    claim_id="claim-met-002",
    text="Scope 1 emissions: 450,000 tCO2e. Scope 2 emissions (location-based): 1.2 million tCO2e; (market-based): 800,000 tCO2e. Scope 3 emissions: 12.4 million tCO2e, with Category 1 (Purchased goods and services) at 5.1 million tCO2e, Category 11 (Use of sold products) at 4.8 million tCO2e, and remaining categories at 2.5 million tCO2e combined.",
    page_number=68,
    claim_type="quantitative",
    ifrs_paragraphs=["S2.29(a)", "S2.29(a)(i)", "S2.29(a)(ii)", "S2.29(a)(iii)"],
    priority="high",
    source_location={"source_context": "Section 7.2 GHG Emissions Table"},
    agent_reasoning="Comprehensive GHG emissions claim with all scopes and category breakdown."
)

RISK_MANAGEMENT_CLAIM = Claim(
    claim_id="claim-rm-001",
    text="Annual climate risk assessment conducted using TCFD framework, covering physical and transition risks across operations. Climate opportunities identified through strategic planning process, including low-carbon product development and energy efficiency investments. Climate risks are integrated into the enterprise risk register and reviewed by the Risk Committee alongside financial and operational risks.",
    page_number=38,
    claim_type="legal_governance",
    ifrs_paragraphs=["S2.25(a)", "S2.26", "S1.41(a)", "S1.41(d)"],
    priority="medium",
    source_location={"source_context": "Section 4.1 Risk Management"},
    agent_reasoning="Risk management claim about identification, assessment, and ERM integration."
)

NO_TRANSITION_PLAN_CLAIM = Claim(
    claim_id="claim-str-003",
    text="We are committed to reducing our environmental impact and have set ambitious sustainability goals for the future.",
    page_number=5,
    claim_type="strategic",
    ifrs_paragraphs=["S2.14"],
    priority="low",
    source_location={"source_context": "Executive Summary"},
    agent_reasoning="Vague strategic claim with no specific transition plan details."
)


# ============================================================================
# Sample Routing Assignments
# ============================================================================

ROUTING_GOVERNANCE = RoutingAssignment(
    claim_id="claim-gov-001",
    assigned_agents=["legal"],
    reasoning="Governance claim about board oversight and climate competencies."
)

ROUTING_STRATEGIC = RoutingAssignment(
    claim_id="claim-str-001",
    assigned_agents=["legal"],
    reasoning="Strategic transition plan claim requiring IFRS compliance assessment."
)

ROUTING_STRATEGIC_INCOMPLETE = RoutingAssignment(
    claim_id="claim-str-002",
    assigned_agents=["legal"],
    reasoning="Strategic claim about transition plan requiring compliance assessment."
)

ROUTING_METRICS = RoutingAssignment(
    claim_id="claim-met-001",
    assigned_agents=["legal", "data_metrics"],
    reasoning="Metrics claim requiring both legal compliance and quantitative validation."
)

ROUTING_METRICS_COMPLETE = RoutingAssignment(
    claim_id="claim-met-002",
    assigned_agents=["legal", "data_metrics"],
    reasoning="Comprehensive GHG emissions claim requiring validation."
)

ROUTING_RISK_MANAGEMENT = RoutingAssignment(
    claim_id="claim-rm-001",
    assigned_agents=["legal"],
    reasoning="Risk management claim requiring IFRS compliance assessment."
)

ROUTING_NO_LEGAL = RoutingAssignment(
    claim_id="claim-geo-001",
    assigned_agents=["geography"],
    reasoning="Geographic claim about facility location - not assigned to legal."
)


# ============================================================================
# Sample Claims Lists
# ============================================================================

ALL_SAMPLE_CLAIMS = [
    GOVERNANCE_CLAIM,
    STRATEGIC_CLAIM_TRANSITION_PLAN,
    STRATEGIC_CLAIM_INCOMPLETE,
    METRICS_CLAIM_SCOPE_3,
    METRICS_CLAIM_COMPLETE,
    RISK_MANAGEMENT_CLAIM,
    NO_TRANSITION_PLAN_CLAIM,
]

LEGAL_ASSIGNED_CLAIMS = [
    GOVERNANCE_CLAIM,
    STRATEGIC_CLAIM_TRANSITION_PLAN,
    STRATEGIC_CLAIM_INCOMPLETE,
    METRICS_CLAIM_SCOPE_3,
    METRICS_CLAIM_COMPLETE,
    RISK_MANAGEMENT_CLAIM,
]

ALL_ROUTING_ASSIGNMENTS = [
    ROUTING_GOVERNANCE,
    ROUTING_STRATEGIC,
    ROUTING_STRATEGIC_INCOMPLETE,
    ROUTING_METRICS,
    ROUTING_METRICS_COMPLETE,
    ROUTING_RISK_MANAGEMENT,
    ROUTING_NO_LEGAL,
]
