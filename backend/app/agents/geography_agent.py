"""Geography Agent - verifies geographic claims via satellite imagery.

Implements FRD 10.

Model: Gemini 2.5 Pro (best multimodal/vision capabilities)
Data Source: Microsoft Planetary Computer (Sentinel-2 imagery)
"""

from app.agents.state import SibylState


async def investigate_geography(state: SibylState) -> dict:
    """
    Investigate geographic and environmental claims using satellite imagery.

    Capabilities:
    - Vegetation change detection (NDVI analysis)
    - Land cover classification
    - Temporal comparison (before/after imagery)
    - Environmental impact indicators

    Args:
        state: Current pipeline state with assigned geographic claims

    Returns:
        Partial state update with geographic findings
    """
    pass
