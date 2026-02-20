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


# ============================================================================
# Academic/Research Agent Sample Claims (FRD 9)
# ============================================================================

ACADEMIC_CLAIM_METHODOLOGY = Claim(
    claim_id="claim-acad-001",
    text="Our total Scope 3 emissions were 12.4 million tonnes CO2e in FY2024, calculated using spend-based methodology for upstream categories and life-cycle analysis for downstream. Measurement follows GHG Protocol Corporate Value Chain Standard.",
    page_number=67,
    claim_type="quantitative",
    ifrs_paragraphs=["S2.29(a)(iii)", "S1.46"],
    priority="high",
    source_location={"source_context": "Section 7.2 GHG Emissions"},
    agent_reasoning="Methodology claim about Scope 3 emissions requiring academic validation of spend-based method.",
)

ACADEMIC_CLAIM_CERTIFICATION = Claim(
    claim_id="claim-acad-002",
    text="100% of our electricity comes from certified renewable sources via I-REC certificates purchased through the International REC Standard registry.",
    page_number=34,
    claim_type="environmental",
    ifrs_paragraphs=["S2.29(b)"],
    priority="high",
    source_location={"source_context": "Section 6.3 Renewable Energy"},
    agent_reasoning="Certification claim requiring validation of I-REC certificate legitimacy and additionality.",
)

ACADEMIC_CLAIM_SBTI = Claim(
    claim_id="claim-acad-003",
    text="We have committed to achieving net-zero emissions by 2050, validated by the Science Based Targets initiative. Our near-term target is a 42% reduction in Scope 1 and 2 emissions by 2030 from a 2019 baseline, aligned with a 1.5°C pathway.",
    page_number=8,
    claim_type="strategic",
    ifrs_paragraphs=["S2.33", "S2.14(a)(iv)"],
    priority="high",
    source_location={"source_context": "Executive Summary"},
    agent_reasoning="SBTi validation claim requiring verification of target alignment and validation status.",
)

ACADEMIC_CLAIM_BENCHMARK = Claim(
    claim_id="claim-acad-004",
    text="Our Scope 1 emission intensity is 0.15 tCO2e per $1M revenue, placing us among the top quartile of performers in the manufacturing sector.",
    page_number=50,
    claim_type="quantitative",
    ifrs_paragraphs=["S2.29(e)", "S2.30"],
    priority="medium",
    source_location={"source_context": "Section 7.3 Emission Intensity"},
    agent_reasoning="Benchmark claim requiring comparison against industry sector averages.",
)

ACADEMIC_CLAIM_RESEARCH = Claim(
    claim_id="claim-acad-005",
    text="Our new carbon capture and utilisation technology at the Surabaya plant reduces facility emissions by 30%, based on pilot testing completed in 2024.",
    page_number=72,
    claim_type="environmental",
    ifrs_paragraphs=["S2.14(a)"],
    priority="medium",
    source_location={"source_context": "Section 9.1 Technology Innovation"},
    agent_reasoning="Technology effectiveness claim requiring validation against peer-reviewed research.",
)

ACADEMIC_CLAIM_OFFSET = Claim(
    claim_id="claim-acad-006",
    text="We offset 50,000 tonnes CO2e through Verified Carbon Standard (VCS) REDD+ forestry projects in the Amazon basin.",
    page_number=58,
    claim_type="environmental",
    ifrs_paragraphs=["S2.29(d)"],
    priority="high",
    source_location={"source_context": "Section 7.5 Carbon Offsets"},
    agent_reasoning="Carbon offset claim requiring validation of VCS standard and additionality assessment.",
)


# ============================================================================
# Academic/Research Agent Routing Assignments
# ============================================================================

ROUTING_ACADEMIC_METHODOLOGY = RoutingAssignment(
    claim_id="claim-acad-001",
    assigned_agents=["academic", "data_metrics"],
    reasoning="Methodology claim requiring academic validation and quantitative check.",
)

ROUTING_ACADEMIC_CERTIFICATION = RoutingAssignment(
    claim_id="claim-acad-002",
    assigned_agents=["academic"],
    reasoning="Certification claim requiring academic research on I-REC legitimacy.",
)

ROUTING_ACADEMIC_SBTI = RoutingAssignment(
    claim_id="claim-acad-003",
    assigned_agents=["academic", "legal"],
    reasoning="SBTi target claim requiring framework validation and compliance assessment.",
)

