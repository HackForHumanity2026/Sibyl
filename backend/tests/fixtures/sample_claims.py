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
# Data Metrics Agent Sample Claims
# ============================================================================

DATA_METRICS_CLAIM_SCOPE_TOTALS = Claim(
    claim_id="claim-dm-001",
    text="Scope 1: 2.3M tCO2e, Scope 2: 1.1M tCO2e, Scope 3: 8.5M tCO2e, Total: 12.0M tCO2e",
    page_number=45,
    claim_type="quantitative",
    ifrs_paragraphs=["S2.29(a)(i)", "S2.29(a)(ii)", "S2.29(a)(iii)"],
    priority="high",
    source_location={"source_context": "Section 7.1 GHG Emissions Summary"},
    agent_reasoning="Quantitative claim with scope emissions totals requiring consistency check."
)

DATA_METRICS_CLAIM_SCOPE_MISMATCH = Claim(
    claim_id="claim-dm-002",
    text="Scope 1: 2.3M tCO2e, Scope 2: 1.1M tCO2e, Scope 3: 8.5M tCO2e, Total: 15.0M tCO2e",
    page_number=46,
    claim_type="quantitative",
    ifrs_paragraphs=["S2.29(a)(i)", "S2.29(a)(ii)", "S2.29(a)(iii)"],
    priority="high",
    source_location={"source_context": "Section 7.1 GHG Emissions Summary"},
    agent_reasoning="Quantitative claim with INCORRECT total - scope sum does not match reported total."
)

DATA_METRICS_CLAIM_YOY_CHANGE = Claim(
    claim_id="claim-dm-003",
    text="Our emissions decreased 6.1% from 2.45M tCO2e in FY2023 to 2.3M tCO2e in FY2024",
    page_number=47,
    claim_type="quantitative",
    ifrs_paragraphs=["S2.29"],
    priority="high",
    source_location={"source_context": "Section 7.2 Year-over-Year Performance"},
    agent_reasoning="Quantitative claim with YoY percentage change requiring validation."
)

DATA_METRICS_CLAIM_TARGET = Claim(
    claim_id="claim-dm-004",
    text="42% reduction in Scope 1+2 emissions by 2030 from 2019 baseline of 2.5M tCO2e",
    page_number=52,
    claim_type="quantitative",
    ifrs_paragraphs=["S2.33", "S2.34", "S2.35"],
    priority="high",
    source_location={"source_context": "Section 8.1 Climate Targets"},
    agent_reasoning="Target claim requiring achievability assessment and IFRS S2.33-36 compliance."
)

DATA_METRICS_CLAIM_TARGET_AGGRESSIVE = Claim(
    claim_id="claim-dm-005",
    text="90% reduction in total emissions by 2029 from 2024 baseline of 5.0M tCO2e",
    page_number=53,
    claim_type="quantitative",
    ifrs_paragraphs=["S2.33", "S2.34"],
    priority="high",
    source_location={"source_context": "Section 8.1 Climate Targets"},
    agent_reasoning="Aggressive target claim that may be mathematically questionable."
)

DATA_METRICS_CLAIM_INTENSITY = Claim(
    claim_id="claim-dm-006",
    text="Emission intensity: 0.5 tCO2e per $1M revenue for our manufacturing operations",
    page_number=48,
    claim_type="quantitative",
    ifrs_paragraphs=["S2.29(e)", "S2.30"],
    priority="medium",
    source_location={"source_context": "Section 7.3 Emission Intensity"},
    agent_reasoning="Intensity metric claim requiring benchmark comparison."
)

