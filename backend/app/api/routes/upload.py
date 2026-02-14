"""Upload endpoints for PDF ingestion.

Implements FRD 2 (PDF Upload & Ingestion).
"""

import logging
from uuid import UUID

import redis.asyncio as redis
from fastapi import APIRouter, HTTPException, UploadFile, status
from sqlalchemy import select

from app.core.config import settings
from app.core.database import DbSession
from app.core.dependencies import RAGServiceDep, RedisDep
from app.models.report import Report
from app.schemas.upload import (
    ReportStatusResponse,
    RetryResponse,
    UploadResponse,
)
from app.services.task_worker import TASK_QUEUE_KEY

logger = logging.getLogger(__name__)

router = APIRouter()

# Maximum upload size in bytes
MAX_UPLOAD_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF file",
    description="Upload a sustainability report PDF for parsing and analysis.",
)
async def upload_pdf(
    file: UploadFile,
    db: DbSession,
    redis_client: RedisDep,
) -> UploadResponse:
    """Upload a PDF file for processing.

    Validates the file type and size, creates a Report record, stores the
    PDF binary, and enqueues a background parsing task.
    """
    # Validate content type
    content_type = file.content_type or ""
    filename = file.filename or "unknown.pdf"

    # Accept application/pdf or application/octet-stream with .pdf extension
    is_valid_type = content_type == "application/pdf" or (
        content_type == "application/octet-stream"
        and filename.lower().endswith(".pdf")
    )

    if not is_valid_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files are accepted.",
        )

    # Read file content
    content = await file.read()

    # Validate file is not empty
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    # Validate file size
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds the maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    # Create Report record
    report = Report(
        filename=filename,
        file_size_bytes=len(content),
        status="uploaded",
        pdf_binary=content,
    )
    db.add(report)
    await db.flush()  # Get the ID assigned

    # Enqueue parsing task
    await redis_client.lpush(TASK_QUEUE_KEY, str(report.id))
    logger.info("Enqueued parse task for report %s", report.id)

    await db.commit()

    return UploadResponse(
        report_id=str(report.id),
        filename=report.filename,
        file_size_bytes=report.file_size_bytes,
        status=report.status,
        created_at=report.created_at,
    )


@router.get(
    "/{report_id}/status",
    response_model=ReportStatusResponse,
    summary="Get report processing status",
    description="Poll the current status of an uploaded report.",
)
async def get_report_status(
    report_id: str,
    db: DbSession,
) -> ReportStatusResponse:
    """Get the current processing status of a report.

    Returns the report status, and if parsing is complete, includes
    the content structure preview.
    """
    try:
        uuid = UUID(report_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )

    stmt = select(Report).where(Report.id == uuid)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )

    return ReportStatusResponse(
        report_id=str(report.id),
        filename=report.filename,
        file_size_bytes=report.file_size_bytes,
        status=report.status,
        page_count=report.page_count,
        content_structure=report.content_structure,
        error_message=report.error_message,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.post(
    "/{report_id}/retry",
    response_model=RetryResponse,
    summary="Retry a failed report",
    description="Re-queue a report that failed parsing for another attempt.",
)
async def retry_report(
    report_id: str,
    db: DbSession,
    redis_client: RedisDep,
    rag_service: RAGServiceDep,
) -> RetryResponse:
    """Retry processing a failed report.

    Resets the report status to 'uploaded', clears error fields,
    deletes existing embeddings, and re-enqueues for processing.
    """
    try:
        uuid = UUID(report_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )

    stmt = select(Report).where(Report.id == uuid)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found.",
        )

    if report.status != "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report is not in an error state.",
        )

    # Delete existing embeddings for this report
    await rag_service.delete_report_embeddings(report_id)

    # Reset report status and clear fields
    report.status = "uploaded"
    report.error_message = None
    report.parsed_content = None
    report.content_structure = None
    report.page_count = None

    # Re-enqueue parsing task
    await redis_client.lpush(TASK_QUEUE_KEY, report_id)
    logger.info("Re-enqueued parse task for report %s", report_id)

    await db.commit()

    return RetryResponse(
        report_id=report_id,
        status="uploaded",
        message="Report has been re-queued for processing.",
    )
