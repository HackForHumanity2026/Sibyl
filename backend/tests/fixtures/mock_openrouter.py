"""Mock OpenRouter API responses for testing.

Provides pre-defined LLM responses for legal agent testing without
consuming actual API credits.
"""

import json

# ============================================================================
# Mock LLM Response Data
# ============================================================================

MOCK_COMPLIANCE_FULLY_ADDRESSED = {
    "ifrs_mappings": [
        {
            "paragraph_id": "S2.14(a)(iv)",
            "pillar": "strategy",
            "section": "Decision-Making",
            "requirement_text": "An entity shall disclose its transition plan, including information about: key assumptions; dependencies; timeline.",
            "sub_requirements": [
                {
                    "requirement": "key_assumptions",
                    "addressed": True,
                    "evidence": "The report states: 'Our transition plan assumes a 2.5% annual GDP growth rate, carbon price of $75/tCO2e by 2030, and availability of carbon capture and storage technology by 2028.'"
                },
                {
                    "requirement": "dependencies",
                    "addressed": True,
                    "evidence": "The report discloses: 'Our transition plan relies on policy support for carbon pricing, market demand for low-carbon products, and deployment of renewable energy infrastructure.'"
                },
                {
                    "requirement": "timeline",
                    "addressed": True,
                    "evidence": "The report includes a detailed timeline showing milestones: 2025 (20% reduction), 2030 (42% reduction), 2040 (70% reduction), 2050 (net-zero)."
                }
            ],
            "compliance_status": "fully_addressed",
            "s1_counterpart": "S1.33"
        }
    ],
    "evidence": [
        "The report contains detailed transition plan on pages 45-52.",
        "Key assumptions explicitly stated including carbon price trajectory.",
        "Dependencies on policy and technology clearly documented.",
        "Timeline with interim milestones to 2050 provided."
    ],
    "gaps": [],
    "confidence": "high"
}


MOCK_COMPLIANCE_PARTIALLY_ADDRESSED = {
    "ifrs_mappings": [
        {
            "paragraph_id": "S2.14(a)(iv)",
            "pillar": "strategy",
            "section": "Decision-Making",
            "requirement_text": "An entity shall disclose its transition plan, including information about: key assumptions; dependencies; timeline.",
            "sub_requirements": [
                {
                    "requirement": "key_assumptions",
                    "addressed": False,
                    "evidence": None,
                    "gap_reason": "The report mentions a transition plan but does not disclose the key assumptions used in developing it (e.g., economic growth, carbon price, technology availability)."
                },
                {
                    "requirement": "dependencies",
                    "addressed": False,
                    "evidence": None,
                    "gap_reason": "The report does not disclose dependencies on which the transition plan relies."
                },
                {
                    "requirement": "timeline",
                    "addressed": True,
                    "evidence": "The report includes a timeline: 'We aim to achieve net-zero by 2050 with interim targets in 2030 and 2040.'"
                }
            ],
            "compliance_status": "partially_addressed",
            "s1_counterpart": "S1.33"
        }
    ],
    "evidence": [
        "Report mentions transition plan with timeline.",
        "Net-zero target of 2050 stated with interim milestones."
    ],
    "gaps": [
        "Missing key assumptions sub-requirement",
        "Missing dependencies sub-requirement"
    ],
    "confidence": "high"
}


MOCK_COMPLIANCE_NOT_ADDRESSED = {
    "ifrs_mappings": [
        {
            "paragraph_id": "S2.14(a)(iv)",
            "pillar": "strategy",
            "section": "Decision-Making",
            "requirement_text": "An entity shall disclose its transition plan, including information about: key assumptions; dependencies; timeline.",
            "sub_requirements": [
                {
                    "requirement": "key_assumptions",
                    "addressed": False,
                    "evidence": None,
                    "gap_reason": "No transition plan disclosed."
                },
                {
                    "requirement": "dependencies",
                    "addressed": False,
                    "evidence": None,
                    "gap_reason": "No transition plan disclosed."
                },
                {
                    "requirement": "timeline",
                    "addressed": False,
                    "evidence": None,
                    "gap_reason": "No transition plan disclosed."
                }
            ],
            "compliance_status": "not_addressed",
            "s1_counterpart": "S1.33"
        }
    ],
    "evidence": [],
    "gaps": [
        "Transition plan not disclosed",
        "All S2.14(a)(iv) sub-requirements missing"
    ],
    "confidence": "high"
}


MOCK_GOVERNANCE_ASSESSMENT = {
    "ifrs_mappings": [
        {
            "paragraph_id": "S2.6",
            "pillar": "governance",
            "section": "Climate Governance Body Oversight",
            "requirement_text": "Disclose information about the governance body(s) or individual(s) responsible for oversight of climate-related risks and opportunities.",
            "sub_requirements": [
                {
                    "requirement": "identify_climate_governance_body",
                    "addressed": True,
                    "evidence": "The Board's Sustainability Committee, chaired by an independent director, has primary oversight responsibility for climate-related matters."
                },
                {
                    "requirement": "climate_competencies",
                    "addressed": True,
                    "evidence": "Committee members include directors with energy sector experience and climate risk management expertise."
                },
                {
                    "requirement": "climate_reporting_frequency",
                    "addressed": True,
                    "evidence": "The Committee meets quarterly and reports to the full Board on climate matters at each regular Board meeting."
                },
                {
                    "requirement": "climate_target_remuneration",
                    "addressed": True,
                    "evidence": "15% of executive bonus is tied to achievement of annual GHG reduction targets."
                }
            ],
            "compliance_status": "fully_addressed",
            "s1_counterpart": "S1.27(a)"
        }
    ],
    "evidence": [
        "Sustainability Committee identified with clear mandate.",
        "Director competencies in climate matters disclosed.",
        "Quarterly reporting cadence established.",
        "Remuneration link to climate targets quantified."
    ],
    "gaps": [],
    "confidence": "high"
}


