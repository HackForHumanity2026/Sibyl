"""Unit tests for Geocoding Service.

Tests geocoding with mocked Nominatim API responses.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.geocoding_service import GeocodingService
from tests.fixtures.mock_satellite import (
    MOCK_NOMINATIM_RESPONSE_BORNEO,
    MOCK_NOMINATIM_RESPONSE_SURABAYA,
    MOCK_NOMINATIM_RESPONSE_EMPTY,
)


class TestGeocodingService:
    """Tests for GeocodingService."""

    @pytest.fixture
    def service(self):
        """Create a fresh GeocodingService for each test."""
        svc = GeocodingService()
        svc._rate_limit_seconds = 0.0  # Disable rate limiting for tests
        return svc

    @pytest.mark.asyncio
    async def test_geocode_borneo(self, service, mocker):
        """Test geocoding 'Central Kalimantan, Borneo'."""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_NOMINATIM_RESPONSE_BORNEO
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        mocker.patch("app.services.geocoding_service.httpx.AsyncClient", return_value=mock_client)

        result = await service.geocode("Central Kalimantan, Borneo, Indonesia")

        assert result is not None
        lat, lon = result
        assert lat == pytest.approx(-1.5, abs=0.01)
        assert lon == pytest.approx(113.5, abs=0.01)

    @pytest.mark.asyncio
    async def test_geocode_surabaya(self, service, mocker):
        """Test geocoding 'Surabaya, Indonesia'."""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_NOMINATIM_RESPONSE_SURABAYA
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        mocker.patch("app.services.geocoding_service.httpx.AsyncClient", return_value=mock_client)

        result = await service.geocode("Surabaya, Indonesia")

        assert result is not None
        lat, lon = result
        assert lat == pytest.approx(-7.2575, abs=0.01)
        assert lon == pytest.approx(112.7521, abs=0.01)

    @pytest.mark.asyncio
    async def test_geocode_not_found(self, service, mocker):
        """Test geocoding a location that returns no results."""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_NOMINATIM_RESPONSE_EMPTY
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        mocker.patch("app.services.geocoding_service.httpx.AsyncClient", return_value=mock_client)

        result = await service.geocode("Nonexistent Place XYZ123")

        assert result is None

    @pytest.mark.asyncio
    async def test_geocode_caching(self, service, mocker):
        """Test that repeated geocoding uses cache."""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_NOMINATIM_RESPONSE_BORNEO
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        mocker.patch("app.services.geocoding_service.httpx.AsyncClient", return_value=mock_client)

        # First call
        result1 = await service.geocode("Central Kalimantan, Borneo, Indonesia")
        # Second call (should use cache)
        result2 = await service.geocode("Central Kalimantan, Borneo, Indonesia")

        assert result1 == result2
        # Only one HTTP call should have been made
        assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_geocode_with_country_code(self, service, mocker):
        """Test geocoding with country code parameter."""
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_NOMINATIM_RESPONSE_SURABAYA
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        mocker.patch("app.services.geocoding_service.httpx.AsyncClient", return_value=mock_client)

        result = await service.geocode("Surabaya", country_code="id")

        assert result is not None

    @pytest.mark.asyncio
    async def test_geocode_network_error(self, service, mocker):
        """Test handling of network errors."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        mocker.patch("app.services.geocoding_service.httpx.AsyncClient", return_value=mock_client)

        result = await service.geocode("Some Location")

        assert result is None

    def test_validate_coordinates_valid(self):
        """Test coordinate validation with valid inputs."""
        assert GeocodingService.validate_coordinates(0.0, 0.0)
        assert GeocodingService.validate_coordinates(-90.0, -180.0)
        assert GeocodingService.validate_coordinates(90.0, 180.0)

    def test_validate_coordinates_invalid(self):
        """Test coordinate validation with invalid inputs."""
        assert not GeocodingService.validate_coordinates(91.0, 0.0)
        assert not GeocodingService.validate_coordinates(0.0, 181.0)
        assert not GeocodingService.validate_coordinates(-91.0, 0.0)

    def test_clear_cache(self, service):
        """Test cache clearing."""
        service._cache["test:"] = (1.0, 2.0)
        assert len(service._cache) == 1
        service.clear_cache()
        assert len(service._cache) == 0
