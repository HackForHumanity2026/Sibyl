"""Pytest configuration and shared fixtures for Sibyl backend tests.

This module provides common fixtures used across all test modules:
- Mock OpenRouter API (LLM calls)
- Mock RAG service (IFRS/SASB retrieval)
- Mock database sessions
- Sample state fixtures
- Paragraph registry mocking
"""

import json
import os
import sys
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

# Set environment variables BEFORE importing app modules
# This prevents pydantic-settings validation errors and database connection attempts
os.environ.setdefault("OPENROUTER_API_KEY", "test-dummy-key-for-testing")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

import httpx
import pytest
import respx

# Add the backend directory to the path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


# ============================================================================
# OpenRouter API Mocking
# ============================================================================

@pytest.fixture
def respx_mock():
    """Provide a respx mock router for HTTP mocking."""
    with respx.mock(assert_all_called=False) as router:
        yield router


@pytest.fixture
def mock_openrouter(mocker):
    """Mock OpenRouter client chat_completion method directly.
    
    This patches the openrouter_client instance used by legal_agent,
    avoiding any real HTTP calls.
    
    Usage:
        def test_example(mock_openrouter):
            mock_openrouter('{"result": "test"}')
            # Now any call to openrouter_client.chat_completion will return this
    """
    def _mock_completion(response_content: str, status_code: int = 200):
        mock_chat = AsyncMock(return_value=response_content)
        mocker.patch(
            "app.agents.legal_agent.openrouter_client.chat_completion",
            mock_chat
        )
        mocker.patch(
            "app.services.openrouter_client.openrouter_client.chat_completion",
            mock_chat
        )
        return mock_chat
    return _mock_completion


@pytest.fixture
def mock_openrouter_sequence(mocker):
    """Mock OpenRouter API with a sequence of responses.
    
    Useful when testing functions that make multiple LLM calls.
    
    Usage:
        def test_example(mock_openrouter_sequence):
            mock_openrouter_sequence([
                '{"first": "response"}',
                '{"second": "response"}',
            ])
    """
    def _mock_sequence(responses: list[str]):
        mock_chat = AsyncMock(side_effect=responses)
        mocker.patch(
            "app.agents.legal_agent.openrouter_client.chat_completion",
            mock_chat
        )
        return mock_chat
    return _mock_sequence


@pytest.fixture
def mock_openrouter_error(mocker):
    """Mock OpenRouter API to raise errors.
    
    Usage:
        def test_error_handling(mock_openrouter_error):
            mock_openrouter_error(500, "Internal Server Error")
    """
    def _mock_error(status_code: int, message: str):
        error = Exception(f"OpenRouter error {status_code}: {message}")
        mock_chat = AsyncMock(side_effect=error)
        mocker.patch(
            "app.agents.legal_agent.openrouter_client.chat_completion",
            mock_chat
        )
        return mock_chat
    return _mock_error


# ============================================================================
# RAG Service Mocking
# ============================================================================

@pytest.fixture
def mock_rag_service(mocker):
    """Mock the RAG service to return sample IFRS paragraphs.
    
    Patches the rag_lookup functions at the import location used by legal_agent.
    """
    sample_rag_result = """--- Result 1 (source: ifrs_s2, score: 0.92) ---
[Paragraph: S2.14(a)(iv) | Pillar: Strategy | Section: Decision-Making]

S2.14(a)(iv): An entity shall disclose its transition plan, including information about key assumptions, dependencies, and timeline.

--- No more results ---"""

    # Create mock tools that return canned responses
    mock_rag_lookup = MagicMock()
    mock_rag_lookup.ainvoke = AsyncMock(return_value=sample_rag_result)
    
    mock_rag_lookup_report = MagicMock()
    mock_rag_lookup_report.ainvoke = AsyncMock(return_value="--- No report content found ---")
    
    # Patch at the location where legal_agent imports them
    mocker.patch("app.agents.legal_agent.rag_lookup", mock_rag_lookup, create=True)
    mocker.patch("app.agents.tools.rag_lookup.rag_lookup", mock_rag_lookup)
    mocker.patch("app.agents.tools.rag_lookup.rag_lookup_report", mock_rag_lookup_report)
    
    return {
        "lookup": mock_rag_lookup,
        "lookup_report": mock_rag_lookup_report,
    }