ROUTING_ACADEMIC_BENCHMARK = RoutingAssignment(
    claim_id="claim-acad-004",
    assigned_agents=["academic", "data_metrics"],
    reasoning="Benchmark claim requiring sector comparison research.",
)

ROUTING_ACADEMIC_RESEARCH = RoutingAssignment(
    claim_id="claim-acad-005",
    assigned_agents=["academic"],
    reasoning="Technology effectiveness claim needing peer-reviewed research validation.",
)

ROUTING_ACADEMIC_OFFSET = RoutingAssignment(
    claim_id="claim-acad-006",
    assigned_agents=["academic", "news_media"],
    reasoning="Carbon offset claim requiring academic validation and news verification.",
)

ROUTING_NO_ACADEMIC = RoutingAssignment(
    claim_id="claim-gov-001",
    assigned_agents=["legal"],
    reasoning="Governance claim not assigned to academic agent.",
)


# ============================================================================
# Academic/Research Claims Lists
# ============================================================================

ACADEMIC_CLAIMS = [
    ACADEMIC_CLAIM_METHODOLOGY,
    ACADEMIC_CLAIM_CERTIFICATION,
    ACADEMIC_CLAIM_SBTI,
    ACADEMIC_CLAIM_BENCHMARK,
    ACADEMIC_CLAIM_RESEARCH,
    ACADEMIC_CLAIM_OFFSET,
]

ACADEMIC_ROUTING_ASSIGNMENTS = [
    ROUTING_ACADEMIC_METHODOLOGY,
    ROUTING_ACADEMIC_CERTIFICATION,
    ROUTING_ACADEMIC_SBTI,
    ROUTING_ACADEMIC_BENCHMARK,
    ROUTING_ACADEMIC_RESEARCH,
    ROUTING_ACADEMIC_OFFSET,
]


# ============================================================================
# Geography Agent Sample Claims (FRD 10)
# ============================================================================

GEOGRAPHY_CLAIM_REFORESTATION = Claim(
    claim_id="claim-geo-reforest-001",
    text="Our reforestation initiative in Central Kalimantan, Borneo has successfully restored 5,000 hectares of degraded peatland forest since 2020, in partnership with local conservation organizations.",
    page_number=55,
    claim_type="environmental",
    ifrs_paragraphs=["S2.14(a)"],
    priority="high",
    source_location={"source_context": "Section 7.3 Nature-Based Solutions"},
    agent_reasoning="Geographic environmental claim requiring satellite imagery verification of reforestation.",
)

GEOGRAPHY_CLAIM_FACILITY = Claim(
    claim_id="claim-geo-facility-001",
    text="Our Surabaya manufacturing facility operates on a 50-hectare site with dedicated green space comprising 30% of the total area.",
    page_number=22,
    claim_type="geographic",
    ifrs_paragraphs=[],
    priority="medium",
    source_location={"source_context": "Section 3.4 Operations Overview"},
    agent_reasoning="Facility claim requiring satellite imagery verification of site characteristics.",
)

GEOGRAPHY_CLAIM_DEFORESTATION = Claim(
    claim_id="claim-geo-deforest-001",
    text="We have achieved zero deforestation across our palm oil supply chain in Sumatra since 2022, verified by annual satellite monitoring.",
    page_number=60,
    claim_type="environmental",
    ifrs_paragraphs=["S2.25(b)"],
    priority="high",
    source_location={"source_context": "Section 8.2 Deforestation Policy"},
    agent_reasoning="Deforestation claim requiring temporal satellite imagery comparison.",
)

GEOGRAPHY_CLAIM_SOLAR = Claim(
    claim_id="claim-geo-solar-001",
    text="We installed 200MW of solar capacity across our Chennai campus in 2024, covering approximately 400 hectares of rooftop and ground-mounted panels.",
    page_number=40,
    claim_type="environmental",
    ifrs_paragraphs=["S2.14(a)"],
    priority="medium",
    source_location={"source_context": "Section 6.2 Renewable Energy"},
    agent_reasoning="Solar installation claim verifiable via satellite land cover analysis.",
)


# ============================================================================
# Geography Agent Routing Assignments
# ============================================================================

ROUTING_GEO_REFORESTATION = RoutingAssignment(
    claim_id="claim-geo-reforest-001",
    assigned_agents=["geography", "news_media"],
    reasoning="Reforestation claim requiring satellite imagery and news verification.",
)

ROUTING_GEO_FACILITY = RoutingAssignment(
    claim_id="claim-geo-facility-001",
    assigned_agents=["geography"],
    reasoning="Facility claim requiring satellite imagery analysis.",
)

