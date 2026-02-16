"""Unit tests for News/Media Agent helper functions.

Tests the internal helper functions directly, mocking all external dependencies
(OpenRouter, Tavily) to avoid consuming tokens or API credits.
"""

import json

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.news_media_agent import (
    SearchQuerySet,
    SourceCredibilityResult,
    ContradictionAnalysis,
    NewsMediaAssessmentResult,
    TIER_1_DOMAINS,
    TIER_2_DOMAINS,
    TIER_3_DOMAINS,
    SOCIAL_MEDIA_DOMAINS,
    _construct_search_queries,
    _construct_fallback_queries,
    _execute_web_searches,
    _assign_tier_by_domain,
    _assign_credibility_tier,
    _detect_contradiction,
    _generate_relevance_summary,
    _create_source_finding,
    _create_summary_finding,
    _should_request_cross_domain,
    _clean_json_response,
)
from app.agents.state import Claim
from tests.fixtures.mock_openrouter import (
    get_mock_news_query_response,
    get_mock_news_credibility_response,
    get_mock_news_contradiction_response,
    MOCK_NEWS_RELEVANCE_SUMMARY,
)
from tests.fixtures.mock_tavily import get_formatted_tavily_response
from tests.fixtures.sample_claims import (
    NEWS_CLAIM_EMISSIONS_REDUCTION,
    NEWS_CLAIM_CERTIFICATION,
    NEWS_CLAIM_CONTROVERSY,
    NEWS_CLAIM_REFORESTATION,
)


# ============================================================================
# Query Construction Tests
# ============================================================================


class TestQueryConstruction:
    """Tests for search query construction."""

    @pytest.mark.asyncio
    async def test_constructs_queries_via_llm(self, mocker):
        """Test that query construction uses LLM to generate queries."""
        mock_response = get_mock_news_query_response("emissions")
        mock_chat = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )

        result = await _construct_search_queries(
            claim=NEWS_CLAIM_EMISSIONS_REDUCTION,
            company_name="TestCorp"
        )

        assert isinstance(result, SearchQuerySet)
        # Verify that we got a result with the three query fields
        assert result.company_specific
        assert result.industry_wide
        assert result.controversy
        mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_constructs_certification_queries(self, mocker):
        """Test query construction for certification claims."""
        mock_response = get_mock_news_query_response("certification")
        mock_chat = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )

        result = await _construct_search_queries(
            claim=NEWS_CLAIM_CERTIFICATION,
            company_name="TestCorp"
        )

        assert isinstance(result, SearchQuerySet)
        assert result.company_specific
        assert result.industry_wide
        assert result.controversy

    @pytest.mark.asyncio
    async def test_query_construction_handles_llm_error(self, mocker):
        """Test that query construction falls back on LLM error."""
        mock_chat = AsyncMock(side_effect=Exception("API timeout"))
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )

        result = await _construct_search_queries(
            claim=NEWS_CLAIM_EMISSIONS_REDUCTION,
            company_name="TestCorp"
        )

        # Should return fallback queries
        assert isinstance(result, SearchQuerySet)
        assert "TestCorp" in result.company_specific or "TestCorp" in result.controversy

    def test_fallback_queries_include_company_name(self):
        """Test that fallback queries include the company name."""
        result = _construct_fallback_queries(
            claim=NEWS_CLAIM_EMISSIONS_REDUCTION,
            company_name="Acme Corp"
        )

        assert isinstance(result, SearchQuerySet)
        assert "Acme Corp" in result.company_specific
        assert "Acme Corp" in result.controversy

    def test_fallback_queries_include_claim_keywords(self):
        """Test that fallback queries include relevant keywords from claim."""
        result = _construct_fallback_queries(
            claim=NEWS_CLAIM_CONTROVERSY,
            company_name="TestCorp"
        )

        # Controversy query should include violation-related terms
        assert any(term in result.controversy.lower() for term in 
                   ["violation", "investigation", "lawsuit", "greenwashing"])


# ============================================================================
# Web Search Execution Tests
# ============================================================================


