"""Web search tool for News/Media and Academic agents.

Provides web search functionality via Tavily Search API for gathering
external evidence to verify sustainability claims.

Used by:
- News/Media Agent (FRD 8)
- Academic/Research Agent (FRD 9)
"""

import asyncio
import logging
from typing import Optional
from urllib.parse import urlparse

from langchain_core.tools import tool

from app.core.config import settings
from app.core.sanitize import sanitize_string

logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================


class SearchAPIError(Exception):
    """Raised when web search API fails after retries."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# ============================================================================
# Domain Extraction Helper
# ============================================================================


def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc or ""
    except Exception:
        return ""


# ============================================================================
# Tavily Search Provider
# ============================================================================


class TavilySearchProvider:
    """Tavily Search API provider with retry logic."""

    def __init__(self, api_key: str):
        """Initialize Tavily client.
        
        Args:
            api_key: Tavily API key
        """
        from tavily import TavilyClient
        
        self.client = TavilyClient(api_key=api_key)
        self._max_retries = 3
        self._base_delay = 1.0  # seconds

    async def search(
        self,
        query: str,
        max_results: int = 10,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        time_range: str | None = None,
        search_depth: str = "basic",
    ) -> dict:
        """Execute a Tavily search with retry logic.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            include_domains: Optional list of domains to include
            exclude_domains: Optional list of domains to exclude
            time_range: Optional time filter (day, week, month, year, all)
            search_depth: "basic" or "advanced" search depth
            
        Returns:
            Dictionary with results and metadata
            
        Raises:
            SearchAPIError: If search fails after all retries
        """
        search_kwargs = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
        }

        if include_domains:
            search_kwargs["include_domains"] = include_domains
        if exclude_domains:
            search_kwargs["exclude_domains"] = exclude_domains

        # Note: time_range is available for future implementation
        # Tavily doesn't support time_range directly, but it's kept for API compatibility
        _ = time_range  # Acknowledge parameter for future use

        last_exception: Exception | None = None
        
        for attempt in range(self._max_retries):
            try:
                # Run synchronous Tavily client in thread pool
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.search(**search_kwargs)
                )

                # Parse results and sanitize text fields to remove PostgreSQL-incompatible
                # characters (null bytes, unpaired surrogates) from external API responses
                results = []
                for result in response.get("results", []):
                    result_dict = {
                        "title": sanitize_string(result.get("title", "")),
                        "url": sanitize_string(result.get("url", "")),
                        "snippet": sanitize_string(result.get("content", "")),  # Tavily uses "content"
                        "published_date": result.get("published_date"),
                        "source_domain": _extract_domain(result.get("url", "")),
                        "relevance_score": result.get("score"),
                    }
                    results.append(result_dict)

                # Filter by time_range if specified (post-query filtering)
                # Note: Tavily doesn't support time_range directly
                # For now, we return all results and let the agent filter
                
                return {
                    "results": results,
                    "total_results": len(results),
                    "query": query,
                    "search_provider": "tavily",
                }

            except Exception as e:
                last_exception = e
                error_str = str(e).lower()
                
                # Check for retryable errors
                is_retryable = any([
                    "rate limit" in error_str,
                    "429" in error_str,
                    "500" in error_str,
                    "502" in error_str,
                    "503" in error_str,
                    "504" in error_str,
                    "timeout" in error_str,
                    "connection" in error_str,
                ])
                
                if not is_retryable:
                    logger.error("Non-retryable search error: %s", e)
                    raise SearchAPIError(
                        message=f"Search failed: {str(e)}",
                        status_code=None
                    ) from e
                
                if attempt < self._max_retries - 1:
                    delay = self._base_delay * (2 ** attempt)
                    logger.warning(
                        "Search attempt %d failed, retrying in %.1fs: %s",
                        attempt + 1, delay, e
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "Search failed after %d attempts: %s",
                        self._max_retries, e
                    )
        
        raise SearchAPIError(
            message=f"Search failed after {self._max_retries} attempts: {last_exception}",
            status_code=None
        )


# ============================================================================
# Singleton Provider Instance
# ============================================================================


_search_provider: TavilySearchProvider | None = None


def _get_search_provider() -> TavilySearchProvider:
    """Get or create the search provider singleton."""
    global _search_provider
    
    if _search_provider is None:
        if not settings.TAVILY_API_KEY:
            raise SearchAPIError(
                message="Tavily API key not configured. Set TAVILY_API_KEY environment variable.",
                status_code=None
            )
        _search_provider = TavilySearchProvider(settings.TAVILY_API_KEY)
    
    return _search_provider


# ============================================================================
# LangChain Tool
# ============================================================================


@tool
async def search_web(
    query: str,
    max_results: Optional[int] = None,
    include_domains: Optional[list[str]] = None,
    exclude_domains: Optional[list[str]] = None,
    time_range: Optional[str] = None,
    search_depth: str = "basic",
) -> dict:
    """Search the web for news articles, press releases, and public sources.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: config.SEARCH_MAX_RESULTS)
        include_domains: Optional list of domains to restrict search to (e.g., ["reuters.com", "bloomberg.com"])
        exclude_domains: Optional list of domains to exclude (e.g., ["twitter.com", "facebook.com"])
        time_range: Optional time filter: "day", "week", "month", "year", or "all" (default: "all")
        search_depth: "basic" for fast results or "advanced" for deeper search (default: "basic")

    Returns:
        Dictionary with search results:
        {
            "results": [
                {
                    "title": str,
                    "url": str,
                    "snippet": str,
                    "published_date": str | None,
                    "source_domain": str,
                    "relevance_score": float | None
                },
                ...
            ],
            "total_results": int,
            "query": str,
            "search_provider": str
        }

    Raises:
        SearchAPIError: If the search API fails after retries
    """
    provider = _get_search_provider()
    
    return await provider.search(
        query=query,
        max_results=max_results or settings.SEARCH_MAX_RESULTS,
        include_domains=include_domains,
        exclude_domains=exclude_domains,
        time_range=time_range,
        search_depth=search_depth,
    )


# ============================================================================
# Direct async function for non-tool invocation
# ============================================================================


async def search_web_async(
    query: str,
    max_results: int | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    time_range: str | None = None,
    search_depth: str = "basic",
) -> dict:
    """Direct async search function (bypasses LangChain tool wrapper).
    
    Use this when calling search directly from agent code.
    Same parameters and return value as search_web tool.
    """
    provider = _get_search_provider()
    
    return await provider.search(
        query=query,
        max_results=max_results or settings.SEARCH_MAX_RESULTS,
        include_domains=include_domains,
        exclude_domains=exclude_domains,
        time_range=time_range,
        search_depth=search_depth,
    )
