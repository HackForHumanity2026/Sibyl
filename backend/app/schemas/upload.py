"""Upload request/response schemas.

Implements FRD 2 (PDF Upload & Ingestion).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SectionInfo(BaseModel):
    """A section detected in the document."""

    title: str
    level: int
    page_start: int
    page_end: int | None = None
    children: list["SectionInfo"] = []

    model_config = ConfigDict(from_attributes=True)


class ContentStructure(BaseModel):
    """Structural summary of the parsed document."""

    sections: list[SectionInfo]
    table_count: int
    page_count: int
    estimated_word_count: int

    model_config = ConfigDict(from_attributes=True)


class UploadResponse(BaseModel):
    """Response after successful file upload."""

    report_id: str
    filename: str
    file_size_bytes: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportStatusResponse(BaseModel):
    """Response for report status polling."""

    report_id: str
    filename: str
    file_size_bytes: int
    status: str
    page_count: int | None = None
    content_structure: ContentStructure | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RetryResponse(BaseModel):
    """Response after retrying a failed report."""

    report_id: str
    status: str
    message: str

    model_config = ConfigDict(from_attributes=True)
