# Feature Requirements Document: FRD 10 -- Geography Agent (v1.0)

| Field | Value |
|---|---|
| **Project** | Sibyl |
| **Parent Document** | [PRD v0.3](../PRD.md) |
| **FRD Order** | [FRD Order](../FRD-order.md) |
| **PRD Sections** | 4.4 (Geography Agent -- Satellite Verification) |
| **Type** | Feature |
| **Depends On** | FRD 5 (Orchestrator Agent & LangGraph Pipeline) |
| **Delivers** | Microsoft Planetary Computer integration, Sentinel-2 imagery queries, geocoding, NDVI analysis, land cover classification, temporal comparison, satellite image processing, evidence output with image references, LangGraph node, inter-agent communication participation |
| **Created** | 2026-02-09 |

---

## Summary

FRD 10 delivers the Geography Agent -- a specialist investigation agent in the Sibyl multi-agent pipeline that investigates geographic and environmental claims by analyzing satellite imagery from Microsoft Planetary Computer (MPC). The Geography Agent (`app/agents/geography_agent.py`) replaces the FRD 5 stub with a functional LangGraph node that receives routed geographic claims from the Orchestrator, extracts location information from claim text (facility names, geographic regions, coordinates), geocodes location names to geographic coordinates, queries MPC's STAC API via `pystac-client` for Sentinel-2 multispectral satellite imagery, performs analysis including NDVI vegetation change detection, land cover classification, temporal comparison (before/after imagery), and environmental impact indicators, processes satellite images using Gemini 2.5 Pro's multimodal capabilities, and produces evidence findings with satellite image references, analysis results, temporal comparisons, and plain-language summaries supporting or contradicting the claims. The agent participates in the inter-agent communication protocol (InfoRequest/InfoResponse) and emits StreamEvents for the detective dashboard, including satellite image references for visual display. The satellite service (`app/services/satellite_service.py`) handles MPC connection, STAC catalog queries, and asset retrieval, while the MPC query tool (`app/agents/tools/query_mpc.py`) provides a LangChain tool interface for the agent. The Geography Agent uses Gemini 2.5 Pro for multimodal satellite image analysis and spatial reasoning. After FRD 10, given routed geographic claims, the agent queries satellite imagery from MPC and produces visual evidence supporting or contradicting the claims.

---

## Given Context (Preconditions)

The following are assumed to be in place from prior FRDs:

| Prerequisite | Source FRD | Deliverable |
|---|---|---|
| LangGraph StateGraph with `investigate_geography` node stub | FRD 5 | `app/agents/graph.py` |
| `SibylState` Pydantic schema with `AgentFinding`, `InfoRequest`, `InfoResponse`, `StreamEvent` types | FRD 5 | `app/agents/state.py` |
| Orchestrator routing logic that routes geographic claims to Geography Agent | FRD 5 | `app/agents/orchestrator_agent.py` |
| SSE streaming infrastructure with `StreamEvent` emission | FRD 5 | `app/agents/callbacks.py`, `app/api/routes/stream.py` |
| Inter-agent communication protocol (InfoRequest/InfoResponse) | FRD 5 | Shared state mechanism |
| OpenRouter client wrapper with `Models.GEMINI_PRO` constant | FRD 0 | `app/services/openrouter_client.py` |
| `Claim` model with `claim_text`, `claim_type`, `source_page`, `source_location` | FRD 3 | `app/models/claim.py` |
| `AgentFinding` schema with `evidence_type`, `summary`, `details`, `supports_claim`, `confidence` | FRD 0 | `app/agents/state.py` |
| Detective dashboard infrastructure (FRD 12 placeholder) | FRD 5 | SSE event consumption |
| `pystac-client` Python package available | FRD 0 | `requirements.txt` |
| Microsoft Planetary Computer STAC API accessible at `https://planetarycomputer.microsoft.com/api/stac/v1` | External | No API key required |

### Terms

| Term | Definition |
|---|---|
| Microsoft Planetary Computer (MPC) | A free, publicly accessible STAC API providing access to Sentinel-2 and other satellite imagery collections |
| STAC | SpatioTemporal Asset Catalog -- a JSON-based specification for describing geospatial data |
| Sentinel-2 | European Space Agency satellite constellation providing multispectral imagery at 10-60m resolution |
| Geocoding | The process of converting location names (e.g., "Borneo, Indonesia") to geographic coordinates (latitude, longitude) |
| NDVI | Normalized Difference Vegetation Index -- a spectral index calculated as (NIR - Red) / (NIR + Red) to measure vegetation health |
| Multispectral imagery | Satellite imagery captured across multiple wavelength bands (visible, near-infrared, shortwave infrared) enabling spectral analysis |
| Temporal comparison | Analysis comparing satellite imagery from different time periods to detect changes (deforestation, reforestation, urban expansion) |
| Land cover classification | Categorizing pixels in satellite imagery into classes (forest, water, urban, agriculture, bare ground) |
| STAC Item | A single observation (e.g., one Sentinel-2 scene) with metadata and links to image assets |
| STAC Collection | A group of STAC Items sharing common characteristics (e.g., "sentinel-2-l2a" for Sentinel-2 Level-2A products) |
| Cloud cover | Percentage of a satellite scene obscured by clouds; lower values indicate clearer imagery |
| Asset | A downloadable file associated with a STAC Item (e.g., a GeoTIFF image file for a specific spectral band) |
| Spectral band | A specific wavelength range captured by the satellite sensor (e.g., B04 = Red, B08 = Near-Infrared) |

---

## Executive Summary (Gherkin-Style)

```gherkin
Feature: Geography Agent -- Satellite Imagery Verification

  Background:
    Given  FRD 0, FRD 1, FRD 2, FRD 3, and FRD 5 are complete
    And    all services are running (backend, frontend, PostgreSQL, Redis)
    And    a sustainability report has been uploaded, parsed, and claims extracted
    And    the Orchestrator has routed geographic claims to the Geography Agent
    And    Microsoft Planetary Computer STAC API is accessible

  Scenario: Geography Agent receives routed claims
    Given  the Orchestrator has created a routing plan with geographic claims
    When   the investigate_geography node executes
    Then   it receives claims assigned to the Geography Agent from the routing plan
    And    it extracts location information from each claim's text

  Scenario: Geocode location names to coordinates
    Given  a claim mentions a location name (e.g., "Borneo, Indonesia")
    When   the agent processes the claim
    Then   it geocodes the location name to latitude/longitude coordinates
    And    it handles ambiguous locations by selecting the most relevant match
    And    it stores coordinates for satellite querying

  Scenario: Query Microsoft Planetary Computer for satellite imagery
    Given  a claim with geographic coordinates and a time range
    When   the agent queries MPC's STAC API
    Then   it searches the Sentinel-2 collection for scenes covering the location
    And    it filters by time range (before/after dates from the claim)
    And    it selects scenes with low cloud cover (< 20% preferred)
    And    it retrieves STAC Items with metadata and asset links

  Scenario: Download and process satellite imagery
    Given  STAC Items have been retrieved from MPC
    When   the agent processes the imagery
    Then   it downloads required spectral bands (Red, NIR, and others as needed)
    And    it computes NDVI for vegetation analysis
    And    it performs land cover classification
    And    it prepares images for temporal comparison

  Scenario: Analyze satellite imagery with Gemini 2.5 Pro
    Given  satellite images have been downloaded and processed
    When   the agent analyzes the imagery
    Then   it sends images to Gemini 2.5 Pro with analysis prompts
    And    Gemini performs visual analysis (vegetation detection, land use, changes)
    And    the agent receives structured analysis results

  Scenario: Perform temporal comparison for change detection
    Given  a claim asserts environmental change over time (e.g., "restored 5,000 hectares since 2020")
    When   the agent analyzes the claim
    Then   it retrieves imagery from before and after the stated time period
    And    it computes NDVI differences between time periods
    And    it generates before/after image pairs
    And    it quantifies the extent of change (hectares, percentage)

  Scenario: Produce evidence findings with image references
    Given  satellite analysis is complete
    When   the agent produces findings
    Then   it creates AgentFinding objects with:
      - evidence_type: "satellite_imagery"
      - summary: Plain-language analysis result
      - details: NDVI values, land cover classes, change metrics, image URLs
      - supports_claim: Boolean indicating if evidence supports the claim
      - confidence: Confidence score (0.0-1.0)
    And    findings include references to satellite image assets (MPC URLs)
    And    findings include temporal comparison results if applicable

  Scenario: Emit StreamEvents for detective dashboard
    Given  the agent is processing claims
    When   it performs analysis steps
    Then   it emits StreamEvent objects:
      - agent_started: Geography Agent begins processing
      - agent_thinking: Progress updates ("Geocoding location...", "Querying MPC...", "Analyzing imagery...")
      - evidence_found: Satellite evidence discovered with image references
      - agent_completed: Processing finished with summary
    And    events include satellite image URLs for dashboard display

  Scenario: Participate in inter-agent communication
    Given  another agent posts an InfoRequest requesting geographic verification
    When   the Orchestrator routes the request to the Geography Agent
    Then   the Geography Agent processes the request
    And    it queries satellite imagery if needed
    And    it posts an InfoResponse with geographic findings
    And    the requesting agent can access the response

  Scenario: Handle MPC unavailability gracefully
    Given  Microsoft Planetary Computer API is unavailable
    When   the agent attempts to query satellite imagery
    Then   it emits an error StreamEvent
    And    it produces a finding with evidence_type "error"
    And    it sets supports_claim to null (unable to verify)
    And    the pipeline continues with other agents

  Scenario: Handle claims with no imagery available
    Given  a claim references a location with no Sentinel-2 coverage
    When   the agent queries MPC
    Then   it receives zero STAC Items
    And    it produces a finding indicating insufficient satellite data
    And    it sets supports_claim to null
    And    it includes reasoning about why imagery is unavailable

  Scenario: Handle high cloud cover scenarios
    Given  all available Sentinel-2 scenes have > 50% cloud cover
    When   the agent processes the imagery
    Then   it selects the clearest available scene
    And    it notes cloud cover limitations in the finding
    And    it adjusts confidence scores downward to reflect uncertainty
```

