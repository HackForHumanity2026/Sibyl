"""Unit tests for Satellite Service.

Tests NDVI calculation, land cover classification, change detection,
and bounding box computation without network access.
"""

import math
import numpy as np
import pytest

from app.services.satellite_service import SatelliteService


class TestComputeBbox:
    """Tests for bounding box computation."""

    def test_basic_bbox(self):
        """Test basic bounding box around equatorial point."""
        bbox = SatelliteService.compute_bbox(0.0, 100.0, radius_km=5.0)
        assert len(bbox) == 4
        assert bbox[0] < 100.0  # min_lon < center
        assert bbox[1] < 0.0    # min_lat < center
        assert bbox[2] > 100.0  # max_lon > center
        assert bbox[3] > 0.0    # max_lat > center

    def test_bbox_symmetry_at_equator(self):
        """Test that bbox is roughly symmetric at equator."""
        bbox = SatelliteService.compute_bbox(0.0, 100.0, radius_km=10.0)
        lat_range = bbox[3] - bbox[1]
        lon_range = bbox[2] - bbox[0]
        # At equator, lat and lon deltas should be approximately equal
        assert abs(lat_range - lon_range) < 0.01

    def test_bbox_high_latitude(self):
        """Test bbox at high latitude (lon delta should be larger)."""
        bbox = SatelliteService.compute_bbox(60.0, 10.0, radius_km=5.0)
        lat_range = bbox[3] - bbox[1]
        lon_range = bbox[2] - bbox[0]
        # At 60° latitude, lon delta should be ~2x lat delta
        assert lon_range > lat_range

    def test_bbox_from_area(self):
        """Test bbox computation from area in hectares."""
        bbox = SatelliteService.compute_bbox_from_area(-1.5, 113.5, 5000.0)
        assert len(bbox) == 4
        assert bbox[0] < 113.5
        assert bbox[2] > 113.5

    def test_small_radius(self):
        """Test very small radius."""
        bbox = SatelliteService.compute_bbox(0.0, 0.0, radius_km=0.1)
        assert bbox[2] - bbox[0] > 0  # Has width
        assert bbox[3] - bbox[1] > 0  # Has height


class TestCalculateNDVI:
    """Tests for NDVI calculation."""

    def test_basic_ndvi(self):
        """Test NDVI with simple reflectance values."""
        red = np.array([[0.1, 0.2], [0.3, 0.05]], dtype=np.float32)
        nir = np.array([[0.5, 0.4], [0.3, 0.6]], dtype=np.float32)

        ndvi = SatelliteService.calculate_ndvi(red, nir)

        assert ndvi.shape == (2, 2)
        # Dense vegetation (high NIR, low red) → high NDVI
        assert ndvi[0, 0] > 0.5
        # Equal NIR and Red → NDVI = 0
        assert abs(ndvi[1, 0]) < 0.01

    def test_ndvi_range(self):
        """Test that NDVI is within -1 to 1."""
        red = np.random.rand(10, 10).astype(np.float32)
        nir = np.random.rand(10, 10).astype(np.float32)

        ndvi = SatelliteService.calculate_ndvi(red, nir)

        assert np.nanmin(ndvi) >= -1.0
        assert np.nanmax(ndvi) <= 1.0

    def test_ndvi_with_sentinel2_scaling(self):
        """Test NDVI with Sentinel-2 DN values (needs /10000 scaling)."""
        red = np.array([[1000, 2000]], dtype=np.float32)  # DN values
        nir = np.array([[5000, 4000]], dtype=np.float32)

        ndvi = SatelliteService.calculate_ndvi(red, nir)

        assert ndvi.shape == (1, 2)
        assert ndvi[0, 0] > 0.5  # (0.5 - 0.1) / (0.5 + 0.1) ≈ 0.67

    def test_ndvi_zero_denominator(self):
        """Test NDVI handles zero denominator (both red and NIR = 0)."""
        red = np.array([[0.0, 0.1]], dtype=np.float32)
        nir = np.array([[0.0, 0.4]], dtype=np.float32)

        ndvi = SatelliteService.calculate_ndvi(red, nir)

        assert np.isnan(ndvi[0, 0])  # 0/0 → NaN
        assert not np.isnan(ndvi[0, 1])


