"""Unit tests for Geography Agent helper functions.

Tests location extraction, time range parsing, finding generation,
and Gemini analysis with mocked external dependencies.
"""

import json

import pytest
from unittest.mock import AsyncMock

from app.agents.geography_agent import (
    ExtractedLocation,
    SatelliteAnalysisResult,
    _extract_location,
    _extract_location_fallback,
    _extract_time_range,
    _create_geography_finding,
    _parse_area_hectares,
    _clean_json_response,
    _analyze_with_gemini,
    _get_reinvestigation_context,
)
from app.agents.state import Claim, ReinvestigationRequest
from tests.fixtures.sample_claims import (
    GEOGRAPHY_CLAIM_REFORESTATION,
    GEOGRAPHY_CLAIM_FACILITY,
    GEOGRAPHY_CLAIM_DEFORESTATION,
)
from tests.fixtures.mock_openrouter import (
    get_mock_geo_location_response,
    get_mock_geo_analysis_response,
)


# ============================================================================
# Location Extraction Tests
# ============================================================================


class TestLocationExtraction:
    """Tests for location extraction from claim text."""

    @pytest.mark.asyncio
    async def test_extracts_location_via_llm(self, mocker):
        """Test that location extraction uses LLM."""
        mock_response = get_mock_geo_location_response("reforestation")
        mock_chat = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.geography_agent.openrouter_client.chat_completion",
            mock_chat,
        )

        result = await _extract_location(GEOGRAPHY_CLAIM_REFORESTATION)

        assert isinstance(result, ExtractedLocation)
        assert result.location_name is not None
        assert result.confidence > 0.0

    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self, mocker):
        """Test fallback extraction when LLM fails."""
        mock_chat = AsyncMock(side_effect=Exception("API error"))
        mocker.patch(
            "app.agents.geography_agent.openrouter_client.chat_completion",
            mock_chat,
        )

        result = await _extract_location(GEOGRAPHY_CLAIM_REFORESTATION)

        assert isinstance(result, ExtractedLocation)

    def test_fallback_extracts_location_name(self):
        """Test that fallback extracts location from 'in X' pattern."""
        result = _extract_location_fallback(GEOGRAPHY_CLAIM_REFORESTATION)
        # Should find "Central Kalimantan" or similar
        assert result.location_name is not None or result.confidence > 0

    def test_fallback_extracts_time_range(self):
        """Test fallback extracts 'since 2020' pattern."""
        result = _extract_location_fallback(GEOGRAPHY_CLAIM_REFORESTATION)
        assert result.time_range is not None
        assert result.time_range[0].startswith("2020")

    def test_fallback_extracts_area(self):
        """Test fallback extracts '5,000 hectares' pattern."""
        result = _extract_location_fallback(GEOGRAPHY_CLAIM_REFORESTATION)
        assert result.area_description is not None
        assert "hectares" in result.area_description.lower() or "5" in result.area_description


# ============================================================================
# Time Range Extraction Tests
# ============================================================================


class TestTimeRangeExtraction:
    """Tests for time range extraction from claim text."""

    def test_since_pattern(self):
        """Test 'since YYYY' pattern."""
        result = _extract_time_range("restored 5,000 hectares since 2020")
        assert result is not None
        assert result[0] == "2020-01-01"

    def test_from_to_pattern(self):
        """Test 'from YYYY to YYYY' pattern."""
        result = _extract_time_range("from 2020 to 2024 we reduced emissions")
        assert result is not None
        assert result[0] == "2020-01-01"
        assert result[1] == "2024-12-31"

    def test_between_and_pattern(self):
        """Test 'between YYYY and YYYY' pattern."""
        result = _extract_time_range("between 2019 and 2023")
        assert result is not None
        assert result[0] == "2019-01-01"
        assert result[1] == "2023-12-31"

    def test_in_year_pattern(self):
        """Test 'in YYYY' pattern."""
        result = _extract_time_range("installed solar panels in 2024")
        assert result is not None
        assert result[0] == "2024-01-01"
        assert result[1] == "2024-12-31"

    def test_no_time_range(self):
        """Test text without time references."""
        result = _extract_time_range("our facility has green space")
        assert result is None


# ============================================================================
# Area Parsing Tests
# ============================================================================


class TestAreaParsing:
    """Tests for area parsing from description strings."""

    def test_parse_hectares(self):
        """Test parsing '5,000 hectares'."""
        result = _parse_area_hectares("5,000 hectares")
        assert result == 5000.0

    def test_parse_ha(self):
        """Test parsing '50 ha'."""
        result = _parse_area_hectares("50 ha")
        assert result == 50.0

    def test_parse_none(self):
        """Test parsing None input."""
        result = _parse_area_hectares(None)
        assert result is None

    def test_parse_no_area(self):
        """Test parsing text without area."""
        result = _parse_area_hectares("some random text")
        assert result is None


# ============================================================================
# Gemini Analysis Tests
# ============================================================================