@pytest.fixture
def mock_rag_service_empty(mocker):
    """Mock RAG service to return empty results."""
    mock_rag_lookup = MagicMock()
    mock_rag_lookup.ainvoke = AsyncMock(return_value="--- No results found ---")
    
    mock_rag_lookup_report = MagicMock()
    mock_rag_lookup_report.ainvoke = AsyncMock(return_value="--- No report content found ---")
    
    mocker.patch("app.agents.tools.rag_lookup.rag_lookup", mock_rag_lookup)
    mocker.patch("app.agents.tools.rag_lookup.rag_lookup_report", mock_rag_lookup_report)
    
    return {"lookup": mock_rag_lookup, "lookup_report": mock_rag_lookup_report}


@pytest.fixture
def mock_rag_service_error(mocker):
    """Mock RAG service to raise an exception."""
    error = Exception("RAG service unavailable")
    
    mock_rag_lookup = MagicMock()
    mock_rag_lookup.ainvoke = AsyncMock(side_effect=error)
    
    mock_rag_lookup_report = MagicMock()
    mock_rag_lookup_report.ainvoke = AsyncMock(side_effect=error)
    
    mocker.patch("app.agents.tools.rag_lookup.rag_lookup", mock_rag_lookup)
    mocker.patch("app.agents.tools.rag_lookup.rag_lookup_report", mock_rag_lookup_report)
    
    return {"lookup": mock_rag_lookup, "lookup_report": mock_rag_lookup_report, "error": error}


# ============================================================================
# Paragraph Registry Mocking
# ============================================================================

@pytest.fixture
def mock_paragraph_registry(mocker):
    """Mock the IFRS paragraph registry file loading."""
    sample_registry = {
        "version": "1.0",
        "last_updated": "2026-02-16",
        "paragraphs": [
            {
                "paragraph_id": "S2.14(a)(iv)",
                "standard": "S2",
                "pillar": "strategy",
                "section": "Decision-Making",
                "requirement_text": "Transition plan with key assumptions, dependencies, timeline.",
                "sub_requirements": [
                    {"requirement": "key_assumptions", "required": True, "description": "Key assumptions"},
                    {"requirement": "dependencies", "required": True, "description": "Dependencies"},
                    {"requirement": "timeline", "required": True, "description": "Timeline"}
                ],
                "s1_counterpart": "S1.33",
                "materiality_note": "Critical for climate strategy credibility.",
                "applicability": "all_entities"
            },
            {
                "paragraph_id": "S2.6",
                "standard": "S2",
                "pillar": "governance",
                "section": "Climate Governance Body Oversight",
                "requirement_text": "Governance body oversight of climate matters.",
                "sub_requirements": [
                    {"requirement": "identify_climate_governance_body", "required": True, "description": "Identify body"},
                    {"requirement": "climate_competencies", "required": True, "description": "Competencies"},
                    {"requirement": "climate_reporting_frequency", "required": True, "description": "Reporting frequency"}
                ],
                "s1_counterpart": "S1.27(a)",
                "materiality_note": "Fundamental governance disclosure.",
                "applicability": "all_entities"
            },
            {
                "paragraph_id": "S2.29(a)(iii)",
                "standard": "S2",
                "pillar": "metrics_targets",
                "section": "Scope 3 Emissions",
                "requirement_text": "Scope 3 emissions by category per GHG Protocol.",
                "sub_requirements": [
                    {"requirement": "scope_3_total", "required": True, "description": "Total Scope 3"},
                    {"requirement": "scope_3_by_category", "required": True, "description": "By category"},
                    {"requirement": "ghg_protocol_alignment", "required": True, "description": "GHG Protocol alignment"}
                ],
                "s1_counterpart": "S1.46",
                "materiality_note": "Scope 3 typically majority of emissions.",
                "applicability": "all_entities"
            }
        ]
    }
    
    mock_open = mocker.mock_open(read_data=json.dumps(sample_registry))
    mocker.patch("builtins.open", mock_open)
    mocker.patch("pathlib.Path.exists", return_value=True)
    
    return sample_registry


# ============================================================================
# Database Mocking
# ============================================================================