class TestComputeNDVIStatistics:
    """Tests for NDVI statistics computation."""

    def test_basic_statistics(self):
        """Test statistics on a simple NDVI array."""
        ndvi = np.array([0.1, 0.3, 0.5, 0.7, 0.8])
        stats = SatelliteService.compute_ndvi_statistics(ndvi)

        assert stats["mean"] == pytest.approx(0.48, abs=0.01)
        assert stats["median"] == pytest.approx(0.5, abs=0.01)
        assert stats["vegetation_percentage"] > 0
        assert stats["dense_vegetation_percentage"] > 0

    def test_all_vegetation(self):
        """Test array with all vegetation (NDVI > 0.3)."""
        ndvi = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        stats = SatelliteService.compute_ndvi_statistics(ndvi)

        assert stats["vegetation_percentage"] == 100.0

    def test_no_vegetation(self):
        """Test array with no vegetation."""
        ndvi = np.array([0.0, 0.1, 0.05, -0.1])
        stats = SatelliteService.compute_ndvi_statistics(ndvi)

        assert stats["vegetation_percentage"] == 0.0
        assert stats["dense_vegetation_percentage"] == 0.0

    def test_handles_nan(self):
        """Test that NaN values are properly excluded."""
        ndvi = np.array([0.5, np.nan, 0.7, np.nan])
        stats = SatelliteService.compute_ndvi_statistics(ndvi)

        assert stats["mean"] == pytest.approx(0.6, abs=0.01)

    def test_empty_array(self):
        """Test empty/all-NaN array."""
        ndvi = np.array([np.nan, np.nan])
        stats = SatelliteService.compute_ndvi_statistics(ndvi)

        assert stats["mean"] == 0.0


class TestClassifyLandCover:
    """Tests for land cover classification."""

    def test_forest_dominance(self):
        """Test classification with mostly high NDVI (forest)."""
        ndvi = np.array([0.7, 0.8, 0.9, 0.65, 0.75])
        result = SatelliteService.classify_land_cover(ndvi)

        assert result["forest"] > 50.0

    def test_water_detection(self):
        """Test classification with negative NDVI (water)."""
        ndvi = np.array([-0.5, -0.3, -0.1, 0.1, 0.5])
        result = SatelliteService.classify_land_cover(ndvi)

        assert result["water"] > 0.0

    def test_all_classes_sum_to_100(self):
        """Test that all class percentages sum to ~100%."""
        ndvi = np.array([-0.3, 0.0, 0.1, 0.3, 0.5, 0.7, 0.9])
        result = SatelliteService.classify_land_cover(ndvi)

        total = sum(result.values())
        assert total == pytest.approx(100.0, abs=1.0)


class TestDetectVegetationChange:
    """Tests for vegetation change detection."""

    def test_reforestation_detected(self):
        """Test detection of reforestation (NDVI increase)."""
        ndvi_before = np.array([0.2, 0.3, 0.25, 0.15])
        ndvi_after = np.array([0.6, 0.7, 0.65, 0.55])

        result = SatelliteService.detect_vegetation_change(
            ndvi_before, ndvi_after, threshold=0.1
        )

        assert result["change_direction"] == "increase"
        assert result["ndvi_mean_after"] > result["ndvi_mean_before"]
        assert result["change_percentage"] > 0

    def test_deforestation_detected(self):
        """Test detection of deforestation (NDVI decrease)."""
        ndvi_before = np.array([0.7, 0.8, 0.75, 0.65])
        ndvi_after = np.array([0.1, 0.2, 0.15, 0.1])

        result = SatelliteService.detect_vegetation_change(
            ndvi_before, ndvi_after, threshold=0.1
        )

        assert result["change_direction"] == "decrease"
        assert result["ndvi_mean_after"] < result["ndvi_mean_before"]
        assert result["change_percentage"] < 0

    def test_no_significant_change(self):
        """Test when change is below threshold."""
        ndvi_before = np.array([0.5, 0.55, 0.52])
        ndvi_after = np.array([0.52, 0.54, 0.51])

        result = SatelliteService.detect_vegetation_change(
            ndvi_before, ndvi_after, threshold=0.1
        )

        assert result["change_direction"] == "mixed"
        assert result["change_area_hectares"] == 0.0

    def test_change_area_calculation(self):
        """Test that change area is calculated correctly."""
        # 100 pixels that change significantly
        ndvi_before = np.zeros(100)
        ndvi_after = np.ones(100) * 0.5

        result = SatelliteService.detect_vegetation_change(
            ndvi_before, ndvi_after, threshold=0.1
        )

        # 100 pixels × 100 m² / 10000 = 1.0 hectare
        assert result["change_area_hectares"] == pytest.approx(1.0, abs=0.01)
