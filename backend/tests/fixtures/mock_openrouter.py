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
# Data Metrics Agent Mock Responses
# ============================================================================

MOCK_SCOPE_ADDITION_PASS = {
    "claim_id": "claim-dm-001",
    "consistency_checks": [
        {
            "check_name": "scope_addition",
            "claim_id": "claim-dm-001",
            "result": "pass",
            "details": {
                "scope1": 2300000,
                "scope2": 1100000,
                "scope3": 8500000,
                "calculated_total": 11900000,
                "reported_total": 12000000,
                "discrepancy_percent": 0.83
            },
            "severity": "info",
            "message": "Scope 1+2+3 equals reported total within 1% tolerance (0.83% discrepancy)"
        }
    ],
    "unit_validation": {
        "units_valid": True,
        "methodology_aligned": True,
        "conversion_factors_appropriate": True,
        "issues": []
    },
    "benchmark_comparison": None,
    "target_achievability": None,
    "historical_consistency": None,
    "ifrs_compliance": {
        "claim_id": "claim-dm-001",
        "ifrs_paragraphs": ["S2.29(a)(i)", "S2.29(a)(ii)", "S2.29(a)(iii)"],
        "compliance_status": "compliant",
        "missing_requirements": [],
        "compliance_details": {
            "scope1_disclosed": True,
            "scope2_disclosed": True,
            "scope3_disclosed": True,
            "methodology_stated": True
        },
        "reasoning": "Claim discloses all three emission scopes with totals, meeting S2.29(a) requirements."
    },
    "summary": "All scope emissions correctly sum to total within tolerance. IFRS S2.29 compliant.",
    "supports_claim": True,
    "confidence": "high",
    "missing_data": []
}


MOCK_SCOPE_ADDITION_FAIL = {
    "claim_id": "claim-dm-002",
    "consistency_checks": [
        {
            "check_name": "scope_addition",
            "claim_id": "claim-dm-002",
            "result": "fail",
            "details": {
                "scope1": 2300000,
                "scope2": 1100000,
                "scope3": 8500000,
                "calculated_total": 11900000,
                "reported_total": 15000000,
                "discrepancy_percent": 26.05
            },
            "severity": "critical",
            "message": "Scope 1+2+3 does not equal reported total. Discrepancy: 26.05% (exceeds 1% tolerance)"
        }
    ],
    "unit_validation": {
        "units_valid": True,
        "methodology_aligned": True,
        "conversion_factors_appropriate": True,
        "issues": []
    },
    "benchmark_comparison": None,
    "target_achievability": None,
    "historical_consistency": None,
    "ifrs_compliance": {
        "claim_id": "claim-dm-002",
        "ifrs_paragraphs": ["S2.29(a)(i)", "S2.29(a)(ii)", "S2.29(a)(iii)"],
        "compliance_status": "partially_compliant",
        "missing_requirements": ["Internal consistency of reported totals"],
        "compliance_details": {
            "scope1_disclosed": True,
            "scope2_disclosed": True,
            "scope3_disclosed": True,
            "totals_consistent": False
        },
        "reasoning": "Scopes are disclosed but total is inconsistent with sum of scopes."
    },
    "summary": "Critical: Scope totals do not add up. 26% discrepancy between sum and reported total.",
    "supports_claim": False,
    "confidence": "high",
    "missing_data": []
}


MOCK_YOY_PERCENTAGE_PASS = {
    "claim_id": "claim-dm-003",
    "consistency_checks": [
        {
            "check_name": "yoy_percentage",
            "claim_id": "claim-dm-003",
            "result": "pass",
            "details": {
                "prior_value": 2450000,
                "current_value": 2300000,
                "reported_change_percent": -6.1,
                "calculated_change_percent": -6.12,
                "discrepancy_pp": 0.02
            },
            "severity": "info",
            "message": "Reported YoY change (6.1% decrease) matches calculated change within 0.1pp tolerance"
        }
    ],
    "unit_validation": {
        "units_valid": True,
        "methodology_aligned": True,
        "conversion_factors_appropriate": True,
        "issues": []
    },
    "benchmark_comparison": None,
    "target_achievability": None,
    "historical_consistency": {
        "claim_id": "claim-dm-003",
        "current_year": 2024,
        "current_value": 2300000,
        "prior_years": [{"year": 2023, "value": 2450000}],
        "yoy_change_consistent": True,
        "trend_consistent": True,
        "methodology_changes": [],
        "unexplained_deviations": [],
        "assessment": "consistent",
        "reasoning": "YoY change of 6.1% matches calculated value and continues downward trend."
    },
    "ifrs_compliance": {
        "claim_id": "claim-dm-003",
        "ifrs_paragraphs": ["S2.29"],
        "compliance_status": "compliant",
        "missing_requirements": [],
        "compliance_details": {},
        "reasoning": "Year-over-year comparison with prior period as required by S2.29."
    },
    "summary": "YoY percentage change verified. 6.1% decrease is mathematically accurate.",
    "supports_claim": True,
    "confidence": "high",
    "missing_data": []
}


