"""Integration tests for Geography Agent node invocation.

Tests the full investigate_geography function with direct node invocation,
mocking all external dependencies (OpenRouter, MPC, Nominatim) to verify
the agent's behavior end-to-end without consuming tokens or network access.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.geography_agent import investigate_geography
from app.agents.state import (
    AgentFinding,
    AgentStatus,
    StreamEvent,
)
from tests.fixtures.mock_openrouter import (
    get_mock_geo_location_response,
    get_mock_geo_analysis_response,
)
from tests.fixtures.mock_satellite import (
    get_mock_stac_search_results,
    MOCK_GEOCODE_BORNEO,
    MOCK_GEOCODE_SURABAYA,
)
from tests.fixtures.sample_states import (
    create_state_with_geo_reforestation_claim,
    create_state_with_geo_facility_claim,
    create_state_with_geo_deforestation_claim,
    create_state_with_geo_multiple_claims,
    create_state_with_geo_reinvestigation,
    create_state_with_no_geo_claims,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_geo_agent(mocker):
    """Mock OpenRouter, MPC, and Nominatim for full geography agent testing."""

    def _configure(
        location_type: str = "reforestation",
        analysis_type: str = "reforestation",
        stac_scenario: str = "temporal_pair",
        geocode_result: tuple[float, float] | None = (-1.5, 113.5),
    ):
        # Mock OpenRouter: location extraction + satellite analysis
        location_response = get_mock_geo_location_response(location_type)
        analysis_response = get_mock_geo_analysis_response(analysis_type)

        mock_chat = AsyncMock(side_effect=[location_response, analysis_response])
        mocker.patch(
            "app.agents.geography_agent.openrouter_client.chat_completion",
            mock_chat,
        )

        # Mock geocoding service
        mock_geocode = AsyncMock(return_value=geocode_result)
        mocker.patch(
            "app.agents.geography_agent._geocode_location",
            mock_geocode,
        )

        # Mock satellite query
        stac_items = get_mock_stac_search_results(stac_scenario)
        mock_query = AsyncMock(return_value=stac_items)
        mocker.patch(
            "app.agents.geography_agent._query_satellite_imagery",
            mock_query,
        )

        return mock_chat, mock_geocode, mock_query

    return _configure


# ============================================================================
# Basic Invocation Tests
# ============================================================================


class TestGeographyAgentNodeBasic:
    """Tests for basic node invocation."""

    @pytest.mark.asyncio
    async def test_processes_reforestation_claim(self, mock_geo_agent):
        """Test processing a reforestation claim with temporal imagery."""
        mock_geo_agent("reforestation", "reforestation", "temporal_pair")
        state = create_state_with_geo_reforestation_claim()

        result = await investigate_geography(state)

        assert "findings" in result
        assert len(result["findings"]) >= 1
        finding = result["findings"][0]
        assert finding.agent_name == "geography"
        assert finding.evidence_type == "satellite_imagery"

    @pytest.mark.asyncio
    async def test_processes_facility_claim(self, mock_geo_agent):
        """Test processing a facility verification claim."""
        mock_geo_agent("facility", "facility", "recent_only", (-7.2575, 112.7521))
        state = create_state_with_geo_facility_claim()

        result = await investigate_geography(state)

        assert len(result["findings"]) >= 1
        finding = result["findings"][0]
        assert finding.evidence_type == "satellite_imagery"

    @pytest.mark.asyncio
    async def test_handles_no_assigned_claims(self):
        """Test when no claims are assigned to geography agent."""
        state = create_state_with_no_geo_claims()

        result = await investigate_geography(state)

        assert len(result["findings"]) == 0
        assert result["agent_status"]["geography"].status == "completed"
        assert result["agent_status"]["geography"].claims_assigned == 0


# ============================================================================
# Multiple Claims Tests
# ============================================================================


class TestGeographyAgentMultipleClaims:
    """Tests for processing multiple geographic claims."""

    @pytest.mark.asyncio
    async def test_processes_multiple_claims(self, mocker):
        """Test processing multiple claims."""
        # Build responses: for each claim, location extraction + analysis
        location_responses = [
            get_mock_geo_location_response("reforestation"),
            get_mock_geo_location_response("facility"),
            get_mock_geo_location_response("reforestation"),  # deforestation uses same pattern
        ]
        analysis_responses = [
            get_mock_geo_analysis_response("reforestation"),
            get_mock_geo_analysis_response("facility"),
            get_mock_geo_analysis_response("deforestation"),
        ]

        # Interleave: loc1, analysis1, loc2, analysis2, ...
        responses = []
        for loc, analysis in zip(location_responses, analysis_responses):
            responses.append(loc)
            responses.append(analysis)

        mocker.patch(
            "app.agents.geography_agent.openrouter_client.chat_completion",
            AsyncMock(side_effect=responses),
        )

        mocker.patch(
            "app.agents.geography_agent._geocode_location",
            AsyncMock(return_value=(-1.5, 113.5)),
        )

        stac_items = get_mock_stac_search_results("temporal_pair")
        mocker.patch(
            "app.agents.geography_agent._query_satellite_imagery",
            AsyncMock(return_value=stac_items),
        )

        state = create_state_with_geo_multiple_claims()

        result = await investigate_geography(state)

        assert len(result["findings"]) >= 3
        assert result["agent_status"]["geography"].claims_assigned == 3
        assert result["agent_status"]["geography"].claims_completed == 3


# ============================================================================
# StreamEvent Tests
# ============================================================================


class TestGeographyAgentEvents:
    """Tests for StreamEvent emissions."""

    @pytest.mark.asyncio
    async def test_emits_start_and_complete_events(self, mock_geo_agent):
        """Test agent_started and agent_completed events."""
        mock_geo_agent("reforestation", "reforestation")
        state = create_state_with_geo_reforestation_claim()

        result = await investigate_geography(state)

        events = result["events"]
        event_types = [e.event_type for e in events]

        assert "agent_started" in event_types
        assert "agent_completed" in event_types
        assert events[0].event_type == "agent_started"
        assert events[0].agent_name == "geography"
        assert events[-1].event_type == "agent_completed"

    @pytest.mark.asyncio
    async def test_emits_thinking_events(self, mock_geo_agent):
        """Test agent_thinking events during processing."""
        mock_geo_agent("reforestation", "reforestation")
        state = create_state_with_geo_reforestation_claim()

        result = await investigate_geography(state)

        events = result["events"]
        thinking_events = [e for e in events if e.event_type == "agent_thinking"]

        assert len(thinking_events) >= 1

    @pytest.mark.asyncio
    async def test_emits_evidence_found_with_image_urls(self, mock_geo_agent):
        """Test evidence_found event includes image references."""
        mock_geo_agent("reforestation", "reforestation")
        state = create_state_with_geo_reforestation_claim()

        result = await investigate_geography(state)

        events = result["events"]
        evidence_events = [e for e in events if e.event_type == "evidence_found"]

        assert len(evidence_events) >= 1
        ev = evidence_events[0]
        assert "claim_id" in ev.data
        assert "image_urls" in ev.data or "imagery_count" in ev.data


# ============================================================================
# No Imagery Tests
# ============================================================================


class TestGeographyAgentNoImagery:
    """Tests for scenarios with no available imagery."""

    @pytest.mark.asyncio
    async def test_handles_no_stac_items(self, mocker):
        """Test handling when MPC returns zero STAC items."""
        mocker.patch(
            "app.agents.geography_agent.openrouter_client.chat_completion",
            AsyncMock(side_effect=[
                get_mock_geo_location_response("reforestation"),
                get_mock_geo_analysis_response("reforestation"),
            ]),
        )

        mocker.patch(
            "app.agents.geography_agent._geocode_location",
            AsyncMock(return_value=(-1.5, 113.5)),
        )

        mocker.patch(
            "app.agents.geography_agent._query_satellite_imagery",
            AsyncMock(return_value=[]),  # No imagery
        )

        state = create_state_with_geo_reforestation_claim()

        result = await investigate_geography(state)

        assert len(result["findings"]) >= 1
        assert result["agent_status"]["geography"].status == "completed"

    @pytest.mark.asyncio
    async def test_handles_geocoding_failure(self, mocker):
        """Test handling when geocoding fails."""
        mocker.patch(
            "app.agents.geography_agent.openrouter_client.chat_completion",
            AsyncMock(return_value=get_mock_geo_location_response("reforestation")),
        )

        # Geocoding fails
        mocker.patch(
            "app.agents.geography_agent._geocode_location",
            AsyncMock(return_value=None),
        )

        state = create_state_with_geo_facility_claim()

        result = await investigate_geography(state)

        # Should produce a finding indicating geocoding failure
        assert len(result["findings"]) >= 1
        assert result["agent_status"]["geography"].status == "completed"


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestGeographyAgentErrorHandling:
    """Tests for error handling and graceful degradation."""

    @pytest.mark.asyncio
    async def test_handles_llm_failure_gracefully(self, mocker):
        """Test handling when all LLM calls fail."""
        mocker.patch(
            "app.agents.geography_agent.openrouter_client.chat_completion",
            AsyncMock(side_effect=Exception("LLM unavailable")),
        )

        state = create_state_with_geo_reforestation_claim()

        result = await investigate_geography(state)

        # Should still complete with findings (possibly error findings)
        assert len(result["findings"]) >= 1
        assert result["agent_status"]["geography"].status == "completed"

    @pytest.mark.asyncio
    async def test_handles_mpc_failure_gracefully(self, mocker):
        """Test handling when MPC query fails."""
        mocker.patch(
            "app.agents.geography_agent.openrouter_client.chat_completion",
            AsyncMock(side_effect=[
                get_mock_geo_location_response("reforestation"),
                get_mock_geo_analysis_response("reforestation"),
            ]),
        )

        mocker.patch(
            "app.agents.geography_agent._geocode_location",
            AsyncMock(return_value=(-1.5, 113.5)),
        )

        mocker.patch(
            "app.agents.geography_agent._query_satellite_imagery",
            AsyncMock(side_effect=Exception("MPC unavailable")),
        )

        state = create_state_with_geo_reforestation_claim()

        result = await investigate_geography(state)

        assert len(result["findings"]) >= 1
        assert result["agent_status"]["geography"].status == "completed"


# ============================================================================
# Re-Investigation Tests
# ============================================================================


class TestGeographyAgentReinvestigation:
    """Tests for re-investigation handling."""

    @pytest.mark.asyncio
    async def test_handles_reinvestigation(self, mock_geo_agent):
        """Test processing a re-investigation request."""
        mock_geo_agent("reforestation", "reforestation")
        state = create_state_with_geo_reinvestigation()

        result = await investigate_geography(state)

        assert len(result["findings"]) >= 1
        # Iteration should be 2 (reinvestigation)
        assert result["findings"][0].iteration == 2


# ============================================================================
# Agent Status Tests
# ============================================================================


class TestGeographyAgentStatus:
    """Tests for agent status management."""

    @pytest.mark.asyncio
    async def test_status_completed(self, mock_geo_agent):
        """Test agent status is 'completed' after processing."""
        mock_geo_agent("reforestation", "reforestation")
        state = create_state_with_geo_reforestation_claim()

        result = await investigate_geography(state)

        status = result["agent_status"]["geography"]
        assert status.status == "completed"
        assert status.claims_assigned == 1
        assert status.claims_completed == 1

    @pytest.mark.asyncio
    async def test_status_zero_claims(self):
        """Test agent status with no assigned claims."""
        state = create_state_with_no_geo_claims()

        result = await investigate_geography(state)

        status = result["agent_status"]["geography"]
        assert status.status == "completed"
        assert status.claims_assigned == 0