@pytest.fixture
def mock_db_session(mocker):
    """Mock database session for tests that don't need real DB."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    
    mocker.patch("app.core.database.async_session_maker", return_value=mock_session)
    
    return mock_session


# ============================================================================
# Sample State Fixtures
# ============================================================================

@pytest.fixture
def sample_state_governance():
    """State with a single governance claim."""
    from tests.fixtures.sample_states import create_state_with_single_governance_claim
    return create_state_with_single_governance_claim()


@pytest.fixture
def sample_state_strategic():
    """State with a strategic transition plan claim."""
    from tests.fixtures.sample_states import create_state_with_strategic_claim
    return create_state_with_strategic_claim()


@pytest.fixture
def sample_state_strategic_incomplete():
    """State with an incomplete strategic claim."""
    from tests.fixtures.sample_states import create_state_with_incomplete_strategic_claim
    return create_state_with_incomplete_strategic_claim()


@pytest.fixture
def sample_state_metrics():
    """State with a metrics claim."""
    from tests.fixtures.sample_states import create_state_with_metrics_claim
    return create_state_with_metrics_claim()


@pytest.fixture
def sample_state_multiple_claims():
    """State with multiple claims of different types."""
    from tests.fixtures.sample_states import create_state_with_multiple_claims
    return create_state_with_multiple_claims()


@pytest.fixture
def sample_state_no_legal_claims():
    """State where no claims are routed to legal agent."""
    from tests.fixtures.sample_states import create_state_with_no_legal_claims
    return create_state_with_no_legal_claims()


@pytest.fixture
def sample_state_reinvestigation():
    """State with a re-investigation request."""
    from tests.fixtures.sample_states import create_state_with_reinvestigation_request
    return create_state_with_reinvestigation_request()


@pytest.fixture
def sample_state_info_response():
    """State with an InfoResponse for the legal agent."""
    from tests.fixtures.sample_states import create_state_with_info_response
    return create_state_with_info_response()


@pytest.fixture
def sample_state_gap_detection():
    """State for testing gap detection."""
    from tests.fixtures.sample_states import create_state_for_gap_detection
    return create_state_for_gap_detection()


# ============================================================================
# Data Metrics Agent Mocking
# ============================================================================

@pytest.fixture
def mock_openrouter_data_metrics(mocker):
    """Mock OpenRouter client for data_metrics_agent with tool support.
    
    This patches the openrouter_client's _client to handle tool calling flow.
    
    Usage:
        def test_example(mock_openrouter_data_metrics):
            mock_openrouter_data_metrics('{"result": "test"}')
    """
    def _mock_completion(response_content: str, tool_calls: list | None = None):
        # Build response structure matching OpenRouter format
        response_data = {
            "choices": [{
                "message": {
                    "content": response_content,
                    "tool_calls": tool_calls or [],
                },
                "finish_reason": "stop" if not tool_calls else "tool_calls",
            }],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 200,
            }
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_response.raise_for_status = MagicMock()
        
        mock_post = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.data_metrics_agent.openrouter_client._client.post",
            mock_post
        )
        return mock_post
    return _mock_completion


@pytest.fixture
def mock_openrouter_data_metrics_tool_loop(mocker):
    """Mock OpenRouter with tool calling sequence for data_metrics_agent.
    
    Simulates a tool loop where the LLM first calls calculator, then returns final JSON.
    
    Usage:
        def test_tool_loop(mock_openrouter_data_metrics_tool_loop):
            mock_openrouter_data_metrics_tool_loop(
                calculator_calls=[("2+2", "4")],
                final_response='{"claim_id": "test", ...}'
            )
    """
    def _mock_tool_loop(calculator_calls: list[tuple[str, str]], final_response: str):
        responses = []
        
        # Add tool call responses
        for expression, result in calculator_calls:
            tool_response = {
                "choices": [{
                    "message": {
                        "content": "",
                        "tool_calls": [{
                            "id": f"call_{len(responses)}",
                            "type": "function",
                            "function": {
                                "name": "calculator",
                                "arguments": json.dumps({"expression": expression})
                            }
                        }]
                    },
                    "finish_reason": "tool_calls",
                }],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50}
            }
            responses.append(tool_response)
        
        # Add final response
        final = {
            "choices": [{
                "message": {
                    "content": final_response,
                    "tool_calls": [],
                },
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 200, "completion_tokens": 500}
        }
        responses.append(final)
        
        mock_responses = []
        for resp_data in responses:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = resp_data
            mock_resp.raise_for_status = MagicMock()
            mock_responses.append(mock_resp)
        
        mock_post = AsyncMock(side_effect=mock_responses)
        mocker.patch(
            "app.agents.data_metrics_agent.openrouter_client._client.post",
            mock_post
        )
        return mock_post
    return _mock_tool_loop


@pytest.fixture
def mock_calculator_tool(mocker):
    """Mock the calculator tool directly for unit testing.
    
    Usage:
        def test_example(mock_calculator_tool):
            mock_calculator_tool({"2+2": "4", "3*4": "12"})
    """
    def _mock_calculator(results: dict[str, str]):
        def calculator_side_effect(args):
            expression = args.get("expression", "")
            return results.get(expression, f"Unknown: {expression}")
        
        from app.agents.tools import calculator
        mock = MagicMock(side_effect=calculator_side_effect)
        mocker.patch.object(calculator.calculator, "invoke", mock)
        return mock
    return _mock_calculator


# ============================================================================
# Data Metrics Sample State Fixtures
# ============================================================================

@pytest.fixture
def sample_state_emissions():
    """State with a scope emissions claim for data_metrics agent."""
    from tests.fixtures.sample_states import create_state_with_emissions_claim
    return create_state_with_emissions_claim()


@pytest.fixture
def sample_state_scope_mismatch():
    """State with a scope claim that has incorrect totals."""
    from tests.fixtures.sample_states import create_state_with_scope_mismatch_claim
    return create_state_with_scope_mismatch_claim()


@pytest.fixture
def sample_state_yoy():
    """State with a YoY percentage change claim."""
    from tests.fixtures.sample_states import create_state_with_yoy_claim
    return create_state_with_yoy_claim()


@pytest.fixture
def sample_state_target():
    """State with a target achievability claim."""
    from tests.fixtures.sample_states import create_state_with_target_claim
    return create_state_with_target_claim()


@pytest.fixture
def sample_state_aggressive_target():
    """State with an aggressive target that may be questionable."""
    from tests.fixtures.sample_states import create_state_with_aggressive_target_claim
    return create_state_with_aggressive_target_claim()


@pytest.fixture
def sample_state_intensity():
    """State with an intensity metric claim."""
    from tests.fixtures.sample_states import create_state_with_intensity_claim
    return create_state_with_intensity_claim()


@pytest.fixture
def sample_state_multiple_quantitative():
    """State with multiple quantitative claims."""
    from tests.fixtures.sample_states import create_state_with_multiple_quantitative_claims
    return create_state_with_multiple_quantitative_claims()


@pytest.fixture
def sample_state_benchmark_response():
    """State with benchmark InfoResponse for data_metrics agent."""
    from tests.fixtures.sample_states import create_state_with_benchmark_info_response
    return create_state_with_benchmark_info_response()


@pytest.fixture
def sample_state_data_metrics_reinvestigation():
    """State with re-investigation request for data_metrics agent."""
    from tests.fixtures.sample_states import create_state_with_data_metrics_reinvestigation
    return create_state_with_data_metrics_reinvestigation()


@pytest.fixture
def sample_state_no_data_metrics_claims():
    """State where no claims are routed to data_metrics agent."""
    from tests.fixtures.sample_states import create_state_with_no_data_metrics_claims
    return create_state_with_no_data_metrics_claims()


# ============================================================================
# News/Media Agent Mocking - Tavily Search API
# ============================================================================


@pytest.fixture
def mock_tavily_search(mocker):
    """Mock Tavily search API calls.
    
    Usage:
        def test_example(mock_tavily_search):
            from tests.fixtures.mock_tavily import get_formatted_tavily_response
            mock_tavily_search(get_formatted_tavily_response("supporting"))
    """
    def _mock_search(response_data: dict):
        # Mock the TavilySearchProvider's search method
        mock_provider = MagicMock()
        mock_provider.search = AsyncMock(return_value=response_data)
        
        # Patch the provider getter
        mocker.patch(
            "app.agents.tools.search_web._get_search_provider",
            return_value=mock_provider
        )
        return mock_provider.search
    return _mock_search


@pytest.fixture
def mock_tavily_search_sequence(mocker):
    """Mock Tavily with multiple sequential responses for different queries.
    
    Usage:
        def test_example(mock_tavily_search_sequence):
            mock_tavily_search_sequence([
                response_1,  # For company_specific query
                response_2,  # For industry_wide query
                response_3,  # For controversy query
            ])
    """
    def _mock_sequence(responses: list[dict]):
        mock_provider = MagicMock()
        mock_provider.search = AsyncMock(side_effect=responses)
        
        mocker.patch(
            "app.agents.tools.search_web._get_search_provider",
            return_value=mock_provider
        )
        return mock_provider.search
    return _mock_sequence


@pytest.fixture
def mock_tavily_search_error(mocker):
    """Mock Tavily to raise errors.
    
    Usage:
        def test_example(mock_tavily_search_error):
            mock_tavily_search_error(SearchAPIError("Rate limit exceeded"))
    """
    def _mock_error(error: Exception):
        from app.agents.tools.search_web import SearchAPIError
        
        mock_provider = MagicMock()
        mock_provider.search = AsyncMock(side_effect=error)
        
        mocker.patch(
            "app.agents.tools.search_web._get_search_provider",
            return_value=mock_provider
        )
        return mock_provider.search
    return _mock_error


# ============================================================================
# News/Media Agent Mocking - OpenRouter
# ============================================================================


@pytest.fixture
def mock_openrouter_news(mocker):
    """Mock OpenRouter for news_media_agent LLM calls.
    
    Usage:
        def test_example(mock_openrouter_news):
            mock_openrouter_news('{"tier": 2, "reasoning": "test"}')
    """
    def _mock_completion(response_content: str):
        mock_chat = AsyncMock(return_value=response_content)
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )
        return mock_chat
    return _mock_completion


@pytest.fixture
def mock_openrouter_news_sequence(mocker):
    """Mock OpenRouter with sequence for multiple LLM calls in news_media_agent.
    
    The news agent makes multiple LLM calls per claim:
    1. Query construction
    2. Credibility classification (per source)
    3. Contradiction detection (per source)
    4. Relevance summary (per source)
    
    Usage:
        def test_example(mock_openrouter_news_sequence):
            mock_openrouter_news_sequence([
                query_response,        # Query construction
                credibility_response,  # First source credibility
                contradiction_response, # First source contradiction
                relevance_response,    # First source relevance
                # ... more responses for additional sources
            ])
    """
    def _mock_sequence(responses: list[str]):
        mock_chat = AsyncMock(side_effect=responses)
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )
        return mock_chat
    return _mock_sequence


@pytest.fixture
def mock_openrouter_news_error(mocker):
    """Mock OpenRouter to raise errors for news_media_agent.
    
    Usage:
        def test_example(mock_openrouter_news_error):
            mock_openrouter_news_error(Exception("API timeout"))
    """
    def _mock_error(error: Exception):
        mock_chat = AsyncMock(side_effect=error)
        mocker.patch(
            "app.agents.news_media_agent.openrouter_client.chat_completion",
            mock_chat
        )
        return mock_chat
    return _mock_error


# ============================================================================
# News/Media Agent Sample State Fixtures
# ============================================================================


@pytest.fixture
def sample_state_news_claim():
    """State with a single emissions claim for news_media agent."""
    from tests.fixtures.sample_states import create_state_with_news_claim
    return create_state_with_news_claim()


@pytest.fixture
def sample_state_news_certification():
    """State with a certification claim for news_media verification."""
    from tests.fixtures.sample_states import create_state_with_news_certification_claim
    return create_state_with_news_certification_claim()


@pytest.fixture
def sample_state_news_controversy():
    """State with a controversy claim for news_media investigation."""
    from tests.fixtures.sample_states import create_state_with_news_controversy_claim
    return create_state_with_news_controversy_claim()


@pytest.fixture
def sample_state_news_multiple_claims():
    """State with multiple news-related claims."""
    from tests.fixtures.sample_states import create_state_with_news_multiple_claims
    return create_state_with_news_multiple_claims()


@pytest.fixture
def sample_state_news_reinvestigation():
    """State with re-investigation request for news_media agent."""
    from tests.fixtures.sample_states import create_state_with_news_reinvestigation
    return create_state_with_news_reinvestigation()


@pytest.fixture
def sample_state_news_info_request():
    """State with InfoRequest for news_media agent."""
    from tests.fixtures.sample_states import create_state_with_news_info_request
    return create_state_with_news_info_request()


@pytest.fixture
def sample_state_news_info_response():
    """State with InfoResponse for news_media agent."""
    from tests.fixtures.sample_states import create_state_with_news_info_response
    return create_state_with_news_info_response()


@pytest.fixture
def sample_state_no_news_claims():
    """State where no claims are routed to news_media agent."""
    from tests.fixtures.sample_states import create_state_with_no_news_claims
    return create_state_with_no_news_claims()


@pytest.fixture
def sample_state_news_supply_chain():
    """State with supply chain claim for investigative news verification."""
    from tests.fixtures.sample_states import create_state_with_news_supply_chain_claim
    return create_state_with_news_supply_chain_claim()


# ============================================================================
# Judge Agent Mock Fixtures (FRD 11)
# ============================================================================


@pytest.fixture
def mock_openrouter_judge(mocker):
    """Mock OpenRouter for judge_agent LLM calls.
    
    Usage:
        def test_example(mock_openrouter_judge):
            mock_openrouter_judge('{"verdict": "verified", ...}')
            result = await judge_evidence(state)
    """
    def _mock_completion(response_content: str):
        mock_chat = AsyncMock(return_value=response_content)
        mocker.patch(
            "app.agents.judge_agent.openrouter_client.chat_completion",
            mock_chat
        )
        return mock_chat
    return _mock_completion


@pytest.fixture
def mock_openrouter_judge_sequence(mocker):
    """Mock OpenRouter with sequence for judge_agent multiple LLM calls.
    
    Usage:
        def test_example(mock_openrouter_judge_sequence):
            mock_openrouter_judge_sequence([
                '{"verdict": "verified", ...}',  # First claim
                '{"verdict": "insufficient_evidence", ...}',  # Second claim
            ])
    """
    def _mock_sequence(responses: list[str]):
        mock_chat = AsyncMock(side_effect=responses)
        mocker.patch(
            "app.agents.judge_agent.openrouter_client.chat_completion",
            mock_chat
        )
        return mock_chat
    return _mock_sequence


@pytest.fixture
def mock_openrouter_judge_error(mocker):
    """Mock OpenRouter to raise errors for judge_agent.
    
    Usage:
        def test_example(mock_openrouter_judge_error):
            mock_openrouter_judge_error(Exception("API timeout"))
    """
    def _mock_error(error: Exception):
        mock_chat = AsyncMock(side_effect=error)
        mocker.patch(
            "app.agents.judge_agent.openrouter_client.chat_completion",
            mock_chat
        )
        return mock_chat
    return _mock_error


# ============================================================================
# Judge Agent Sample State Fixtures
# ============================================================================


@pytest.fixture
def sample_state_judge_verified():
    """State with sufficient evidence for verified verdict."""
    from tests.fixtures.sample_states import create_state_with_verified_evidence
    return create_state_with_verified_evidence()


@pytest.fixture
def sample_state_judge_insufficient():
    """State with insufficient evidence, needs reinvestigation."""
    from tests.fixtures.sample_states import create_state_with_insufficient_evidence
    return create_state_with_insufficient_evidence()


@pytest.fixture
def sample_state_judge_contradicting():
    """State with contradicting evidence."""
    from tests.fixtures.sample_states import create_state_with_contradicting_evidence
    return create_state_with_contradicting_evidence()


@pytest.fixture
def sample_state_judge_no_evidence():
    """State with no evidence from any agent."""
    from tests.fixtures.sample_states import create_state_with_no_evidence
    return create_state_with_no_evidence()


@pytest.fixture
def sample_state_judge_errored_agents():
    """State where some agents errored."""
    from tests.fixtures.sample_states import create_state_with_errored_agents
    return create_state_with_errored_agents()


@pytest.fixture
def sample_state_judge_reinvestigation():
    """State simulating second iteration."""
    from tests.fixtures.sample_states import create_state_for_reinvestigation
    return create_state_for_reinvestigation()


@pytest.fixture
def sample_state_judge_max_iterations():
    """State at max iterations."""
    from tests.fixtures.sample_states import create_state_at_max_iterations
    return create_state_at_max_iterations()


@pytest.fixture
def sample_state_judge_multiple_claims():
    """State with multiple claims requiring different verdicts."""
    from tests.fixtures.sample_states import create_state_with_multiple_claims_mixed_verdicts
    return create_state_with_multiple_claims_mixed_verdicts()