MOCK_TARGET_ACHIEVABILITY_ACHIEVABLE = {
    "claim_id": "claim-dm-004",
    "consistency_checks": [
        {
            "check_name": "target_calculation",
            "claim_id": "claim-dm-004",
            "result": "pass",
            "details": {
                "baseline_value": 2500000,
                "target_percentage": 42,
                "target_value_calculated": 1450000,
                "years_to_target": 11,
                "required_annual_rate": 4.8
            },
            "severity": "info",
            "message": "42% reduction from 2.5M tCO2e requires 4.8% annual reduction rate"
        }
    ],
    "unit_validation": {
        "units_valid": True,
        "methodology_aligned": True,
        "conversion_factors_appropriate": True,
        "issues": []
    },
    "benchmark_comparison": None,
    "target_achievability": {
        "claim_id": "claim-dm-004",
        "target_type": "absolute_reduction",
        "baseline_year": 2019,
        "baseline_value": 2500000,
        "target_year": 2030,
        "target_value": 1450000,
        "target_percentage": 42.0,
        "required_annual_reduction_rate": 4.8,
        "achievability_assessment": "achievable",
        "interim_targets_consistent": True,
        "ifrs_s2_33_36_compliant": True,
        "missing_ifrs_requirements": [],
        "reasoning": "4.8% annual reduction rate is consistent with sector averages for companies with similar transition plans. SBTi 1.5C pathway requires ~4.2% annual reduction."
    },
    "historical_consistency": None,
    "ifrs_compliance": {
        "claim_id": "claim-dm-004",
        "ifrs_paragraphs": ["S2.33", "S2.34", "S2.35", "S2.36"],
        "compliance_status": "compliant",
        "missing_requirements": [],
        "compliance_details": {
            "target_disclosed": True,
            "baseline_disclosed": True,
            "timeline_disclosed": True,
            "scope_specified": True
        },
        "reasoning": "Target disclosure meets S2.33-36 requirements with baseline, timeline, and scope."
    },
    "summary": "42% reduction target by 2030 is achievable with 4.8% annual rate. IFRS S2.33-36 compliant.",
    "supports_claim": True,
    "confidence": "high",
    "missing_data": []
}


MOCK_TARGET_ACHIEVABILITY_QUESTIONABLE = {
    "claim_id": "claim-dm-005",
    "consistency_checks": [
        {
            "check_name": "target_calculation",
            "claim_id": "claim-dm-005",
            "result": "pass",
            "details": {
                "baseline_value": 5000000,
                "target_percentage": 90,
                "target_value_calculated": 500000,
                "years_to_target": 5,
                "required_annual_rate": 36.9
            },
            "severity": "warning",
            "message": "90% reduction in 5 years requires 36.9% annual reduction rate - significantly above historical norms"
        }
    ],
    "unit_validation": {
        "units_valid": True,
        "methodology_aligned": True,
        "conversion_factors_appropriate": True,
        "issues": []
    },
    "benchmark_comparison": None,
    "target_achievability": {
        "claim_id": "claim-dm-005",
        "target_type": "absolute_reduction",
        "baseline_year": 2024,
        "baseline_value": 5000000,
        "target_year": 2029,
        "target_value": 500000,
        "target_percentage": 90.0,
        "required_annual_reduction_rate": 36.9,
        "achievability_assessment": "questionable",
        "interim_targets_consistent": None,
        "ifrs_s2_33_36_compliant": False,
        "missing_ifrs_requirements": ["Interim milestones", "Transition plan details"],
        "reasoning": "36.9% annual reduction is far beyond any documented sector achievement. Average is 3-5% annually. This target appears unrealistic without extraordinary circumstances."
    },
    "historical_consistency": None,
    "ifrs_compliance": {
        "claim_id": "claim-dm-005",
        "ifrs_paragraphs": ["S2.33", "S2.34"],
        "compliance_status": "partially_compliant",
        "missing_requirements": ["S2.34 interim milestones", "S2.35 transition plan"],
        "compliance_details": {
            "target_disclosed": True,
            "baseline_disclosed": True,
            "interim_milestones": False,
            "transition_plan": False
        },
        "reasoning": "Target lacks interim milestones and transition plan required by S2.34-35."
    },
    "summary": "90% reduction in 5 years is mathematically questionable (36.9% annual rate). Missing IFRS requirements.",
    "supports_claim": False,
    "confidence": "high",
    "missing_data": ["Interim targets", "Transition plan details"]
}


