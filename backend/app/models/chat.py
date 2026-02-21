"""Chat models for conversation persistence.

Implements FRD 14 (Chatbot) Section 14 - Chat Data Model.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, generate_uuid7

if TYPE_CHECKING:
    from app.models.report import Report


class Conversation(Base):
    """
    Represents a chat conversation for a specific report.

    Each report has exactly one conversation that persists across sessions.
    """

    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=generate_uuid7,
    )
    report_id: Mapped[UUID] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One conversation per report
    )
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
    report: Mapped["Report"] = relationship(back_populates="conversation")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base):
    """
    Represents a single message in a chat conversation.

    Stores both user messages and assistant responses with citations.
    Citations are stored as JSONB for flexible querying and to avoid
    a separate table join for the common case of fetching conversation history.
    """

    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=generate_uuid7,
    )
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
    )
    """
    List of citation objects for assistant messages:
    [
        {
            "citation_number": 1,
            "source_type": "claim" | "finding" | "ifrs_paragraph" | "verdict" | "gap",
            "source_id": "uuid or paragraph_id",
            "navigation_target": "pdf_viewer" | "finding_panel" | "ifrs_viewer" | "source_of_truth" | "disclosure_gaps",
            "display_text": "Human-readable citation label"
        }
    ]
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    # Indexes
    __table_args__ = (
        Index("ix_chat_messages_conversation_id", "conversation_id"),
        Index("ix_chat_messages_created_at", "created_at"),
    )
