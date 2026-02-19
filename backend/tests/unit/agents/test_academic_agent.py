"""Unit tests for Academic/Research Agent helper functions.

Tests the internal helper functions directly, mocking all external dependencies
(OpenRouter, Tavily) to avoid consuming tokens or API credits.
"""

import json

import pytest
from unittest.mock import AsyncMock, patch

from app.agents.academic_agent import (
    AcademicSearchQuerySet,
    AcademicAnalysisResult,
    _classify_investigation_type,
    _construct_academic_queries,
    _construct_fallback_queries,
    _execute_academic_searches,
    _analyze_search_results,
    _create_academic_finding,
    _should_request_cross_domain,
    _clean_json_response,
)
from app.agents.state import Claim
from tests.fixtures.sample_claims import (
    ACADEMIC_CLAIM_METHODOLOGY,
    ACADEMIC_CLAIM_CERTIFICATION,
    ACADEMIC_CLAIM_SBTI,
    ACADEMIC_CLAIM_BENCHMARK,
    ACADEMIC_CLAIM_RESEARCH,
    ACADEMIC_CLAIM_OFFSET,
)
from tests.fixtures.mock_openrouter import (
    get_mock_academic_query_response,
    get_mock_academic_analysis_response,
)
from tests.fixtures.mock_tavily import get_formatted_tavily_response


# ============================================================================
# Investigation Type Classification Tests
# ============================================================================


class TestClassifyInvestigationType:
    """Tests for _classify_investigation_type."""

    def test_methodology_claim(self):
        result = _classify_investigation_type(ACADEMIC_CLAIM_METHODOLOGY)
        assert result == "methodology_validation"

    def test_certification_claim(self):
        result = _classify_investigation_type(ACADEMIC_CLAIM_CERTIFICATION)
        assert result == "certification_validation"

    def test_sbti_claim(self):
        result = _classify_investigation_type(ACADEMIC_CLAIM_SBTI)
        assert result == "sbti_validation"

    def test_benchmark_claim(self):
        result = _classify_investigation_type(ACADEMIC_CLAIM_BENCHMARK)
        assert result == "benchmark_comparison"

    def test_research_claim(self):
        result = _classify_investigation_type(ACADEMIC_CLAIM_RESEARCH)
        assert result == "research_support"

    def test_offset_claim_classified_as_certification(self):
        """Carbon offset claims should be classified as certification_validation."""
        result = _classify_investigation_type(ACADEMIC_CLAIM_OFFSET)
        assert result == "certification_validation"

    def test_generic_quantitative_defaults_to_benchmark(self):
        """Generic quantitative claim without keywords should default to benchmark."""
        claim = Claim(
            claim_id="test-quant",
            text="Our emissions in FY2024 were 450,000 tCO2e.",
            page_number=1,
            claim_type="quantitative",
        )
        result = _classify_investigation_type(claim)
        assert result == "benchmark_comparison"

    def test_generic_strategic_defaults_to_methodology(self):
        """Generic strategic claim should default to methodology."""
        claim = Claim(
            claim_id="test-strat",
            text="We have developed a comprehensive plan for the future.",
            page_number=1,
            claim_type="strategic",
        )
        result = _classify_investigation_type(claim)
        assert result == "methodology_validation"


# ============================================================================
# Query Construction Tests
# ============================================================================