class TestWebSearchExecution:
    """Tests for web search execution."""

    @pytest.mark.asyncio
    async def test_executes_all_query_types(self, mocker):
        """Test that search is executed for all query types."""
        mock_response = get_formatted_tavily_response("supporting")
        mock_search = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.news_media_agent.search_web_async",
            mock_search
        )

        queries = SearchQuerySet(
            company_specific="test company query",
            industry_wide="test industry query",
            controversy="test controversy query"
        )

        results = await _execute_web_searches(queries)

        # Should call search 3 times (once per query type)
        assert mock_search.call_count == 3
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_deduplicates_results_by_url(self, mocker):
        """Test that duplicate URLs are removed from combined results."""
        # Same response for all queries
        mock_response = get_formatted_tavily_response("supporting")
        mock_search = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.news_media_agent.search_web_async",
            mock_search
        )

        queries = SearchQuerySet(
            company_specific="query1",
            industry_wide="query2",
            controversy="query3"
        )

        results = await _execute_web_searches(queries)

        # Results should be deduplicated
        urls = [r.get("url") for r in results]
        assert len(urls) == len(set(urls))

    @pytest.mark.asyncio
    async def test_adds_query_type_to_results(self, mocker):
        """Test that query_type is added to each result."""
        mock_response = get_formatted_tavily_response("supporting")
        mock_search = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.news_media_agent.search_web_async",
            mock_search
        )

        queries = SearchQuerySet(
            company_specific="query1",
            industry_wide="query2",
            controversy="query3"
        )

        results = await _execute_web_searches(queries)

        # First query's results should have query_type
        if results:
            assert "query_type" in results[0]

    @pytest.mark.asyncio
    async def test_continues_on_partial_search_failure(self, mocker):
        """Test that search continues if one query fails."""
        from app.agents.tools.search_web import SearchAPIError

        mock_responses = [
            SearchAPIError("First search failed"),
            get_formatted_tavily_response("supporting"),
            get_formatted_tavily_response("supporting"),
        ]
        mock_search = AsyncMock(side_effect=mock_responses)
        mocker.patch(
            "app.agents.news_media_agent.search_web_async",
            mock_search
        )

        queries = SearchQuerySet(
            company_specific="query1",
            industry_wide="query2",
            controversy="query3"
        )

        results = await _execute_web_searches(queries)

        # Should still return results from successful searches
        assert isinstance(results, list)
        assert mock_search.call_count == 3


# ============================================================================
# Credibility Tiering Tests
# ============================================================================


class TestCredibilityTiering:
    """Tests for source credibility tier assignment."""

    def test_tier_1_domain_classification(self):
        """Test that Tier 1 domains are correctly classified."""
        for domain in ["propublica.org", "sec.gov", "justice.gov"]:
            tier = _assign_tier_by_domain(domain)
            assert tier == 1, f"Expected Tier 1 for {domain}, got {tier}"

    def test_tier_2_domain_classification(self):
        """Test that Tier 2 domains are correctly classified."""
        for domain in ["nytimes.com", "wsj.com", "bloomberg.com", "bbc.com", "reuters.com"]:
            tier = _assign_tier_by_domain(domain)
            assert tier == 2, f"Expected Tier 2 for {domain}, got {tier}"

    def test_tier_3_domain_classification(self):
        """Test that Tier 3 domains are correctly classified."""
        for domain in ["prnewswire.com", "businesswire.com", "globenewswire.com"]:
            tier = _assign_tier_by_domain(domain)
            assert tier == 3, f"Expected Tier 3 for {domain}, got {tier}"

    def test_tier_4_social_media_classification(self):
        """Test that social media domains are classified as Tier 4."""
        for domain in ["twitter.com", "x.com", "facebook.com", "reddit.com"]:
            tier = _assign_tier_by_domain(domain)
            assert tier == 4, f"Expected Tier 4 for {domain}, got {tier}"

    def test_unknown_domain_returns_none(self):
        """Test that unknown domains return None for LLM fallback."""
        tier = _assign_tier_by_domain("unknown-blog.example.com")
        assert tier is None

    def test_subdomain_matching(self):
        """Test that subdomains are matched correctly."""
        # reuters.com/investigates should still match
        tier = _assign_tier_by_domain("news.reuters.com")
        assert tier == 2

    @pytest.mark.asyncio
    async def test_llm_fallback_for_unknown_domain(self, mocker):
        """Test that LLM is used for unknown domains."""
        mock_response = get_mock_news_credibility_response(tier=2)
        mock_chat = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )

        source = {
            "title": "Industry Analysis Report",
            "url": "https://unknown-industry-journal.com/report",
            "snippet": "Expert analysis of emissions trends...",
            "source_domain": "unknown-industry-journal.com",
        }

        result = await _assign_credibility_tier(source)

        assert isinstance(result, SourceCredibilityResult)
        mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_known_domain_skips_llm(self, mocker):
        """Test that known domains don't trigger LLM call."""
        mock_chat = AsyncMock()
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )

        source = {
            "title": "Reuters Report",
            "url": "https://reuters.com/article",
            "snippet": "Reuters reports...",
            "source_domain": "reuters.com",
        }

        result = await _assign_credibility_tier(source)

        assert result.tier == 2
        mock_chat.assert_not_called()

    @pytest.mark.asyncio
    async def test_llm_fallback_on_error_defaults_to_tier_4(self, mocker):
        """Test that LLM errors default to Tier 4."""
        mock_chat = AsyncMock(side_effect=Exception("API error"))
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )

        source = {
            "title": "Unknown Source",
            "url": "https://unknown.com/article",
            "snippet": "Some content...",
            "source_domain": "unknown.com",
        }

        result = await _assign_credibility_tier(source)

        assert result.tier == 4
        assert "defaulting" in result.reasoning.lower() or "unknown" in result.reasoning.lower()


