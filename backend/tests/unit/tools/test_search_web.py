"""Unit tests for search_web tool.

Tests the search web tool functionality, mocking the Tavily API
to avoid consuming API credits.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.tools.search_web import (
    TavilySearchProvider,
    SearchAPIError,
    search_web_async,
    _extract_domain,
    _get_search_provider,
)
from tests.fixtures.mock_tavily import (
    MOCK_TAVILY_RESPONSE_SUPPORTING,
    MOCK_TAVILY_RESPONSE_EMPTY,
    get_formatted_tavily_response,
)


# ============================================================================
# Domain Extraction Tests
# ============================================================================


class TestDomainExtraction:
    """Tests for domain extraction from URLs."""

    def test_extracts_simple_domain(self):
        """Test extraction from simple URL."""
        url = "https://example.com/article"
        assert _extract_domain(url) == "example.com"

    def test_extracts_subdomain(self):
        """Test extraction with subdomain."""
        url = "https://news.reuters.com/article/123"
        assert _extract_domain(url) == "news.reuters.com"

    def test_extracts_domain_with_port(self):
        """Test extraction with port number."""
        url = "https://localhost:8080/test"
        assert _extract_domain(url) == "localhost:8080"

    def test_handles_invalid_url(self):
        """Test handling of invalid URLs."""
        url = "not-a-valid-url"
        result = _extract_domain(url)
        assert result == "" or result == "not-a-valid-url"

    def test_handles_empty_string(self):
        """Test handling of empty string."""
        assert _extract_domain("") == ""


# ============================================================================
# TavilySearchProvider Tests
# ============================================================================


class TestTavilySearchProvider:
    """Tests for TavilySearchProvider class."""

    @pytest.mark.asyncio
    async def test_search_returns_structured_results(self, mocker):
        """Test that search returns properly structured results."""
        # Mock the TavilyClient import inside the class
        mock_client = MagicMock()
        mock_client.search.return_value = MOCK_TAVILY_RESPONSE_SUPPORTING
        mocker.patch(
            "tavily.TavilyClient",
            return_value=mock_client
        )

        provider = TavilySearchProvider(api_key="test-key")
        result = await provider.search("test query")

        assert "results" in result
        assert "total_results" in result
        assert "query" in result
        assert "search_provider" in result
        assert result["search_provider"] == "tavily"

    @pytest.mark.asyncio
    async def test_search_parses_result_fields(self, mocker):
        """Test that individual results have expected fields."""
        mock_client = MagicMock()
        mock_client.search.return_value = MOCK_TAVILY_RESPONSE_SUPPORTING
        mocker.patch(
            "tavily.TavilyClient",
            return_value=mock_client
        )

        provider = TavilySearchProvider(api_key="test-key")
        result = await provider.search("test query")

        if result["results"]:
            first = result["results"][0]
            assert "title" in first
            assert "url" in first
            assert "snippet" in first
            assert "source_domain" in first
            assert "relevance_score" in first

    @pytest.mark.asyncio
    async def test_search_extracts_domain_from_url(self, mocker):
        """Test that domain is extracted from result URLs."""
        mock_client = MagicMock()
        mock_client.search.return_value = MOCK_TAVILY_RESPONSE_SUPPORTING
        mocker.patch(
            "tavily.TavilyClient",
            return_value=mock_client
        )

        provider = TavilySearchProvider(api_key="test-key")
        result = await provider.search("test query")

        if result["results"]:
            first = result["results"][0]
            assert first["source_domain"] != ""
            # Domain should be extracted from the URL
            assert "reuters.com" in first["source_domain"] or "bloomberg.com" in first["source_domain"]

    @pytest.mark.asyncio
    async def test_search_handles_empty_results(self, mocker):
        """Test handling of empty search results."""
        mock_client = MagicMock()
        mock_client.search.return_value = MOCK_TAVILY_RESPONSE_EMPTY
        mocker.patch(
            "tavily.TavilyClient",
            return_value=mock_client
        )

        provider = TavilySearchProvider(api_key="test-key")
        result = await provider.search("obscure nonexistent query")

        assert result["results"] == []
        assert result["total_results"] == 0

    @pytest.mark.asyncio
    async def test_search_passes_parameters(self, mocker):
        """Test that search parameters are passed correctly."""
        mock_client = MagicMock()
        mock_client.search.return_value = MOCK_TAVILY_RESPONSE_SUPPORTING
        mocker.patch(
            "tavily.TavilyClient",
            return_value=mock_client
        )

        provider = TavilySearchProvider(api_key="test-key")
        await provider.search(
            query="test query",
            max_results=5,
            include_domains=["reuters.com"],
            exclude_domains=["twitter.com"],
            search_depth="advanced",
        )

        # Verify the call was made with correct parameters
        call_kwargs = mock_client.search.call_args.kwargs
        assert call_kwargs["query"] == "test query"
        assert call_kwargs["max_results"] == 5
        assert call_kwargs["include_domains"] == ["reuters.com"]
        assert call_kwargs["exclude_domains"] == ["twitter.com"]
        assert call_kwargs["search_depth"] == "advanced"

    @pytest.mark.asyncio
    async def test_search_retries_on_transient_error(self, mocker):
        """Test that transient errors trigger retry."""
        mock_client = MagicMock()
        # First two calls fail, third succeeds
        mock_client.search.side_effect = [
            Exception("503 Service Unavailable"),
            Exception("Connection timeout"),
            MOCK_TAVILY_RESPONSE_SUPPORTING,
        ]
        mocker.patch(
            "tavily.TavilyClient",
            return_value=mock_client
        )

        # Mock sleep to speed up test
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        provider = TavilySearchProvider(api_key="test-key")
        result = await provider.search("test query")

        assert mock_client.search.call_count == 3
        assert "results" in result

    @pytest.mark.asyncio
    async def test_search_raises_after_max_retries(self, mocker):
        """Test that SearchAPIError is raised after max retries."""
        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("503 Service Unavailable")
        mocker.patch(
            "tavily.TavilyClient",
            return_value=mock_client
        )

        # Mock sleep to speed up test
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        provider = TavilySearchProvider(api_key="test-key")

        with pytest.raises(SearchAPIError) as exc_info:
            await provider.search("test query")

        assert "3 attempts" in str(exc_info.value.message)
        assert mock_client.search.call_count == 3

    @pytest.mark.asyncio
    async def test_search_handles_rate_limit(self, mocker):
        """Test handling of rate limit errors (429)."""
        mock_client = MagicMock()
        mock_client.search.side_effect = [
            Exception("429 Rate limit exceeded"),
            MOCK_TAVILY_RESPONSE_SUPPORTING,
        ]
        mocker.patch(
            "tavily.TavilyClient",
            return_value=mock_client
        )

        # Mock sleep to speed up test
        mocker.patch("asyncio.sleep", new_callable=AsyncMock)

        provider = TavilySearchProvider(api_key="test-key")
        result = await provider.search("test query")

        assert "results" in result
        assert mock_client.search.call_count == 2

    @pytest.mark.asyncio
    async def test_search_no_retry_on_non_retryable_error(self, mocker):
        """Test that non-retryable errors fail immediately."""
        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("Invalid API key")
        mocker.patch(
            "tavily.TavilyClient",
            return_value=mock_client
        )

        provider = TavilySearchProvider(api_key="invalid-key")

        with pytest.raises(SearchAPIError):
            await provider.search("test query")

        # Should only try once for non-retryable errors
        assert mock_client.search.call_count == 1


# ============================================================================
# search_web_async Function Tests
# ============================================================================


class TestSearchWebAsync:
    """Tests for search_web_async function."""

    @pytest.mark.asyncio
    async def test_search_uses_config_defaults(self, mocker):
        """Test that search uses config defaults for max_results."""
        mock_provider = MagicMock()
        mock_provider.search = AsyncMock(return_value=get_formatted_tavily_response("supporting"))
        mocker.patch(
            "app.agents.tools.search_web._get_search_provider",
            return_value=mock_provider
        )

        result = await search_web_async(query="test query")

        assert "results" in result
        # Default max_results from config should be used
        call_kwargs = mock_provider.search.call_args.kwargs
        assert "max_results" in call_kwargs

    @pytest.mark.asyncio
    async def test_search_applies_domain_filters(self, mocker):
        """Test that domain filters are applied."""
        mock_provider = MagicMock()
        mock_provider.search = AsyncMock(return_value=get_formatted_tavily_response("supporting"))
        mocker.patch(
            "app.agents.tools.search_web._get_search_provider",
            return_value=mock_provider
        )

        await search_web_async(
            query="test query",
            include_domains=["reuters.com", "bbc.com"],
            exclude_domains=["twitter.com"],
        )

        call_kwargs = mock_provider.search.call_args.kwargs
        assert call_kwargs.get("include_domains") == ["reuters.com", "bbc.com"]
        assert call_kwargs.get("exclude_domains") == ["twitter.com"]

    @pytest.mark.asyncio
    async def test_search_applies_time_range(self, mocker):
        """Test that time range parameter is passed."""
        mock_provider = MagicMock()
        mock_provider.search = AsyncMock(return_value=get_formatted_tavily_response("supporting"))
        mocker.patch(
            "app.agents.tools.search_web._get_search_provider",
            return_value=mock_provider
        )

        await search_web_async(
            query="test query",
            time_range="week",
        )

        call_kwargs = mock_provider.search.call_args.kwargs
        assert call_kwargs.get("time_range") == "week"

    @pytest.mark.asyncio
    async def test_search_applies_search_depth(self, mocker):
        """Test that search depth parameter is passed."""
        mock_provider = MagicMock()
        mock_provider.search = AsyncMock(return_value=get_formatted_tavily_response("supporting"))
        mocker.patch(
            "app.agents.tools.search_web._get_search_provider",
            return_value=mock_provider
        )

        await search_web_async(
            query="test query",
            search_depth="advanced",
        )

        call_kwargs = mock_provider.search.call_args.kwargs
        assert call_kwargs.get("search_depth") == "advanced"

    @pytest.mark.asyncio
    async def test_search_respects_max_results(self, mocker):
        """Test that max_results parameter limits results."""
        mock_provider = MagicMock()
        mock_provider.search = AsyncMock(return_value=get_formatted_tavily_response("supporting"))
        mocker.patch(
            "app.agents.tools.search_web._get_search_provider",
            return_value=mock_provider
        )

        await search_web_async(
            query="test query",
            max_results=5,
        )

        call_kwargs = mock_provider.search.call_args.kwargs
        assert call_kwargs.get("max_results") == 5


# ============================================================================
# Provider Singleton Tests
# ============================================================================


class TestProviderSingleton:
    """Tests for search provider singleton management."""

    def test_raises_error_without_api_key(self, mocker):
        """Test that missing API key raises error."""
        # Reset the singleton
        import app.agents.tools.search_web as search_module
        search_module._search_provider = None
        
        # Mock settings to have no API key
        mock_settings = MagicMock()
        mock_settings.TAVILY_API_KEY = None
        mocker.patch.object(search_module, "settings", mock_settings)

        with pytest.raises(SearchAPIError) as exc_info:
            _get_search_provider()

        assert "API key not configured" in str(exc_info.value.message)

    def test_creates_provider_with_api_key(self, mocker):
        """Test that provider is created with valid API key."""
        # Reset the singleton
        import app.agents.tools.search_web as search_module
        search_module._search_provider = None
        
        # Mock settings
        mock_settings = MagicMock()
        mock_settings.TAVILY_API_KEY = "test-api-key"
        mocker.patch.object(search_module, "settings", mock_settings)
        
        # Mock TavilyClient to avoid actual initialization
        mocker.patch(
            "tavily.TavilyClient",
            return_value=MagicMock()
        )

        provider = _get_search_provider()

        assert provider is not None
        assert isinstance(provider, TavilySearchProvider)


# ============================================================================
# SearchAPIError Tests
# ============================================================================


class TestSearchAPIError:
    """Tests for SearchAPIError exception."""

    def test_error_with_message(self):
        """Test error creation with message."""
        error = SearchAPIError("Test error message")
        assert error.message == "Test error message"
        assert error.status_code is None

    def test_error_with_status_code(self):
        """Test error creation with status code."""
        error = SearchAPIError("Rate limited", status_code=429)
        assert error.message == "Rate limited"
        assert error.status_code == 429

    def test_error_string_representation(self):
        """Test error string representation."""
        error = SearchAPIError("Test error")
        assert "Test error" in str(error)