class TestQueryConstruction:
    """Tests for query construction."""

    @pytest.mark.asyncio
    async def test_constructs_queries_via_llm(self, mocker):
        """Test that query construction uses LLM to generate queries."""
        mock_response = get_mock_academic_query_response("methodology")
        mock_chat = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.academic_agent.openrouter_client.chat_completion",
            mock_chat,
        )

        result = await _construct_academic_queries(
            ACADEMIC_CLAIM_METHODOLOGY, "methodology_validation"
        )

        assert isinstance(result, AcademicSearchQuerySet)
        assert len(result.queries) >= 2
        mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self, mocker):
        """Test that fallback queries are used when LLM fails."""
        mock_chat = AsyncMock(side_effect=Exception("API error"))
        mocker.patch(
            "app.agents.academic_agent.openrouter_client.chat_completion",
            mock_chat,
        )

        result = await _construct_academic_queries(
            ACADEMIC_CLAIM_METHODOLOGY, "methodology_validation"
        )

        assert isinstance(result, AcademicSearchQuerySet)
        assert len(result.queries) >= 2

    def test_fallback_queries_methodology(self):
        """Test fallback queries for methodology validation."""
        result = _construct_fallback_queries(
            ACADEMIC_CLAIM_METHODOLOGY, "methodology_validation"
        )
        assert isinstance(result, AcademicSearchQuerySet)
        assert any("GHG Protocol" in q for q in result.queries)

    def test_fallback_queries_certification(self):
        """Test fallback queries for certification validation."""
        result = _construct_fallback_queries(
            ACADEMIC_CLAIM_CERTIFICATION, "certification_validation"
        )
        assert isinstance(result, AcademicSearchQuerySet)
        assert any("certificate" in q.lower() or "additionality" in q.lower() for q in result.queries)

    def test_fallback_queries_sbti(self):
        """Test fallback queries for SBTi validation."""
        result = _construct_fallback_queries(
            ACADEMIC_CLAIM_SBTI, "sbti_validation"
        )
        assert isinstance(result, AcademicSearchQuerySet)
        assert any("SBTi" in q or "sbti" in q.lower() for q in result.queries)

    def test_fallback_queries_benchmark(self):
        """Test fallback queries for benchmark comparison."""
        result = _construct_fallback_queries(
            ACADEMIC_CLAIM_BENCHMARK, "benchmark_comparison"
        )
        assert isinstance(result, AcademicSearchQuerySet)
        assert any("benchmark" in q.lower() for q in result.queries)

    def test_fallback_queries_research(self):
        """Test fallback queries for research support."""
        result = _construct_fallback_queries(
            ACADEMIC_CLAIM_RESEARCH, "research_support"
        )
        assert isinstance(result, AcademicSearchQuerySet)
        assert any("peer-reviewed" in q.lower() for q in result.queries)


# ============================================================================
# Search Execution Tests
# ============================================================================


class TestSearchExecution:
    """Tests for web search execution."""

    @pytest.mark.asyncio
    async def test_executes_searches_and_deduplicates(self, mocker):
        """Test that searches are executed and results deduplicated."""
        tavily_response = get_formatted_tavily_response("supporting")
        mock_search = AsyncMock(return_value=tavily_response)
        mocker.patch(
            "app.agents.academic_agent.search_web_async",
            mock_search,
        )

        queries = AcademicSearchQuerySet(
            queries=["query1", "query2", "query3"]
        )
        results = await _execute_academic_searches(queries)

        assert len(results) > 0
        # Check deduplication: URLs should be unique
        urls = [r.get("url") for r in results]
        assert len(urls) == len(set(urls))

    @pytest.mark.asyncio
    async def test_handles_search_failure_gracefully(self, mocker):
        """Test graceful handling of search API failures."""
        from app.agents.tools.search_web import SearchAPIError

        mock_search = AsyncMock(side_effect=SearchAPIError("API error"))
        mocker.patch(
            "app.agents.academic_agent.search_web_async",
            mock_search,
        )

        queries = AcademicSearchQuerySet(queries=["failing query"])
        results = await _execute_academic_searches(queries)

        assert results == []


# ============================================================================
# LLM Analysis Tests
# ============================================================================


class TestAnalyzeSearchResults:
    """Tests for LLM-based search result analysis."""

    @pytest.mark.asyncio
    async def test_analyzes_methodology_results(self, mocker):
        """Test analysis of methodology validation results."""
        mock_response = get_mock_academic_analysis_response("methodology")
        mock_chat = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.academic_agent.openrouter_client.chat_completion",
            mock_chat,
        )

        results = [
            {"title": "GHG Protocol Standard", "url": "https://example.com/ghg", "snippet": "Test"},
        ]

        analysis = await _analyze_search_results(
            ACADEMIC_CLAIM_METHODOLOGY, results, "methodology_validation"
        )

        assert isinstance(analysis, AcademicAnalysisResult)
        assert analysis.investigation_type == "methodology_validation"
        assert analysis.confidence >= 0.0
        mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_analysis_failure(self, mocker):
        """Test graceful degradation when LLM analysis fails."""
        mock_chat = AsyncMock(side_effect=Exception("API error"))
        mocker.patch(
            "app.agents.academic_agent.openrouter_client.chat_completion",
            mock_chat,
        )

        analysis = await _analyze_search_results(
            ACADEMIC_CLAIM_METHODOLOGY, [], "methodology_validation"
        )

        assert isinstance(analysis, AcademicAnalysisResult)
        assert analysis.supports_claim is None
        assert analysis.confidence == 0.0
        assert len(analysis.limitations) > 0

    @pytest.mark.asyncio
    async def test_handles_empty_results(self, mocker):
        """Test analysis with no search results."""
        mock_response = get_mock_academic_analysis_response("methodology")
        mock_chat = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.academic_agent.openrouter_client.chat_completion",
            mock_chat,
        )

        analysis = await _analyze_search_results(
            ACADEMIC_CLAIM_METHODOLOGY, [], "methodology_validation"
        )

        assert isinstance(analysis, AcademicAnalysisResult)