# ============================================================================
# Contradiction Detection Tests
# ============================================================================


class TestContradictionDetection:
    """Tests for contradiction detection."""

    @pytest.mark.asyncio
    async def test_detects_direct_contradiction(self, mocker):
        """Test detection of direct contradictions."""
        mock_response = get_mock_news_contradiction_response("direct")
        mock_chat = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )

        source = {
            "title": "EPA Data Shows Emissions Increased",
            "url": "https://epa.gov/data",
            "snippet": "Emissions increased by 8%...",
            "published_date": "2024-09-01",
        }

        result = await _detect_contradiction(NEWS_CLAIM_EMISSIONS_REDUCTION, source)

        assert isinstance(result, ContradictionAnalysis)
        assert result.contradicts is True
        assert result.contradiction_type == "direct"

    @pytest.mark.asyncio
    async def test_detects_contextual_contradiction(self, mocker):
        """Test detection of contextual contradictions."""
        mock_response = get_mock_news_contradiction_response("contextual")
        mock_chat = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )

        source = {
            "title": "Divestiture Behind Emissions Drop",
            "url": "https://example.com/article",
            "snippet": "Reductions due to asset sales...",
            "published_date": "2024-06-01",
        }

        result = await _detect_contradiction(NEWS_CLAIM_EMISSIONS_REDUCTION, source)

        assert result.contradicts is True
        assert result.contradiction_type == "contextual"

    @pytest.mark.asyncio
    async def test_detects_omission_contradiction(self, mocker):
        """Test detection of omission contradictions."""
        mock_response = get_mock_news_contradiction_response("omission")
        mock_chat = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )

        source = {
            "title": "Ongoing EPA Investigation",
            "url": "https://example.com/article",
            "snippet": "Investigation not disclosed...",
            "published_date": "2024-07-01",
        }

        result = await _detect_contradiction(NEWS_CLAIM_CONTROVERSY, source)

        assert result.contradicts is True
        assert result.contradiction_type == "omission"

    @pytest.mark.asyncio
    async def test_detects_timeline_contradiction(self, mocker):
        """Test detection of timeline contradictions."""
        mock_response = get_mock_news_contradiction_response("timeline")
        mock_chat = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )

        source = {
            "title": "Company Delays Net-Zero Target",
            "url": "https://example.com/article",
            "snippet": "Target pushed from 2050 to 2060...",
            "published_date": "2024-08-01",
        }

        result = await _detect_contradiction(NEWS_CLAIM_EMISSIONS_REDUCTION, source)

        assert result.contradicts is True
        assert result.contradiction_type == "timeline"

    @pytest.mark.asyncio
    async def test_no_contradiction_for_supporting_source(self, mocker):
        """Test that supporting sources don't show contradiction."""
        mock_response = get_mock_news_contradiction_response(None)
        mock_chat = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )

        source = {
            "title": "Company Achieves Emissions Target",
            "url": "https://reuters.com/article",
            "snippet": "Third-party verification confirms reductions...",
            "published_date": "2024-06-15",
        }

        result = await _detect_contradiction(NEWS_CLAIM_EMISSIONS_REDUCTION, source)

        assert result.contradicts is False
        assert result.contradiction_type is None

    @pytest.mark.asyncio
    async def test_contradiction_detection_handles_error(self, mocker):
        """Test that contradiction detection handles LLM errors gracefully."""
        mock_chat = AsyncMock(side_effect=Exception("API error"))
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )

        source = {
            "title": "Test Article",
            "url": "https://example.com/article",
            "snippet": "Some content...",
            "published_date": "2024-01-01",
        }

        result = await _detect_contradiction(NEWS_CLAIM_EMISSIONS_REDUCTION, source)

        # Should return non-contradicting with low confidence
        assert result.contradicts is False
        assert result.confidence == 0.0
        assert "failed" in result.explanation.lower()


