"""Chat endpoints for the contextual chatbot.

Implements FRD 14 (Chatbot) Section 13 - Backend Chat Endpoint.

Provides:
- POST /chat/{report_id}/message - Send a message and stream response via SSE
- GET /chat/{report_id}/history - Get conversation history
"""

import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.report import Report
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    Citation,
    ConversationHistoryResponse,
)
from app.services.chat_service import ChatService
from app.services.embedding_service import EmbeddingService
from app.services.openrouter_client import openrouter_client
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_report_or_404(report_id: str, db: AsyncSession) -> Report:
    """Get a report by ID or raise 404."""
    try:
        uuid = UUID(report_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid report ID format") from e

    stmt = select(Report).where(Report.id == uuid)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return report


def format_sse_event(event_type: str, data: dict, event_id: int) -> str:
    """Format an SSE event string.

    Args:
        event_type: The event type name
        data: The data payload (will be JSON serialized)
        event_id: Sequential event ID

    Returns:
        SSE-formatted string
    """
    data_str = json.dumps(data)
    lines = [
        f"event: {event_type}",
        f"data: {data_str}",
        f"id: {event_id}",
        "",
        "",  # Double newline terminates the event
    ]
    return "\n".join(lines)


@router.post("/{report_id}/message")
async def send_chat_message(
    report_id: str,
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Send a chat message and receive a streaming response.

    This endpoint streams the chatbot response via Server-Sent Events (SSE).
    The response includes:
    - chat_token events: Individual tokens as they're generated
    - chat_citations events: Citation data after response completion
    - chat_done events: Final event with complete message
    - chat_error events: Error information if something fails

    Args:
        report_id: UUID of the report to chat about
        request: Chat message request body

    Returns:
        StreamingResponse with SSE content
    """
    # Verify report exists
    await get_report_or_404(report_id, db)

    # Initialize services
    embedding_service = EmbeddingService()
    rag_service = RAGService(db, embedding_service)
    chat_service = ChatService(db, rag_service, openrouter_client)

    # Get or create conversation
    conversation = await chat_service.get_or_create_conversation(report_id)

    # Get conversation history
    history_messages = await chat_service.get_conversation_history(conversation.id)
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in history_messages
    ]

    # Persist user message
    await chat_service.persist_message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    )
    await db.commit()

    async def generate_sse():
        """Generate SSE events for the chat response."""
        event_id = 0
        full_content = ""
        citations_data = []

        try:
            async for event in chat_service.generate_response_stream(
                report_id=report_id,
                user_message=request.message,
                conversation_history=conversation_history,
            ):
                event_type = event["type"]
                data = event["data"]

                if event_type == "token":
                    full_content += data
                    yield format_sse_event("chat_token", {"token": data}, event_id)
                    event_id += 1

                elif event_type == "citations":
                    citations_data = data
                    yield format_sse_event("chat_citations", {"citations": data}, event_id)
                    event_id += 1

                elif event_type == "done":
                    # Persist assistant message
                    # Need to get a fresh session since we're in a generator
                    citations = [
                        Citation(**c) for c in citations_data
                    ] if citations_data else None

                    # Persist inside the generator using the same session
                    assistant_message = await chat_service.persist_message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=full_content,
                        citations=citations,
                    )
                    await db.commit()

                    yield format_sse_event(
                        "chat_done",
                        {
                            "message_id": str(assistant_message.id),
                            "full_content": full_content,
                        },
                        event_id,
                    )
                    event_id += 1

                elif event_type == "error":
                    yield format_sse_event("chat_error", {"error": data}, event_id)
                    event_id += 1

        except Exception as e:
            logger.error("SSE generation error: %s", e, exc_info=True)
            yield format_sse_event("chat_error", {"error": str(e)}, event_id)

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{report_id}/history", response_model=ConversationHistoryResponse)
async def get_chat_history(
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> ConversationHistoryResponse:
    """Get the conversation history for a report.

    Returns all messages in the conversation, ordered chronologically.

    Args:
        report_id: UUID of the report

    Returns:
        ConversationHistoryResponse with all messages
    """
    # Verify report exists
    await get_report_or_404(report_id, db)

    # Initialize chat service
    embedding_service = EmbeddingService()
    rag_service = RAGService(db, embedding_service)
    chat_service = ChatService(db, rag_service, openrouter_client)

    # Get or create conversation
    conversation = await chat_service.get_or_create_conversation(report_id)

    # Get messages
    messages = await chat_service.get_conversation_history(conversation.id)

    return ConversationHistoryResponse(
        conversation_id=str(conversation.id),
        report_id=report_id,
        messages=[
            ChatMessageResponse(
                id=str(msg.id),
                role=msg.role,  # type: ignore
                content=msg.content,
                citations=[
                    Citation(**c) for c in msg.citations
                ] if msg.citations else [],
                timestamp=msg.created_at,
            )
            for msg in messages
        ],
    )

