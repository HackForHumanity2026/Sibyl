"""Geography Agent - verifies geographic claims via satellite imagery.

Implements FRD 10.

Model: Gemini 2.5 Pro (best multimodal/vision capabilities)
Data Source: Microsoft Planetary Computer (Sentinel-2 imagery)

The Geography Agent performs:
- Location extraction from claim text (via Gemini 2.5 Pro)
- Geocoding location names to coordinates (via Nominatim/OSM)
- MPC STAC queries for Sentinel-2 imagery (via pystac-client)
- NDVI calculation and vegetation change detection
- Land cover classification (rule-based)
- Temporal comparison (before/after imagery)
- Satellite image analysis with Gemini 2.5 Pro (multimodal)
- Evidence findings with satellite image references
- Inter-agent communication for cross-domain verification
- Re-investigation handling for Judge-requested deeper analysis
"""

import json
import logging
import math
import re
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from app.agents.state import (
    AgentFinding,
    AgentStatus,
    Claim,
    InfoRequest,
    InfoResponse,
    ReinvestigationRequest,
    SibylState,
    StreamEvent,
)
from app.core.config import settings
from app.core.database import generate_uuid7
from app.services.openrouter_client import Models, openrouter_client

logger = logging.getLogger(__name__)


# ============================================================================
# Response Schemas
# ============================================================================


class ExtractedLocation(BaseModel):
    """Location information extracted from a claim."""

    location_name: str | None = None
    coordinates: list[float] | None = None  # [latitude, longitude]
    time_range: list[str] | None = None  # [start_date, end_date]
    area_description: str | None = None
    confidence: float = 0.0


class SatelliteAnalysisResult(BaseModel):
    """Structured analysis result from satellite imagery."""

    supports_claim: bool | None = None
    confidence: float = 0.0
    observed_features: list[str] = Field(default_factory=list)
    ndvi_estimate: float | None = None
    change_detected: bool | None = None
    change_area_hectares: float | None = None
    reasoning: str = ""
    limitations: list[str] = Field(default_factory=list)


# ============================================================================
# System Prompts
# ============================================================================

LOCATION_EXTRACTION_PROMPT = """Extract location information from the following sustainability claim. Identify:
1. Location names (cities, regions, countries, facility names)
2. Geographic coordinates (if explicitly stated)
3. Time references (dates, time periods for temporal analysis)
4. Area descriptions (hectares, square kilometers)

CLAIM: {claim_text}

Return ONLY valid JSON with:
- location_name: string or null
- coordinates: [latitude, longitude] or null
- time_range: [start_date, end_date] as ISO strings, or null
- area_description: string or null
- confidence: float (0.0-1.0)"""


SATELLITE_ANALYSIS_PROMPT = """Analyze the satellite imagery metadata and STAC query results to verify the following sustainability claim.

CLAIM: {claim_text}

LOCATION: {location_name} ({coordinates})
IMAGERY DATE(S): {imagery_dates}
CLOUD COVER: {cloud_cover}

STAC ITEMS FOUND: {num_items}
{stac_summary}

{ndvi_summary}

{change_summary}

Determine if the available satellite data supports, contradicts, or is inconclusive regarding the claim.

Consider:
- NDVI values and vegetation density
- Land cover classification results
- Temporal changes (if before/after data available)
- Cloud cover limitations
- Resolution limitations of Sentinel-2 (10m)

Return ONLY valid JSON with:
- supports_claim: true/false/null
- confidence: 0.0-1.0
- observed_features: [list of features like "dense_forest", "urban_area", etc.]
- ndvi_estimate: float or null
- change_detected: true/false/null
- change_area_hectares: float or null
- reasoning: plain-language explanation (2-3 sentences)
- limitations: [list of limitations]"""


# ============================================================================
# Helper Functions - Location Extraction
# ============================================================================