---

## Table of Contents

1. [LangGraph Node Implementation](#1-langgraph-node-implementation)
2. [Satellite Service Architecture](#2-satellite-service-architecture)
3. [Geocoding Implementation](#3-geocoding-implementation)
4. [MPC STAC Query Logic](#4-mpc-stac-query-logic)
5. [Sentinel-2 Band Information and Usage](#5-sentinel-2-band-information-and-usage)
6. [NDVI Calculation and Vegetation Analysis](#6-ndvi-calculation-and-vegetation-analysis)
7. [Land Cover Classification](#7-land-cover-classification)
8. [Temporal Comparison Methodology](#8-temporal-comparison-methodology)
9. [Satellite Image Processing Pipeline](#9-satellite-image-processing-pipeline)
10. [Gemini 2.5 Pro Multimodal Analysis](#10-gemini-25-pro-multimodal-analysis)
11. [Evidence Output and Finding Structure](#11-evidence-output-and-finding-structure)
12. [Satellite Image Storage and References](#12-satellite-image-storage-and-references)
13. [Inter-Agent Communication Participation](#13-inter-agent-communication-participation)
14. [Re-Investigation Handling](#14-re-investigation-handling)
15. [StreamEvent Emissions](#15-streamevent-emissions)
16. [Error Handling](#16-error-handling)
17. [Backend Dependencies and Configuration](#17-backend-dependencies-and-configuration)
18. [Exit Criteria](#18-exit-criteria)
19. [Appendix A: Geography Agent Prompt Templates](#appendix-a-geography-agent-prompt-templates)
20. [Appendix B: STAC Query Examples](#appendix-b-stac-query-examples)
21. [Appendix C: NDVI Analysis Algorithm](#appendix-c-ndvi-analysis-algorithm)
22. [Appendix D: Sentinel-2 Band Reference](#appendix-d-sentinel-2-band-reference)
23. [Design Decisions Log](#design-decisions-log)

---

## 1. LangGraph Node Implementation

### 1.1 Overview

The Geography Agent (`app/agents/geography_agent.py`) replaces the FRD 5 stub with a functional LangGraph node that investigates geographic and environmental claims using satellite imagery from Microsoft Planetary Computer. The node receives routed claims from the Orchestrator, extracts location information, queries satellite imagery, performs analysis, and produces evidence findings.

### 1.2 Node Function

```python
async def investigate_geography(state: SibylState) -> dict:
    """Geography Agent: Investigate geographic claims using satellite imagery.

    Reads: state.routing_plan, state.claims, state.info_requests,
           state.iteration_count
    Writes: state.findings, state.agent_status, state.info_responses,
            state.events

    Responsibilities:
    1. Extract location information from routed geographic claims.
    2. Geocode location names to coordinates.
    3. Query Microsoft Planetary Computer for Sentinel-2 imagery.
    4. Download and process satellite images.
    5. Perform NDVI analysis, land cover classification, temporal comparison.
    6. Analyze imagery with Gemini 2.5 Pro (multimodal).
    7. Produce evidence findings with image references.
    8. Handle InfoRequests from other agents.

    Returns:
        Partial state update with findings, agent status, and events.
    """
```

### 1.3 Node Processing Steps

The `investigate_geography` node shall execute the following steps:

1. **Emit start event:** Append a `StreamEvent` with `event_type = "agent_started"`, `agent_name = "geography"`.

2. **Find assigned claims:** Filter `state.routing_plan` to find `RoutingAssignment` objects where `"geography"` is in `assigned_agents`. Load the corresponding `Claim` objects from `state.claims`.

3. **Update agent status:** Set `agent_status["geography"] = AgentStatus(status="working", claims_assigned=len(assigned_claims), claims_completed=0)`.

4. **Process each claim:**
   a. Extract location information from `claim_text` (location names, coordinates, time ranges).
   b. Geocode location names to coordinates (see Section 3).
   c. Determine time range for temporal analysis (extract dates from claim text or use default ranges).
   d. Query MPC for Sentinel-2 imagery (see Section 4).
   e. Download required spectral bands (see Section 5).
   f. Compute NDVI and perform land cover classification (see Sections 6-7).
   g. Perform temporal comparison if applicable (see Section 8).
   h. Analyze imagery with Gemini 2.5 Pro (see Section 10).
   i. Produce evidence finding (see Section 11).
   j. Emit `evidence_found` StreamEvent with image references.

5. **Process InfoRequests:** Scan `state.info_requests` for items with `status = "routed"` and `target_agents` containing `"geography"`. Process each request and post `InfoResponse` objects (see Section 13).

6. **Update agent status:** Set `agent_status["geography"] = AgentStatus(status="completed", claims_assigned=len(assigned_claims), claims_completed=len(findings))`.

7. **Emit completion event:** Append a `StreamEvent` with `event_type = "agent_completed"`, `agent_name = "geography"`, including summary statistics.

8. **Return partial state:** Return updated `findings`, `agent_status`, `info_responses`, and `events`.

### 1.4 Model Configuration

| Parameter | Value | Rationale |
|---|---|---|
| Model | `google/gemini-2.5-pro` (`Models.GEMINI_PRO`) | Best multimodal/vision capabilities for analyzing satellite imagery; strong spatial reasoning (PRD Section 4.4) |
| Temperature | `0.2` | Slightly higher than other agents to allow nuanced interpretation of visual satellite data |
| Max output tokens | `8192` | Sufficient for detailed analysis results and structured findings |
| Response format | JSON schema (structured output) | Ensures parseable analysis results |

### 1.5 Location Extraction from Claims

The system shall extract location information from claim text using a combination of:

1. **Named entity recognition:** Use Gemini 2.5 Pro to identify location names, coordinates, and time references in claim text.
2. **Pattern matching:** Regex patterns for coordinates (`lat, lon` or `latitude, longitude`), dates, and common location phrases.
3. **Context analysis:** Parse surrounding text to disambiguate location references (e.g., "our facility in Borneo" vs. "Borneo rainforest").

Extracted location data structure:

```python
class ExtractedLocation(BaseModel):
    """Location information extracted from a claim."""
    location_name: str | None = None      # e.g., "Borneo, Indonesia"
    coordinates: tuple[float, float] | None = None  # (latitude, longitude)
    time_range: tuple[datetime, datetime] | None = None  # (start, end) for temporal analysis
    area_description: str | None = None    # e.g., "5,000 hectares", "50-hectare site"
    confidence: float                      # 0.0-1.0 confidence in extraction
```

---

## 2. Satellite Service Architecture

### 2.1 Overview

The satellite service (`app/services/satellite_service.py`) provides a high-level interface for interacting with Microsoft Planetary Computer's STAC API. It handles connection management, STAC catalog queries, asset retrieval, and image download coordination.

### 2.2 Service Interface

```python
class SatelliteService:
    """Service for querying and retrieving satellite imagery from MPC."""

    def __init__(self):
        self.stac_url = "https://planetarycomputer.microsoft.com/api/stac/v1"
        self.catalog = None  # pystac_client.Client

    async def connect(self) -> None:
        """Connect to MPC STAC catalog."""
        from pystac_client import Client
        self.catalog = Client.open(self.stac_url)

    async def search_sentinel2(
        self,
        bbox: list[float],  # [min_lon, min_lat, max_lon, max_lat]
        datetime: str | tuple[str, str],  # ISO datetime or range
        cloud_cover_max: float = 20.0,
        limit: int = 10
    ) -> list[dict]:
        """Search Sentinel-2 collection for scenes matching criteria.

        Returns:
            List of STAC Item dictionaries with metadata and asset links.
        """

    async def get_item_assets(
        self,
        item_id: str,
        bands: list[str] = ["B04", "B08"]  # Red, NIR for NDVI
    ) -> dict[str, str]:
        """Get asset URLs for specific spectral bands of a STAC Item.

        Returns:
            Dictionary mapping band names to signed asset URLs.
        """

    async def download_asset(
        self,
        asset_url: str,
        output_path: str | None = None
    ) -> bytes:
        """Download a satellite image asset (GeoTIFF).

        Returns:
            Raw image bytes (can be saved or processed in-memory).
        """
```

### 2.3 STAC Catalog Connection

The system shall connect to MPC's STAC catalog using `pystac-client`:

```python
from pystac_client import Client

catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
```

MPC requires no API key and is free for non-commercial use. The connection is established once per service instance and reused for multiple queries.

### 2.4 Collection Selection

The system shall query the `sentinel-2-l2a` collection, which provides Sentinel-2 Level-2A (atmospherically corrected) products. This collection offers:

- 10m resolution for visible and NIR bands (B02, B03, B04, B08)
- 20m resolution for red-edge and SWIR bands (B05, B06, B07, B11, B12)
- Pre-calculated cloud masks
- Atmospheric correction applied

### 2.5 Asset Signing

MPC requires asset URLs to be signed before download. The `pystac-client` library handles signing automatically when accessing assets through the client. The system shall use signed URLs provided by the client rather than constructing URLs manually.

---

## 3. Geocoding Implementation

### 3.1 Overview

Geocoding converts location names (e.g., "Borneo, Indonesia", "Surabaya manufacturing facility") to geographic coordinates (latitude, longitude) required for satellite imagery queries. The system uses a free geocoding service (Nominatim/OpenStreetMap) to resolve location names.

### 3.2 Geocoding Service

```python
# app/services/geocoding_service.py

import httpx
from typing import Optional

class GeocodingService:
    """Service for geocoding location names to coordinates."""

    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            "User-Agent": "Sibyl-Geography-Agent/1.0"  # Required by Nominatim
        }

    async def geocode(
        self,
        location_name: str,
        country_code: str | None = None
    ) -> Optional[tuple[float, float]]:
        """Geocode a location name to (latitude, longitude).

        Args:
            location_name: Location name (e.g., "Borneo, Indonesia")
            country_code: Optional ISO country code to narrow results

        Returns:
            (latitude, longitude) tuple or None if not found
        """

    async def geocode_with_context(
        self,
        location_name: str,
        claim_context: str
    ) -> Optional[tuple[float, float, str]]:
        """Geocode with claim context to disambiguate.

        Returns:
            (latitude, longitude, matched_location_name) or None
        """
```

### 3.3 Geocoding Strategy

The system shall:

1. **Primary attempt:** Query Nominatim with the extracted location name.
2. **Disambiguation:** If multiple results are returned, use claim context (surrounding text) to select the most relevant match.
3. **Fallback:** If Nominatim fails, use Gemini 2.5 Pro to extract coordinates from claim text (some claims may include explicit coordinates).
4. **Coordinate validation:** Verify coordinates are within valid ranges (latitude: -90 to 90, longitude: -180 to 180).

### 3.4 Rate Limiting

Nominatim has a rate limit (1 request per second). The system shall:

1. Implement request throttling (1 second delay between requests).
2. Cache geocoding results in memory (same location name → same coordinates).
3. For batch processing, queue geocoding requests with delays.

### 3.5 Coordinate Precision

Geocoded coordinates are rounded to 4 decimal places (~11m precision), sufficient for Sentinel-2 queries (10m pixel resolution). For area-based claims (e.g., "5,000 hectares"), the system computes a bounding box centered on the coordinates with an estimated radius.

---

## 4. MPC STAC Query Logic

### 4.1 Overview

The MPC STAC query logic searches the Sentinel-2 collection for satellite scenes covering a specified geographic area and time range. The query filters by bounding box, datetime, and cloud cover to find the most suitable imagery.

### 4.2 Query Parameters

```python
class STACQueryParams(BaseModel):
    """Parameters for STAC search query."""
    bbox: list[float]  # [min_lon, min_lat, max_lon, max_lat]
    datetime: str | tuple[str, str]  # ISO datetime string or range
    collection: str = "sentinel-2-l2a"
    cloud_cover_max: float = 20.0  # Maximum acceptable cloud cover percentage
    limit: int = 10  # Maximum number of items to return
```

### 4.3 Bounding Box Calculation

For a point location (latitude, longitude), the system computes a bounding box:

```python
def compute_bbox(lat: float, lon: float, radius_km: float = 5.0) -> list[float]:
    """Compute bounding box around a point.

    Args:
        lat: Center latitude
        lon: Center longitude
        radius_km: Radius in kilometers (default 5km for facility-level claims)

    Returns:
        [min_lon, min_lat, max_lon, max_lat]
    """
    # Approximate: 1 degree latitude ≈ 111 km
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * abs(math.cos(math.radians(lat))))
    
    return [
        lon - lon_delta,  # min_lon
        lat - lat_delta,  # min_lat
        lon + lon_delta,  # max_lon
        lat + lat_delta   # max_lat
    ]
```

For area-based claims (e.g., "5,000 hectares"), the radius is computed from the stated area: `radius_km = sqrt(area_hectares / 100 / pi)`.

### 4.4 Time Range Extraction

The system extracts time ranges from claim text:

1. **Explicit dates:** "since 2020", "in FY2024", "between 2020 and 2024"
2. **Relative dates:** "last 5 years", "over the past decade"
3. **Default ranges:** If no time range is specified, use:
   - **Before/after comparison:** 2 years before stated date → 1 month after stated date
   - **Single date claim:** 1 month before → 1 month after

### 4.5 Cloud Cover Filtering

The system prioritizes scenes with low cloud cover:

1. **Preferred:** Cloud cover < 20%
2. **Acceptable:** Cloud cover 20-50% (with confidence adjustment)
3. **Avoid:** Cloud cover > 50% (only used if no alternatives)

The `eo:cloud_cover` property in STAC Items provides cloud cover percentage.

### 4.6 Query Execution

```python
async def search_sentinel2(
    self,
    bbox: list[float],
    datetime: str | tuple[str, str],
    cloud_cover_max: float = 20.0,
    limit: int = 10
) -> list[dict]:
    """Search Sentinel-2 collection."""
    search = self.catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=datetime,
        query={"eo:cloud_cover": {"lt": cloud_cover_max}},
        limit=limit
    )
    
    items = []
    for item in search.items():
        items.append({
            "id": item.id,
            "datetime": item.datetime.isoformat() if item.datetime else None,
            "bbox": item.bbox,
            "cloud_cover": item.properties.get("eo:cloud_cover", 100.0),
            "assets": {band: asset.href for band, asset in item.assets.items()}
        })
    
    return items
```

### 4.7 Scene Selection

When multiple scenes are available, the system selects:

1. **Lowest cloud cover** (primary criterion)
2. **Closest to target date** (for temporal claims)
3. **Most recent** (if no specific date requirement)

---

## 5. Sentinel-2 Band Information and Usage

### 5.1 Overview

Sentinel-2 captures multispectral imagery across 13 spectral bands. The Geography Agent uses specific bands for NDVI calculation, land cover classification, and visual analysis.

### 5.2 Band Reference

| Band | Wavelength (nm) | Resolution | Common Name | Usage |
|---|---|---|---|---|
| B01 | 443 | 60m | Coastal aerosol | Atmospheric correction |
| B02 | 490 | 10m | Blue | True-color visualization |
| B03 | 560 | 10m | Green | True-color visualization |
| B04 | 665 | 10m | Red | NDVI calculation, true-color |
| B05 | 705 | 20m | Red Edge 1 | Vegetation stress |
| B06 | 740 | 20m | Red Edge 2 | Vegetation health |
| B07 | 783 | 20m | Red Edge 3 | Vegetation health |
| B08 | 842 | 10m | Near-Infrared (NIR) | NDVI calculation, vegetation |
| B08A | 865 | 20m | Red Edge 4 | Vegetation analysis |
| B09 | 945 | 60m | Water vapor | Atmospheric correction |
| B11 | 1610 | 20m | SWIR 1 | Land cover, moisture |
| B12 | 2190 | 20m | SWIR 2 | Land cover, moisture |

### 5.3 Required Bands for Geography Agent

For NDVI calculation:
- **B04 (Red):** Required
- **B08 (NIR):** Required

For true-color visualization (RGB):
- **B04 (Red):** Required
- **B03 (Green):** Required
- **B02 (Blue):** Required

For land cover classification:
- **B04, B08:** Required (NDVI)
- **B11, B12 (SWIR):** Optional but recommended for better classification

### 5.4 Band Asset Retrieval

The system retrieves band assets from STAC Items:

```python
async def get_item_assets(
    self,
    item_id: str,
    bands: list[str] = ["B02", "B03", "B04", "B08"]
) -> dict[str, str]:
    """Get signed asset URLs for spectral bands."""
    item = self.catalog.get_item(item_id)
    
    assets = {}
    for band in bands:
        if band in item.assets:
            # pystac-client handles signing automatically
            assets[band] = item.assets[band].href
    
    return assets
```

### 5.5 Resolution Handling

Sentinel-2 bands have different resolutions (10m, 20m, 60m). The system:

1. Downloads bands at their native resolution.
2. Resamples 20m and 60m bands to 10m for NDVI calculation (using nearest-neighbor or bilinear interpolation).
3. Maintains resolution metadata for accurate area calculations.

---

## 6. NDVI Calculation and Vegetation Analysis

### 6.1 Overview

NDVI (Normalized Difference Vegetation Index) measures vegetation health and density. It is calculated from Red and Near-Infrared bands and ranges from -1 to +1, where higher values indicate healthier, denser vegetation.

### 6.2 NDVI Formula

```
NDVI = (NIR - Red) / (NIR + Red)
```

Where:
- **NIR** = Near-Infrared band (B08) reflectance
- **Red** = Red band (B04) reflectance

### 6.3 NDVI Interpretation

| NDVI Value | Interpretation |
|---|---|
| -1.0 to 0.0 | Water, clouds, snow, or bare soil |
| 0.0 to 0.2 | Sparse vegetation, urban areas |
| 0.2 to 0.5 | Moderate vegetation (shrubland, grassland) |
| 0.5 to 0.8 | Dense vegetation (forests, healthy crops) |
| 0.8 to 1.0 | Very dense vegetation (tropical rainforests) |

### 6.4 NDVI Calculation Implementation

```python
import numpy as np
from rasterio import open as rasterio_open
from rasterio.warp import reproject, Resampling

def calculate_ndvi(red_band_path: str, nir_band_path: str) -> np.ndarray:
    """Calculate NDVI from Red and NIR GeoTIFF files.

    Args:
        red_band_path: Path to Red band (B04) GeoTIFF
        nir_band_path: Path to NIR band (B08) GeoTIFF

    Returns:
        NDVI array (values -1.0 to 1.0)
    """
    with rasterio_open(red_band_path) as red_src:
        red = red_src.read(1).astype(np.float32)
        
    with rasterio_open(nir_band_path) as nir_src:
        nir = nir_src.read(1).astype(np.float32)
    
    # Handle resolution mismatch (if NIR is 20m, resample to match Red 10m)
    if nir.shape != red.shape:
        # Resample NIR to match Red resolution
        # (implementation details omitted)
        pass
    
    # Avoid division by zero
    denominator = nir + red
    denominator[denominator == 0] = np.nan
    
    ndvi = (nir - red) / denominator
    
    return ndvi
```

### 6.5 NDVI Statistics

For each analyzed area, the system computes:

- **Mean NDVI:** Average vegetation index
- **Median NDVI:** Median value (less sensitive to outliers)
- **NDVI standard deviation:** Variability in vegetation
- **Vegetation area:** Pixels with NDVI > 0.3 (vegetation threshold)
- **Dense vegetation area:** Pixels with NDVI > 0.6

### 6.6 NDVI Change Detection

For temporal comparisons, the system calculates:

- **NDVI difference:** `NDVI_after - NDVI_before`
- **Percentage change:** `(NDVI_after - NDVI_before) / NDVI_before * 100`
- **Area of change:** Pixels where `|NDVI_after - NDVI_before| > threshold` (default 0.1)

### 6.7 NDVI Visualization

The system generates NDVI visualization images:

1. **Color mapping:** 
   - Red/Brown (NDVI < 0.2): Non-vegetated
   - Yellow (0.2-0.4): Sparse vegetation
   - Green (0.4-0.6): Moderate vegetation
   - Dark Green (0.6-1.0): Dense vegetation
2. **Overlay:** NDVI map overlaid on true-color base image for context.

---

## 7. Land Cover Classification

### 7.1 Overview

Land cover classification categorizes pixels in satellite imagery into classes (forest, water, urban, agriculture, bare ground). This enables verification of facility presence, land use assertions, and environmental impact assessment.

### 7.2 Classification Approach

The Geography Agent uses a rule-based classification approach combining:

1. **NDVI thresholds:** Vegetation vs. non-vegetation
2. **Spectral indices:** Water index (NDWI), built-up index
3. **Band ratios:** SWIR bands for moisture/vegetation discrimination
4. **Gemini 2.5 Pro visual analysis:** LLM-based classification for complex scenes

### 7.3 Classification Classes

| Class | NDVI Range | Additional Criteria | Use Case |
|---|---|---|---|
| **Forest** | > 0.6 | High NIR reflectance | Deforestation/reforestation claims |
| **Grassland/Agriculture** | 0.2-0.6 | Moderate NIR, regular patterns | Land use verification |
| **Urban/Built-up** | < 0.2 | High SWIR reflectance, geometric patterns | Facility location claims |
| **Water** | < 0.0 | Low reflectance in all bands | Water body change detection |
| **Bare Ground** | 0.0-0.2 | Low NIR, high SWIR | Land clearing, mining |

### 7.4 Classification Implementation

```python
def classify_land_cover(
    ndvi: np.ndarray,
    red: np.ndarray,
    nir: np.ndarray,
    swir: np.ndarray | None = None
) -> np.ndarray:
    """Classify land cover from spectral bands.

    Returns:
        Classification array with class labels (0=water, 1=bare, 2=urban, 3=vegetation, 4=forest)
    """
    classification = np.zeros_like(ndvi, dtype=np.uint8)
    
    # Water: NDVI < 0 and low overall reflectance
    water_mask = (ndvi < 0) & (nir < 0.1)
    classification[water_mask] = 0
    
    # Forest: High NDVI
    forest_mask = ndvi > 0.6
    classification[forest_mask] = 4
    
    # Vegetation: Moderate NDVI
    vegetation_mask = (ndvi >= 0.2) & (ndvi <= 0.6)
    classification[vegetation_mask] = 3
    
    # Urban: Low NDVI, high SWIR (if available)
    if swir is not None:
        urban_mask = (ndvi < 0.2) & (swir > 0.3)
    else:
        urban_mask = (ndvi < 0.2) & (nir < 0.15)
    classification[urban_mask] = 2
    
    # Bare ground: Low NDVI, not urban
    bare_mask = (ndvi >= 0.0) & (ndvi < 0.2) & ~urban_mask
    classification[bare_mask] = 1
    
    return classification
```

### 7.5 Classification Accuracy

Rule-based classification provides approximate results. For higher accuracy, the system:

1. Uses Gemini 2.5 Pro to visually analyze classification results and correct errors.
2. Notes classification confidence in findings (lower confidence for ambiguous scenes).
3. Focuses on clear cases (e.g., dense forest vs. clear-cut) where classification is reliable.

---

## 8. Temporal Comparison Methodology

### 8.1 Overview

Temporal comparison analyzes satellite imagery from different time periods to detect changes (deforestation, reforestation, urban expansion, water body changes). This enables verification of claims asserting environmental changes over time.

### 8.2 Before/After Image Selection

The system selects imagery pairs:

1. **Before image:** Closest scene to the "before" date (start of claimed period or baseline year).
2. **After image:** Closest scene to the "after" date (end of claimed period or current date).
3. **Time gap:** Minimum 6 months between images to ensure detectable change (accounting for seasonal variations).

### 8.3 Change Detection Process

```python
def detect_vegetation_change(
    ndvi_before: np.ndarray,
    ndvi_after: np.ndarray,
    threshold: float = 0.1
) -> dict:
    """Detect vegetation change between two time periods.

    Returns:
        Dictionary with change metrics:
        - change_area_hectares: Area of significant change
        - ndvi_mean_before: Mean NDVI before
        - ndvi_mean_after: Mean NDVI after
        - change_direction: "increase" | "decrease" | "mixed"
        - change_percentage: Percentage change in mean NDVI
    """
    ndvi_diff = ndvi_after - ndvi_before
    
    # Significant change pixels
    change_mask = np.abs(ndvi_diff) > threshold
    
    # Calculate area (assuming 10m pixel resolution)
    pixel_area_m2 = 10 * 10  # 100 m² per pixel
    change_area_hectares = np.sum(change_mask) * pixel_area_m2 / 10000
    
    # Mean NDVI change
    ndvi_mean_before = np.nanmean(ndvi_before)
    ndvi_mean_after = np.nanmean(ndvi_after)
    change_percentage = ((ndvi_after - ndvi_before) / ndvi_before * 100) if ndvi_before > 0 else 0
    
    # Determine change direction
    if ndvi_mean_after > ndvi_mean_before + 0.05:
        change_direction = "increase"  # Reforestation
    elif ndvi_mean_after < ndvi_mean_before - 0.05:
        change_direction = "decrease"  # Deforestation
    else:
        change_direction = "mixed"
    
    return {
        "change_area_hectares": change_area_hectares,
        "ndvi_mean_before": float(ndvi_mean_before),
        "ndvi_mean_after": float(ndvi_mean_after),
        "change_direction": change_direction,
        "change_percentage": float(change_percentage)
    }
```

### 8.4 Seasonal Variation Handling

Vegetation NDVI varies seasonally. The system:

1. **Seasonal alignment:** Prefers comparing images from the same season (e.g., both summer) to minimize seasonal effects.
2. **Multi-year comparison:** For long-term claims (e.g., "since 2020"), compares annual averages rather than single scenes.
3. **Confidence adjustment:** Notes when comparisons span different seasons and adjusts confidence accordingly.

### 8.5 Before/After Visualization

The system generates side-by-side comparison images:

1. **True-color comparison:** Before and after RGB images side-by-side.
2. **NDVI comparison:** Before and after NDVI maps with color coding.
3. **Change map:** Highlighted areas of significant change overlaid on base image.

---

## 9. Satellite Image Processing Pipeline

### 9.1 Overview

The satellite image processing pipeline downloads Sentinel-2 assets, processes spectral bands, computes indices, and prepares images for analysis. The pipeline handles GeoTIFF format, coordinate systems, and image resampling.

### 9.2 Processing Steps

```python
async def process_satellite_imagery(
    stac_item: dict,
    bands: list[str],
    output_dir: str
) -> dict:
    """Download and process satellite imagery.

    Returns:
        Dictionary with processed image paths and metadata:
        - band_paths: {band_name: file_path}
        - ndvi_path: Path to computed NDVI GeoTIFF
        - rgb_path: Path to true-color RGB composite
        - metadata: Scene metadata (date, cloud cover, etc.)
    """
```

### 9.3 Download Pipeline

1. **Get signed asset URLs:** Retrieve asset URLs from STAC Item (already signed by pystac-client).
2. **Download bands:** Download required spectral bands as GeoTIFF files.
3. **Verify downloads:** Check file integrity and metadata.
4. **Store temporarily:** Save to temporary directory (cleaned up after processing).

### 9.4 Image Processing

1. **Open GeoTIFFs:** Use `rasterio` to read GeoTIFF files.
2. **Extract area of interest:** Crop to bounding box around claim location.
3. **Resample to common resolution:** Resample 20m/60m bands to 10m if needed.
4. **Compute NDVI:** Calculate NDVI from Red and NIR bands.
5. **Generate RGB composite:** Create true-color image from B04, B03, B02.
6. **Apply cloud mask:** Mask out cloudy pixels using Sentinel-2 cloud mask (if available).

### 9.5 Coordinate System Handling

Sentinel-2 imagery uses UTM (Universal Transverse Mercator) projection. The system:

1. Maintains original projection for accurate area calculations.
2. Reprojects to WGS84 (lat/lon) only when needed for visualization.
3. Uses `rasterio` for coordinate transformations.

### 9.6 Temporary File Management

Processed images are stored temporarily:

1. **Temporary directory:** Created per analysis run (`/tmp/sibyl-geography-{report_id}-{claim_id}/`).
2. **Cleanup:** Temporary files deleted after findings are produced and image URLs are stored.
3. **Size limits:** Monitor disk usage; fail gracefully if disk space is insufficient.

---

## 10. Gemini 2.5 Pro Multimodal Analysis

### 10.1 Overview

Gemini 2.5 Pro's multimodal capabilities enable visual analysis of satellite imagery. The agent sends satellite images (RGB composites, NDVI maps, before/after comparisons) to Gemini along with analysis prompts, receiving structured analysis results.

### 10.2 Image Preparation for LLM

Before sending to Gemini, images are:

1. **Converted to PNG/JPEG:** GeoTIFF files converted to standard image formats.
2. **Resized:** Downsampled to reasonable size (max 2048x2048) while preserving key features.
3. **Annotated:** Overlaid with location labels, date stamps, and scale bars for context.

### 10.3 Analysis Prompt Structure

```python
def build_analysis_prompt(
    claim_text: str,
    location: ExtractedLocation,
    analysis_type: str  # "vegetation_change" | "land_cover" | "facility_verification"
) -> str:
    """Build prompt for Gemini 2.5 Pro satellite image analysis."""
    
    if analysis_type == "vegetation_change":
        prompt = f"""
Analyze the provided satellite imagery to verify the following claim:

CLAIM: {claim_text}

LOCATION: {location.location_name} ({location.coordinates})

TASK: Determine if the satellite imagery supports or contradicts the claim about vegetation change (deforestation/reforestation).

Provide:
1. Observed NDVI values and vegetation density
2. Comparison between before/after images
3. Estimated area of change (if applicable)
4. Whether the evidence supports, contradicts, or is inconclusive
5. Confidence level (0.0-1.0)
"""
    # ... other analysis types
    
    return prompt
```

### 10.4 Multimodal Request Format

The system sends images to Gemini 2.5 Pro via OpenRouter's multimodal API:

```python
async def analyze_with_gemini(
    images: list[str],  # Base64-encoded or file paths
    prompt: str
) -> dict:
    """Send satellite images to Gemini 2.5 Pro for analysis."""
    
    # OpenRouter multimodal format
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                *[{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}} 
                  for img in images]
            ]
        }
    ]
    
    response = await openrouter_client.chat_completion(
        model=Models.GEMINI_PRO,
        messages=messages,
        response_format={"type": "json_schema", "schema": AnalysisResultSchema}
    )
    
    return response
```

### 10.5 Analysis Result Schema

```python
class AnalysisResult(BaseModel):
    """Structured analysis result from Gemini 2.5 Pro."""
    supports_claim: bool | None  # True/False/None (inconclusive)
    confidence: float  # 0.0-1.0
    observed_features: list[str]  # e.g., ["dense_forest", "water_body", "urban_area"]
    ndvi_estimate: float | None  # Estimated mean NDVI
    change_detected: bool | None  # For temporal claims
    change_area_hectares: float | None  # Estimated area of change
    reasoning: str  # Plain-language explanation
    limitations: list[str]  # e.g., ["cloud_cover_affects_visibility", "seasonal_variation"]
```

### 10.6 Combining Automated and LLM Analysis

The system combines:

1. **Automated metrics:** NDVI values, classification statistics, change detection results.
2. **LLM visual analysis:** Gemini's interpretation of visual features, context, and claim alignment.
3. **Final assessment:** Weighted combination of automated and LLM results.

---

## 11. Evidence Output and Finding Structure

### 11.1 Overview

The Geography Agent produces `AgentFinding` objects containing satellite imagery evidence, analysis results, and plain-language summaries. Findings are stored in the shared state and persisted to the database.

### 11.2 Finding Schema

```python
class GeographyFinding(AgentFinding):
    """Geography Agent finding with satellite imagery evidence."""
    finding_id: str  # UUID
    agent_name: str = "geography"
    claim_id: str
    evidence_type: str = "satellite_imagery"
    
    summary: str  # Plain-language summary (e.g., "Satellite imagery from 2024 shows dense forest cover consistent with reforestation claim")
    
    details: dict  # Structured evidence:
        # - location: {name, coordinates}
        # - imagery_dates: [before_date, after_date]
        # - ndvi_values: {before: float, after: float}
        # - change_metrics: {area_hectares: float, direction: str}
        # - land_cover: {class: percentage}
        # - image_references: [MPC URLs]
        # - cloud_cover: float
        # - analysis_confidence: float
    
    supports_claim: bool | None  # True/False/None (inconclusive)
    confidence: float  # 0.0-1.0
    
    iteration: int  # Investigation cycle number
```

### 11.3 Finding Details Structure

```python
finding_details = {
    "location": {
        "name": "Borneo, Indonesia",
        "coordinates": [-0.5, 113.0],
        "bbox": [-1.0, 112.0, 0.0, 114.0]
    },
    "imagery_dates": {
        "before": "2020-06-15",
        "after": "2024-06-20"
    },
    "ndvi_values": {
        "before": 0.45,
        "after": 0.72,
        "change": 0.27,
        "change_percentage": 60.0
    },
    "change_metrics": {
        "area_hectares": 4200.0,  # Area of significant change
        "direction": "increase",  # Reforestation
        "change_threshold": 0.1
    },
    "land_cover": {
        "before": {"forest": 0.3, "grassland": 0.5, "bare": 0.2},
        "after": {"forest": 0.75, "grassland": 0.2, "bare": 0.05}
    },
    "image_references": [
        "https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-2-l2a/items/S2A_MSIL2A_20200615T023551_N0214_R089_T49MGV_20200615T060552",
        "https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-2-l2a/items/S2A_MSIL2A_20240620T023551_N0214_R089_T49MGV_20240620T060552"
    ],
    "cloud_cover": {
        "before": 5.2,
        "after": 8.1
    },
    "analysis_confidence": 0.85,
    "gemini_analysis": {
        "supports_claim": True,
        "reasoning": "Satellite imagery shows clear increase in vegetation density...",
        "observed_features": ["dense_forest", "reforestation_pattern"]
    }
}
```

### 11.4 Summary Generation

The system generates plain-language summaries:

```python
def generate_finding_summary(
    claim: Claim,
    analysis_result: AnalysisResult,
    change_metrics: dict
) -> str:
    """Generate plain-language finding summary."""
    
    if analysis_result.supports_claim is True:
        summary = f"Satellite imagery from {analysis_result.imagery_dates['after']} supports the claim. "
        if change_metrics.get("direction") == "increase":
            summary += f"NDVI analysis indicates reforestation: mean NDVI increased from {analysis_result.ndvi_values['before']:.2f} to {analysis_result.ndvi_values['after']:.2f} (+{change_metrics['change_percentage']:.1f}%). "
            summary += f"Approximately {change_metrics['area_hectares']:.0f} hectares show significant vegetation increase."
        # ... other cases
    
    elif analysis_result.supports_claim is False:
        summary = f"Satellite imagery contradicts the claim. "
        # ... contradiction details
    
    else:
        summary = f"Satellite imagery is inconclusive. "
        # ... limitations
    
    return summary
```

---

## 12. Satellite Image Storage and References

### 12.1 Overview

Satellite images are not stored locally long-term. Instead, the system stores references (MPC STAC Item URLs) that enable on-demand retrieval and visualization in the detective dashboard.

### 12.2 Image Reference Format

Findings include `image_references` as a list of MPC STAC Item URLs:

```python
image_references = [
    "https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-2-l2a/items/{item_id}"
]
```

These URLs point to STAC Items, from which specific band assets can be retrieved.

### 12.3 Asset URL Generation

For dashboard display, the system generates signed asset URLs:

```python
def get_visualization_url(stac_item_id: str, band: str = "visual") -> str:
    """Generate signed URL for visualization asset.
    
    The 'visual' asset is a pre-computed true-color RGB composite.
    """
    item = catalog.get_item(stac_item_id)
    if "visual" in item.assets:
        return item.assets["visual"].href  # Already signed
    # Fallback: construct from B02, B03, B04
    return construct_rgb_url(item, ["B02", "B03", "B04"])
```

### 12.4 Dashboard Image Display

The detective dashboard (FRD 12) displays satellite images:

1. **Fetch STAC Item:** Retrieve item metadata from MPC.
2. **Get signed asset URL:** Access the "visual" asset or construct RGB composite.
3. **Display in agent node:** Render image tile with caption (location, date, coordinates).

### 12.5 Image Caching

For performance, the system:

1. **Caches STAC Item metadata:** Avoids repeated API calls for the same item.
2. **Does not cache image binaries:** Images are fetched on-demand from MPC (MPC handles caching).

---

## 13. Inter-Agent Communication Participation

### 13.1 Overview

The Geography Agent participates in the inter-agent communication protocol (PRD Section 5.4). It can receive `InfoRequest` objects from other agents and post `InfoResponse` objects with geographic findings.

### 13.2 Receiving InfoRequests

When the Orchestrator routes an `InfoRequest` to the Geography Agent:

```python
# In investigate_geography node
for request in state.info_requests:
    if (request.status == "routed" and 
        "geography" in request.target_agents and
        request.requesting_agent != "geography"):
        
        # Process the request
        response = await process_info_request(request, state)
        
        # Post response
        info_responses.append(InfoResponse(
            request_id=request.request_id,
            requesting_agent=request.requesting_agent,
            responding_agent="geography",
            summary=response.summary,
            details=response.details,
            timestamp=datetime.utcnow()
        ))
```

### 13.3 Processing InfoRequests

The Geography Agent handles requests such as:

- **"Verify facility location at coordinates X, Y"** → Query satellite imagery, confirm facility presence.
- **"Check land use at location Z"** → Perform land cover classification.
- **"Assess environmental impact at site A"** → Analyze NDVI, detect changes.

### 13.4 Posting InfoRequests

The Geography Agent may post requests to other agents:

- **To Legal Agent:** "What are the IFRS S2.13 requirements for geographic risk disclosure?"
- **To Data/Metrics Agent:** "Verify the claimed area calculation (5,000 hectares) matches satellite measurements."
- **To News/Media Agent:** "Has there been public reporting about environmental issues at this location?"

### 13.5 InfoRequest Visibility

All InfoRequests and InfoResponses are emitted as `StreamEvent` objects for the detective dashboard, showing cross-agent communication flows.

---

## 14. Re-Investigation Handling

### 14.1 Overview

When the Judge Agent requests re-investigation (FRD 11), the Geography Agent receives refined queries and additional context to address specific evidence gaps.

### 14.2 Re-Investigation Context

The Geography Agent receives `ReinvestigationRequest` objects with:

- `claim_id`: The claim to re-investigate
- `evidence_gap`: Description of what evidence is missing
- `refined_queries`: Specific questions to address
- `required_evidence`: What would constitute sufficient evidence

### 14.3 Re-Investigation Processing

```python
# In investigate_geography node
for reinv_request in state.reinvestigation_requests:
    if reinv_request.target_agents and "geography" in reinv_request.target_agents:
        # Re-investigate with refined focus
        claim = find_claim_by_id(state.claims, reinv_request.claim_id)
        
        # Apply refined queries (e.g., "Focus on NDVI change in the northern sector")
        refined_location = extract_refined_location(reinv_request.refined_queries)
        refined_time_range = extract_refined_time_range(reinv_request.refined_queries)
        
        # Query with refined parameters
        findings = await investigate_with_refined_params(
            claim, refined_location, refined_time_range
        )
```

### 14.4 Iteration Tracking

Findings include `iteration` field indicating the investigation cycle:

- `iteration=1`: First investigation
- `iteration=2`: First re-investigation
- `iteration=3`: Second re-investigation (if needed)

---

## 15. StreamEvent Emissions

### 15.1 Overview

The Geography Agent emits `StreamEvent` objects throughout its execution, providing real-time updates to the detective dashboard (FRD 12) and enabling visualization of satellite imagery.

### 15.2 Event Types

| Event Type | Data Fields | When |
|---|---|---|
| `agent_started` | `{}` | Node begins execution |
| `agent_thinking` | `{message: str}` | Progress updates ("Geocoding location...", "Querying MPC...", "Analyzing imagery...") |
| `evidence_found` | `{claim_id: str, evidence_type: "satellite_imagery", image_urls: [str], summary: str}` | Satellite evidence discovered |
| `agent_completed` | `{claims_processed: int, findings_count: int}` | Processing finished |

### 15.3 Satellite Image Events

The `evidence_found` event includes satellite image references:

```python
StreamEvent(
    event_type="evidence_found",
    agent_name="geography",
    data={
        "claim_id": claim.claim_id,
        "evidence_type": "satellite_imagery",
        "image_urls": [
            "https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-2-l2a/items/{item_id}"
        ],
        "location": {"name": "Borneo", "coordinates": [-0.5, 113.0]},
        "imagery_date": "2024-06-20",
        "summary": "Found satellite imagery supporting reforestation claim"
    },
    timestamp=datetime.utcnow().isoformat()
)
```

### 15.4 Dashboard Integration

The detective dashboard (FRD 12) consumes these events to:

1. Display satellite image tiles in the Geography Agent node.
2. Show location markers on a map.
3. Render before/after image comparisons for temporal claims.

---

## 16. Error Handling

### 16.1 MPC API Errors

| Error | Trigger | Handling |
|---|---|---|
| MPC API unavailable | Connection timeout, 503 error | Emit error StreamEvent; produce finding with `evidence_type="error"`, `supports_claim=None`; pipeline continues |
| STAC query timeout | Query exceeds 30 seconds | Retry once; if still fails, produce finding indicating timeout |
| Invalid STAC response | Malformed JSON, missing fields | Log error; skip problematic items; continue with valid items |

### 16.2 Geocoding Errors

| Error | Trigger | Handling |
|---|---|---|
| Location not found | Nominatim returns no results | Use Gemini 2.5 Pro to extract coordinates from claim text; if still fails, produce finding with `supports_claim=None` |
| Ambiguous location | Multiple geocoding results | Use claim context to disambiguate; select most relevant; note ambiguity in finding |
| Geocoding rate limit | 429 Too Many Requests | Implement exponential backoff; queue requests with delays |

### 16.3 Image Processing Errors

| Error | Trigger | Handling |
|---|---|---|
| Download failure | Asset URL returns 404 or timeout | Retry once; if fails, produce finding indicating image unavailable |
| Corrupt GeoTIFF | File cannot be read by rasterio | Skip corrupted file; try alternative scene; note limitation in finding |
| Insufficient disk space | Temporary directory full | Emit error; produce finding with limitation note; cleanup temporary files |

### 16.4 Analysis Errors

| Error | Trigger | Handling |
|---|---|---|
| Gemini API failure | OpenRouter returns error | Retry up to 3 times (handled by OpenRouter client); if fails, use automated analysis only (lower confidence) |
| No imagery available | Zero STAC Items returned | Produce finding with `supports_claim=None`, reasoning: "No Sentinel-2 imagery available for this location/time period" |
| High cloud cover | All scenes > 50% cloud cover | Use clearest available scene; note cloud cover limitation; adjust confidence downward |

### 16.5 Graceful Degradation

The Geography Agent degrades gracefully:

1. **Partial failure:** If one claim fails, continue processing other claims.
2. **Reduced analysis:** If image processing fails, use STAC Item metadata only (lower confidence).
3. **Error findings:** Produce findings with `evidence_type="error"` rather than crashing.

---

## 17. Backend Dependencies and Configuration

### 17.1 Python Dependencies

The system shall add the following packages to `requirements.txt`:

```
pystac-client>=0.7.0
rasterio>=1.3.0
numpy>=1.24.0
httpx>=0.25.0  # For geocoding service
```

### 17.2 Configuration

```python
# app/core/config.py

# Microsoft Planetary Computer
MPC_STAC_URL: str = "https://planetarycomputer.microsoft.com/api/stac/v1"
MPC_COLLECTION: str = "sentinel-2-l2a"

# Geocoding
GEOCODING_SERVICE_URL: str = "https://nominatim.openstreetmap.org/search"
GEOCODING_RATE_LIMIT_SECONDS: float = 1.0

# Image Processing
TEMP_IMAGE_DIR: str = "/tmp/sibyl-geography"
MAX_TEMP_DIR_SIZE_GB: float = 5.0

# Analysis
NDVI_CHANGE_THRESHOLD: float = 0.1
CLOUD_COVER_MAX_PREFERRED: float = 20.0
CLOUD_COVER_MAX_ACCEPTABLE: float = 50.0
```

### 17.3 Service Initialization

```python
# app/services/satellite_service.py

satellite_service = SatelliteService()
geocoding_service = GeocodingService()

# Initialize on startup
async def startup():
    await satellite_service.connect()
```

---

## 18. Exit Criteria

FRD 10 is complete when ALL of the following are satisfied:

| # | Criterion | Verification |
|---|---|---|
| 1 | Geography Agent node executes | Start analysis with geographic claims; verify `investigate_geography` node runs |
| 2 | Location extraction works | Verify location names and coordinates are extracted from claim text |
| 3 | Geocoding resolves location names | Test with "Borneo, Indonesia"; verify coordinates are returned |
| 4 | MPC STAC query succeeds | Verify Sentinel-2 scenes are retrieved for a test location |
| 5 | Satellite images are downloaded | Verify GeoTIFF files are downloaded for required bands |
| 6 | NDVI calculation works | Verify NDVI values are computed correctly (range -1 to 1) |
| 7 | Land cover classification works | Verify pixels are classified into forest/urban/water/etc. |
| 8 | Temporal comparison works | Test with before/after dates; verify change metrics are computed |
| 9 | Gemini 2.5 Pro analyzes imagery | Verify multimodal analysis produces structured results |
| 10 | Evidence findings are produced | Verify `AgentFinding` objects include satellite evidence |
| 11 | Findings include image references | Verify `image_references` contain MPC STAC Item URLs |
| 12 | Findings include NDVI values | Verify NDVI statistics are included in finding details |
| 13 | Findings include change metrics | For temporal claims, verify area and direction of change |
| 14 | StreamEvents are emitted | Verify events stream to frontend with image URLs |
| 15 | Inter-agent communication works | Post InfoRequest from another agent; verify Geography Agent responds |
| 16 | Re-investigation works | Trigger re-investigation; verify refined queries are processed |
| 17 | Error handling works | Simulate MPC unavailability; verify graceful degradation |
| 18 | High cloud cover handled | Test with >50% cloud cover; verify limitation is noted |
| 19 | No imagery scenario handled | Test location with no Sentinel-2 coverage; verify appropriate finding |
| 20 | Detective dashboard displays images | Verify satellite image tiles appear in Geography Agent node (FRD 12) |

---

## Appendix A: Geography Agent Prompt Templates

### A.1 Location Extraction Prompt

```
Extract location information from the following sustainability claim. Identify:
1. Location names (cities, regions, countries, facility names)
2. Geographic coordinates (if explicitly stated)
3. Time references (dates, time periods for temporal analysis)
4. Area descriptions (hectares, square kilometers)

CLAIM: {claim_text}

Return structured JSON with:
- location_name: string or null
- coordinates: [latitude, longitude] or null
- time_range: [start_date, end_date] or null
- area_description: string or null
- confidence: float (0.0-1.0)
```

### A.2 Satellite Image Analysis Prompt

```
Analyze the provided satellite imagery to verify the following sustainability claim.

CLAIM: {claim_text}
LOCATION: {location_name} ({coordinates})
IMAGERY DATE: {imagery_date}

TASK: Determine if the satellite imagery supports, contradicts, or is inconclusive regarding the claim.

Consider:
- Vegetation density (NDVI values)
- Land cover classification (forest, urban, water, etc.)
- Visible features (facilities, infrastructure, environmental changes)
- Temporal changes (if before/after images provided)

Provide structured analysis:
- supports_claim: true/false/null
- confidence: 0.0-1.0
- observed_features: [list of features]
- ndvi_estimate: float or null
- reasoning: plain-language explanation
- limitations: [list of limitations, e.g., cloud cover, resolution]
```

### A.3 Temporal Comparison Prompt

```
Compare the provided before/after satellite imagery to verify a temporal environmental claim.

CLAIM: {claim_text}
LOCATION: {location_name}
BEFORE DATE: {before_date}
AFTER DATE: {after_date}

TASK: Assess whether the imagery shows the claimed environmental change (deforestation, reforestation, etc.).

Analyze:
- NDVI changes between time periods
- Land cover changes
- Visible environmental impacts
- Estimated area of change

Provide:
- change_detected: true/false/null
- change_direction: "increase" | "decrease" | "mixed"
- change_area_hectares: float or null
- ndvi_before: float
- ndvi_after: float
- change_percentage: float
- reasoning: explanation of observed changes
```

---

## Appendix B: STAC Query Examples

### B.1 Basic Sentinel-2 Search

```python
from pystac_client import Client

catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")

search = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=[112.0, -1.0, 114.0, 0.0],  # [min_lon, min_lat, max_lon, max_lat]
    datetime="2024-01-01/2024-12-31",
    query={"eo:cloud_cover": {"lt": 20}},
    limit=10
)

for item in search.items():
    print(f"Item ID: {item.id}")
    print(f"Date: {item.datetime}")
    print(f"Cloud Cover: {item.properties.get('eo:cloud_cover')}%")
    print(f"Assets: {list(item.assets.keys())}")
```

### B.2 Retrieve Specific Band Assets

```python
item = catalog.get_item("S2A_MSIL2A_20240620T023551_N0214_R089_T49MGV_20240620T060552")

# Get Red band (B04)
red_asset = item.assets["B04"]
red_url = red_asset.href  # Signed URL

# Get NIR band (B08)
nir_asset = item.assets["B08"]
nir_url = nir_asset.href  # Signed URL

# Get true-color visual asset (if available)
if "visual" in item.assets:
    visual_url = item.assets["visual"].href
```

### B.3 Temporal Comparison Query

```python
# Before image
before_search = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=bbox,
    datetime="2020-01-01/2020-12-31",
    query={"eo:cloud_cover": {"lt": 20}},
    limit=1
)
before_item = next(before_search.items(), None)

# After image
after_search = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=bbox,
    datetime="2024-01-01/2024-12-31",
    query={"eo:cloud_cover": {"lt": 20}},
    limit=1
)
after_item = next(after_search.items(), None)
```

---

## Appendix C: NDVI Analysis Algorithm

### C.1 NDVI Calculation Pseudocode

```
function calculate_ndvi(red_band, nir_band):
    // Ensure bands are same resolution
    if red_band.resolution != nir_band.resolution:
        nir_band = resample(nir_band, target_resolution=red_band.resolution)
    
    // Convert to reflectance (if needed)
    red_reflectance = red_band / 10000.0  // Sentinel-2 scaling factor
    nir_reflectance = nir_band / 10000.0
    
    // Calculate NDVI
    numerator = nir_reflectance - red_reflectance
    denominator = nir_reflectance + red_reflectance
    
    // Avoid division by zero
    denominator[denominator == 0] = NaN
    
    ndvi = numerator / denominator
    
    // Clip to valid range
    ndvi = clip(ndvi, min=-1.0, max=1.0)
    
    return ndvi
```

### C.2 NDVI Statistics Calculation

```
function compute_ndvi_statistics(ndvi_array, area_of_interest_mask):
    masked_ndvi = ndvi_array[area_of_interest_mask]
    
    mean_ndvi = mean(masked_ndvi)
    median_ndvi = median(masked_ndvi)
    std_ndvi = standard_deviation(masked_ndvi)
    
    vegetation_pixels = count(masked_ndvi > 0.3)
    dense_vegetation_pixels = count(masked_ndvi > 0.6)
    
    total_pixels = count(area_of_interest_mask)
    vegetation_percentage = vegetation_pixels / total_pixels * 100
    dense_vegetation_percentage = dense_vegetation_pixels / total_pixels * 100
    
    return {
        mean: mean_ndvi,
        median: median_ndvi,
        std: std_ndvi,
        vegetation_percentage: vegetation_percentage,
        dense_vegetation_percentage: dense_vegetation_percentage
    }
```

### C.3 NDVI Change Detection

```
function detect_ndvi_change(ndvi_before, ndvi_after, threshold=0.1):
    ndvi_diff = ndvi_after - ndvi_before
    
    // Significant change mask
    change_mask = abs(ndvi_diff) > threshold
    
    // Calculate change area (assuming 10m pixel resolution)
    pixel_area_m2 = 10 * 10  // 100 m²
    change_area_m2 = count(change_mask) * pixel_area_m2
    change_area_hectares = change_area_m2 / 10000
    
    // Mean change
    mean_before = mean(ndvi_before)
    mean_after = mean(ndvi_after)
    mean_change = mean_after - mean_before
    change_percentage = (mean_change / mean_before) * 100 if mean_before > 0 else 0
    
    // Direction
    if mean_change > 0.05:
        direction = "increase"  // Reforestation
    elif mean_change < -0.05:
        direction = "decrease"  // Deforestation
    else:
        direction = "mixed"
    
    return {
        change_area_hectares: change_area_hectares,
        mean_before: mean_before,
        mean_after: mean_after,
        mean_change: mean_change,
        change_percentage: change_percentage,
        direction: direction
    }
```

---

## Appendix D: Sentinel-2 Band Reference

### D.1 Complete Band Specifications

| Band | Central Wavelength (nm) | Bandwidth (nm) | Resolution | Common Use |
|---|---|---|---|---|
| B01 | 443 | 20 | 60m | Aerosol correction |
| B02 | 490 | 65 | 10m | Blue (RGB) |
| B03 | 560 | 35 | 10m | Green (RGB) |
| B04 | 665 | 30 | 10m | Red (RGB, NDVI) |
| B05 | 705 | 15 | 20m | Red Edge 1 |
| B06 | 740 | 15 | 20m | Red Edge 2 |
| B07 | 783 | 20 | 20m | Red Edge 3 |
| B08 | 842 | 115 | 10m | NIR (NDVI) |
| B08A | 865 | 20 | 20m | Red Edge 4 |
| B09 | 945 | 20 | 60m | Water vapor |
| B11 | 1610 | 90 | 20m | SWIR 1 (land cover) |
| B12 | 2190 | 180 | 20m | SWIR 2 (land cover) |

### D.2 Band Combinations for Common Analyses

**True-Color RGB:**
- Red: B04
- Green: B03
- Blue: B02

**False-Color Infrared:**
- Red: B08 (NIR)
- Green: B04 (Red)
- Blue: B03 (Green)
- Highlights vegetation in red

**NDVI:**
- NIR: B08
- Red: B04
- Formula: (B08 - B04) / (B08 + B04)

**Land Cover Classification:**
- Primary: B04, B08 (NDVI)
- Enhanced: B11, B12 (SWIR for moisture/vegetation discrimination)

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| Use `pystac-client` over direct STAC API calls | `pystac-client` handles authentication, signing, pagination, and error handling. Direct API calls would require manual URL construction, signing logic, and pagination handling. |
| Free geocoding (Nominatim) over paid service | Nominatim is free and sufficient for hackathon scope. Paid services (Google Geocoding API) offer higher accuracy but add cost and API key management complexity. |
| Rule-based land cover classification over ML model | Training a custom ML model requires labeled data and training infrastructure. Rule-based classification provides good results for clear cases (forest vs. clear-cut) and is sufficient for MVP. Gemini 2.5 Pro visual analysis supplements rule-based results. |
| Store image references (URLs) over image binaries | Satellite images are large (10-50MB per scene). Storing binaries would bloat the database. MPC URLs enable on-demand retrieval. Images are cached by MPC's CDN. |
| Temporary file storage over in-memory processing | Large GeoTIFF files (100MB+) exceed reasonable memory limits. Temporary files enable processing of large scenes without memory exhaustion. Cleanup ensures disk space is reclaimed. |
| Gemini 2.5 Pro for multimodal analysis over vision-only models | Gemini 2.5 Pro combines vision with strong spatial reasoning, enabling contextual interpretation of satellite imagery. Vision-only models lack the reasoning capability to connect imagery to claim verification. |
| NDVI as primary vegetation metric over other indices | NDVI is the most widely recognized vegetation index, well-documented, and easy to interpret. Other indices (EVI, SAVI) offer improvements but add complexity. NDVI is sufficient for MVP. |
| 10m resolution focus over 20m/60m bands | 10m resolution (B04, B08) provides sufficient detail for facility-level and area-level claims. 20m/60m bands are used only when needed (SWIR for land cover). |
| Cloud cover filtering (<20% preferred) over accepting all scenes | Low cloud cover ensures reliable analysis. High cloud cover obscures ground features and reduces confidence. The system accepts up to 50% cloud cover if no alternatives exist, with confidence adjustment. |
| Temporal comparison with 6-month minimum gap | Ensures detectable change while accounting for seasonal variation. Shorter gaps may capture seasonal effects rather than actual environmental change. |
| Geocoding cache to reduce API calls | Nominatim rate limits (1 req/sec) would slow batch processing. Caching avoids redundant geocoding for repeated location names. |
| Structured output (JSON schema) from Gemini | Ensures parseable analysis results. Free-text responses would require complex parsing and are error-prone. |
| Error findings instead of failing silently | Producing error findings maintains pipeline continuity. Other agents can still investigate claims even if Geography Agent fails. The Judge evaluates available evidence. |
| MPC STAC API (no API key) over commercial providers | MPC is free and ideal for hackathon. Commercial providers (Planet, Maxar) offer higher resolution but require API keys and may have usage limits. |
| Sentinel-2 Level-2A (atmospherically corrected) over Level-1C | Level-2A products have atmospheric correction applied, improving NDVI accuracy. Level-1C requires additional processing. Level-2A is the standard for analysis. |
| Percentage-based area calculations over pixel counting | Accounts for coordinate system distortions. Pixel counting assumes uniform pixel size, which is inaccurate at high latitudes. Percentage-based calculations use actual geographic area. |
| Combined automated + LLM analysis over LLM-only | Automated metrics (NDVI, classification) provide objective measurements. LLM analysis provides contextual interpretation. Combining both yields more reliable results than LLM-only. |
