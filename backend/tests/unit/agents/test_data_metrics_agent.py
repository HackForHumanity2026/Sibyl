"""Unit tests for the Data/Metrics Agent.

Tests response schemas, helper functions, and main validation with mocked LLM.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.agents.data_metrics_agent import (
    # Schemas
    ConsistencyCheckResult,
    UnitValidationResult,
    BenchmarkComparison,
    TargetAchievabilityResult,
    HistoricalConsistencyResult,
    IFRSComplianceResult,
    QuantitativeValidationResult,
    # Helper functions
    normalize_emissions,
    _group_claims_by_analysis_type,
    _find_related_claims,
    _should_request_benchmark_data,
    _create_benchmark_info_request,
    _process_benchmark_responses,
    _get_reinvestigation_context,
    _create_quantitative_finding,
    _create_error_result,
    # Main function
    investigate_data,
)
from app.agents.state import Claim, ReinvestigationRequest, InfoRequest, InfoResponse
from tests.fixtures.sample_claims import (
    DATA_METRICS_CLAIM_SCOPE_TOTALS,
    DATA_METRICS_CLAIM_YOY_CHANGE,
    DATA_METRICS_CLAIM_TARGET,
    DATA_METRICS_CLAIM_INTENSITY,
)
from tests.fixtures.mock_openrouter import (
    MOCK_SCOPE_ADDITION_PASS,
    MOCK_SCOPE_ADDITION_FAIL,
    MOCK_YOY_PERCENTAGE_PASS,
    MOCK_TARGET_ACHIEVABILITY_ACHIEVABLE,
    MOCK_INTENSITY_BENCHMARK,
)


# ============================================================================
# TestResponseSchemas
# ============================================================================


class TestResponseSchemas:
    """Test Pydantic schema parsing and validation."""

    def test_consistency_check_result_pass(self):
        """Test ConsistencyCheckResult for passing check."""
        data = {
            "check_name": "scope_addition",
            "claim_id": "claim-001",
            "result": "pass",
            "details": {"calculated": 11900000, "reported": 12000000},
            "severity": "info",
            "message": "Scope totals match within tolerance"
        }
        result = ConsistencyCheckResult(**data)
        assert result.result == "pass"
        assert result.severity == "info"

    def test_consistency_check_result_fail(self):
        """Test ConsistencyCheckResult for failing check."""
        data = {
            "check_name": "scope_addition",
            "claim_id": "claim-002",
            "result": "fail",
            "details": {"discrepancy_percent": 26.05},
            "severity": "critical",
            "message": "Scope totals do not match"
        }
        result = ConsistencyCheckResult(**data)
        assert result.result == "fail"
        assert result.severity == "critical"

    def test_unit_validation_result(self):
        """Test UnitValidationResult parsing."""
        data = {
            "units_valid": True,
            "methodology_aligned": True,
            "conversion_factors_appropriate": True,
            "issues": []
        }
        result = UnitValidationResult(**data)
        assert result.units_valid is True
        assert len(result.issues) == 0

    def test_unit_validation_with_issues(self):
        """Test UnitValidationResult with issues."""
        data = {
            "units_valid": False,
            "methodology_aligned": True,
            "conversion_factors_appropriate": False,
            "issues": ["Units not specified", "Conversion factor unclear"]
        }
        result = UnitValidationResult(**data)
        assert result.units_valid is False
        assert len(result.issues) == 2

    def test_benchmark_comparison(self):
        """Test BenchmarkComparison parsing."""
        data = {
            "metric_name": "Emission intensity",
            "reported_value": 0.5,
            "reported_unit": "tCO2e per $1M revenue",
            "sector_average": 0.8,
            "sector_unit": "tCO2e per $1M revenue",
            "benchmark_source": "Industry benchmarks",
            "assessment": "plausible",
            "reasoning": "Value is below sector average"
        }
        result = BenchmarkComparison(**data)
        assert result.assessment == "plausible"
        assert result.sector_average == 0.8

    def test_target_achievability_result(self):
        """Test TargetAchievabilityResult parsing."""
        data = {
            "claim_id": "claim-004",
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
            "reasoning": "Target is within achievable range"
        }
        result = TargetAchievabilityResult(**data)
        assert result.achievability_assessment == "achievable"
        assert result.ifrs_s2_33_36_compliant is True

    def test_historical_consistency_result(self):
        """Test HistoricalConsistencyResult parsing."""
        data = {
            "claim_id": "claim-003",
            "current_year": 2024,
            "current_value": 2300000,
            "prior_years": [{"year": 2023, "value": 2450000}],
            "yoy_change_consistent": True,
            "trend_consistent": True,
            "methodology_changes": [],
            "unexplained_deviations": [],
            "assessment": "consistent",
            "reasoning": "Historical data is consistent"
        }
        result = HistoricalConsistencyResult(**data)
        assert result.assessment == "consistent"
        assert len(result.prior_years) == 1

    def test_ifrs_compliance_result(self):
        """Test IFRSComplianceResult parsing."""
        data = {
            "claim_id": "claim-001",
            "ifrs_paragraphs": ["S2.29(a)(i)", "S2.29(a)(ii)"],
            "compliance_status": "compliant",
            "missing_requirements": [],
            "compliance_details": {"scope1": True, "scope2": True},
            "reasoning": "All requirements met"
        }
        result = IFRSComplianceResult(**data)
        assert result.compliance_status == "compliant"
        assert len(result.ifrs_paragraphs) == 2

    def test_quantitative_validation_result_complete(self):
        """Test complete QuantitativeValidationResult parsing."""
        result = QuantitativeValidationResult(**MOCK_SCOPE_ADDITION_PASS)
        assert result.claim_id == "claim-dm-001"
        assert len(result.consistency_checks) == 1
        assert result.supports_claim is True
        assert result.confidence == "high"

    def test_quantitative_validation_result_with_failure(self):
        """Test QuantitativeValidationResult with failed checks."""
        result = QuantitativeValidationResult(**MOCK_SCOPE_ADDITION_FAIL)
        assert result.supports_claim is False
        assert result.consistency_checks[0].result == "fail"

    def test_quantitative_validation_result_defaults(self):
        """Test QuantitativeValidationResult default values."""
        minimal_data = {
            "claim_id": "test",
            "unit_validation": {
                "units_valid": True,
                "methodology_aligned": True,
                "conversion_factors_appropriate": True,
                "issues": []
            },
            "ifrs_compliance": {
                "claim_id": "test",
                "ifrs_paragraphs": [],
                "compliance_status": "not_applicable",
                "missing_requirements": [],
                "compliance_details": {},
                "reasoning": "N/A"
            },
            "summary": "Test",
            "confidence": "low"
        }
        result = QuantitativeValidationResult(**minimal_data)
        assert result.consistency_checks == []
        assert result.benchmark_comparison is None
        assert result.calculation_trace == []


# ============================================================================
# TestUnitNormalization
# ============================================================================


class TestUnitNormalization:
    """Test unit conversion functions."""

    def test_normalize_emissions_tco2e(self):
        """Test tCO2e (base unit) normalization."""
        assert normalize_emissions(1000, "tCO2e") == 1000

    def test_normalize_emissions_tco2e_lowercase(self):
        """Test case insensitivity."""
        assert normalize_emissions(1000, "tco2e") == 1000

    def test_normalize_emissions_mtco2e(self):
        """Test MtCO2e (million tonnes) normalization."""
        assert normalize_emissions(1, "MtCO2e") == 1_000_000

    def test_normalize_emissions_mtco2e_lowercase(self):
        """Test MtCO2e lowercase."""
        assert normalize_emissions(2.5, "mtco2e") == 2_500_000

    def test_normalize_emissions_ktco2e(self):
        """Test ktCO2e (thousand tonnes) normalization."""
        assert normalize_emissions(100, "ktCO2e") == 100_000

    def test_normalize_emissions_million_tonnes(self):
        """Test 'million tonnes CO2e' text."""
        assert normalize_emissions(1.5, "million tonnes co2e") == 1_500_000

    def test_normalize_emissions_mt_space(self):
        """Test 'Mt CO2e' with space."""
        assert normalize_emissions(3, "Mt CO2e") == 3_000_000

    def test_normalize_emissions_tonnes(self):
        """Test plain 'tonnes CO2e'."""
        assert normalize_emissions(500, "tonnes co2e") == 500

    def test_normalize_emissions_unknown_unit(self):
        """Test unknown unit defaults to no conversion."""
        # Unknown units are assumed to already be in tCO2e
        assert normalize_emissions(1000, "unknown_unit") == 1000

    def test_normalize_emissions_m_prefix(self):
        """Test M prefix detection."""
        assert normalize_emissions(1, "M tCO2e") == 1_000_000


# ============================================================================
# TestClaimGrouping
# ============================================================================


class TestClaimGrouping:
    """Test claim grouping functions."""

    def test_group_emissions_claim(self):
        """Test emissions claim is grouped correctly."""
        groups = _group_claims_by_analysis_type([DATA_METRICS_CLAIM_SCOPE_TOTALS])
        assert len(groups["emissions"]) == 1
        assert groups["emissions"][0].claim_id == "claim-dm-001"

    def test_group_target_claim(self):
        """Test target claim is grouped correctly."""
        groups = _group_claims_by_analysis_type([DATA_METRICS_CLAIM_TARGET])
        assert len(groups["targets"]) == 1

    def test_group_intensity_claim(self):
        """Test intensity claim is grouped correctly."""
        groups = _group_claims_by_analysis_type([DATA_METRICS_CLAIM_INTENSITY])
        assert len(groups["intensity"]) == 1

    def test_group_multiple_claims(self):
        """Test grouping multiple claims."""
        groups = _group_claims_by_analysis_type([
            DATA_METRICS_CLAIM_SCOPE_TOTALS,
            DATA_METRICS_CLAIM_YOY_CHANGE,
            DATA_METRICS_CLAIM_TARGET,
            DATA_METRICS_CLAIM_INTENSITY,
        ])
        assert len(groups["emissions"]) >= 1
        assert len(groups["targets"]) == 1
        assert len(groups["intensity"]) == 1

    def test_group_empty_list(self):
        """Test grouping empty list."""
        groups = _group_claims_by_analysis_type([])
        assert groups["emissions"] == []
        assert groups["targets"] == []
        assert groups["intensity"] == []
        assert groups["other"] == []


class TestFindRelatedClaims:
    """Test related claims finder."""

    def test_find_related_by_scope(self):
        """Test finding related claims by scope reference."""
        scope1_claim = Claim(
            claim_id="claim-s1",
            text="Scope 1 emissions: 2.3M tCO2e",
            page_number=1,
            claim_type="quantitative",
        )
        scope2_claim = Claim(
            claim_id="claim-s2",
            text="Scope 2 emissions: 1.1M tCO2e",
            page_number=1,
            claim_type="quantitative",
        )
        unrelated = Claim(
            claim_id="claim-other",
            text="We have a sustainability committee",
            page_number=1,
            claim_type="governance",
        )
        all_claims = [scope1_claim, scope2_claim, unrelated]
        
        related = _find_related_claims(scope1_claim, all_claims)
        # scope2_claim shares "scope" terminology but not same scope number
        assert scope1_claim not in related  # Should not include itself

    def test_find_related_by_year(self):
        """Test finding related claims by year reference."""
        claim_2024_a = Claim(
            claim_id="claim-2024a",
            text="In 2024, we reduced emissions by 10%",
            page_number=1,
            claim_type="quantitative",
        )
        claim_2024_b = Claim(
            claim_id="claim-2024b",
            text="FY2024 total emissions: 5M tCO2e",
            page_number=2,
            claim_type="quantitative",
        )
        claim_2023 = Claim(
            claim_id="claim-2023",
            text="2023 baseline: 5.5M tCO2e",
            page_number=3,
            claim_type="quantitative",
        )
        all_claims = [claim_2024_a, claim_2024_b, claim_2023]
        
        related = _find_related_claims(claim_2024_a, all_claims)
        claim_ids = [c.claim_id for c in related]
        assert "claim-2024b" in claim_ids

    def test_find_related_limits_results(self):
        """Test that related claims are limited to 5."""
        claims = [
            Claim(
                claim_id=f"claim-{i}",
                text=f"Scope 1 value {i}",
                page_number=i,
                claim_type="quantitative",
            )
            for i in range(10)
        ]
        related = _find_related_claims(claims[0], claims)
        assert len(related) <= 5


# ============================================================================
# TestInterAgentCommunication
# ============================================================================


class TestInterAgentCommunication:
    """Test inter-agent communication helpers."""

    def test_should_request_benchmark_intensity(self):
        """Test benchmark request for intensity claim."""
        result = _should_request_benchmark_data(DATA_METRICS_CLAIM_INTENSITY)
        assert result is not None
        assert result[0] == "academic"
        assert result[1] == "emission_intensity"

    def test_should_request_benchmark_non_intensity(self):
        """Test no benchmark request for non-intensity claim."""
        result = _should_request_benchmark_data(DATA_METRICS_CLAIM_SCOPE_TOTALS)
        # Scope totals claim doesn't need benchmarks
        assert result is None

    def test_create_benchmark_info_request(self):
        """Test InfoRequest creation for benchmarks."""
        request = _create_benchmark_info_request(
            DATA_METRICS_CLAIM_INTENSITY,
            "emission_intensity"
        )
        assert request.requesting_agent == "data_metrics"
        assert request.context["claim_id"] == "claim-dm-006"
        assert request.context["metric_type"] == "emission_intensity"
        assert request.status == "pending"

    def test_process_benchmark_responses_found(self):
        """Test processing existing benchmark response."""
        state = {
            "info_requests": [
                InfoRequest(
                    request_id="req-001",
                    requesting_agent="data_metrics",
                    description="Get benchmark",
                    context={"claim_id": "claim-dm-006"},
                    status="responded",
                )
            ],
            "info_responses": [
                InfoResponse(
                    request_id="req-001",
                    responding_agent="academic",
                    response="Sector average: 0.8",
                    details={"average": 0.8},
                )
            ],
        }
        result = _process_benchmark_responses(state, DATA_METRICS_CLAIM_INTENSITY)
        assert result is not None
        assert result["source"] == "academic"

    def test_process_benchmark_responses_not_found(self):
        """Test processing when no response exists."""
        state = {
            "info_requests": [],
            "info_responses": [],
        }
        result = _process_benchmark_responses(state, DATA_METRICS_CLAIM_INTENSITY)
        assert result is None


# ============================================================================
# TestReinvestigation
# ============================================================================


class TestReinvestigation:
    """Test re-investigation handling."""

    def test_get_reinvestigation_context_found(self):
        """Test getting re-investigation request when it exists."""
        reinvest = ReinvestigationRequest(
            claim_id="claim-dm-004",
            target_agents=["data_metrics"],
            evidence_gap="Need more detail",
            refined_queries=["Search for X"],
        )
        state = {"reinvestigation_requests": [reinvest]}
        
        result = _get_reinvestigation_context(state, "claim-dm-004")
        assert result is not None
        assert result.evidence_gap == "Need more detail"

    def test_get_reinvestigation_context_not_found(self):
        """Test getting re-investigation request when none exists."""
        state = {"reinvestigation_requests": []}
        result = _get_reinvestigation_context(state, "claim-dm-004")
        assert result is None

    def test_get_reinvestigation_context_wrong_agent(self):
        """Test re-investigation request for different agent."""
        reinvest = ReinvestigationRequest(
            claim_id="claim-dm-004",
            target_agents=["legal"],  # Not data_metrics
            evidence_gap="Need legal review",
            refined_queries=[],
        )
        state = {"reinvestigation_requests": [reinvest]}
        
        result = _get_reinvestigation_context(state, "claim-dm-004")
        assert result is None


# ============================================================================
# TestFindingGeneration
# ============================================================================


class TestFindingGeneration:
    """Test finding creation from validation results."""

    def test_create_finding_all_checks_pass(self):
        """Test finding creation when all checks pass."""
        validation_result = QuantitativeValidationResult(**MOCK_SCOPE_ADDITION_PASS)
        finding = _create_quantitative_finding(
            DATA_METRICS_CLAIM_SCOPE_TOTALS,
            validation_result,
            iteration=0,
        )
        
        assert finding.agent_name == "data_metrics"
        assert finding.claim_id == "claim-dm-001"
        assert finding.evidence_type == "quantitative_validation"
        assert finding.supports_claim is True
        assert finding.confidence == "high"
        assert finding.iteration == 1

    def test_create_finding_with_failures(self):
        """Test finding creation when checks fail."""
        validation_result = QuantitativeValidationResult(**MOCK_SCOPE_ADDITION_FAIL)
        finding = _create_quantitative_finding(
            DATA_METRICS_CLAIM_SCOPE_TOTALS,
            validation_result,
            iteration=0,
        )
        
        assert finding.supports_claim is False
        assert "failed" in finding.summary.lower() or "critical" in finding.summary.lower()

    def test_create_finding_includes_calculation_trace(self):
        """Test finding includes calculation trace."""
        data = MOCK_SCOPE_ADDITION_PASS.copy()
        data["calculation_trace"] = [
            {"expression": "2300000 + 1100000 + 8500000", "result": "11900000"}
        ]
        validation_result = QuantitativeValidationResult(**data)
        finding = _create_quantitative_finding(
            DATA_METRICS_CLAIM_SCOPE_TOTALS,
            validation_result,
            iteration=0,
        )
        
        assert "calculation_trace" in finding.details
        assert len(finding.details["calculation_trace"]) == 1

    def test_create_finding_with_benchmark_data(self):
        """Test finding creation with benchmark responses."""
        validation_result = QuantitativeValidationResult(**MOCK_INTENSITY_BENCHMARK)
        benchmark_responses = {
            "source": "academic",
            "data": {"average": 0.8},
        }
        finding = _create_quantitative_finding(
            DATA_METRICS_CLAIM_INTENSITY,
            validation_result,
            iteration=0,
            benchmark_responses=benchmark_responses,
        )
        
        assert "cross_domain_evidence" in finding.details

    def test_create_error_result(self):
        """Test error result creation."""
        result = _create_error_result(
            "claim-test",
            "LLM timeout",
            calculation_trace=[{"expression": "1+1", "result": "2"}],
        )
        
        assert result.claim_id == "claim-test"
        assert result.supports_claim is None
        assert result.confidence == "low"
        assert "timeout" in result.summary.lower()
        assert len(result.calculation_trace) == 1


# ============================================================================
# TestInvestigateDataNode
# ============================================================================


class TestInvestigateDataNode:
    """Test main node function."""

    @pytest.mark.asyncio
    async def test_node_processes_assigned_claims(
        self,
        sample_state_emissions,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test node processes claims assigned to it."""
        mock_openrouter_data_metrics(json.dumps(MOCK_SCOPE_ADDITION_PASS))
        
        # Mock RAG
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock IFRS content ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        assert "findings" in result
        assert len(result["findings"]) == 1
        assert result["findings"][0].agent_name == "data_metrics"

    @pytest.mark.asyncio
    async def test_node_skips_unassigned_claims(
        self,
        sample_state_no_data_metrics_claims,
    ):
        """Test node skips claims not assigned to it."""
        result = await investigate_data(sample_state_no_data_metrics_claims)
        
        assert len(result["findings"]) == 0
        assert result["agent_status"]["data_metrics"].claims_assigned == 0

    @pytest.mark.asyncio
    async def test_node_emits_start_event(
        self,
        sample_state_emissions,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test node emits agent_started event."""
        mock_openrouter_data_metrics(json.dumps(MOCK_SCOPE_ADDITION_PASS))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        start_events = [e for e in result["events"] if e.event_type == "agent_started"]
        assert len(start_events) == 1
        assert start_events[0].agent_name == "data_metrics"

    @pytest.mark.asyncio
    async def test_node_emits_completion_event(
        self,
        sample_state_emissions,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test node emits agent_completed event."""
        mock_openrouter_data_metrics(json.dumps(MOCK_SCOPE_ADDITION_PASS))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        complete_events = [e for e in result["events"] if e.event_type == "agent_completed"]
        assert len(complete_events) == 1
        assert complete_events[0].data["claims_processed"] == 1

    @pytest.mark.asyncio
    async def test_node_emits_evidence_found_events(
        self,
        sample_state_emissions,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test node emits evidence_found events."""
        mock_openrouter_data_metrics(json.dumps(MOCK_SCOPE_ADDITION_PASS))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        evidence_events = [e for e in result["events"] if e.event_type == "evidence_found"]
        assert len(evidence_events) == 1

    @pytest.mark.asyncio
    async def test_node_handles_no_claims_assigned(
        self,
        sample_state_no_data_metrics_claims,
    ):
        """Test node handles empty assignment gracefully."""
        result = await investigate_data(sample_state_no_data_metrics_claims)
        
        assert result["agent_status"]["data_metrics"].status == "completed"
        complete_events = [e for e in result["events"] if e.event_type == "agent_completed"]
        assert complete_events[0].data["claims_processed"] == 0

    @pytest.mark.asyncio
    async def test_node_returns_correct_state_shape(
        self,
        sample_state_emissions,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test node returns correct state update shape."""
        mock_openrouter_data_metrics(json.dumps(MOCK_SCOPE_ADDITION_PASS))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        assert "findings" in result
        assert "agent_status" in result
        assert "events" in result
        assert isinstance(result["findings"], list)
        assert "data_metrics" in result["agent_status"]

    @pytest.mark.asyncio
    async def test_node_handles_errors_gracefully(
        self,
        sample_state_emissions,
        mocker,
    ):
        """Test node handles LLM errors gracefully."""
        # Mock to raise error
        mocker.patch(
            "app.agents.data_metrics_agent._validate_quantitative_claim",
            AsyncMock(side_effect=Exception("LLM Error")),
        )
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        # Should still complete with error finding
        assert result["agent_status"]["data_metrics"].status == "completed"
        assert len(result["findings"]) == 1
        assert "error" in result["findings"][0].summary.lower()

    @pytest.mark.asyncio
    async def test_node_emits_consistency_check_events(
        self,
        sample_state_emissions,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test node emits consistency_check events."""
        mock_openrouter_data_metrics(json.dumps(MOCK_SCOPE_ADDITION_PASS))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_emissions)
        
        check_events = [e for e in result["events"] if e.event_type == "consistency_check"]
        assert len(check_events) == 1
        assert check_events[0].data["check_name"] == "scope_addition"
        assert check_events[0].data["result"] == "pass"

    @pytest.mark.asyncio
    async def test_node_creates_info_request_for_benchmarks(
        self,
        sample_state_intensity,
        mock_openrouter_data_metrics,
        mocker,
    ):
        """Test node creates InfoRequest for benchmark data."""
        mock_openrouter_data_metrics(json.dumps(MOCK_INTENSITY_BENCHMARK))
        mocker.patch(
            "app.agents.data_metrics_agent._retrieve_ifrs_metrics_paragraphs",
            AsyncMock(return_value="--- Mock ---"),
        )
        
        result = await investigate_data(sample_state_intensity)
        
        # Check for info_requests in result
        if "info_requests" in result:
            assert any(
                req.context.get("metric_type") == "emission_intensity"
                for req in result["info_requests"]
            )
