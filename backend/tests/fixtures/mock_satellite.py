"""Mock satellite service responses for Geography Agent testing.

Provides pre-defined STAC search results and satellite imagery metadata
for testing without requiring network access to Microsoft Planetary Computer.
"""

from datetime import datetime


# ============================================================================
# Mock STAC Search Results
# ============================================================================

MOCK_STAC_ITEM_RECENT = {
    "id": "S2A_MSIL2A_20240620T023551_N0214_R089_T49MGV_20240620T060552",
    "datetime": "2024-06-20T02:35:51Z",
    "bbox": [112.0, -1.5, 114.0, 0.0],
    "cloud_cover": 5.2,
    "assets": {
        "B02": "https://planetarycomputer.microsoft.com/api/data/v1/item/sentinel-2-l2a/S2A_20240620/B02.tif",
        "B03": "https://planetarycomputer.microsoft.com/api/data/v1/item/sentinel-2-l2a/S2A_20240620/B03.tif",
        "B04": "https://planetarycomputer.microsoft.com/api/data/v1/item/sentinel-2-l2a/S2A_20240620/B04.tif",
        "B08": "https://planetarycomputer.microsoft.com/api/data/v1/item/sentinel-2-l2a/S2A_20240620/B08.tif",
        "B11": "https://planetarycomputer.microsoft.com/api/data/v1/item/sentinel-2-l2a/S2A_20240620/B11.tif",
        "B12": "https://planetarycomputer.microsoft.com/api/data/v1/item/sentinel-2-l2a/S2A_20240620/B12.tif",
        "visual": "https://planetarycomputer.microsoft.com/api/data/v1/item/sentinel-2-l2a/S2A_20240620/visual.tif",
    },
}

MOCK_STAC_ITEM_BASELINE = {
    "id": "S2A_MSIL2A_20200615T023551_N0214_R089_T49MGV_20200615T060552",
    "datetime": "2020-06-15T02:35:51Z",
    "bbox": [112.0, -1.5, 114.0, 0.0],
    "cloud_cover": 8.1,
    "assets": {
        "B02": "https://planetarycomputer.microsoft.com/api/data/v1/item/sentinel-2-l2a/S2A_20200615/B02.tif",
        "B03": "https://planetarycomputer.microsoft.com/api/data/v1/item/sentinel-2-l2a/S2A_20200615/B03.tif",
        "B04": "https://planetarycomputer.microsoft.com/api/data/v1/item/sentinel-2-l2a/S2A_20200615/B04.tif",
        "B08": "https://planetarycomputer.microsoft.com/api/data/v1/item/sentinel-2-l2a/S2A_20200615/B08.tif",
        "B11": "https://planetarycomputer.microsoft.com/api/data/v1/item/sentinel-2-l2a/S2A_20200615/B11.tif",
        "B12": "https://planetarycomputer.microsoft.com/api/data/v1/item/sentinel-2-l2a/S2A_20200615/B12.tif",
        "visual": "https://planetarycomputer.microsoft.com/api/data/v1/item/sentinel-2-l2a/S2A_20200615/visual.tif",
    },
}

MOCK_STAC_ITEM_CLOUDY = {
    "id": "S2A_MSIL2A_20240720T023551_N0214_R089_T49MGV_20240720T060552",
    "datetime": "2024-07-20T02:35:51Z",
    "bbox": [112.0, -1.5, 114.0, 0.0],
    "cloud_cover": 65.0,
    "assets": {
        "B04": "https://planetarycomputer.microsoft.com/api/data/v1/item/sentinel-2-l2a/S2A_20240720/B04.tif",
        "B08": "https://planetarycomputer.microsoft.com/api/data/v1/item/sentinel-2-l2a/S2A_20240720/B08.tif",
    },
}


# ============================================================================
# Mock Geocoding Responses
# ============================================================================

MOCK_GEOCODE_BORNEO = {
    "lat": -1.5,
    "lon": 113.5,
    "display_name": "Central Kalimantan, Borneo, Indonesia",
}

MOCK_GEOCODE_SURABAYA = {
    "lat": -7.2575,
    "lon": 112.7521,
    "display_name": "Surabaya, East Java, Indonesia",
}

MOCK_GEOCODE_SUMATRA = {
    "lat": 0.5897,
    "lon": 101.3431,
    "display_name": "Sumatra, Indonesia",
}

MOCK_GEOCODE_CHENNAI = {
    "lat": 13.0827,
    "lon": 80.2707,
    "display_name": "Chennai, Tamil Nadu, India",
}


# ============================================================================
# Mock Nominatim API Responses (raw JSON from the API)
# ============================================================================

MOCK_NOMINATIM_RESPONSE_BORNEO = [
    {
        "place_id": 123456,
        "licence": "Data OpenStreetMap contributors",
        "osm_type": "relation",
        "osm_id": 2345678,
        "lat": "-1.5",
        "lon": "113.5",
        "display_name": "Central Kalimantan, Borneo, Indonesia",
        "class": "boundary",
        "type": "administrative",
        "importance": 0.75,
    }
]

MOCK_NOMINATIM_RESPONSE_SURABAYA = [
    {
        "place_id": 234567,
        "licence": "Data OpenStreetMap contributors",
        "osm_type": "relation",
        "osm_id": 3456789,
        "lat": "-7.2575",
        "lon": "112.7521",
        "display_name": "Surabaya, East Java, Indonesia",
        "class": "place",
        "type": "city",
        "importance": 0.85,
    }
]

MOCK_NOMINATIM_RESPONSE_EMPTY = []


# ============================================================================
# Mock NDVI Data
# ============================================================================

MOCK_NDVI_STATS_BEFORE = {
    "mean": 0.35,
    "median": 0.33,
    "std": 0.15,
    "vegetation_percentage": 45.0,
    "dense_vegetation_percentage": 10.0,
}

MOCK_NDVI_STATS_AFTER = {
    "mean": 0.68,
    "median": 0.70,
    "std": 0.12,
    "vegetation_percentage": 85.0,
    "dense_vegetation_percentage": 55.0,
}

MOCK_CHANGE_DETECTION = {
    "change_area_hectares": 4200.0,
    "ndvi_mean_before": 0.35,
    "ndvi_mean_after": 0.68,
    "change_direction": "increase",
    "change_percentage": 94.3,
}


# ============================================================================
# Helper Functions
# ============================================================================


def get_mock_stac_search_results(
    scenario: str = "temporal_pair",
) -> list[dict]:
    """Get mock STAC search results for various scenarios.

    Args:
        scenario: One of "temporal_pair", "recent_only", "cloudy", "empty"

    Returns:
        List of STAC item dicts
    """
    if scenario == "temporal_pair":
        return [MOCK_STAC_ITEM_RECENT, MOCK_STAC_ITEM_BASELINE]
    elif scenario == "recent_only":
        return [MOCK_STAC_ITEM_RECENT]
    elif scenario == "cloudy":
        return [MOCK_STAC_ITEM_CLOUDY]
    elif scenario == "empty":
        return []
    return [MOCK_STAC_ITEM_RECENT]


def get_mock_geocode_result(location: str = "borneo") -> dict | None:
    """Get a mock geocoding result.

    Args:
        location: One of "borneo", "surabaya", "sumatra", "chennai", "unknown"

    Returns:
        Geocode dict or None for unknown
    """
    results = {
        "borneo": MOCK_GEOCODE_BORNEO,
        "surabaya": MOCK_GEOCODE_SURABAYA,
        "sumatra": MOCK_GEOCODE_SUMATRA,
        "chennai": MOCK_GEOCODE_CHENNAI,
    }
    return results.get(location)