DATA_METRICS_CLAIM_MULTIPLE_SCOPES = Claim(
    claim_id="claim-dm-007",
    text="Total GHG emissions of 14.2M tCO2e, comprising Scope 1 (2.1M), Scope 2 location-based (1.5M), Scope 2 market-based (1.2M), and Scope 3 (10.6M).",
    page_number=49,
    claim_type="quantitative",
    ifrs_paragraphs=["S2.29(a)", "S2.29(a)(i)", "S2.29(a)(ii)", "S2.29(a)(iii)"],
    priority="high",
    source_location={"source_context": "Section 7.1 Complete GHG Profile"},
    agent_reasoning="Complex emissions claim with both location and market-based Scope 2."
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


# Data Metrics Agent Routing Assignments
ROUTING_DATA_METRICS_SCOPE = RoutingAssignment(
    claim_id="claim-dm-001",
    assigned_agents=["data_metrics"],
    reasoning="Scope emissions claim requiring consistency validation."
)

ROUTING_DATA_METRICS_SCOPE_MISMATCH = RoutingAssignment(
    claim_id="claim-dm-002",
    assigned_agents=["data_metrics"],
    reasoning="Scope emissions claim with potential mismatch."
)

ROUTING_DATA_METRICS_YOY = RoutingAssignment(
    claim_id="claim-dm-003",
    assigned_agents=["data_metrics"],
    reasoning="YoY percentage change claim requiring calculation validation."
)

ROUTING_DATA_METRICS_TARGET = RoutingAssignment(
    claim_id="claim-dm-004",
    assigned_agents=["data_metrics"],
    reasoning="Target claim requiring achievability assessment."
)

ROUTING_DATA_METRICS_TARGET_AGGRESSIVE = RoutingAssignment(
    claim_id="claim-dm-005",
    assigned_agents=["data_metrics"],
    reasoning="Aggressive target claim requiring critical assessment."
)

ROUTING_DATA_METRICS_INTENSITY = RoutingAssignment(
    claim_id="claim-dm-006",
    assigned_agents=["data_metrics", "academic"],
    reasoning="Intensity claim requiring benchmark comparison."
)

ROUTING_DATA_METRICS_MULTIPLE = RoutingAssignment(
    claim_id="claim-dm-007",
    assigned_agents=["data_metrics", "legal"],
    reasoning="Complex emissions claim requiring both quantitative and compliance validation."
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


# Data Metrics Claims Lists
DATA_METRICS_CLAIMS = [
    DATA_METRICS_CLAIM_SCOPE_TOTALS,
    DATA_METRICS_CLAIM_SCOPE_MISMATCH,
    DATA_METRICS_CLAIM_YOY_CHANGE,
    DATA_METRICS_CLAIM_TARGET,
    DATA_METRICS_CLAIM_TARGET_AGGRESSIVE,
    DATA_METRICS_CLAIM_INTENSITY,
    DATA_METRICS_CLAIM_MULTIPLE_SCOPES,
]

DATA_METRICS_ROUTING_ASSIGNMENTS = [
    ROUTING_DATA_METRICS_SCOPE,
    ROUTING_DATA_METRICS_SCOPE_MISMATCH,
    ROUTING_DATA_METRICS_YOY,
    ROUTING_DATA_METRICS_TARGET,
    ROUTING_DATA_METRICS_TARGET_AGGRESSIVE,
    ROUTING_DATA_METRICS_INTENSITY,
    ROUTING_DATA_METRICS_MULTIPLE,
]


# ============================================================================
# News/Media Agent Sample Claims
# ============================================================================

NEWS_CLAIM_EMISSIONS_REDUCTION = Claim(
    claim_id="claim-news-001",
    text="Our total Scope 1 emissions decreased by 12% year-over-year, from 2.45 million tonnes CO2e in FY2023 to 2.15 million tonnes CO2e in FY2024, reflecting significant investments in operational efficiency and fuel switching.",
    page_number=42,
    claim_type="quantitative",
    ifrs_paragraphs=["S2.29(a)(i)"],
    priority="high",
    source_location={"source_context": "Section 6.1 GHG Emissions Performance"},
    agent_reasoning="Quantitative emissions claim requiring public news verification."
)

NEWS_CLAIM_CERTIFICATION = Claim(
    claim_id="claim-news-002",
    text="Our Singapore facility has achieved ISO 14001:2015 certification for environmental management, with annual surveillance audits conducted by an accredited third-party certifier.",
    page_number=28,
    claim_type="legal_governance",
    ifrs_paragraphs=["S2.6"],
    priority="medium",
    source_location={"source_context": "Section 4.2 Environmental Management"},
    agent_reasoning="Certification claim requiring external verification via public sources."
)

NEWS_CLAIM_CONTROVERSY = Claim(
    claim_id="claim-news-003",
    text="We maintain strong environmental compliance across all operations, with no material environmental violations or enforcement actions during the reporting period.",
    page_number=35,
    claim_type="legal_governance",
    ifrs_paragraphs=["S2.25(a)"],
    priority="high",
    source_location={"source_context": "Section 5.1 Regulatory Compliance"},
    agent_reasoning="Compliance claim that may be contradicted by public news of violations."
)

NEWS_CLAIM_NET_ZERO_TARGET = Claim(
    claim_id="claim-news-004",
    text="We have committed to achieving net-zero greenhouse gas emissions by 2050, with interim targets of 42% reduction by 2030 from our 2019 baseline.",
    page_number=8,
    claim_type="strategic",
    ifrs_paragraphs=["S2.14(a)(iv)", "S2.33"],
    priority="high",
    source_location={"source_context": "Executive Summary"},
    agent_reasoning="Strategic target claim that should be verifiable through public announcements."
)

NEWS_CLAIM_REFORESTATION = Claim(
    claim_id="claim-news-005",
    text="Our reforestation initiative in Central Kalimantan, Borneo has successfully restored 5,000 hectares of degraded peatland forest since 2020, in partnership with local conservation organizations.",
    page_number=55,
    claim_type="environmental",
    ifrs_paragraphs=["S2.14(a)"],
    priority="medium",
    source_location={"source_context": "Section 7.3 Nature-Based Solutions"},
    agent_reasoning="Environmental initiative claim requiring verification via news and NGO sources."
)

NEWS_CLAIM_SUPPLY_CHAIN = Claim(
    claim_id="claim-news-006",
    text="We have achieved 100% traceability for palm oil in our supply chain, with all suppliers audited against RSPO certification requirements.",
    page_number=62,
    claim_type="environmental",
    ifrs_paragraphs=["S2.25(b)"],
    priority="high",
    source_location={"source_context": "Section 8.1 Supply Chain Sustainability"},
    agent_reasoning="Supply chain claim that may be verified or contradicted by investigative reporting."
)


# ============================================================================
# News/Media Agent Routing Assignments
# ============================================================================

ROUTING_NEWS_EMISSIONS = RoutingAssignment(
    claim_id="claim-news-001",
    assigned_agents=["news_media", "data_metrics"],
    reasoning="Quantitative emissions claim requiring both news verification and data validation."
)

ROUTING_NEWS_CERTIFICATION = RoutingAssignment(
    claim_id="claim-news-002",
    assigned_agents=["news_media", "legal"],
    reasoning="Certification claim requiring news verification and legal compliance assessment."
)

ROUTING_NEWS_CONTROVERSY = RoutingAssignment(
    claim_id="claim-news-003",
    assigned_agents=["news_media"],
    reasoning="Compliance claim specifically requiring news/media investigation for violations."
)

ROUTING_NEWS_NET_ZERO = RoutingAssignment(
    claim_id="claim-news-004",
    assigned_agents=["news_media", "legal"],
    reasoning="Strategic target claim requiring news verification of public commitments."
)

ROUTING_NEWS_REFORESTATION = RoutingAssignment(
    claim_id="claim-news-005",
    assigned_agents=["news_media", "geography"],
    reasoning="Reforestation claim requiring news verification and geographic validation."
)

ROUTING_NEWS_SUPPLY_CHAIN = RoutingAssignment(
    claim_id="claim-news-006",
    assigned_agents=["news_media"],
    reasoning="Supply chain claim requiring investigation of public reporting on supply chain issues."
)

ROUTING_NO_NEWS = RoutingAssignment(
    claim_id="claim-gov-001",
    assigned_agents=["legal"],
    reasoning="Governance claim not assigned to news_media agent."
)


# ============================================================================
# News/Media Claims Lists
# ============================================================================

NEWS_MEDIA_CLAIMS = [
    NEWS_CLAIM_EMISSIONS_REDUCTION,
    NEWS_CLAIM_CERTIFICATION,
    NEWS_CLAIM_CONTROVERSY,
    NEWS_CLAIM_NET_ZERO_TARGET,
    NEWS_CLAIM_REFORESTATION,
    NEWS_CLAIM_SUPPLY_CHAIN,
]

NEWS_MEDIA_ROUTING_ASSIGNMENTS = [
    ROUTING_NEWS_EMISSIONS,
    ROUTING_NEWS_CERTIFICATION,
    ROUTING_NEWS_CONTROVERSY,
    ROUTING_NEWS_NET_ZERO,
    ROUTING_NEWS_REFORESTATION,
    ROUTING_NEWS_SUPPLY_CHAIN,
]
