"""Microsoft Planetary Computer query tool for Geography Agent.

Implements FRD 10 Section 2.

Provides satellite imagery access via pystac-client.
Used by:
- Geography Agent (FRD 10)

Data sources:
- Sentinel-2 multispectral imagery
- No API key required (free for non-commercial use)
"""

import logging
from typing import Optional

from langchain_core.tools import tool

from app.services.satellite_service import satellite_service

logger = logging.getLogger(__name__)


@tool
async def query_mpc(
    bbox: list[float],
    datetime_range: str,
    cloud_cover_max: Optional[float] = None,
    limit: int = 10,
) -> dict:
    """Query Microsoft Planetary Computer for Sentinel-2 satellite imagery.

    Args:
        bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
        datetime_range: ISO datetime range (e.g., "2024-01-01/2024-12-31")
        cloud_cover_max: Maximum cloud cover percentage (default: 20.0)
        limit: Maximum number of scenes to return (default: 10)

    Returns:
        Dictionary with search results:
        {
            "items": [
                {
                    "id": str,
                    "datetime": str,
                    "bbox": list,
                    "cloud_cover": float,
                    "assets": {band_name: url}
                },
                ...
            ],
            "total_items": int,
            "bbox": list,
            "datetime_range": str
        }
    """
    if cloud_cover_max is None:
        cloud_cover_max = 20.0

    # Ensure catalog is connected
    if satellite_service.catalog is None:
        await satellite_service.connect()

    items = satellite_service.search_sentinel2(
        bbox=bbox,
        datetime_range=datetime_range,
        cloud_cover_max=cloud_cover_max,
        limit=limit,
    )

    return {
        "items": items,
        "total_items": len(items),
        "bbox": bbox,
        "datetime_range": datetime_range,
    }


async def query_mpc_async(
    bbox: list[float],
    datetime_range: str,
    cloud_cover_max: float = 20.0,
    limit: int = 10,
) -> dict:
    """Direct async MPC query function (bypasses LangChain tool wrapper).

    Use this when calling from agent code directly.
    Same parameters and return value as query_mpc tool.
    """
    # Ensure catalog is connected
    if satellite_service.catalog is None:
        await satellite_service.connect()

    items = satellite_service.search_sentinel2(
        bbox=bbox,
        datetime_range=datetime_range,
        cloud_cover_max=cloud_cover_max,
        limit=limit,
    )

    return {
        "items": items,
        "total_items": len(items),
        "bbox": bbox,
        "datetime_range": datetime_range,
    }
