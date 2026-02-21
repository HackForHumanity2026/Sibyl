"""Satellite imagery API routes for Detective Dashboard (FRD 12)."""

import json
import logging
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Security: Allowlist for STAC item URLs
ALLOWED_STAC_HOSTS = ["planetarycomputer.microsoft.com"]
ALLOWED_STAC_PATH_PREFIX = "/api/stac/v1/"

# Security: Allowlist for asset URLs (includes Azure blob storage for MPC assets)
ALLOWED_ASSET_HOSTS = [
    "planetarycomputer.microsoft.com",
    "ai4edatasetspublicassets.blob.core.windows.net",
    "sentinel2l2a01.blob.core.windows.net",
    "sentinel2l2a02.blob.core.windows.net",
]


class SignedUrlResponse(BaseModel):
    """Response containing a signed URL for satellite imagery."""

    url: str


def validate_stac_url(url: str) -> None:
    """Validate that a STAC item URL is from an allowed host.
    
    Raises:
        HTTPException: If the URL is not allowed
    """
    parsed = urlparse(url)
    if parsed.scheme != "https":
        logger.warning("Rejected non-HTTPS STAC URL: %s", parsed.scheme)
        raise HTTPException(status_code=400, detail="Only HTTPS URLs are allowed")
    if parsed.netloc not in ALLOWED_STAC_HOSTS:
        logger.warning("Rejected STAC URL from disallowed host: %s", parsed.netloc)
        raise HTTPException(status_code=400, detail="URL host not in allowlist")
    if not parsed.path.startswith(ALLOWED_STAC_PATH_PREFIX):
        logger.warning("Rejected STAC URL with invalid path: %s", parsed.path)
        raise HTTPException(status_code=400, detail="Invalid STAC path")


def validate_asset_url(url: str) -> None:
    """Validate that an asset URL is from an allowed host.
    
    Raises:
        HTTPException: If the URL is not allowed
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        logger.warning("Rejected asset URL with invalid scheme: %s", parsed.scheme)
        raise HTTPException(status_code=400, detail="Invalid asset URL scheme")
    if not any(parsed.netloc.endswith(host) for host in ALLOWED_ASSET_HOSTS):
        logger.warning("Rejected asset URL from disallowed host: %s", parsed.netloc)
        raise HTTPException(status_code=400, detail="Asset URL host not in allowlist")


@router.get("/signed-url", response_model=SignedUrlResponse)
async def get_signed_satellite_url(
    stac_item_url: str = Query(
        ...,
        description="The STAC item URL from Microsoft Planetary Computer",
        example="https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-2-l2a/items/S2A_MSIL2A_...",
    ),
) -> SignedUrlResponse:
    """
    Fetch and sign a STAC asset URL for frontend display.

    Takes a STAC item URL from Microsoft Planetary Computer and returns
    a signed URL for the visual (true color) thumbnail or rendered preview.

    Args:
        stac_item_url: The STAC item URL to sign

    Returns:
        A signed URL that can be used to fetch the image directly

    Raises:
        HTTPException: If the STAC item cannot be fetched or signed
    """
    # Security: Validate the STAC item URL before fetching
    validate_stac_url(stac_item_url)
    
    logger.info("Fetching STAC item: %s", stac_item_url)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch the STAC item to get asset links
            response = await client.get(stac_item_url)
            if response.status_code != 200:
                logger.error("STAC fetch failed with status %d", response.status_code)
                raise HTTPException(
                    status_code=502,
                    detail="Failed to fetch STAC item",
                )

            # Parse JSON with error handling
            try:
                item_data = response.json()
            except json.JSONDecodeError as exc:
                logger.error("Invalid JSON response from STAC server")
                raise HTTPException(
                    status_code=502,
                    detail="Invalid JSON response from STAC server",
                ) from exc
            
            assets = item_data.get("assets", {})

            # Try to find a visual/preview asset (in order of preference)
            asset_keys = ["rendered_preview", "visual", "thumbnail", "overview"]
            asset_url = None

            for key in asset_keys:
                if key in assets:
                    asset_url = assets[key].get("href")
                    if asset_url:
                        break

            if not asset_url:
                # Fall back to first available image asset
                for asset in assets.values():
                    if asset.get("type", "").startswith("image/"):
                        asset_url = asset.get("href")
                        break

            if not asset_url:
                logger.warning("No visual asset found in STAC item")
                raise HTTPException(
                    status_code=404,
                    detail="No visual asset found in STAC item",
                )

            # Security: Validate the asset URL before signing
            validate_asset_url(asset_url)
            
            logger.info("Found asset URL, requesting signature")

            # Sign the URL using Planetary Computer's signing service
            sign_response = await client.get(
                settings.MPC_SIGNING_URL,
                params={"href": asset_url},
            )

            if sign_response.status_code != 200:
                # If signing fails, return the original URL (some assets may be public)
                logger.warning("Signing failed for asset, returning unsigned URL")
                return SignedUrlResponse(url=asset_url)

            # Parse signing response with error handling
            try:
                signed_data = sign_response.json()
            except json.JSONDecodeError as exc:
                logger.error("Invalid JSON response from signing service")
                raise HTTPException(
                    status_code=502,
                    detail="Invalid response from signing service",
                ) from exc
            
            signed_url = signed_data.get("href", asset_url)
            logger.info("Successfully signed asset URL")

            return SignedUrlResponse(url=signed_url)

    except httpx.TimeoutException as exc:
        logger.error("Timeout while fetching STAC item")
        raise HTTPException(
            status_code=504,
            detail="Timeout while fetching STAC item",
        ) from exc
    except httpx.RequestError as e:
        logger.error("Error fetching STAC item: %s", e)
        raise HTTPException(
            status_code=502,
            detail="Error fetching STAC item",
        ) from e
