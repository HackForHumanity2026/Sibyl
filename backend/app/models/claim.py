"""Claim model - represents a verifiable sustainability claim."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, generate_uuid7

if TYPE_CHECKING:
    from app.models.finding import Finding
    from app.models.report import Report
    from app.models.verdict import Verdict


class Claim(Base):
    """
    Represents a verifiable sustainability claim extracted from a report.

    Claim types:
    - geographic: Facility locations, land use, deforestation, water usage
    - quantitative: Emission figures, percentage targets, financial impacts, Scope 1/2/3
    - legal_governance: Board oversight, committee responsibilities, compliance assertions
    - strategic: Transition plans, future targets, investment commitments
    - environmental: Biodiversity, waste management, resource efficiency, renewables

    Priority levels: high, medium, low
    """

    __tablename__ = "claims"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=generate_uuid7,
    )
    report_id: Mapped[UUID] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_page: Mapped[int] = mapped_column(Integer, nullable=False)
    source_location: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ifrs_paragraphs: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )
    agent_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    report: Mapped["Report"] = relationship("Report", back_populates="claims")
    findings: Mapped[list["Finding"]] = relationship(
        "Finding",
        back_populates="claim",
        cascade="all, delete-orphan",
    )
    verdict: Mapped["Verdict | None"] = relationship(
        "Verdict",
        back_populates="claim",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_claims_report_id", "report_id"),
        Index("ix_claims_claim_type", "claim_type"),
    )