# ============================================================================
# Finding Generation Tests
# ============================================================================


class TestFindingGeneration:
    """Tests for finding generation."""

    def test_creates_methodology_finding(self):
        """Test creation of methodology validation finding."""
        analysis = AcademicAnalysisResult(
            investigation_type="methodology_validation",
            supports_claim=True,
            confidence=0.85,
            standard_alignment="aligned",
            research_consensus="Method is recognized.",
            limitations=["Higher uncertainty"],
            references=[
                {"type": "standard_document", "title": "GHG Protocol", "url": "https://example.com"}
            ],
            summary="Method aligns with GHG Protocol.",
        )

        finding = _create_academic_finding(
            claim=ACADEMIC_CLAIM_METHODOLOGY,
            analysis=analysis,
            search_results=[{"url": "https://example.com"}],
            iteration=1,
        )

        assert finding.agent_name == "academic"
        assert finding.claim_id == ACADEMIC_CLAIM_METHODOLOGY.claim_id
        assert finding.evidence_type == "methodology_validation"
        assert finding.supports_claim is True
        assert finding.confidence == "high"
        assert "standard_alignment" in finding.details
        assert finding.details["standard_alignment"] == "aligned"

    def test_creates_benchmark_finding_with_range(self):
        """Test creation of benchmark comparison finding."""
        analysis = AcademicAnalysisResult(
            investigation_type="benchmark_comparison",
            supports_claim=True,
            confidence=0.75,
            plausibility="plausible",
            benchmark_range={"min": 0.10, "max": 0.25, "reported": 0.15, "unit": "tCO2e/$M"},
            summary="Within plausible range.",
        )

        finding = _create_academic_finding(
            claim=ACADEMIC_CLAIM_BENCHMARK,
            analysis=analysis,
            search_results=[],
            iteration=1,
        )

        assert finding.evidence_type == "benchmark_comparison"
        assert "benchmark_range" in finding.details
        assert finding.details["benchmark_range"]["reported"] == 0.15

    def test_creates_low_confidence_finding(self):
        """Test that low confidence analysis maps to 'low' string."""
        analysis = AcademicAnalysisResult(
            investigation_type="research_support",
            supports_claim=None,
            confidence=0.2,
            summary="Insufficient evidence.",
        )

        finding = _create_academic_finding(
            claim=ACADEMIC_CLAIM_RESEARCH,
            analysis=analysis,
            search_results=[],
            iteration=1,
        )

        assert finding.confidence == "low"
        assert finding.supports_claim is None


# ============================================================================
# Cross-Domain Communication Tests
# ============================================================================


class TestCrossDomainCommunication:
    """Tests for inter-agent communication helpers."""

    def test_requests_data_metrics_for_benchmark(self):
        """Test that benchmark claims with scope references request data_metrics."""
        claim = Claim(
            claim_id="test-scope",
            text="Our Scope 1 emissions intensity is 0.15 tCO2e per $1M revenue.",
            page_number=1,
            claim_type="quantitative",
        )

        result = _should_request_cross_domain(claim, "benchmark_comparison", [])

        assert result is not None
        assert result[0] == "data_metrics"

    def test_requests_geography_for_facility(self):
        """Test that facility-related claims request geography."""
        claim = Claim(
            claim_id="test-facility",
            text="Our Surabaya facility has achieved ISO 14001 certification.",
            page_number=1,
            claim_type="environmental",
        )

        result = _should_request_cross_domain(claim, "certification_validation", [])

        assert result is not None
        assert result[0] == "geography"

    def test_no_cross_domain_for_generic(self):
        """Test that generic claims don't trigger cross-domain requests."""
        claim = Claim(
            claim_id="test-generic",
            text="We follow international best practices for carbon accounting.",
            page_number=1,
            claim_type="strategic",
        )

        result = _should_request_cross_domain(claim, "methodology_validation", [])

        assert result is None


# ============================================================================
# Utility Tests
# ============================================================================


class TestUtilities:
    """Tests for utility functions."""

    def test_clean_json_response_plain(self):
        """Test cleaning a plain JSON response."""
        raw = '{"key": "value"}'
        assert _clean_json_response(raw) == '{"key": "value"}'

    def test_clean_json_response_with_markdown(self):
        """Test cleaning a markdown-wrapped JSON response."""
        raw = '```json\n{"key": "value"}\n```'
        cleaned = _clean_json_response(raw)
        assert json.loads(cleaned) == {"key": "value"}

    def test_clean_json_response_with_whitespace(self):
        """Test cleaning a response with extra whitespace."""
        raw = '  \n {"key": "value"} \n  '
        cleaned = _clean_json_response(raw)
        assert json.loads(cleaned) == {"key": "value"}
