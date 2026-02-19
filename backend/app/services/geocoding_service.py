"""Geocoding service using Nominatim (OpenStreetMap).

Implements FRD 10 Section 3.

Converts location names (e.g., "Borneo, Indonesia") to geographic
coordinates (latitude, longitude) for satellite imagery queries.

Features:
- Nominatim/OpenStreetMap geocoding (free, no API key)
- Rate limiting (1 request/second per Nominatim ToS)
- In-memory caching to reduce API calls
- Coordinate validation
"""

import asyncio
import logging
import time
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeocodingService:
    """Service for geocoding location names to coordinates."""

    def __init__(self):
        self.base_url = settings.GEOCODING_SERVICE_URL
        self.headers = {
            "User-Agent": "Sibyl-Geography-Agent/1.0 (sustainability-verification)"
        }
        self._cache: dict[str, tuple[float, float] | None] = {}
        self._last_request_time: float = 0.0
        self._rate_limit_seconds: float = settings.GEOCODING_RATE_LIMIT_SECONDS

    async def _rate_limit(self) -> None:
        """Enforce rate limiting (1 request per second)."""
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self._rate_limit_seconds:
            await asyncio.sleep(self._rate_limit_seconds - elapsed)
        self._last_request_time = time.monotonic()

    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> bool:
        """Validate that coordinates are within valid ranges.

        Args:
            lat: Latitude (-90 to 90)
            lon: Longitude (-180 to 180)

        Returns:
            True if coordinates are valid
        """
        return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0

    async def geocode(
        self,
        location_name: str,
        country_code: str | None = None,
    ) -> Optional[tuple[float, float]]:
        """Geocode a location name to (latitude, longitude).

        Args:
            location_name: Location name (e.g., "Borneo, Indonesia")
            country_code: Optional ISO country code to narrow results

        Returns:
            (latitude, longitude) tuple or None if not found
        """
        # Check cache
        cache_key = f"{location_name}:{country_code or ''}"
        if cache_key in self._cache:
            logger.debug("Geocoding cache hit: %s", location_name)
            return self._cache[cache_key]

        # Rate limit
        await self._rate_limit()

        # Build query params
        params: dict[str, str | int] = {
            "q": location_name,
            "format": "json",
            "limit": "5",
        }
        if country_code:
            params["countrycodes"] = country_code

        try:
            async with httpx.AsyncClient(
                headers=self.headers, timeout=10.0
            ) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()

                results = response.json()

                if not results:
                    logger.info("No geocoding results for: %s", location_name)
                    self._cache[cache_key] = None
                    return None

                # Take first (most relevant) result
                best = results[0]
                lat = float(best["lat"])
                lon = float(best["lon"])

                # Validate
                if not self.validate_coordinates(lat, lon):
                    logger.warning(
                        "Invalid coordinates for %s: (%f, %f)",
                        location_name, lat, lon,
                    )
                    self._cache[cache_key] = None
                    return None

                # Round to 4 decimal places (~11m precision)
                lat = round(lat, 4)
                lon = round(lon, 4)

                logger.info(
                    "Geocoded '%s' → (%f, %f) [%s]",
                    location_name, lat, lon,
                    best.get("display_name", ""),
                )

                result = (lat, lon)
                self._cache[cache_key] = result
                return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("Geocoding rate limited, retrying after delay")
                await asyncio.sleep(2.0)
                # Retry once
                return await self._geocode_retry(location_name, params, cache_key)
            logger.error("Geocoding HTTP error: %s", e)
            return None

        except Exception as e:
            logger.error("Geocoding error for '%s': %s", location_name, e)
            return None

    async def _geocode_retry(
        self,
        location_name: str,
        params: dict,
        cache_key: str,
    ) -> Optional[tuple[float, float]]:
        """Single retry after rate limiting."""
        try:
            async with httpx.AsyncClient(
                headers=self.headers, timeout=10.0
            ) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()

                results = response.json()
                if not results:
                    self._cache[cache_key] = None
                    return None

                best = results[0]
                lat = round(float(best["lat"]), 4)
                lon = round(float(best["lon"]), 4)

                if not self.validate_coordinates(lat, lon):
                    self._cache[cache_key] = None
                    return None

                result = (lat, lon)
                self._cache[cache_key] = result
                return result

        except Exception as e:
            logger.error("Geocoding retry failed for '%s': %s", location_name, e)
            return None

    async def geocode_with_context(
        self,
        location_name: str,
        claim_context: str,
    ) -> Optional[tuple[float, float, str]]:
        """Geocode with claim context to disambiguate.

        Returns:
            (latitude, longitude, matched_location_name) or None
        """
        result = await self.geocode(location_name)
        if result is not None:
            return (result[0], result[1], location_name)
        return None

    def clear_cache(self) -> None:
        """Clear the geocoding cache."""
        self._cache.clear()


# Singleton instance
geocoding_service = GeocodingService()