MOCK_INTENSITY_BENCHMARK = {
    "claim_id": "claim-dm-006",
    "consistency_checks": [],
    "unit_validation": {
        "units_valid": True,
        "methodology_aligned": True,
        "conversion_factors_appropriate": True,
        "issues": []
    },
    "benchmark_comparison": {
        "metric_name": "Emission intensity",
        "reported_value": 0.5,
        "reported_unit": "tCO2e per $1M revenue",
        "sector_average": 0.8,
        "sector_unit": "tCO2e per $1M revenue",
        "benchmark_source": "Industry sector benchmark data",
        "assessment": "plausible",
        "reasoning": "Reported intensity of 0.5 tCO2e/$M is 37.5% below sector average of 0.8 tCO2e/$M. This is within plausible range for companies with advanced efficiency measures."
    },
    "target_achievability": None,
    "historical_consistency": None,
    "ifrs_compliance": {
        "claim_id": "claim-dm-006",
        "ifrs_paragraphs": ["S2.29(e)", "S2.30"],
        "compliance_status": "compliant",
        "missing_requirements": [],
        "compliance_details": {
            "intensity_metric_disclosed": True,
            "unit_appropriate": True,
            "methodology_clear": True
        },
        "reasoning": "Intensity metric meets S2.29(e) requirements for cross-entity comparison."
    },
    "summary": "Intensity metric of 0.5 tCO2e/$M is plausible (37.5% below sector average).",
    "supports_claim": True,
    "confidence": "medium",
    "missing_data": []
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


# ============================================================================
# Data Metrics Helper Functions
# ============================================================================


def get_mock_data_metrics_response(scenario: str = "scope_addition_pass") -> str:
    """Get a mock LLM response for data metrics validation.
    
    Args:
        scenario: One of:
            - "scope_addition_pass"
            - "scope_addition_fail"
            - "yoy_percentage_pass"
            - "target_achievable"
            - "target_questionable"
            - "intensity_benchmark"
        
    Returns:
        JSON string of the mock response
    """
    responses = {
        "scope_addition_pass": MOCK_SCOPE_ADDITION_PASS,
        "scope_addition_fail": MOCK_SCOPE_ADDITION_FAIL,
        "yoy_percentage_pass": MOCK_YOY_PERCENTAGE_PASS,
        "target_achievable": MOCK_TARGET_ACHIEVABILITY_ACHIEVABLE,
        "target_questionable": MOCK_TARGET_ACHIEVABILITY_QUESTIONABLE,
        "intensity_benchmark": MOCK_INTENSITY_BENCHMARK,
    }
    return json.dumps(responses.get(scenario, MOCK_SCOPE_ADDITION_PASS))


def get_mock_scope_addition_response(pass_fail: str = "pass") -> str:
    """Get a mock LLM response for scope addition check.
    
    Args:
        pass_fail: Either "pass" or "fail"
        
    Returns:
        JSON string of the mock response
    """
    if pass_fail == "fail":
        return json.dumps(MOCK_SCOPE_ADDITION_FAIL)
    return json.dumps(MOCK_SCOPE_ADDITION_PASS)


def get_mock_target_response(achievability: str = "achievable") -> str:
    """Get a mock LLM response for target achievability assessment.
    
    Args:
        achievability: Either "achievable" or "questionable"
        
    Returns:
        JSON string of the mock response
    """
    if achievability == "questionable":
        return json.dumps(MOCK_TARGET_ACHIEVABILITY_QUESTIONABLE)
    return json.dumps(MOCK_TARGET_ACHIEVABILITY_ACHIEVABLE)


# ============================================================================
# News/Media Agent Mock Responses
# ============================================================================

MOCK_NEWS_QUERY_CONSTRUCTION = {
    "company_specific": '"ExxonMobil" Scope 1 emissions reduction 2024',
    "industry_wide": "oil gas industry emissions reduction targets 2024",
    "controversy": '"ExxonMobil" emissions (violation OR investigation OR greenwashing)',
}

MOCK_NEWS_QUERY_CONSTRUCTION_CERTIFICATION = {
    "company_specific": '"TestCorp" ISO 14001 certification environmental management',
    "industry_wide": "manufacturing ISO 14001 environmental certification trends",
    "controversy": '"TestCorp" certification (revoked OR violation OR fraud)',
}

MOCK_NEWS_CREDIBILITY_TIER_1 = {
    "tier": 1,
    "reasoning": "Major regulatory enforcement source (SEC filing)",
}

MOCK_NEWS_CREDIBILITY_TIER_2 = {
    "tier": 2,
    "reasoning": "Established news organization with editorial standards",
}

MOCK_NEWS_CREDIBILITY_TIER_3 = {
    "tier": 3,
    "reasoning": "Company press release distributed via wire service",
}

MOCK_NEWS_CREDIBILITY_TIER_4 = {
    "tier": 4,
    "reasoning": "Personal blog without editorial oversight or verification",
}

MOCK_NEWS_CONTRADICTION_DIRECT = {
    "contradicts": True,
    "contradiction_type": "direct",
    "confidence": 0.92,
    "explanation": "The source explicitly states emissions increased by 8%, directly contradicting the claim of a 12% decrease.",
}

MOCK_NEWS_CONTRADICTION_CONTEXTUAL = {
    "contradicts": True,
    "contradiction_type": "contextual",
    "confidence": 0.78,
    "explanation": "While the source does not directly dispute the numbers, it reveals that the reported reductions are primarily due to asset divestiture rather than operational improvements, undermining the claim's implication of genuine sustainability progress.",
}

MOCK_NEWS_CONTRADICTION_OMISSION = {
    "contradicts": True,
    "contradiction_type": "omission",
    "confidence": 0.85,
    "explanation": "The source reveals an ongoing EPA investigation into emissions reporting at the company that was not disclosed in the sustainability report, representing a material omission.",
}

MOCK_NEWS_CONTRADICTION_TIMELINE = {
    "contradicts": True,
    "contradiction_type": "timeline",
    "confidence": 0.88,
    "explanation": "The source reports the company delayed its net-zero target from 2050 to 2060, contradicting the sustainability report which states a 2050 target.",
}

MOCK_NEWS_NO_CONTRADICTION = {
    "contradicts": False,
    "contradiction_type": None,
    "confidence": 0.75,
    "explanation": "The source corroborates the claim, confirming the reported emissions reductions and noting positive third-party verification.",
}

MOCK_NEWS_RELEVANCE_SUMMARY = "This Reuters article discusses the company's annual sustainability report, confirming the reported 12% reduction in Scope 1 emissions. The source cites third-party verification of the emissions data."


# ============================================================================
# News/Media Agent Helper Functions
# ============================================================================

def get_mock_news_query_response(claim_type: str = "emissions") -> str:
    """Get a mock LLM response for search query construction.
    
    Args:
        claim_type: Either "emissions" or "certification"
        
    Returns:
        JSON string of the mock response
    """
    if claim_type == "certification":
        return json.dumps(MOCK_NEWS_QUERY_CONSTRUCTION_CERTIFICATION)
    return json.dumps(MOCK_NEWS_QUERY_CONSTRUCTION)


def get_mock_news_credibility_response(tier: int = 2) -> str:
    """Get a mock LLM response for source credibility classification.
    
    Args:
        tier: Credibility tier (1-4)
        
    Returns:
        JSON string of the mock response
    """
    tier_responses = {
        1: MOCK_NEWS_CREDIBILITY_TIER_1,
        2: MOCK_NEWS_CREDIBILITY_TIER_2,
        3: MOCK_NEWS_CREDIBILITY_TIER_3,
        4: MOCK_NEWS_CREDIBILITY_TIER_4,
    }
    return json.dumps(tier_responses.get(tier, MOCK_NEWS_CREDIBILITY_TIER_2))


def get_mock_news_contradiction_response(
    contradiction_type: str | None = None
) -> str:
    """Get a mock LLM response for contradiction detection.
    
    Args:
        contradiction_type: One of "direct", "contextual", "omission", "timeline", 
                          or None for no contradiction
        
    Returns:
        JSON string of the mock response
    """
    if contradiction_type is None:
        return json.dumps(MOCK_NEWS_NO_CONTRADICTION)
    
    type_responses = {
        "direct": MOCK_NEWS_CONTRADICTION_DIRECT,
        "contextual": MOCK_NEWS_CONTRADICTION_CONTEXTUAL,
        "omission": MOCK_NEWS_CONTRADICTION_OMISSION,
        "timeline": MOCK_NEWS_CONTRADICTION_TIMELINE,
    }
    return json.dumps(type_responses.get(contradiction_type, MOCK_NEWS_NO_CONTRADICTION))


def get_mock_news_relevance_summary() -> str:
    """Get a mock relevance summary response.
    
    Returns:
        Plain text summary string
    """
    return MOCK_NEWS_RELEVANCE_SUMMARY


# ============================================================================
# Academic/Research Agent Mock Responses (FRD 9)
# ============================================================================

MOCK_ACADEMIC_QUERY_METHODOLOGY = {
    "queries": [
        "GHG Protocol Scope 3 spend-based method calculation guidance",
        "spend-based carbon footprint methodology peer-reviewed accuracy",
        "GHG Protocol Corporate Value Chain Standard Scope 3 categories",
    ]
}

MOCK_ACADEMIC_QUERY_CERTIFICATION = {
    "queries": [
        "I-REC international renewable energy certificate standard legitimacy",
        "renewable energy certificate additionality peer-reviewed research",
        "I-REC greenwashing risks academic study",
    ]
}

MOCK_ACADEMIC_QUERY_SBTI = {
    "queries": [
        "SBTi net-zero standard validation criteria requirements",
        "SBTi 1.5C pathway manufacturing sector targets",
        "science based targets initiative validated companies database",
    ]
}

MOCK_ACADEMIC_QUERY_BENCHMARK = {
    "queries": [
        "manufacturing sector Scope 1 emission intensity benchmark 2024",
        "CDP manufacturing disclosure emission intensity average",
        "emission intensity per revenue manufacturing peer-reviewed",
    ]
}

MOCK_ACADEMIC_QUERY_RESEARCH = {
    "queries": [
        "carbon capture utilisation technology emission reduction effectiveness peer-reviewed",
        "carbon capture CCS CCU 30% reduction research study",
        "industrial carbon capture pilot results journal",
    ]
}

MOCK_ACADEMIC_ANALYSIS_METHODOLOGY = {
    "investigation_type": "methodology_validation",
    "supports_claim": True,
    "confidence": 0.85,
    "standard_alignment": "aligned",
    "research_consensus": "The spend-based method is a recognized approach under the GHG Protocol Scope 3 Standard for estimating upstream emissions when activity-based data is unavailable. Peer-reviewed research indicates accuracy within ±30% for initial estimates.",
    "limitations": [
        "Higher uncertainty compared to activity-based methods",
        "Requires accurate spend data and appropriate emission factors"
    ],
    "references": [
        {
            "type": "standard_document",
            "title": "GHG Protocol Scope 3 Standard",
            "url": "https://ghgprotocol.org/scope-3-standard",
            "snippet": "The spend-based method uses financial data to estimate emissions by multiplying spend by sector-specific emission factors."
        },
        {
            "type": "academic_paper",
            "title": "Accuracy of Spend-Based Carbon Footprinting",
            "authors": "Smith et al.",
            "publication_date": "2023",
            "url": "https://example.com/paper1",
            "snippet": "Spend-based methods show acceptable accuracy for Scope 3 estimates within ±30%.",
            "source_credibility": 1
        }
    ],
    "summary": "The claimed spend-based method for Scope 3 emissions aligns with GHG Protocol guidance. Peer-reviewed research supports the method's use for initial estimates but notes higher uncertainty than activity-based methods."
}

MOCK_ACADEMIC_ANALYSIS_CERTIFICATION = {
    "investigation_type": "certification_validation",
    "supports_claim": None,
    "confidence": 0.70,
    "legitimacy_assessment": "legitimate",
    "research_consensus": "I-RECs are recognized certificates but academic research questions additionality when certificates are unbundled from physical electricity. Studies suggest I-RECs may not drive additional renewable energy investment.",
    "limitations": [
        "Additionality concerns for unbundled certificates",
        "Greenwashing risks identified in academic literature"
    ],
    "references": [
        {
            "type": "standard_document",
            "title": "I-REC Standard Registry",
            "url": "https://irecstandard.org",
            "snippet": "The I-REC Standard provides a standardized framework for tracking renewable energy attributes."
        },
        {
            "type": "academic_paper",
            "title": "Renewable Energy Certificates and Additionality: A Critical Review",
            "authors": "Jones et al.",
            "publication_date": "2024",
            "url": "https://example.com/paper2",
            "snippet": "I-RECs show limited additionality when purchased separately from physical electricity delivery.",
            "source_credibility": 1
        }
    ],
    "summary": "The I-REC certification is recognized by the I-REC Standard registry. However, academic research raises concerns about additionality and greenwashing risks for unbundled certificates."
}

MOCK_ACADEMIC_ANALYSIS_SBTI = {
    "investigation_type": "sbti_validation",
    "supports_claim": True,
    "confidence": 0.80,
    "sbti_validation_status": "validated",
    "standard_alignment": "aligned",
    "research_consensus": "The 42% reduction by 2030 from a 2019 baseline aligns with SBTi 1.5°C pathway requirements for the manufacturing sector, which requires approximately 4.2% annual reduction.",
    "limitations": [
        "SBTi validation database should be checked directly for latest status",
        "Scope 3 targets may have different requirements"
    ],
    "references": [
        {
            "type": "standard_document",
            "title": "SBTi Target Setting Manual",
            "url": "https://sciencebasedtargets.org/resources/files/SBTi-Target-Setting-Manual.pdf",
            "snippet": "Near-term targets must be aligned with 1.5°C or well-below 2°C pathways."
        }
    ],
    "summary": "The claimed science-based target aligns with SBTi framework requirements. The 42% reduction by 2030 is consistent with 1.5°C pathway for the sector."
}

MOCK_ACADEMIC_ANALYSIS_BENCHMARK = {
    "investigation_type": "benchmark_comparison",
    "supports_claim": True,
    "confidence": 0.75,
    "plausibility": "plausible",
    "benchmark_range": {
        "min": 0.10,
        "max": 0.25,
        "median": 0.18,
        "reported": 0.15,
        "unit": "tCO2e per $1M revenue"
    },
    "research_consensus": "Manufacturing sector Scope 1 emission intensities range from 0.10-0.25 tCO2e/$1M revenue based on CDP disclosures and peer-reviewed research. The reported 0.15 is within the plausible range.",
    "limitations": [
        "Benchmark range varies by sub-sector",
        "Revenue-based intensity can be affected by pricing changes"
    ],
    "references": [
        {
            "type": "cdp_disclosure",
            "title": "CDP Manufacturing Sector Disclosure Report 2024",
            "url": "https://cdp.net/manufacturing-2024",
            "snippet": "Sector average Scope 1 intensity: 0.18 tCO2e/$1M revenue.",
            "source_credibility": 2
        }
    ],
    "summary": "The reported Scope 1 emission intensity of 0.15 tCO2e/$M is within the plausible range for manufacturing (0.10-0.25). Top quartile claim requires further verification."
}

MOCK_ACADEMIC_ANALYSIS_RESEARCH = {
    "investigation_type": "research_support",
    "supports_claim": None,
    "confidence": 0.60,
    "research_consensus": "Peer-reviewed research on carbon capture and utilisation technologies reports emission reduction ranges of 15-40% depending on technology maturity, facility type, and CO2 utilisation pathway. The claimed 30% falls within published ranges but is at the upper end for pilot-stage projects.",
    "limitations": [
        "Pilot results may not scale to full operations",
        "Long-term performance data is limited",
        "Effectiveness depends on specific CCU technology variant"
    ],
    "references": [
        {
            "type": "academic_paper",
            "title": "Carbon Capture and Utilisation: A Review of Emission Reduction Potential",
            "authors": "Chen et al.",
            "publication_date": "2024",
            "url": "https://example.com/paper3",
            "snippet": "CCU technologies demonstrate 15-40% emission reduction potential at pilot scale.",
            "source_credibility": 1
        }
    ],
    "summary": "Peer-reviewed research partially supports the claimed 30% reduction. The value falls within published ranges (15-40%) but is optimistic for pilot-stage technology."
}


def get_mock_academic_query_response(investigation_type: str = "methodology") -> str:
    """Get a mock LLM response for academic query construction."""
    responses = {
        "methodology": MOCK_ACADEMIC_QUERY_METHODOLOGY,
        "certification": MOCK_ACADEMIC_QUERY_CERTIFICATION,
        "sbti": MOCK_ACADEMIC_QUERY_SBTI,
        "benchmark": MOCK_ACADEMIC_QUERY_BENCHMARK,
        "research": MOCK_ACADEMIC_QUERY_RESEARCH,
    }
    return json.dumps(responses.get(investigation_type, MOCK_ACADEMIC_QUERY_METHODOLOGY))


def get_mock_academic_analysis_response(investigation_type: str = "methodology") -> str:
    """Get a mock LLM response for academic analysis."""
    responses = {
        "methodology": MOCK_ACADEMIC_ANALYSIS_METHODOLOGY,
        "certification": MOCK_ACADEMIC_ANALYSIS_CERTIFICATION,
        "sbti": MOCK_ACADEMIC_ANALYSIS_SBTI,
        "benchmark": MOCK_ACADEMIC_ANALYSIS_BENCHMARK,
        "research": MOCK_ACADEMIC_ANALYSIS_RESEARCH,
    }
    return json.dumps(responses.get(investigation_type, MOCK_ACADEMIC_ANALYSIS_METHODOLOGY))


# ============================================================================
# Geography Agent Mock Responses (FRD 10)
# ============================================================================

MOCK_GEO_LOCATION_EXTRACTION = {
    "location_name": "Central Kalimantan, Borneo, Indonesia",
    "coordinates": [-1.5, 113.5],
    "time_range": ["2020-01-01", "2024-12-31"],
    "area_description": "5,000 hectares",
    "confidence": 0.9,
}

MOCK_GEO_LOCATION_FACILITY = {
    "location_name": "Surabaya, Indonesia",
    "coordinates": [-7.2575, 112.7521],
    "time_range": None,
    "area_description": "50 hectares",
    "confidence": 0.85,
}

MOCK_GEO_SATELLITE_ANALYSIS_REFORESTATION = {
    "supports_claim": True,
    "confidence": 0.82,
    "observed_features": ["dense_forest", "reforestation_pattern", "peatland_restoration"],
    "ndvi_estimate": 0.68,
    "change_detected": True,
    "change_area_hectares": 4200.0,
    "reasoning": "Satellite imagery analysis shows significant vegetation increase in the specified area of Central Kalimantan between 2020 and 2024. NDVI values increased from approximately 0.35 to 0.68, consistent with forest restoration. The estimated area of change (~4,200 hectares) is close to but slightly below the claimed 5,000 hectares.",
    "limitations": ["Seasonal variation may affect NDVI", "Cloud cover in some scenes limits precision"],
}

MOCK_GEO_SATELLITE_ANALYSIS_FACILITY = {
    "supports_claim": True,
    "confidence": 0.75,
    "observed_features": ["industrial_facility", "urban_area", "green_space"],
    "ndvi_estimate": 0.25,
    "change_detected": None,
    "change_area_hectares": None,
    "reasoning": "Satellite imagery confirms the presence of an industrial facility in the Surabaya area. Some green space is visible but the claimed 30% coverage cannot be precisely verified at Sentinel-2 resolution.",
    "limitations": ["10m resolution insufficient for precise green space measurement", "Building shadows may affect classification"],
}

MOCK_GEO_SATELLITE_ANALYSIS_DEFORESTATION = {
    "supports_claim": True,
    "confidence": 0.88,
    "observed_features": ["intact_forest", "no_clearing_detected"],
    "ndvi_estimate": 0.72,
    "change_detected": False,
    "change_area_hectares": 0.0,
    "reasoning": "Temporal comparison of satellite imagery from 2022 to 2024 shows no significant deforestation in the specified Sumatra region. Forest cover remains consistent with NDVI values above 0.65 throughout the period.",
    "limitations": ["Small-scale selective logging may not be detectable at Sentinel-2 resolution"],
}


def get_mock_geo_location_response(location_type: str = "reforestation") -> str:
    """Get a mock LLM response for location extraction."""
    responses = {
        "reforestation": MOCK_GEO_LOCATION_EXTRACTION,
        "facility": MOCK_GEO_LOCATION_FACILITY,
    }
    return json.dumps(responses.get(location_type, MOCK_GEO_LOCATION_EXTRACTION))


def get_mock_geo_analysis_response(analysis_type: str = "reforestation") -> str:
    """Get a mock LLM response for satellite imagery analysis."""
    responses = {
        "reforestation": MOCK_GEO_SATELLITE_ANALYSIS_REFORESTATION,
        "facility": MOCK_GEO_SATELLITE_ANALYSIS_FACILITY,
        "deforestation": MOCK_GEO_SATELLITE_ANALYSIS_DEFORESTATION,
    }
    return json.dumps(responses.get(analysis_type, MOCK_GEO_SATELLITE_ANALYSIS_REFORESTATION))


# ============================================================================
# Judge Agent Mock Responses (FRD 11)
# ============================================================================

MOCK_JUDGE_VERDICT_VERIFIED = {
    "verdict": "verified",
    "reasoning": "Claim is VERIFIED. Multiple independent sources corroborate:\n"
    "- Legal Agent: Claim meets S2.14(a)(iv) requirements with all sub-requirements addressed.\n"
    "- Geography Agent: Satellite imagery confirms the stated location and conditions.\n"
    "- Academic Agent: Methodology aligns with peer-reviewed standards.\n"
    "Evidence is consistent, high-quality, and sufficient. No contradictions found.",
    "confidence": "high",
}

MOCK_JUDGE_VERDICT_UNVERIFIED = {
    "verdict": "unverified",
    "reasoning": "Claim is UNVERIFIED. No external evidence found by any specialist agent:\n"
    "- Legal Agent: No evidence found\n"
    "- Geography Agent: No evidence found\n"
    "- News Media Agent: No evidence found\n"
    "The claim cannot be independently verified.",
    "confidence": "high",
}

MOCK_JUDGE_VERDICT_CONTRADICTED = {
    "verdict": "contradicted",
    "reasoning": "Claim is CONTRADICTED. Evidence directly contradicts the claim:\n"
    "- News Media Agent: Investigative journalism reports regulatory action against the company, "
    "contradicting the claimed emissions reduction.\n"
    "- Data Metrics Agent: Mathematical analysis shows reported figures are inconsistent.\n"
    "Supporting evidence from: legal\n"
    "The weight of contradicting evidence outweighs supporting evidence.",
    "confidence": "high",
}

MOCK_JUDGE_VERDICT_INSUFFICIENT = {
    "verdict": "insufficient_evidence",
    "reasoning": "Claim has INSUFFICIENT EVIDENCE. Some evidence exists but is not sufficient:\n"
    "- Only 1 source(s) found\n"
    "- Missing agent perspectives: geography, news_media\n"
    "Cannot reach a confident verdict with available evidence.",
    "confidence": "medium",
}

MOCK_JUDGE_REINVESTIGATION_REQUEST = {
    "claim_id": "claim-judge-001",
    "target_agents": ["geography", "news_media"],
    "evidence_gap": "Insufficient sources: only 1 agent(s) found evidence. Need multiple independent sources. "
    "Missing agent perspectives: ['geography', 'news_media'] should have investigated but did not.",
    "refined_queries": [
        "Verify geographic claim: 'Our reforestation initiative restored 5,000 hectares...'. "
        "Focus on satellite imagery analysis for the stated location and time period.",
        "Search for recent news coverage (prioritize Tier 1-2 sources) about: 'Our reforestation initiative...'. "
        "Look for corroboration or contradiction.",
    ],
    "required_evidence": "Satellite imagery showing the claimed location/condition with NDVI analysis "
    "and temporal comparison if applicable. News coverage from Tier 1-2 sources (investigative journalism, "
    "regulatory actions) corroborating or contradicting the claim.",
}

MOCK_JUDGE_FULL_RESPONSE_VERIFIED = {
    "verdicts": [
        {
            "claim_id": "claim-judge-001",
            "verdict": "verified",
            "reasoning": "Multiple independent sources corroborate the claim.",
            "ifrs_mapping": [{"paragraph": "S2.14(a)(iv)", "status": "compliant"}],
            "confidence": "high",
        }
    ],
    "reinvestigation_requests": [],
}

MOCK_JUDGE_FULL_RESPONSE_INSUFFICIENT = {
    "verdicts": [
        {
            "claim_id": "claim-judge-001",
            "verdict": "insufficient_evidence",
            "reasoning": "Only one source found evidence.",
            "ifrs_mapping": [{"paragraph": "S2.14(a)(iv)", "status": "pending"}],
            "confidence": "medium",
        }
    ],
    "reinvestigation_requests": [
        {
            "claim_id": "claim-judge-001",
            "target_agents": ["geography", "news_media"],
            "evidence_gap": "Need additional corroboration from multiple agents.",
            "refined_queries": ["Search for satellite imagery...", "Search for news coverage..."],
        }
    ],
}


def get_mock_judge_verdict_response(verdict_type: str = "verified") -> str:
    """Get a mock LLM response for Judge Agent verdict.
    
    Args:
        verdict_type: One of "verified", "unverified", "contradicted", "insufficient"
        
    Returns:
        JSON string of the mock response
    """
    responses = {
        "verified": MOCK_JUDGE_VERDICT_VERIFIED,
        "unverified": MOCK_JUDGE_VERDICT_UNVERIFIED,
        "contradicted": MOCK_JUDGE_VERDICT_CONTRADICTED,
        "insufficient": MOCK_JUDGE_VERDICT_INSUFFICIENT,
    }
    return json.dumps(responses.get(verdict_type, MOCK_JUDGE_VERDICT_VERIFIED))


def get_mock_judge_full_response(scenario: str = "verified") -> str:
    """Get a mock full Judge Agent response with verdicts and reinvestigation requests.
    
    Args:
        scenario: One of "verified", "insufficient"
        
    Returns:
        JSON string of the mock response
    """
    responses = {
        "verified": MOCK_JUDGE_FULL_RESPONSE_VERIFIED,
        "insufficient": MOCK_JUDGE_FULL_RESPONSE_INSUFFICIENT,
    }
    return json.dumps(responses.get(scenario, MOCK_JUDGE_FULL_RESPONSE_VERIFIED))
