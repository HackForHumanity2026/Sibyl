"""Verdict model - represents the Judge Agent's final verdict on a claim."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.claim import Claim


class Verdict(Base):
    """
    Represents the Judge Agent's final verdict on a claim.

    Verdict values:
    - verified: Multiple independent sources corroborate; no contradictions
    - unverified: No external evidence found to support or contradict
    - contradicted: Evidence from one or more sources directly contradicts
    - insufficient_evidence: Some evidence exists but not enough for confident verdict
    """

    __tablename__ = "verdicts"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid7,
    )
    claim_id: Mapped[UUID] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    verdict: Mapped[str] = mapped_column(String(30), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    ifrs_mapping: Mapped[list] = mapped_column(JSONB, nullable=False)
    evidence_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    iteration_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    claim: Mapped["Claim"] = relationship("Claim", back_populates="verdict")
