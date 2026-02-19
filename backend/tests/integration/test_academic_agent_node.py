"""Integration tests for Academic/Research Agent node invocation.

Tests the full investigate_academic function with direct node invocation,
mocking all external dependencies (OpenRouter, Tavily) to verify
the agent's behavior end-to-end without consuming tokens.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.agents.academic_agent import investigate_academic
from app.agents.state import (
    AgentFinding,
    AgentStatus,
    StreamEvent,
    InfoRequest,
    InfoResponse,
    ReinvestigationRequest,
)
from tests.fixtures.mock_openrouter import (
    get_mock_academic_query_response,
    get_mock_academic_analysis_response,
)
from tests.fixtures.mock_tavily import get_formatted_tavily_response
from tests.fixtures.sample_claims import (
    ACADEMIC_CLAIM_METHODOLOGY,
    ACADEMIC_CLAIM_CERTIFICATION,
    ACADEMIC_CLAIM_SBTI,
    ACADEMIC_CLAIM_BENCHMARK,
    ROUTING_ACADEMIC_METHODOLOGY,
    ROUTING_ACADEMIC_CERTIFICATION,
    ROUTING_ACADEMIC_SBTI,
    ROUTING_ACADEMIC_BENCHMARK,
    ROUTING_NO_ACADEMIC,
)
from tests.fixtures.sample_states import (
    create_state_with_academic_methodology_claim,
    create_state_with_academic_certification_claim,
    create_state_with_academic_sbti_claim,
    create_state_with_academic_multiple_claims,
    create_state_with_academic_reinvestigation,
    create_state_with_no_academic_claims,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_academic_agent(mocker):
    """Mock both Tavily and OpenRouter for full academic agent testing.

    Returns a function that configures the mocks.
    """

    def _configure(
        investigation_type: str = "methodology",
    ):
        # Mock Tavily search
        tavily_response = get_formatted_tavily_response("supporting")
        mocker.patch(
            "app.agents.academic_agent.search_web_async",
            AsyncMock(return_value=tavily_response),
        )

        # Mock OpenRouter: first call = query construction, second = analysis
        query_response = get_mock_academic_query_response(investigation_type)
        analysis_response = get_mock_academic_analysis_response(investigation_type)

        mock_chat = AsyncMock(side_effect=[query_response, analysis_response])
        mocker.patch(
            "app.agents.academic_agent.openrouter_client.chat_completion",
            mock_chat,
        )

        return mock_chat

    return _configure


# ============================================================================
# Basic Invocation Tests
# ============================================================================


class TestAcademicAgentNodeBasic:
    """Tests for basic node invocation."""

    @pytest.mark.asyncio
    async def test_processes_methodology_claim(self, mock_academic_agent):
        """Test processing a methodology validation claim."""
        mock_academic_agent("methodology")
        state = create_state_with_academic_methodology_claim()

        result = await investigate_academic(state)

        assert "findings" in result
        assert len(result["findings"]) >= 1
        assert result["findings"][0].agent_name == "academic"
        assert result["findings"][0].evidence_type == "methodology_validation"

    @pytest.mark.asyncio
    async def test_processes_certification_claim(self, mock_academic_agent):
        """Test processing a certification validation claim."""
        mock_academic_agent("certification")
        state = create_state_with_academic_certification_claim()

        result = await investigate_academic(state)

        assert "findings" in result
        assert len(result["findings"]) >= 1
        finding = result["findings"][0]
        assert finding.evidence_type == "certification_validation"

    @pytest.mark.asyncio
    async def test_processes_sbti_claim(self, mock_academic_agent):
        """Test processing an SBTi validation claim."""
        mock_academic_agent("sbti")
        state = create_state_with_academic_sbti_claim()

        result = await investigate_academic(state)

        assert "findings" in result
        assert len(result["findings"]) >= 1
        finding = result["findings"][0]
        assert finding.evidence_type == "sbti_validation"

    @pytest.mark.asyncio
    async def test_handles_no_assigned_claims(self, mock_academic_agent):
        """Test handling when no claims are assigned to academic agent."""
        state = create_state_with_no_academic_claims()

        result = await investigate_academic(state)

        assert len(result["findings"]) == 0
        assert result["agent_status"]["academic"].status == "completed"
        assert result["agent_status"]["academic"].claims_assigned == 0


# ============================================================================
# Multiple Claims Tests
# ============================================================================


class TestAcademicAgentMultipleClaims:
    """Tests for processing multiple claims."""

    @pytest.mark.asyncio
    async def test_processes_multiple_claims(self, mocker):
        """Test processing multiple claims of different types."""
        tavily_response = get_formatted_tavily_response("supporting")
        mocker.patch(
            "app.agents.academic_agent.search_web_async",
            AsyncMock(return_value=tavily_response),
        )

        # Build response sequence: for each claim, query construction + analysis
        responses = []
        for inv_type in ["methodology", "certification", "sbti", "benchmark"]:
            responses.append(get_mock_academic_query_response(inv_type))
            responses.append(get_mock_academic_analysis_response(inv_type))

        mocker.patch(
            "app.agents.academic_agent.openrouter_client.chat_completion",
            AsyncMock(side_effect=responses),
        )

        state = create_state_with_academic_multiple_claims()

        result = await investigate_academic(state)

        assert len(result["findings"]) >= 4
        assert result["agent_status"]["academic"].claims_assigned == 4
        assert result["agent_status"]["academic"].claims_completed == 4


# ============================================================================
# StreamEvent Tests
# ============================================================================


class TestAcademicAgentEvents:
    """Tests for StreamEvent emissions."""

    @pytest.mark.asyncio
    async def test_emits_start_and_complete_events(self, mock_academic_agent):
        """Test that agent_started and agent_completed events are emitted."""
        mock_academic_agent("methodology")
        state = create_state_with_academic_methodology_claim()

        result = await investigate_academic(state)

        events = result["events"]
        event_types = [e.event_type for e in events]

        assert "agent_started" in event_types
        assert "agent_completed" in event_types

        # Verify start is first
        assert events[0].event_type == "agent_started"
        assert events[0].agent_name == "academic"

        # Verify completed is last
        assert events[-1].event_type == "agent_completed"
        assert events[-1].data["claims_processed"] >= 1

    @pytest.mark.asyncio
    async def test_emits_thinking_events(self, mock_academic_agent):
        """Test that agent_thinking events are emitted during processing."""
        mock_academic_agent("methodology")
        state = create_state_with_academic_methodology_claim()

        result = await investigate_academic(state)

        events = result["events"]
        thinking_events = [e for e in events if e.event_type == "agent_thinking"]

        assert len(thinking_events) >= 1

    @pytest.mark.asyncio
    async def test_emits_evidence_found_event(self, mock_academic_agent):
        """Test that evidence_found events are emitted for findings."""
        mock_academic_agent("methodology")
        state = create_state_with_academic_methodology_claim()

        result = await investigate_academic(state)

        events = result["events"]
        evidence_events = [e for e in events if e.event_type == "evidence_found"]

        assert len(evidence_events) >= 1
        assert "claim_id" in evidence_events[0].data


# ============================================================================
# Re-Investigation Tests
# ============================================================================


class TestAcademicAgentReinvestigation:
    """Tests for re-investigation handling."""

    @pytest.mark.asyncio
    async def test_handles_reinvestigation_request(self, mocker):
        """Test that re-investigation uses refined queries."""
        tavily_response = get_formatted_tavily_response("supporting")
        mock_search = AsyncMock(return_value=tavily_response)
        mocker.patch(
            "app.agents.academic_agent.search_web_async",
            mock_search,
        )

        # Only analysis call (no query construction for reinvestigation)
        analysis_response = get_mock_academic_analysis_response("certification")
        mocker.patch(
            "app.agents.academic_agent.openrouter_client.chat_completion",
            AsyncMock(return_value=analysis_response),
        )

        state = create_state_with_academic_reinvestigation()

        result = await investigate_academic(state)

        assert len(result["findings"]) >= 1
        # Verify search was called with refined queries
        assert mock_search.call_count >= 1
        # Verify iteration is > 1
        assert result["findings"][0].iteration == 2


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestAcademicAgentErrorHandling:
    """Tests for error handling and graceful degradation."""

    @pytest.mark.asyncio
    async def test_handles_complete_search_failure(self, mocker):
        """Test graceful handling when all searches fail."""
        from app.agents.tools.search_web import SearchAPIError

        mocker.patch(
            "app.agents.academic_agent.search_web_async",
            AsyncMock(side_effect=SearchAPIError("All searches failed")),
        )

        # Query construction still works
        query_response = get_mock_academic_query_response("methodology")
        analysis_response = get_mock_academic_analysis_response("methodology")
        mocker.patch(
            "app.agents.academic_agent.openrouter_client.chat_completion",
            AsyncMock(side_effect=[query_response, analysis_response]),
        )

        state = create_state_with_academic_methodology_claim()

        result = await investigate_academic(state)

        # Should still produce findings (with limited evidence)
        assert len(result["findings"]) >= 1
        assert result["agent_status"]["academic"].status == "completed"

    @pytest.mark.asyncio
    async def test_handles_llm_failure_gracefully(self, mocker):
        """Test graceful handling when LLM calls fail."""
        tavily_response = get_formatted_tavily_response("supporting")
        mocker.patch(
            "app.agents.academic_agent.search_web_async",
            AsyncMock(return_value=tavily_response),
        )

        # Both LLM calls fail
        mocker.patch(
            "app.agents.academic_agent.openrouter_client.chat_completion",
            AsyncMock(side_effect=Exception("LLM unavailable")),
        )

        state = create_state_with_academic_methodology_claim()

        result = await investigate_academic(state)

        # Should still complete with at least one finding
        assert len(result["findings"]) >= 1
        assert result["agent_status"]["academic"].status == "completed"


# ============================================================================
# Agent Status Tests
# ============================================================================


class TestAcademicAgentStatus:
    """Tests for agent status management."""

    @pytest.mark.asyncio
    async def test_status_updates_correctly(self, mock_academic_agent):
        """Test that agent status transitions correctly."""
        mock_academic_agent("methodology")
        state = create_state_with_academic_methodology_claim()

        result = await investigate_academic(state)

        status = result["agent_status"]["academic"]
        assert status.status == "completed"
        assert status.claims_assigned == 1
        assert status.claims_completed == 1

    @pytest.mark.asyncio
    async def test_status_zero_claims(self):
        """Test agent status when no claims are assigned."""
        state = create_state_with_no_academic_claims()

        result = await investigate_academic(state)

        status = result["agent_status"]["academic"]
        assert status.status == "completed"
        assert status.claims_assigned == 0
        assert status.claims_completed == 0
