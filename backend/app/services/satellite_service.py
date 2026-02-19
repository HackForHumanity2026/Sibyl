"""Satellite imagery service using Microsoft Planetary Computer.

Implements FRD 10 Sections 2, 4-9.

Provides:
- Sentinel-2 imagery retrieval via pystac-client
- Bounding box computation from coordinates
- NDVI calculation for vegetation change detection
- Land cover classification (rule-based)
- Temporal comparison (before/after change detection)
- NDVI statistics computation
"""

import logging
import math
from typing import Optional

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class SatelliteService:
    """Service for querying and processing satellite imagery from MPC."""

    def __init__(self):
        self.stac_url = settings.MPC_STAC_URL
        self.collection = settings.MPC_COLLECTION
        self.catalog = None

    async def connect(self) -> None:
        """Connect to MPC STAC catalog.

        Uses pystac-client to open the STAC catalog.
        No API key required.
        """
        try:
            from pystac_client import Client

            self.catalog = Client.open(self.stac_url)
            logger.info("Connected to MPC STAC catalog: %s", self.stac_url)
        except ImportError:
            logger.error("pystac-client not installed")
            raise
        except Exception as e:
            logger.error("Failed to connect to MPC: %s", e)
            raise

    def search_sentinel2(
        self,
        bbox: list[float],
        datetime_range: str,
        cloud_cover_max: float = 20.0,
        limit: int = 10,
    ) -> list[dict]:
        """Search Sentinel-2 collection for scenes matching criteria.

        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            datetime_range: ISO datetime string or range (e.g., "2024-01-01/2024-12-31")
            cloud_cover_max: Maximum acceptable cloud cover percentage
            limit: Maximum number of items to return

        Returns:
            List of STAC Item dictionaries with metadata and asset links.
        """
        if self.catalog is None:
            raise RuntimeError("STAC catalog not connected. Call connect() first.")

        try:
            search = self.catalog.search(
                collections=[self.collection],
                bbox=bbox,
                datetime=datetime_range,
                query={"eo:cloud_cover": {"lt": cloud_cover_max}},
                limit=limit,
            )

            items = []
            for item in search.items():
                items.append({
                    "id": item.id,
                    "datetime": item.datetime.isoformat() if item.datetime else None,
                    "bbox": list(item.bbox) if item.bbox else None,
                    "cloud_cover": item.properties.get("eo:cloud_cover", 100.0),
                    "assets": {
                        band: asset.href
                        for band, asset in item.assets.items()
                    },
                })

            logger.info(
                "Found %d Sentinel-2 scenes (bbox=%s, datetime=%s, cloud<%s%%)",
                len(items), bbox, datetime_range, cloud_cover_max,
            )
            return items

        except Exception as e:
            logger.error("STAC search failed: %s", e)
            return []

    def get_item_assets(
        self,
        item: dict,
        bands: list[str] | None = None,
    ) -> dict[str, str]:
        """Get asset URLs for specific spectral bands of a STAC Item.

        Args:
            item: STAC Item dictionary from search results
            bands: List of band names to retrieve. Default: ["B04", "B08"]

        Returns:
            Dictionary mapping band names to asset URLs.
        """
        if bands is None:
            bands = ["B04", "B08"]

        assets = item.get("assets", {})
        result = {}
        for band in bands:
            if band in assets:
                result[band] = assets[band]

        return result

    @staticmethod
    def compute_bbox(
        lat: float,
        lon: float,
        radius_km: float = 5.0,
    ) -> list[float]:
        """Compute bounding box around a point.

        Args:
            lat: Center latitude
            lon: Center longitude
            radius_km: Radius in kilometers (default 5km)

        Returns:
            [min_lon, min_lat, max_lon, max_lat]
        """
        # Approximate: 1 degree latitude ≈ 111 km
        lat_delta = radius_km / 111.0

        # Adjust longitude delta for latitude
        cos_lat = abs(math.cos(math.radians(lat)))
        if cos_lat < 0.001:
            cos_lat = 0.001  # Avoid division by zero near poles
        lon_delta = radius_km / (111.0 * cos_lat)

        return [
            lon - lon_delta,  # min_lon
            lat - lat_delta,  # min_lat
            lon + lon_delta,  # max_lon
            lat + lat_delta,  # max_lat
        ]

    @staticmethod
    def compute_bbox_from_area(
        lat: float,
        lon: float,
        area_hectares: float,
    ) -> list[float]:
        """Compute bounding box from a stated area.

        Args:
            lat: Center latitude
            lon: Center longitude
            area_hectares: Area in hectares

        Returns:
            [min_lon, min_lat, max_lon, max_lat]
        """
        # radius_km = sqrt(area_hectares / 100 / pi)
        radius_km = math.sqrt(area_hectares / 100.0 / math.pi)
        # Add 20% buffer for edge effects
        radius_km *= 1.2
        return SatelliteService.compute_bbox(lat, lon, radius_km)

    @staticmethod
    def calculate_ndvi(
        red: np.ndarray,
        nir: np.ndarray,
    ) -> np.ndarray:
        """Calculate NDVI from Red and NIR band arrays.

        Args:
            red: Red band (B04) array (float or int)
            nir: NIR band (B08) array (float or int)

        Returns:
            NDVI array (values -1.0 to 1.0)
        """
        red_f = red.astype(np.float32)
        nir_f = nir.astype(np.float32)

        # Sentinel-2 scaling factor: reflectance = DN / 10000
        if red_f.max() > 1.0:
            red_f = red_f / 10000.0
        if nir_f.max() > 1.0:
            nir_f = nir_f / 10000.0

        denominator = nir_f + red_f
        # Avoid division by zero
        denominator[denominator == 0] = np.nan

        ndvi = (nir_f - red_f) / denominator

        # Clip to valid range
        ndvi = np.clip(ndvi, -1.0, 1.0)

        return ndvi

    @staticmethod
    def compute_ndvi_statistics(ndvi: np.ndarray) -> dict:
        """Compute NDVI statistics for an area.

        Args:
            ndvi: NDVI array

        Returns:
            Dictionary with mean, median, std, vegetation_percentage, dense_vegetation_percentage
        """
        # Remove NaN values
        valid = ndvi[~np.isnan(ndvi)]

        if len(valid) == 0:
            return {
                "mean": 0.0,
                "median": 0.0,
                "std": 0.0,
                "vegetation_percentage": 0.0,
                "dense_vegetation_percentage": 0.0,
            }

        total_pixels = len(valid)
        vegetation_pixels = np.sum(valid > 0.3)
        dense_vegetation_pixels = np.sum(valid > 0.6)

        return {
            "mean": float(np.nanmean(valid)),
            "median": float(np.nanmedian(valid)),
            "std": float(np.nanstd(valid)),
            "vegetation_percentage": float(vegetation_pixels / total_pixels * 100),
            "dense_vegetation_percentage": float(dense_vegetation_pixels / total_pixels * 100),
        }

    @staticmethod
    def classify_land_cover(
        ndvi: np.ndarray,
        nir: np.ndarray | None = None,
        swir: np.ndarray | None = None,
    ) -> dict[str, float]:
        """Classify land cover from NDVI and optional bands.

        Classes: water, bare, urban, vegetation, forest

        Args:
            ndvi: NDVI array
            nir: Optional NIR band for water/urban discrimination
            swir: Optional SWIR band for urban discrimination

        Returns:
            Dictionary mapping class names to percentage coverage
        """
        valid = ndvi[~np.isnan(ndvi)]
        if len(valid) == 0:
            return {"water": 0.0, "bare": 0.0, "urban": 0.0, "vegetation": 0.0, "forest": 0.0}

        total = len(valid)

        # Water: NDVI < 0
        water = np.sum(valid < 0.0)

        # Forest: NDVI > 0.6
        forest = np.sum(valid > 0.6)

        # Vegetation: 0.2 <= NDVI <= 0.6
        vegetation = np.sum((valid >= 0.2) & (valid <= 0.6))

        # Urban + Bare: NDVI 0.0-0.2
        low_ndvi = np.sum((valid >= 0.0) & (valid < 0.2))

        # Split low_ndvi between urban and bare (rough 50/50 if no SWIR)
        if swir is not None:
            swir_valid = swir[~np.isnan(ndvi)]
            urban = np.sum((valid >= 0.0) & (valid < 0.2) & (swir_valid > 0.3))
            bare = low_ndvi - urban
        else:
            urban = low_ndvi // 2
            bare = low_ndvi - urban

        return {
            "water": float(water / total * 100),
            "bare": float(bare / total * 100),
            "urban": float(urban / total * 100),
            "vegetation": float(vegetation / total * 100),
            "forest": float(forest / total * 100),
        }

    @staticmethod
    def detect_vegetation_change(
        ndvi_before: np.ndarray,
        ndvi_after: np.ndarray,
        threshold: float | None = None,
    ) -> dict:
        """Detect vegetation change between two time periods.

        Args:
            ndvi_before: NDVI array from before period
            ndvi_after: NDVI array from after period
            threshold: Change detection threshold (default from config)

        Returns:
            Dictionary with change metrics
        """
        if threshold is None:
            threshold = settings.NDVI_CHANGE_THRESHOLD

        ndvi_diff = ndvi_after - ndvi_before

        # Handle NaN
        valid_diff = ndvi_diff[~np.isnan(ndvi_diff)]
        if len(valid_diff) == 0:
            return {
                "change_area_hectares": 0.0,
                "ndvi_mean_before": 0.0,
                "ndvi_mean_after": 0.0,
                "change_direction": "mixed",
                "change_percentage": 0.0,
            }

        # Significant change pixels
        change_mask = np.abs(valid_diff) > threshold

        # Calculate area (assuming 10m pixel resolution)
        pixel_area_m2 = 10 * 10  # 100 m² per pixel
        change_area_hectares = float(np.sum(change_mask) * pixel_area_m2 / 10000)

        # Mean NDVI values
        ndvi_mean_before = float(np.nanmean(ndvi_before))
        ndvi_mean_after = float(np.nanmean(ndvi_after))

        # Percentage change
        if ndvi_mean_before > 0:
            change_percentage = float(
                (ndvi_mean_after - ndvi_mean_before) / ndvi_mean_before * 100
            )
        else:
            change_percentage = 0.0

        # Determine direction
        mean_change = ndvi_mean_after - ndvi_mean_before
        if mean_change > 0.05:
            change_direction = "increase"  # Reforestation
        elif mean_change < -0.05:
            change_direction = "decrease"  # Deforestation
        else:
            change_direction = "mixed"

        return {
            "change_area_hectares": change_area_hectares,
            "ndvi_mean_before": ndvi_mean_before,
            "ndvi_mean_after": ndvi_mean_after,
            "change_direction": change_direction,
            "change_percentage": change_percentage,
        }


# Singleton instance
satellite_service = SatelliteService()