ROUTING_GEO_DEFORESTATION = RoutingAssignment(
    claim_id="claim-geo-deforest-001",
    assigned_agents=["geography"],
    reasoning="Deforestation claim requiring temporal satellite comparison.",
)

ROUTING_GEO_SOLAR = RoutingAssignment(
    claim_id="claim-geo-solar-001",
    assigned_agents=["geography"],
    reasoning="Solar installation claim verifiable via satellite land cover analysis.",
)

ROUTING_NO_GEO = RoutingAssignment(
    claim_id="claim-gov-001",
    assigned_agents=["legal"],
    reasoning="Governance claim not assigned to geography agent.",
)


# ============================================================================
# Geography Claims Lists
# ============================================================================

GEOGRAPHY_CLAIMS = [
    GEOGRAPHY_CLAIM_REFORESTATION,
    GEOGRAPHY_CLAIM_FACILITY,
    GEOGRAPHY_CLAIM_DEFORESTATION,
    GEOGRAPHY_CLAIM_SOLAR,
]

GEOGRAPHY_ROUTING_ASSIGNMENTS = [
    ROUTING_GEO_REFORESTATION,
    ROUTING_GEO_FACILITY,
    ROUTING_GEO_DEFORESTATION,
    ROUTING_GEO_SOLAR,
]


# ============================================================================
# Judge Agent Sample Claims and Findings (FRD 11)
# ============================================================================

from app.agents.state import AgentFinding

# Sample claim for Judge Agent testing
JUDGE_CLAIM_TRANSITION_PLAN = Claim(
    claim_id="claim-judge-001",
    text="Our transition plan assumes a 2.5% annual GDP growth rate, carbon price of $75/tCO2e by 2030, "
    "and availability of carbon capture and storage technology by 2028. We target net-zero by 2050 "
    "with interim milestones: 20% reduction by 2025, 42% by 2030, 70% by 2040.",
    page_number=45,
    claim_type="strategic",
    ifrs_paragraphs=["S2.14(a)(iv)", "S1.33"],
    priority="high",
    source_location={"source_context": "Section 5.2 Transition Plan"},
    agent_reasoning="Strategic claim about transition plan with key assumptions, dependencies, and timeline.",
)

JUDGE_CLAIM_EMISSIONS = Claim(
    claim_id="claim-judge-002",
    text="We reduced Scope 1 emissions by 30% from 2020 baseline, achieving 2.3M tCO2e in FY2024.",
    page_number=67,
    claim_type="quantitative",
    ifrs_paragraphs=["S2.29(a)(i)"],
    priority="high",
    source_location={"source_context": "Section 7.2 GHG Emissions"},
    agent_reasoning="Quantitative emissions reduction claim requiring verification.",
)

JUDGE_CLAIM_GOVERNANCE = Claim(
    claim_id="claim-judge-003",
    text="The Board's Sustainability Committee oversees climate-related risks with quarterly reviews.",
    page_number=12,
    claim_type="legal_governance",
    ifrs_paragraphs=["S2.6", "S1.27(a)"],
    priority="medium",
    source_location={"source_context": "Section 3.1 Governance"},
    agent_reasoning="Governance claim about board oversight.",
)

# Sample AgentFindings for Judge Agent testing

FINDING_LEGAL_SUPPORTING = AgentFinding(
    finding_id="finding-legal-001",
    agent_name="legal",
    claim_id="claim-judge-001",
    evidence_type="ifrs_compliance",
    summary="Claim meets S2.14(a)(iv) requirements with all sub-requirements addressed. "
    "Key assumptions, dependencies, and timeline are clearly documented.",
    details={
        "ifrs_mappings": [
            {
                "paragraph_id": "S2.14(a)(iv)",
                "compliance_status": "fully_addressed",
                "sub_requirements": [
                    {"requirement": "key_assumptions", "addressed": True},
                    {"requirement": "dependencies", "addressed": True},
                    {"requirement": "timeline", "addressed": True},
                ],
            }
        ],
    },
    supports_claim=True,
    confidence="high",
    iteration=1,
)

FINDING_GEOGRAPHY_SUPPORTING = AgentFinding(
    finding_id="finding-geo-001",
    agent_name="geography",
    claim_id="claim-judge-001",
    evidence_type="satellite_analysis",
    summary="Satellite imagery confirms the stated environmental conditions and location characteristics.",
    details={
        "ndvi_estimate": 0.72,
        "change_detected": True,
        "observed_features": ["vegetation_increase", "land_restoration"],
    },
    supports_claim=True,
    confidence="high",
    iteration=1,
)