# ============================================================================
# Relevance Summary Tests
# ============================================================================


class TestRelevanceSummary:
    """Tests for relevance summary generation."""

    @pytest.mark.asyncio
    async def test_generates_relevance_summary(self, mocker):
        """Test that relevance summary is generated."""
        mock_chat = AsyncMock(return_value=MOCK_NEWS_RELEVANCE_SUMMARY)
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )

        source = {
            "title": "Company Reports Emissions",
            "url": "https://reuters.com/article",
            "snippet": "The company reported reductions...",
        }

        result = await _generate_relevance_summary(NEWS_CLAIM_EMISSIONS_REDUCTION, source)

        assert isinstance(result, str)
        assert len(result) > 0
        mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_relevance_summary_handles_error(self, mocker):
        """Test that relevance summary handles errors gracefully."""
        mock_chat = AsyncMock(side_effect=Exception("API error"))
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )

        source = {
            "title": "Test Article",
            "url": "https://example.com/article",
            "snippet": "Some content...",
        }

        result = await _generate_relevance_summary(NEWS_CLAIM_EMISSIONS_REDUCTION, source)

        # Should return fallback summary
        assert isinstance(result, str)
        assert "Test Article" in result


# ============================================================================
# Evidence Generation Tests
# ============================================================================


class TestEvidenceGeneration:
    """Tests for evidence finding generation."""

    def test_creates_source_finding(self):
        """Test creation of individual source findings."""
        source = {
            "title": "Reuters Article",
            "url": "https://reuters.com/article/123",
            "source_domain": "reuters.com",
            "snippet": "Company reduced emissions...",
            "published_date": "2024-06-15",
            "query_type": "company_specific",
        }
        contradiction = ContradictionAnalysis(
            contradicts=False,
            contradiction_type=None,
            confidence=0.8,
            explanation="Source supports the claim."
        )

        finding = _create_source_finding(
            claim=NEWS_CLAIM_EMISSIONS_REDUCTION,
            source=source,
            tier=2,
            contradiction=contradiction,
            relevance_summary="Article confirms emissions reductions.",
            iteration=1,
        )

        assert finding.agent_name == "news_media"
        assert finding.claim_id == NEWS_CLAIM_EMISSIONS_REDUCTION.claim_id
        assert finding.evidence_type == "news_source"
        assert finding.details["source_url"] == "https://reuters.com/article/123"
        assert finding.details["source_tier"] == 2
        assert finding.details["contradicts_claim"] is False

    def test_creates_contradiction_finding(self):
        """Test creation of finding for contradicting source."""
        source = {
            "title": "EPA Report",
            "url": "https://epa.gov/enforcement/123",
            "source_domain": "epa.gov",
            "snippet": "Emissions increased...",
            "published_date": "2024-09-01",
            "query_type": "controversy",
        }
        contradiction = ContradictionAnalysis(
            contradicts=True,
            contradiction_type="direct",
            confidence=0.92,
            explanation="EPA data contradicts reported figures."
        )

        finding = _create_source_finding(
            claim=NEWS_CLAIM_EMISSIONS_REDUCTION,
            source=source,
            tier=1,
            contradiction=contradiction,
            relevance_summary="EPA data shows emissions increased.",
            iteration=1,
        )

        assert finding.evidence_type == "news_contradiction"
        assert finding.details["contradicts_claim"] is True
        assert finding.details["contradiction_type"] == "direct"
        assert finding.supports_claim is False

    def test_creates_summary_finding_supporting(self):
        """Test creation of summary finding for supporting evidence."""
        # Create mock source findings
        source_findings = [
            _create_source_finding(
                claim=NEWS_CLAIM_EMISSIONS_REDUCTION,
                source={"url": f"https://example.com/{i}", "source_domain": "reuters.com"},
                tier=2,
                contradiction=ContradictionAnalysis(contradicts=False, contradiction_type=None, confidence=0.8, explanation=""),
                relevance_summary="Supporting source.",
                iteration=1,
            )
            for i in range(3)
        ]

        summary = _create_summary_finding(
            claim=NEWS_CLAIM_EMISSIONS_REDUCTION,
            source_findings=source_findings,
            iteration=1,
        )

        assert summary.agent_name == "news_media"
        assert summary.evidence_type == "news_investigation_summary"
        assert summary.details["total_sources"] == 3
        assert summary.details["contradicting_sources"] == 0
        assert summary.supports_claim is True

    def test_creates_summary_finding_contradicting(self):
        """Test creation of summary finding with contradictions."""
        # Create mock source findings with contradictions
        source_findings = [
            _create_source_finding(
                claim=NEWS_CLAIM_EMISSIONS_REDUCTION,
                source={"url": "https://propublica.org/article", "source_domain": "propublica.org"},
                tier=1,
                contradiction=ContradictionAnalysis(contradicts=True, contradiction_type="direct", confidence=0.9, explanation=""),
                relevance_summary="Contradicting source.",
                iteration=1,
            ),
            _create_source_finding(
                claim=NEWS_CLAIM_EMISSIONS_REDUCTION,
                source={"url": "https://reuters.com/article", "source_domain": "reuters.com"},
                tier=2,
                contradiction=ContradictionAnalysis(contradicts=False, contradiction_type=None, confidence=0.8, explanation=""),
                relevance_summary="Supporting source.",
                iteration=1,
            ),
        ]

        summary = _create_summary_finding(
            claim=NEWS_CLAIM_EMISSIONS_REDUCTION,
            source_findings=source_findings,
            iteration=1,
        )

        # Tier 1 contradiction should result in not supporting
        assert summary.details["contradicting_sources"] == 1
        assert summary.supports_claim is False
        assert summary.confidence == "high"  # High confidence due to Tier 1 contradiction


