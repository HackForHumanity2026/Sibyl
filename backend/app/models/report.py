"""Report model - represents an uploaded sustainability report."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, Index, LargeBinary, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, generate_uuid7

if TYPE_CHECKING:
    from app.models.chat import Conversation
    from app.models.claim import Claim
    from app.models.embedding import Embedding
    from app.models.finding import Finding
    from app.models.verdict import Verdict


class Report(Base):
    """
    Represents an uploaded sustainability report.

    Status values:
    - uploaded: PDF received, not yet parsed
    - parsing: PyMuPDF4LLM extraction in progress
    - embedding: Content parsed, embedding chunks via RAG service
    - parsed: Content extracted and embedded, ready for analysis
    - analyzing: Agent pipeline running
    - completed: Full pipeline complete, Source of Truth available
    - error: Processing failed (see error_message)
    """

    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=generate_uuid7,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="uploaded",
    )
    parsed_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_binary: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    content_structure: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    claims: Mapped[list["Claim"]] = relationship(
        "Claim",
        back_populates="report",
        cascade="all, delete-orphan",
    )
    embeddings: Mapped[list["Embedding"]] = relationship(
        "Embedding",
        back_populates="report",
        cascade="all, delete-orphan",
    )
    findings: Mapped[list["Finding"]] = relationship(
        "Finding",
        back_populates="report",
        cascade="all, delete-orphan",
    )
    verdicts: Mapped[list["Verdict"]] = relationship(
        "Verdict",
        back_populates="report",
        cascade="all, delete-orphan",
    )
    conversation: Mapped["Conversation | None"] = relationship(
        "Conversation",
        back_populates="report",
        cascade="all, delete-orphan",
        uselist=False,
    )

    __table_args__ = (
        Index("ix_reports_status", "status"),
    )