MOCK_METRICS_ASSESSMENT = {
    "ifrs_mappings": [
        {
            "paragraph_id": "S2.29(a)(iii)",
            "pillar": "metrics_targets",
            "section": "Scope 3 Emissions",
            "requirement_text": "Scope 3 greenhouse gas emissions by category, measured in accordance with the GHG Protocol.",
            "sub_requirements": [
                {
                    "requirement": "scope_3_total",
                    "addressed": True,
                    "evidence": "Total Scope 3 emissions: 12.4 million tonnes CO2e in FY2024."
                },
                {
                    "requirement": "scope_3_by_category",
                    "addressed": False,
                    "evidence": None,
                    "gap_reason": "The report discloses total Scope 3 emissions but does not break down by the 15 GHG Protocol categories."
                },
                {
                    "requirement": "scope_3_methodology",
                    "addressed": True,
                    "evidence": "Scope 3 emissions calculated using spend-based methodology for upstream categories and life-cycle analysis for downstream."
                },
                {
                    "requirement": "ghg_protocol_alignment",
                    "addressed": True,
                    "evidence": "Measurement follows GHG Protocol Corporate Value Chain Standard."
                }
            ],
            "compliance_status": "partially_addressed",
            "s1_counterpart": "S1.46"
        }
    ],
    "evidence": [
        "Total Scope 3 emissions disclosed with methodology.",
        "GHG Protocol alignment stated."
    ],
    "gaps": [
        "Scope 3 emissions not disclosed by category"
    ],
    "confidence": "high"
}


MOCK_RISK_MANAGEMENT_ASSESSMENT = {
    "ifrs_mappings": [
        {
            "paragraph_id": "S2.25(a)",
            "pillar": "risk_management",
            "section": "Climate Risk Identification",
            "requirement_text": "The processes and related policies the entity uses to identify climate-related risks and opportunities.",
            "sub_requirements": [
                {
                    "requirement": "climate_risk_identification_process",
                    "addressed": True,
                    "evidence": "Annual climate risk assessment conducted using TCFD framework, covering physical and transition risks across operations."
                },
                {
                    "requirement": "climate_opportunity_identification",
                    "addressed": True,
                    "evidence": "Climate opportunities identified through strategic planning process, including low-carbon product development and energy efficiency investments."
                }
            ],
            "compliance_status": "fully_addressed",
            "s1_counterpart": "S1.41(a)"
        },
        {
            "paragraph_id": "S2.26",
            "pillar": "risk_management",
            "section": "Climate Risk Integration",
            "requirement_text": "How climate risk processes are integrated into overall risk management.",
            "sub_requirements": [
                {
                    "requirement": "climate_erm_integration",
                    "addressed": True,
                    "evidence": "Climate risks are integrated into the enterprise risk register and reviewed by the Risk Committee alongside financial and operational risks."
                }
            ],
            "compliance_status": "fully_addressed",
            "s1_counterpart": "S1.41(d)"
        }
    ],
    "evidence": [
        "Climate risk identification process using TCFD framework.",
        "Integration with enterprise risk management demonstrated."
    ],
    "gaps": [],
    "confidence": "high"
}


MOCK_GAP_DETECTION_CHUNK_COVERAGE = {
    "chunks_cover_paragraph": False,
    "coverage_analysis": "The report content does not address the requirements of this paragraph. No relevant disclosure found.",
    "coverage_status": "fully_unaddressed"
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_mock_compliance_response(compliance_level: str = "fully_addressed") -> str:
    """Get a mock LLM response for compliance assessment.
    
    Args:
        compliance_level: One of "fully_addressed", "partially_addressed", "not_addressed"
        
    Returns:
        JSON string of the mock response
    """
    responses = {
        "fully_addressed": MOCK_COMPLIANCE_FULLY_ADDRESSED,
        "partially_addressed": MOCK_COMPLIANCE_PARTIALLY_ADDRESSED,
        "not_addressed": MOCK_COMPLIANCE_NOT_ADDRESSED,
    }
    return json.dumps(responses.get(compliance_level, MOCK_COMPLIANCE_FULLY_ADDRESSED))


def get_mock_governance_response() -> str:
    """Get a mock LLM response for governance claim assessment."""
    return json.dumps(MOCK_GOVERNANCE_ASSESSMENT)


def get_mock_metrics_response() -> str:
    """Get a mock LLM response for metrics claim assessment."""
    return json.dumps(MOCK_METRICS_ASSESSMENT)


def get_mock_risk_management_response() -> str:
    """Get a mock LLM response for risk management claim assessment."""
    return json.dumps(MOCK_RISK_MANAGEMENT_ASSESSMENT)
