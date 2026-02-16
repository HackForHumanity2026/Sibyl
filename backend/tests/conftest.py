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
