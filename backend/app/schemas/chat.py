"""Chat request/response schemas.

Implements FRD 14 (Chatbot) Section 5 - Inline Citation System.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class CitationSourceType(str, Enum):
    """Types of sources that can be cited in chat responses."""

    CLAIM = "claim"
    FINDING = "finding"
    IFRS_PARAGRAPH = "ifrs_paragraph"
    VERDICT = "verdict"
    GAP = "gap"
    REPORT = "report"
    SASB = "sasb"


class CitationNavigationTarget(str, Enum):
    """Navigation targets for citation clicks in the UI."""

    PDF_VIEWER = "pdf_viewer"
    FINDING_PANEL = "finding_panel"
    IFRS_VIEWER = "ifrs_viewer"
    SOURCE_OF_TRUTH = "source_of_truth"
    DISCLOSURE_GAPS = "disclosure_gaps"


class Citation(BaseModel):
    """A citation linking to a source entity."""

    citation_number: int = Field(
        ...,
        ge=1,
        description="Sequential citation number (1, 2, 3...)",
    )
    source_type: CitationSourceType = Field(
        ...,
        description="Type of source being cited",
    )
    source_id: str = Field(
        ...,
        description="ID of the source (UUID for claims/findings/verdicts, paragraph_id for IFRS)",
    )
    navigation_target: CitationNavigationTarget = Field(
        ...,
        description="UI destination when citation is clicked",
    )
    display_text: str = Field(
        ...,
        description="Human-readable label for the citation",
    )


class ChatMessageRequest(BaseModel):
    """Request body for sending a chat message."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User's chat message",
    )


class ChatMessageResponse(BaseModel):
    """A single chat message with metadata and citations."""

    id: str = Field(..., description="Message UUID")
    role: Literal["user", "assistant"] = Field(
        ...,
        description="Who sent the message",
    )
    content: str = Field(..., description="Message text content")
    citations: list[Citation] = Field(
        default_factory=list,
        description="List of citations for assistant messages",
    )
    timestamp: datetime = Field(..., description="When the message was sent")


class ConversationHistoryResponse(BaseModel):
    """Response containing full conversation history for a report."""

    conversation_id: str = Field(..., description="Conversation UUID")
    report_id: str = Field(..., description="Associated report UUID")
    messages: list[ChatMessageResponse] = Field(
        default_factory=list,
        description="All messages in chronological order",
    )


# SSE Event Schemas for streaming


class ChatTokenEvent(BaseModel):
    """SSE event containing a text token from the streaming response."""

    event_type: Literal["chat_token"] = "chat_token"
    token: str = Field(..., description="Individual text token")


class ChatCitationsEvent(BaseModel):
    """SSE event containing parsed citations after response completion."""

    event_type: Literal["chat_citations"] = "chat_citations"
    citations: list[Citation] = Field(
        default_factory=list,
        description="All citations found in the response",
    )


class ChatDoneEvent(BaseModel):
    """SSE event indicating response completion."""

    event_type: Literal["chat_done"] = "chat_done"
    message_id: str = Field(..., description="ID of the saved message")
    full_content: str = Field(..., description="Complete response text")


class ChatErrorEvent(BaseModel):
    """SSE event indicating an error occurred."""

    event_type: Literal["chat_error"] = "chat_error"
    error: str = Field(..., description="Error message")

