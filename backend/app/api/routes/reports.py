"""Reports endpoints for serving report resources.

Implements FRD 4 (PDF Viewer with Claim Highlights) - PDF serving endpoint.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select

from app.core.database import DbSession
from app.models.report import Report

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/{report_id}/pdf",
    response_class=Response,
    summary="Get report PDF binary",
    description="Serve the original PDF binary for rendering in the PDF viewer.",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF binary file",
        },
        404: {
            "description": "Report not found or PDF binary not available",
        },
    },
)
async def get_report_pdf(
    report_id: str,
    db: DbSession,
) -> Response:
    """Serve the PDF binary for a report.

    Returns the original PDF file stored during upload, suitable for
    rendering in the embedded PDF viewer component.
    """
    # Parse and validate UUID
    try:
        uuid = UUID(report_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        ) from exc

    # Query the report
    stmt = select(Report).where(Report.id == uuid)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )

    # Check if PDF binary exists
    if report.pdf_binary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF binary not available for this report.",
        )

    # Return the PDF binary with appropriate headers
    return Response(
        content=report.pdf_binary,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{report.filename}"',
            "Cache-Control": "private, max-age=3600",
        },
    )
