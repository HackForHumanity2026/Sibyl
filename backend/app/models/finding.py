"""Finding model - represents evidence gathered by a specialist agent."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, generate_uuid7

if TYPE_CHECKING:
    from app.models.claim import Claim
    from app.models.report import Report


class Finding(Base):
    """
    Represents evidence gathered by a specialist agent during claim investigation.

    Agent names: geography, legal, news_media, academic, data_metrics

    Evidence types:
    - satellite_imagery
    - legal_analysis
    - news_article
    - academic_paper
    - quantitative_check
    - benchmark_comparison

    Confidence levels: high, medium, low
    """

    __tablename__ = "findings"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=generate_uuid7,
    )
    report_id: Mapped[UUID] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    claim_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=True,  # May be null for report-level findings
    )
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    supports_claim: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    iteration: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    report: Mapped["Report"] = relationship("Report", back_populates="findings")
    claim: Mapped["Claim"] = relationship("Claim", back_populates="findings")

    __table_args__ = (
        Index("ix_findings_report_id", "report_id"),
        Index("ix_findings_claim_id", "claim_id"),
        Index("ix_findings_agent_name", "agent_name"),
        Index("ix_findings_claim_id_agent_name", "claim_id", "agent_name"),
    )