FINDING_ACADEMIC_SUPPORTING = AgentFinding(
    finding_id="finding-academic-001",
    agent_name="academic",
    claim_id="claim-judge-001",
    evidence_type="methodology_validation",
    summary="Transition plan methodology aligns with SBTi 1.5C pathway requirements and peer-reviewed research.",
    details={
        "sbti_validation_status": "validated",
        "standard_alignment": "aligned",
    },
    supports_claim=True,
    confidence="high",
    iteration=1,
)

FINDING_NEWS_SUPPORTING = AgentFinding(
    finding_id="finding-news-001",
    agent_name="news_media",
    claim_id="claim-judge-001",
    evidence_type="news_corroboration",
    summary="Multiple Tier 2 news sources corroborate the company's transition plan commitment.",
    details={
        "source_tier": 2,
        "sources_found": 3,
    },
    supports_claim=True,
    confidence="medium",
    iteration=1,
)

FINDING_DATA_METRICS_SUPPORTING = AgentFinding(
    finding_id="finding-dm-001",
    agent_name="data_metrics",
    claim_id="claim-judge-001",
    evidence_type="mathematical_consistency",
    summary="Target achievability assessment shows 4.8% annual reduction rate is consistent with sector averages.",
    details={
        "target_achievability": "achievable",
        "required_annual_rate": 4.8,
    },
    supports_claim=True,
    confidence="high",
    iteration=1,
)

FINDING_NEWS_CONTRADICTING = AgentFinding(
    finding_id="finding-news-contradict-001",
    agent_name="news_media",
    claim_id="claim-judge-002",
    evidence_type="news_contradiction",
    summary="Investigative journalism reports regulatory action against the company for emissions violations, "
    "contradicting the claimed 30% reduction.",
    details={
        "source_tier": 1,
        "contradiction_type": "direct",
        "confidence": 0.92,
    },
    supports_claim=False,
    confidence="high",
    iteration=1,
)

FINDING_DATA_METRICS_CONTRADICTING = AgentFinding(
    finding_id="finding-dm-contradict-001",
    agent_name="data_metrics",
    claim_id="claim-judge-002",
    evidence_type="mathematical_inconsistency",
    summary="Mathematical analysis shows reported figures are inconsistent with claimed reduction percentage.",
    details={
        "check_name": "yoy_percentage",
        "result": "fail",
        "discrepancy_percent": 15.3,
    },
    supports_claim=False,
    confidence="high",
    iteration=1,
)

FINDING_LEGAL_WEAK = AgentFinding(
    finding_id="finding-legal-weak-001",
    agent_name="legal",
    claim_id="claim-judge-003",
    evidence_type="ifrs_compliance",
    summary="Partial IFRS compliance - governance claim mentioned but lacks specific details.",
    details={
        "ifrs_mappings": [
            {
                "paragraph_id": "S2.6",
                "compliance_status": "partially_addressed",
            }
        ],
    },
    supports_claim=True,
    confidence="low",
    iteration=1,
)

FINDING_ACADEMIC_INCONCLUSIVE = AgentFinding(
    finding_id="finding-academic-inconclusive-001",
    agent_name="academic",
    claim_id="claim-judge-003",
    evidence_type="research_support",
    summary="Peer-reviewed research partially supports the claim but with caveats about methodology.",
    details={
        "research_consensus": "mixed",
        "limitations": ["Limited sample size", "Methodology concerns"],
    },
    supports_claim=None,
    confidence="medium",
    iteration=1,
)

# Judge Agent Routing Assignments

ROUTING_JUDGE_TRANSITION = RoutingAssignment(
    claim_id="claim-judge-001",
    assigned_agents=["legal", "academic", "news_media"],
    reasoning="Strategic transition plan claim requiring multi-agent verification.",
)

ROUTING_JUDGE_EMISSIONS = RoutingAssignment(
    claim_id="claim-judge-002",
    assigned_agents=["legal", "data_metrics", "news_media"],
    reasoning="Quantitative emissions claim requiring calculation and news verification.",
)

ROUTING_JUDGE_GOVERNANCE = RoutingAssignment(
    claim_id="claim-judge-003",
    assigned_agents=["legal"],
    reasoning="Governance claim requiring legal compliance assessment.",
)