class TestGeminiAnalysis:
    """Tests for Gemini 2.5 Pro satellite analysis."""

    @pytest.mark.asyncio
    async def test_analyzes_reforestation(self, mocker):
        """Test Gemini analysis of reforestation data."""
        mock_response = get_mock_geo_analysis_response("reforestation")
        mock_chat = AsyncMock(return_value=mock_response)
        mocker.patch(
            "app.agents.geography_agent.openrouter_client.chat_completion",
            mock_chat,
        )

        location = ExtractedLocation(
            location_name="Central Kalimantan",
            coordinates=[-1.5, 113.5],
            confidence=0.9,
        )

        stac_items = [
            {"id": "item1", "datetime": "2024-06-20", "cloud_cover": 5.0, "assets": {}},
        ]

        result = await _analyze_with_gemini(
            claim=GEOGRAPHY_CLAIM_REFORESTATION,
            location=location,
            stac_items=stac_items,
        )

        assert isinstance(result, SatelliteAnalysisResult)
        assert result.confidence >= 0.0

    @pytest.mark.asyncio
    async def test_handles_analysis_failure(self, mocker):
        """Test graceful handling when Gemini fails."""
        mock_chat = AsyncMock(side_effect=Exception("API error"))
        mocker.patch(
            "app.agents.geography_agent.openrouter_client.chat_completion",
            mock_chat,
        )

        location = ExtractedLocation(
            location_name="Test Location",
            coordinates=[0.0, 0.0],
            confidence=0.5,
        )

        result = await _analyze_with_gemini(
            claim=GEOGRAPHY_CLAIM_REFORESTATION,
            location=location,
            stac_items=[],
        )

        assert isinstance(result, SatelliteAnalysisResult)
        assert result.supports_claim is None
        assert result.confidence == 0.0


# ============================================================================
# Finding Generation Tests
# ============================================================================


class TestFindingGeneration:
    """Tests for geography finding generation."""

    def test_creates_finding_with_satellite_evidence(self):
        """Test creating a finding with satellite imagery evidence."""
        location = ExtractedLocation(
            location_name="Central Kalimantan",
            coordinates=[-1.5, 113.5],
            confidence=0.9,
        )

        analysis = SatelliteAnalysisResult(
            supports_claim=True,
            confidence=0.82,
            observed_features=["dense_forest", "reforestation_pattern"],
            ndvi_estimate=0.68,
            change_detected=True,
            change_area_hectares=4200.0,
            reasoning="Satellite imagery shows reforestation.",
        )

        stac_items = [
            {
                "id": "S2A_20240620",
                "datetime": "2024-06-20",
                "cloud_cover": 5.0,
                "assets": {},
            },
        ]

        finding = _create_geography_finding(
            claim=GEOGRAPHY_CLAIM_REFORESTATION,
            location=location,
            analysis=analysis,
            stac_items=stac_items,
            ndvi_stats={"mean": 0.68, "vegetation_percentage": 85.0},
            change_metrics={"change_direction": "increase", "change_area_hectares": 4200.0},
            land_cover=None,
            iteration=1,
        )

        assert finding.agent_name == "geography"
        assert finding.evidence_type == "satellite_imagery"
        assert finding.supports_claim is True
        assert finding.confidence == "high"
        assert "image_references" in finding.details
        assert len(finding.details["image_references"]) >= 1
        assert "ndvi_values" in finding.details
        assert "change_metrics" in finding.details

    def test_creates_finding_no_imagery(self):
        """Test creating a finding when no imagery is available."""
        location = ExtractedLocation(
            location_name="Remote Location",
            coordinates=[0.0, 0.0],
            confidence=0.5,
        )

        analysis = SatelliteAnalysisResult(
            supports_claim=None,
            confidence=0.1,
            reasoning="No satellite imagery available.",
            limitations=["No Sentinel-2 coverage for this area"],
        )

        finding = _create_geography_finding(
            claim=GEOGRAPHY_CLAIM_FACILITY,
            location=location,
            analysis=analysis,
            stac_items=[],
            ndvi_stats=None,
            change_metrics=None,
            land_cover=None,
            iteration=1,
        )

        assert finding.supports_claim is None
        assert finding.confidence == "low"


# ============================================================================
# Re-investigation Tests
# ============================================================================


class TestReinvestigation:
    """Tests for re-investigation context retrieval."""

    def test_finds_reinvestigation_request(self):
        """Test finding a re-investigation request for geography agent."""
        state = {
            "reinvestigation_requests": [
                ReinvestigationRequest(
                    claim_id="claim-123",
                    target_agents=["geography"],
                    evidence_gap="Need higher resolution",
                    refined_queries=["Focus on northern sector"],
                ),
            ],
        }

        result = _get_reinvestigation_context(state, "claim-123")
        assert result is not None
        assert result.claim_id == "claim-123"

    def test_no_reinvestigation_request(self):
        """Test when no re-investigation request exists."""
        state = {"reinvestigation_requests": []}
        result = _get_reinvestigation_context(state, "claim-123")
        assert result is None

    def test_reinvestigation_wrong_agent(self):
        """Test when re-investigation targets a different agent."""
        state = {
            "reinvestigation_requests": [
                ReinvestigationRequest(
                    claim_id="claim-123",
                    target_agents=["legal"],
                    evidence_gap="Need compliance check",
                ),
            ],
        }

        result = _get_reinvestigation_context(state, "claim-123")
        assert result is None


# ============================================================================
# Utility Tests
# ============================================================================


class TestUtilities:
    """Tests for utility functions."""

    def test_clean_json_response(self):
        """Test JSON response cleaning."""
        raw = '```json\n{"key": "value"}\n```'
        cleaned = _clean_json_response(raw)
        assert json.loads(cleaned) == {"key": "value"}
