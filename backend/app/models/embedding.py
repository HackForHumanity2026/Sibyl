"""Embedding model - represents a text chunk with its vector embedding for RAG."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.report import Report


class Embedding(Base):
    """
    Represents a text chunk with its vector embedding for RAG retrieval.

    Source types:
    - report: Chunk from an uploaded sustainability report
    - ifrs_s1: Chunk from the IFRS S1 standard text
    - ifrs_s2: Chunk from the IFRS S2 standard text
    - sasb: Chunk from SASB industry standards
    """

    __tablename__ = "embeddings"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid7,
    )
    report_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=True,
    )
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    embedding: Mapped[list] = mapped_column(Vector(1536), nullable=False)
    ts_content: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    report: Mapped["Report | None"] = relationship("Report", back_populates="embeddings")

    __table_args__ = (
        Index("ix_embeddings_report_id", "report_id"),
        Index("ix_embeddings_source_type", "source_type"),
        Index(
            "ix_embeddings_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index(
            "ix_embeddings_ts_content_gin",
            "ts_content",
            postgresql_using="gin",
        ),
    )