# ============================================================================
# Cross-Domain Request Tests
# ============================================================================


class TestCrossDomainRequest:
    """Tests for cross-domain verification requests."""

    def test_requests_geography_for_facility_claims(self):
        """Test that facility claims with location discrepancies trigger geography verification."""
        # Create a claim about a facility
        facility_claim = Claim(
            claim_id="claim-facility-001",
            text="Our facility in Singapore has achieved zero waste to landfill status.",
            page_number=42,
            claim_type="environmental",
            ifrs_paragraphs=["S2.14(a)"],
            priority="medium",
        )
        # Source mentions different location
        sources = [
            {"snippet": "The facility at different location reported significant issues..."}
        ]

        result = _should_request_cross_domain(facility_claim, sources)

        assert result is not None
        assert result[0] == "geography"

    def test_no_request_for_simple_claims(self):
        """Test that simple claims don't trigger cross-domain requests."""
        sources = [
            {"snippet": "Standard emissions report confirmed..."}
        ]

        result = _should_request_cross_domain(NEWS_CLAIM_EMISSIONS_REDUCTION, sources)

        # Emissions claim without location indicators shouldn't trigger
        assert result is None


# ============================================================================
# Utility Function Tests
# ============================================================================


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_clean_json_response_removes_markdown(self):
        """Test that markdown code blocks are removed from JSON."""
        raw = """```json
{"tier": 2, "reasoning": "test"}
```"""
        cleaned = _clean_json_response(raw)
        data = json.loads(cleaned)
        assert data["tier"] == 2

    def test_clean_json_response_handles_plain_json(self):
        """Test that plain JSON is handled correctly."""
        raw = '{"tier": 1, "reasoning": "test"}'
        cleaned = _clean_json_response(raw)
        data = json.loads(cleaned)
        assert data["tier"] == 1

    def test_clean_json_response_handles_whitespace(self):
        """Test that whitespace is trimmed."""
        raw = '  \n  {"key": "value"}  \n  '
        cleaned = _clean_json_response(raw)
        data = json.loads(cleaned)
        assert data["key"] == "value"