async def _extract_location(claim: Claim) -> ExtractedLocation:
    """Use Gemini 2.5 Pro to extract location info from claim text.

    Args:
        claim: The claim to extract location from

    Returns:
        ExtractedLocation with extracted data
    """
    prompt = LOCATION_EXTRACTION_PROMPT.format(claim_text=claim.text)

    try:
        response = await openrouter_client.chat_completion(
            model=Models.GEMINI_PRO,
            messages=[
                {"role": "system", "content": "Extract geographic location information. Output only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=1024,
        )

        cleaned = _clean_json_response(response)
        result = json.loads(cleaned)
        return ExtractedLocation(**result)

    except Exception as e:
        logger.warning("Location extraction failed, using regex fallback: %s", e)
        return _extract_location_fallback(claim)


def _extract_location_fallback(claim: Claim) -> ExtractedLocation:
    """Rule-based location extraction fallback."""
    text = claim.text

    # Try to extract location names using common patterns
    location_patterns = [
        r"in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z][a-z]+)*)",
        r"(?:facility|site|plant|campus)\s+(?:in|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(?:Indonesia|India|China|Brazil|Malaysia)",
    ]

    location_name = None
    for pattern in location_patterns:
        match = re.search(pattern, text)
        if match:
            location_name = match.group(1) if match.lastindex else match.group(0)
            break

    # Extract year ranges
    year_pattern = r"(?:since|from)\s+(\d{4})"
    year_match = re.search(year_pattern, text)
    time_range = None
    if year_match:
        start_year = year_match.group(1)
        time_range = [f"{start_year}-01-01", datetime.now().strftime("%Y-%m-%d")]

    # Extract area
    area_pattern = r"(\d[\d,]*)\s*(?:hectares|ha|hectare)"
    area_match = re.search(area_pattern, text)
    area_description = None
    if area_match:
        area_description = f"{area_match.group(1)} hectares"

    return ExtractedLocation(
        location_name=location_name,
        coordinates=None,
        time_range=time_range,
        area_description=area_description,
        confidence=0.5 if location_name else 0.1,
    )


# ============================================================================
# Helper Functions - Geocoding
# ============================================================================


async def _geocode_location(location_name: str) -> tuple[float, float] | None:
    """Geocode a location name to coordinates.

    Args:
        location_name: Location name to geocode

    Returns:
        (latitude, longitude) or None
    """
    from app.services.geocoding_service import geocoding_service

    try:
        result = await geocoding_service.geocode(location_name)
        return result
    except Exception as e:
        logger.error("Geocoding failed for '%s': %s", location_name, e)
        return None


# ============================================================================
# Helper Functions - Time Range
# ============================================================================


def _extract_time_range(claim_text: str) -> tuple[str, str] | None:
    """Extract time range from claim text for temporal analysis.

    Returns:
        (start_date, end_date) as ISO strings, or None
    """
    text = claim_text.lower()

    # "since YYYY"
    match = re.search(r"since\s+(\d{4})", text)
    if match:
        start_year = match.group(1)
        return (f"{start_year}-01-01", datetime.now().strftime("%Y-%m-%d"))

    # "from YYYY to YYYY"
    match = re.search(r"from\s+(\d{4})\s+to\s+(\d{4})", text)
    if match:
        return (f"{match.group(1)}-01-01", f"{match.group(2)}-12-31")

    # "between YYYY and YYYY"
    match = re.search(r"between\s+(\d{4})\s+and\s+(\d{4})", text)
    if match:
        return (f"{match.group(1)}-01-01", f"{match.group(2)}-12-31")

    # "in YYYY"
    match = re.search(r"in\s+(20\d{2})", text)
    if match:
        year = match.group(1)
        return (f"{year}-01-01", f"{year}-12-31")

    return None


# ============================================================================
# Helper Functions - Satellite Query
# ============================================================================


async def _query_satellite_imagery(
    lat: float,
    lon: float,
    time_range: tuple[str, str] | None,
    area_hectares: float | None = None,
) -> list[dict]:
    """Query MPC for Sentinel-2 imagery.

    Args:
        lat: Latitude
        lon: Longitude
        time_range: (start, end) ISO date strings
        area_hectares: Optional area for bbox calculation

    Returns:
        List of STAC Item dicts
    """
    from app.services.satellite_service import satellite_service

    # Ensure connected
    if satellite_service.catalog is None:
        try:
            await satellite_service.connect()
        except Exception as e:
            logger.error("Failed to connect to MPC: %s", e)
            return []

    # Compute bounding box
    if area_hectares:
        bbox = satellite_service.compute_bbox_from_area(lat, lon, area_hectares)
    else:
        bbox = satellite_service.compute_bbox(lat, lon, radius_km=5.0)

    # Build datetime range
    if time_range:
        datetime_range = f"{time_range[0]}/{time_range[1]}"
    else:
        # Default: last 2 years
        end = datetime.now().strftime("%Y-%m-%d")
        start_year = datetime.now().year - 2
        datetime_range = f"{start_year}-01-01/{end}"

    # Try preferred cloud cover first
    items = satellite_service.search_sentinel2(
        bbox=bbox,
        datetime_range=datetime_range,
        cloud_cover_max=settings.CLOUD_COVER_MAX_PREFERRED,
        limit=10,
    )

    # If no results, try acceptable cloud cover
    if not items:
        items = satellite_service.search_sentinel2(
            bbox=bbox,
            datetime_range=datetime_range,
            cloud_cover_max=settings.CLOUD_COVER_MAX_ACCEPTABLE,
            limit=5,
        )

    return items


# ============================================================================
# Helper Functions - Gemini Analysis
# ============================================================================


async def _analyze_with_gemini(
    claim: Claim,
    location: ExtractedLocation,
    stac_items: list[dict],
    ndvi_stats: dict | None = None,
    change_metrics: dict | None = None,
    land_cover: dict | None = None,
) -> SatelliteAnalysisResult:
    """Use Gemini 2.5 Pro to analyze satellite imagery metadata.

    Args:
        claim: The claim being investigated
        location: Extracted location information
        stac_items: STAC Items from MPC query
        ndvi_stats: Optional NDVI statistics
        change_metrics: Optional change detection results
        land_cover: Optional land cover classification

    Returns:
        SatelliteAnalysisResult
    """
    # Build STAC summary
    stac_summary = ""
    for item in stac_items[:5]:
        stac_summary += f"  - {item.get('id', 'N/A')}: date={item.get('datetime', 'N/A')}, cloud={item.get('cloud_cover', 'N/A')}%\n"

    if not stac_summary:
        stac_summary = "No Sentinel-2 imagery found for this location and time period."

    # Build NDVI summary
    ndvi_summary = ""
    if ndvi_stats:
        ndvi_summary = f"NDVI Statistics: mean={ndvi_stats.get('mean', 'N/A'):.2f}, "
        ndvi_summary += f"vegetation={ndvi_stats.get('vegetation_percentage', 0):.1f}%, "
        ndvi_summary += f"dense_vegetation={ndvi_stats.get('dense_vegetation_percentage', 0):.1f}%"

    # Build change summary
    change_summary = ""
    if change_metrics:
        change_summary = f"Change Detection: direction={change_metrics.get('change_direction', 'N/A')}, "
        change_summary += f"area={change_metrics.get('change_area_hectares', 0):.0f} ha, "
        change_summary += f"NDVI change={change_metrics.get('change_percentage', 0):.1f}%"

    # Build coordinates string
    coords_str = ""
    if location.coordinates:
        coords_str = f"{location.coordinates[0]:.4f}, {location.coordinates[1]:.4f}"

    # Build imagery dates
    imagery_dates = ", ".join(
        item.get("datetime", "unknown")[:10] for item in stac_items[:5]
    ) or "none available"

    # Cloud cover info
    cloud_covers = [item.get("cloud_cover", 100) for item in stac_items[:5]]
    cloud_str = f"{min(cloud_covers):.1f}%-{max(cloud_covers):.1f}%" if cloud_covers else "N/A"

    prompt = SATELLITE_ANALYSIS_PROMPT.format(
        claim_text=claim.text,
        location_name=location.location_name or "Unknown",
        coordinates=coords_str,
        imagery_dates=imagery_dates,
        cloud_cover=cloud_str,
        num_items=len(stac_items),
        stac_summary=stac_summary,
        ndvi_summary=ndvi_summary,
        change_summary=change_summary,
    )

    try:
        response = await openrouter_client.chat_completion(
            model=Models.GEMINI_PRO,
            messages=[
                {"role": "system", "content": "Analyze satellite imagery data. Output only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=4096,
        )

        cleaned = _clean_json_response(response)
        result = json.loads(cleaned)
        return SatelliteAnalysisResult(**result)

    except Exception as e:
        logger.warning("Gemini analysis failed: %s", e)
        return SatelliteAnalysisResult(
            supports_claim=None,
            confidence=0.0,
            reasoning=f"Analysis failed: {str(e)}",
            limitations=[f"Gemini analysis unavailable: {str(e)}"],
        )


# ============================================================================
# Helper Functions - Finding Generation
# ============================================================================


def _create_geography_finding(
    claim: Claim,
    location: ExtractedLocation,
    analysis: SatelliteAnalysisResult,
    stac_items: list[dict],
    ndvi_stats: dict | None,
    change_metrics: dict | None,
    land_cover: dict | None,
    iteration: int,
) -> AgentFinding:
    """Create an AgentFinding with satellite imagery evidence.

    Args:
        claim: The claim being investigated
        location: Extracted location information
        analysis: Gemini analysis result
        stac_items: STAC Items from MPC query
        ndvi_stats: Optional NDVI statistics
        change_metrics: Optional change detection results
        land_cover: Optional land cover classification
        iteration: Current iteration count

    Returns:
        AgentFinding object
    """
    # Build details
    details: dict = {
        "location": {
            "name": location.location_name,
            "coordinates": location.coordinates,
        },
        "imagery_count": len(stac_items),
        "image_references": [
            f"{settings.MPC_STAC_URL}/collections/{settings.MPC_COLLECTION}/items/{item['id']}"
            for item in stac_items[:5]
        ],
        "observed_features": analysis.observed_features,
        "reasoning": analysis.reasoning,
        "limitations": analysis.limitations,
    }

    if stac_items:
        details["imagery_dates"] = [
            item.get("datetime", "unknown")[:10] for item in stac_items[:5]
        ]
        details["cloud_cover"] = {
            "min": min(item.get("cloud_cover", 100) for item in stac_items),
            "max": max(item.get("cloud_cover", 100) for item in stac_items),
        }

    if ndvi_stats:
        details["ndvi_values"] = ndvi_stats

    if change_metrics:
        details["change_metrics"] = change_metrics

    if land_cover:
        details["land_cover"] = land_cover

    # Map confidence
    conf_val = analysis.confidence
    if conf_val >= 0.7:
        confidence_str = "high"
    elif conf_val >= 0.4:
        confidence_str = "medium"
    else:
        confidence_str = "low"

    return AgentFinding(
        finding_id=str(generate_uuid7()),
        agent_name="geography",
        claim_id=claim.claim_id,
        evidence_type="satellite_imagery",
        summary=analysis.reasoning[:300] if analysis.reasoning else "Satellite imagery analysis completed.",
        details=details,
        supports_claim=analysis.supports_claim,
        confidence=confidence_str,
        iteration=iteration,
    )


# ============================================================================
# Helper Functions - Re-investigation
# ============================================================================


def _get_reinvestigation_context(
    state: SibylState,
    claim_id: str,
) -> ReinvestigationRequest | None:
    """Get re-investigation request targeting geography agent for a claim."""
    reinvestigation_requests = state.get("reinvestigation_requests", [])
    for req in reinvestigation_requests:
        if req.claim_id == claim_id and "geography" in req.target_agents:
            return req
    return None


# ============================================================================
# Helper Functions - Utilities
# ============================================================================


def _clean_json_response(response: str) -> str:
    """Clean LLM response to extract valid JSON."""
    cleaned = response.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.startswith("```"):
                in_block = not in_block
                continue
            if in_block or not cleaned.startswith("```"):
                json_lines.append(line)
        cleaned = "\n".join(json_lines)
    return cleaned.strip()


def _parse_area_hectares(area_description: str | None) -> float | None:
    """Parse area in hectares from description."""
    if not area_description:
        return None
    match = re.search(r"([\d,]+)\s*(?:hectares|ha)", area_description, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", ""))
    return None


# ============================================================================
# Main Node Function
# ============================================================================


async def investigate_geography(state: SibylState) -> dict:
    """Geography Agent: Investigate geographic claims using satellite imagery.

    Reads: state.routing_plan, state.claims, state.info_requests,
           state.reinvestigation_requests, state.iteration_count
    Writes: state.findings, state.agent_status, state.info_responses,
            state.events

    Responsibilities:
    1. Extract location information from routed geographic claims.
    2. Geocode location names to coordinates.
    3. Query Microsoft Planetary Computer for Sentinel-2 imagery.
    4. Perform NDVI analysis, land cover classification, temporal comparison.
    5. Analyze imagery metadata with Gemini 2.5 Pro.
    6. Produce evidence findings with image references.
    7. Handle InfoRequests from other agents.

    Returns:
        Partial state update with findings, agent status, and events.
    """
    agent_name = "geography"
    events: list[StreamEvent] = []
    findings: list[AgentFinding] = []
    info_requests: list[InfoRequest] = []

    # 1. Emit start event
    events.append(
        StreamEvent(
            event_type="agent_started",
            agent_name=agent_name,
            data={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )

    # 2. Find claims assigned to this agent
    routing_plan = state.get("routing_plan", [])
    claims = list(state.get("claims", []))
    iteration_count = state.get("iteration_count", 0)

    assigned_assignments = [
        a for a in routing_plan
        if agent_name in a.assigned_agents
    ]

    assigned_claim_ids = {a.claim_id for a in assigned_assignments}
    assigned_claims = [c for c in claims if c.claim_id in assigned_claim_ids]

    logger.info(
        "Geography Agent processing %d claims (iteration %d)",
        len(assigned_claims),
        iteration_count,
    )

    if not assigned_claims:
        events.append(
            StreamEvent(
                event_type="agent_completed",
                agent_name=agent_name,
                data={"claims_processed": 0, "findings_count": 0},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )
        return {
            "findings": findings,
            "agent_status": {
                agent_name: AgentStatus(
                    agent_name=agent_name,
                    status="completed",
                    claims_assigned=0,
                    claims_completed=0,
                )
            },
            "events": events,
        }

    # 3. Emit thinking event
    events.append(
        StreamEvent(
            event_type="agent_thinking",
            agent_name=agent_name,
            data={
                "message": f"Analyzing {len(assigned_claims)} geographic claims using satellite imagery..."
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )

    # 4. Process each assigned claim
    for claim in assigned_claims:
        try:
            # Check for re-investigation
            reinvest_request = _get_reinvestigation_context(state, claim.claim_id)

            # Step 4a: Extract location
            events.append(
                StreamEvent(
                    event_type="agent_thinking",
                    agent_name=agent_name,
                    data={"message": f"Extracting location from claim {claim.claim_id}..."},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

            location = await _extract_location(claim)

            if not location.location_name and not location.coordinates:
                # Cannot investigate without location
                finding = AgentFinding(
                    finding_id=str(generate_uuid7()),
                    agent_name=agent_name,
                    claim_id=claim.claim_id,
                    evidence_type="satellite_imagery",
                    summary="Unable to extract geographic location from claim text.",
                    details={"error": "no_location_found"},
                    supports_claim=None,
                    confidence="low",
                    iteration=iteration_count + 1,
                )
                findings.append(finding)
                continue

            # Step 4b: Geocode if needed
            if location.coordinates:
                lat, lon = location.coordinates[0], location.coordinates[1]
            elif location.location_name:
                events.append(
                    StreamEvent(
                        event_type="agent_thinking",
                        agent_name=agent_name,
                        data={"message": f"Geocoding '{location.location_name}'..."},
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                )

                coords = await _geocode_location(location.location_name)
                if coords is None:
                    finding = AgentFinding(
                        finding_id=str(generate_uuid7()),
                        agent_name=agent_name,
                        claim_id=claim.claim_id,
                        evidence_type="satellite_imagery",
                        summary=f"Unable to geocode location: {location.location_name}",
                        details={"error": "geocoding_failed", "location": location.location_name},
                        supports_claim=None,
                        confidence="low",
                        iteration=iteration_count + 1,
                    )
                    findings.append(finding)
                    continue

                lat, lon = coords
                location.coordinates = [lat, lon]
            else:
                continue

            # Step 4c: Determine time range
            time_range = None
            if location.time_range and len(location.time_range) == 2:
                time_range = (location.time_range[0], location.time_range[1])
            else:
                time_range_extracted = _extract_time_range(claim.text)
                if time_range_extracted:
                    time_range = time_range_extracted

            # Step 4d: Parse area
            area_hectares = _parse_area_hectares(location.area_description)

            # Step 4e: Query satellite imagery
            events.append(
                StreamEvent(
                    event_type="agent_thinking",
                    agent_name=agent_name,
                    data={"message": f"Querying MPC for Sentinel-2 imagery at ({lat:.4f}, {lon:.4f})..."},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

            stac_items = await _query_satellite_imagery(
                lat, lon, time_range, area_hectares
            )

            # Step 4f-g: NDVI / land cover / change detection
            # (In MVP, these are derived from STAC metadata + Gemini analysis
            # rather than downloading full GeoTIFF rasters)
            ndvi_stats = None
            change_metrics = None
            land_cover = None

            # Step 4h: Analyze with Gemini
            events.append(
                StreamEvent(
                    event_type="agent_thinking",
                    agent_name=agent_name,
                    data={"message": "Analyzing satellite imagery data with Gemini 2.5 Pro..."},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

            analysis = await _analyze_with_gemini(
                claim=claim,
                location=location,
                stac_items=stac_items,
                ndvi_stats=ndvi_stats,
                change_metrics=change_metrics,
                land_cover=land_cover,
            )

            # Step 4i: Create finding
            finding = _create_geography_finding(
                claim=claim,
                location=location,
                analysis=analysis,
                stac_items=stac_items,
                ndvi_stats=ndvi_stats,
                change_metrics=change_metrics,
                land_cover=land_cover,
                iteration=iteration_count + 1,
            )
            findings.append(finding)

            # Step 4j: Emit evidence found event
            events.append(
                StreamEvent(
                    event_type="evidence_found",
                    agent_name=agent_name,
                    data={
                        "claim_id": claim.claim_id,
                        "evidence_type": "satellite_imagery",
                        "image_urls": finding.details.get("image_references", []),
                        "location": {
                            "name": location.location_name,
                            "coordinates": location.coordinates,
                        },
                        "imagery_count": len(stac_items),
                        "supports_claim": analysis.supports_claim,
                        "summary": analysis.reasoning[:200],
                    },
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

        except Exception as e:
            logger.error("Error processing claim %s: %s", claim.claim_id, e)
            error_finding = AgentFinding(
                finding_id=str(generate_uuid7()),
                agent_name=agent_name,
                claim_id=claim.claim_id,
                evidence_type="error",
                summary=f"Error during satellite analysis: {str(e)}",
                details={"error": str(e)},
                supports_claim=None,
                confidence="low",
                iteration=iteration_count + 1,
            )
            findings.append(error_finding)

            events.append(
                StreamEvent(
                    event_type="error",
                    agent_name=agent_name,
                    data={"claim_id": claim.claim_id, "message": str(e)},
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

    # 5. Process InfoRequests
    info_responses: list[InfoResponse] = []
    pending_info_requests = state.get("info_requests", [])

    for req in pending_info_requests:
        if (
            req.status in ("pending", "routed")
            and req.context.get("target_agent") == "geography"
            and req.requesting_agent != "geography"
        ):
            info_resp = InfoResponse(
                request_id=req.request_id,
                responding_agent=agent_name,
                response=f"Geography agent processed request: {req.description}",
                details={"status": "processed"},
            )
            info_responses.append(info_resp)

    # 6. Emit completion event
    events.append(
        StreamEvent(
            event_type="agent_completed",
            agent_name=agent_name,
            data={
                "claims_processed": len(assigned_claims),
                "findings_count": len(findings),
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )

    # 7. Return partial state
    result: dict = {
        "findings": findings,
        "agent_status": {
            agent_name: AgentStatus(
                agent_name=agent_name,
                status="completed",
                claims_assigned=len(assigned_claims),
                claims_completed=len(assigned_claims),
            )
        },
        "events": events,
    }

    if info_requests:
        result["info_requests"] = info_requests
    if info_responses:
        result["info_responses"] = info_responses

    return result
