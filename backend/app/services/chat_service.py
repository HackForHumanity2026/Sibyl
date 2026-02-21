"""Chat service for RAG-powered conversational Q&A.

Implements FRD 14 (Chatbot) Sections 1-5.

Provides multi-source RAG retrieval, context assembly with citations,
LLM generation via OpenRouter streaming, and conversation persistence.
"""

import asyncio
import logging
import re
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatMessage, Conversation
from app.models.claim import Claim
from app.models.finding import Finding
from app.models.report import Report
from app.models.verdict import Verdict
from app.schemas.chat import (
    Citation,
    CitationNavigationTarget,
    CitationSourceType,
)
from app.services.openrouter_client import Models, OpenRouterClient
from app.services.rag_service import RAGResult, RAGService

logger = logging.getLogger(__name__)


# Chatbot system prompt as per FRD 14 Appendix A
CHATBOT_SYSTEM_PROMPT = """You are the Sibyl Chatbot, an AI assistant that helps users understand sustainability report analysis results. Your role is to answer questions about the analyzed report, agent findings, IFRS compliance, and disclosure gaps.

## Your Capabilities

1. **Answer questions about the analysis:** Explain what agents found, what claims were verified, and what compliance gaps exist.

2. **Reference specific sources:** Use inline citations [1], [2], etc. to reference the context sources provided. Always cite your sources when making factual claims.

3. **Understand the analysis structure:** You can reference:
   - Specific agents (Claims Agent, Geography Agent, Legal Agent, etc.)
   - Specific claims (by claim ID or description)
   - IFRS paragraphs (e.g., S2.14(a)(iv))
   - Agent findings and evidence
   - Judge verdicts (Verified, Unverified, Contradicted, Insufficient Evidence)
   - Disclosure gaps

4. **Provide contextual answers:** Ground your answers in the actual analysis results, not generic information. If information is not available in the context, say so clearly.

## Response Guidelines

- Be concise but comprehensive
- Use inline citations [1], [2], etc. for all factual claims
- Explain technical terms (IFRS paragraphs, agent names) when helpful
- If asked about something not in the context, explain that the information is not available
- For multi-part questions, address each part systematically
- Maintain a helpful, professional tone

## Citation Format

When referencing sources, use inline citations:
- "The report discloses Scope 3 emissions [1]."
- "The Legal Agent found that this claim does not meet S2.14(a)(iv) requirements [2]."
- "The Judge Agent verified this claim [3]."

The context sources are numbered [1], [2], [3], etc. Use these numbers to cite specific sources."""


class ChatServiceError(Exception):
    """Raised when chat service operations fail."""


class ChatService:
    """Service for chatbot Q&A with RAG retrieval and citation generation."""

    # Maximum number of results per source type
    DEFAULT_TOP_K_PER_SOURCE = 5

    # Maximum conversation history messages to include
    MAX_HISTORY_MESSAGES = 10

    def __init__(
        self,
        db: AsyncSession,
        rag_service: RAGService,
        openrouter_client: OpenRouterClient,
    ):
        """Initialize the chat service.

        Args:
            db: Async SQLAlchemy session
            rag_service: RAG service for retrieval
            openrouter_client: OpenRouter client for LLM calls
        """
        self.db = db
        self.rag_service = rag_service
        self.openrouter_client = openrouter_client

    # -------------------------------------------------------------------------
    # Conversation Management
    # -------------------------------------------------------------------------

    async def get_or_create_conversation(self, report_id: str) -> Conversation:
        """Get or create a conversation for the given report.

        Args:
            report_id: The report's UUID

        Returns:
            Conversation model instance
        """
        stmt = (
            select(Conversation)
            .where(Conversation.report_id == UUID(report_id))
            .options(selectinload(Conversation.messages))
        )
        result = await self.db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            conversation = Conversation(report_id=UUID(report_id))
            self.db.add(conversation)
            await self.db.flush()
            logger.info("Created new conversation for report %s", report_id)

        return conversation

    async def get_conversation_history(
        self,
        conversation_id: UUID,
    ) -> list[ChatMessage]:
        """Get all messages in a conversation.

        Args:
            conversation_id: The conversation's UUID

        Returns:
            List of ChatMessage models ordered by created_at
        """
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def persist_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        citations: list[Citation] | None = None,
    ) -> ChatMessage:
        """Persist a chat message to the database.

        Args:
            conversation_id: The conversation's UUID
            role: "user" or "assistant"
            content: Message text
            citations: List of citations (for assistant messages)

        Returns:
            Created ChatMessage model
        """
        message = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=[c.model_dump() for c in citations] if citations else None,
        )
        self.db.add(message)
        await self.db.flush()
        return message

    # -------------------------------------------------------------------------
    # RAG Retrieval
    # -------------------------------------------------------------------------

    async def retrieve_multi_source(
        self,
        query: str,
        report_id: str,
        top_k_per_source: int = DEFAULT_TOP_K_PER_SOURCE,
    ) -> dict[str, list[RAGResult]]:
        """Retrieve from all source types in parallel.

        Args:
            query: User's question
            report_id: Report to search within
            top_k_per_source: Max results per source type

        Returns:
            Dict mapping source_type to list of RAGResult objects.
        """
        # Parallel retrieval from RAG and database
        results = await asyncio.gather(
            # Report content
            self.rag_service.search(
                query=query,
                top_k=top_k_per_source,
                source_types=["report"],
                report_id=report_id,
            ),
            # IFRS standards
            self.rag_service.search(
                query=query,
                top_k=top_k_per_source,
                source_types=["ifrs_s1", "ifrs_s2"],
            ),
            # SASB standards
            self.rag_service.search(
                query=query,
                top_k=top_k_per_source,
                source_types=["sasb"],
            ),
            # Agent findings (database query)
            self._retrieve_findings(query, report_id, top_k_per_source),
            # Judge verdicts (database query)
            self._retrieve_verdicts(query, report_id, top_k_per_source),
            # Disclosure gaps (database query)
            self._retrieve_gaps(query, report_id, top_k_per_source),
            # Claims (database query)
            self._retrieve_claims(query, report_id, top_k_per_source),
            return_exceptions=True,
        )

        # Handle any exceptions
        processed_results: dict[str, list[RAGResult]] = {
            "report": [],
            "ifrs": [],
            "sasb": [],
            "finding": [],
            "verdict": [],
            "gap": [],
            "claim": [],
        }

        source_keys = ["report", "ifrs", "sasb", "finding", "verdict", "gap", "claim"]
        for i, key in enumerate(source_keys):
            if isinstance(results[i], Exception):
                logger.warning("Error retrieving %s: %s", key, results[i])
            else:
                processed_results[key] = results[i]

        return processed_results

    async def _retrieve_findings(
        self,
        query: str,
        report_id: str,
        top_k: int,
    ) -> list[RAGResult]:
        """Retrieve agent findings relevant to the query."""
        # Simple keyword matching on summary and details
        keywords = query.lower().split()
        keyword_filters = [
            or_(
                Finding.summary.ilike(f"%{kw}%"),
                Finding.agent_name.ilike(f"%{kw}%"),
            )
            for kw in keywords[:5]  # Limit keywords
        ]

        stmt = (
            select(Finding)
            .where(Finding.report_id == UUID(report_id))
            .where(or_(*keyword_filters) if keyword_filters else True)
            .limit(top_k)
        )

        result = await self.db.execute(stmt)
        findings = result.scalars().all()

        return [
            RAGResult(
                chunk_id=str(finding.id),
                chunk_text=f"[{finding.agent_name.title()} Agent] {finding.summary}",
                metadata={
                    "agent_name": finding.agent_name,
                    "claim_id": str(finding.claim_id) if finding.claim_id else None,
                    "evidence_type": finding.evidence_type,
                    "supports_claim": finding.supports_claim,
                    "confidence": finding.confidence,
                },
                source_type="finding",
                report_id=report_id,
                score=0.8,  # Placeholder score for keyword matches
                search_method="keyword",
            )
            for finding in findings
        ]

    async def _retrieve_verdicts(
        self,
        query: str,
        report_id: str,
        top_k: int,
    ) -> list[RAGResult]:
        """Retrieve Judge verdicts relevant to the query."""
        keywords = query.lower().split()
        keyword_filters = [
            Verdict.reasoning.ilike(f"%{kw}%")
            for kw in keywords[:5]
        ]

        stmt = (
            select(Verdict)
            .where(Verdict.report_id == UUID(report_id))
            .where(or_(*keyword_filters) if keyword_filters else True)
            .limit(top_k)
        )

        result = await self.db.execute(stmt)
        verdicts = result.scalars().all()

        return [
            RAGResult(
                chunk_id=str(verdict.id),
                chunk_text=f"[Judge Verdict: {verdict.verdict.title()}] {verdict.reasoning}",
                metadata={
                    "verdict": verdict.verdict,
                    "claim_id": str(verdict.claim_id),
                    "iteration_count": verdict.iteration_count,
                },
                source_type="verdict",
                report_id=report_id,
                score=0.8,
                search_method="keyword",
            )
            for verdict in verdicts
        ]

    async def _retrieve_gaps(
        self,
        query: str,
        report_id: str,
        top_k: int,
    ) -> list[RAGResult]:
        """Retrieve disclosure gaps (findings with evidence_type='disclosure_gap')."""
        keywords = query.lower().split()
        keyword_filters = [
            Finding.summary.ilike(f"%{kw}%")
            for kw in keywords[:5]
        ]

        stmt = (
            select(Finding)
            .where(Finding.report_id == UUID(report_id))
            .where(Finding.evidence_type == "disclosure_gap")
            .where(or_(*keyword_filters) if keyword_filters else True)
            .limit(top_k)
        )

        result = await self.db.execute(stmt)
        gaps = result.scalars().all()

        return [
            RAGResult(
                chunk_id=str(gap.id),
                chunk_text=f"[Disclosure Gap] {gap.summary}",
                metadata={
                    "agent_name": gap.agent_name,
                    "details": gap.details,
                },
                source_type="gap",
                report_id=report_id,
                score=0.8,
                search_method="keyword",
            )
            for gap in gaps
        ]

    async def _retrieve_claims(
        self,
        query: str,
        report_id: str,
        top_k: int,
    ) -> list[RAGResult]:
        """Retrieve claims relevant to the query."""
        keywords = query.lower().split()
        keyword_filters = [
            Claim.claim_text.ilike(f"%{kw}%")
            for kw in keywords[:5]
        ]

        stmt = (
            select(Claim)
            .where(Claim.report_id == UUID(report_id))
            .where(or_(*keyword_filters) if keyword_filters else True)
            .limit(top_k)
        )

        result = await self.db.execute(stmt)
        claims = result.scalars().all()

        return [
            RAGResult(
                chunk_id=str(claim.id),
                chunk_text=f"[Claim | Page {claim.source_page}] {claim.claim_text}",
                metadata={
                    "claim_type": claim.claim_type,
                    "source_page": claim.source_page,
                    "priority": claim.priority,
                    "ifrs_paragraphs": claim.ifrs_paragraphs,
                },
                source_type="claim",
                report_id=report_id,
                score=0.8,
                search_method="keyword",
            )
            for claim in claims
        ]

    # -------------------------------------------------------------------------
    # Context Assembly
    # -------------------------------------------------------------------------

    def assemble_context(
        self,
        retrieval_results: dict[str, list[RAGResult]],
    ) -> tuple[str, dict[int, dict[str, Any]]]:
        """Assemble retrieved chunks into LLM context with citation markers.

        Args:
            retrieval_results: Dict from retrieve_multi_source

        Returns:
            Tuple of (context_text, citation_map)
            - context_text: Formatted context string with [1], [2] markers
            - citation_map: Dict mapping citation number to source metadata
        """
        context_parts: list[str] = []
        citation_map: dict[int, dict[str, Any]] = {}
        citation_num = 1

        # Order: Report, Claims, IFRS, Findings, Verdicts, Gaps, SASB
        source_order = [
            ("report", "Report Content"),
            ("claim", "Claims"),
            ("ifrs", "IFRS Standards"),
            ("finding", "Agent Findings"),
            ("verdict", "Judge Verdicts"),
            ("gap", "Disclosure Gaps"),
            ("sasb", "SASB Standards"),
        ]

        for source_key, section_title in source_order:
            results = retrieval_results.get(source_key, [])
            if not results:
                continue

            section_lines = [f"\n### {section_title}"]
            for result in results:
                # Format the citation entry
                section_lines.append(f"[{citation_num}] {result.chunk_text}")

                # Build citation metadata
                nav_target = self._get_navigation_target(result.source_type)
                display_text = self._get_display_text(result)

                citation_map[citation_num] = {
                    "source_type": result.source_type,
                    "source_id": result.chunk_id,
                    "navigation_target": nav_target,
                    "display_text": display_text,
                    "metadata": result.metadata,
                }

                citation_num += 1

            context_parts.append("\n".join(section_lines))

        context_text = "## Context Sources\n" + "\n".join(context_parts)
        return context_text, citation_map

    def _get_navigation_target(self, source_type: str) -> str:
        """Map source type to navigation target."""
        mapping = {
            "report": "pdf_viewer",
            "claim": "pdf_viewer",
            "finding": "finding_panel",
            "ifrs": "ifrs_viewer",
            "ifrs_s1": "ifrs_viewer",
            "ifrs_s2": "ifrs_viewer",
            "sasb": "ifrs_viewer",
            "verdict": "source_of_truth",
            "gap": "disclosure_gaps",
        }
        return mapping.get(source_type, "source_of_truth")

    def _get_display_text(self, result: RAGResult) -> str:
        """Generate display text for a citation."""
        if result.source_type == "claim":
            page = result.metadata.get("source_page", "?")
            return f"Claim (Page {page})"
        elif result.source_type == "finding":
            agent = result.metadata.get("agent_name", "Agent")
            return f"{agent.title()} Agent Finding"
        elif result.source_type == "verdict":
            verdict = result.metadata.get("verdict", "Verdict")
            return f"Judge Verdict: {verdict.title()}"
        elif result.source_type == "gap":
            return "Disclosure Gap"
        elif result.source_type in ("ifrs", "ifrs_s1", "ifrs_s2"):
            paragraph = result.metadata.get("paragraph_id", "IFRS")
            return f"IFRS {paragraph}"
        elif result.source_type == "sasb":
            topic = result.metadata.get("topic", "SASB Standard")
            return f"SASB: {topic}"
        elif result.source_type == "report":
            return "Report Content"
        return "Source"

    # -------------------------------------------------------------------------
    # LLM Generation
    # -------------------------------------------------------------------------

    def build_messages(
        self,
        context_text: str,
        conversation_history: list[dict[str, str]],
        user_message: str,
    ) -> list[dict[str, str]]:
        """Build the message list for LLM generation.

        Args:
            context_text: Assembled context with citations
            conversation_history: Previous user/assistant messages
            user_message: Current user question

        Returns:
            List of message dicts for OpenRouter API
        """
        messages: list[dict[str, str]] = []

        # System prompt with context
        system_content = f"{CHATBOT_SYSTEM_PROMPT}\n\n{context_text}"
        messages.append({"role": "system", "content": system_content})

        # Add recent conversation history (up to MAX_HISTORY_MESSAGES)
        recent_history = conversation_history[-self.MAX_HISTORY_MESSAGES :]
        for msg in recent_history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    async def generate_response_stream(
        self,
        report_id: str,
        user_message: str,
        conversation_history: list[dict[str, str]],
        top_k_per_source: int = DEFAULT_TOP_K_PER_SOURCE,
    ) -> AsyncIterator[dict[str, Any]]:
        """Generate chatbot response with streaming.

        Args:
            report_id: The report being discussed
            user_message: User's question
            conversation_history: Previous messages
            top_k_per_source: Max RAG results per source type

        Yields:
            Dicts with 'type' and 'data' for SSE streaming:
            - {"type": "token", "data": "word"}
            - {"type": "citations", "data": [Citation, ...]}
            - {"type": "done", "data": {"message_id": "...", "full_content": "..."}}
            - {"type": "error", "data": "error message"}
        """
        try:
            # 1. RAG retrieval
            retrieval_results = await self.retrieve_multi_source(
                query=user_message,
                report_id=report_id,
                top_k_per_source=top_k_per_source,
            )

            # 2. Context assembly
            context_text, citation_map = self.assemble_context(retrieval_results)

            # 3. Build messages
            messages = self.build_messages(
                context_text=context_text,
                conversation_history=conversation_history,
                user_message=user_message,
            )

            # 4. Stream LLM response
            full_content = ""
            async for token in self.openrouter_client.stream_chat_completion(
                model=Models.GEMINI_FLASH,
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
            ):
                full_content += token
                yield {"type": "token", "data": token}

            # 5. Extract citations from response
            citations = self._extract_citations(full_content, citation_map)
            if citations:
                yield {"type": "citations", "data": [c.model_dump() for c in citations]}

            # 6. Done event (message will be persisted by the route handler)
            yield {
                "type": "done",
                "data": {
                    "full_content": full_content,
                    "citations": [c.model_dump() for c in citations],
                },
            }

        except Exception as e:
            logger.error("Chat generation error: %s", e, exc_info=True)
            yield {"type": "error", "data": str(e)}

    def _extract_citations(
        self,
        content: str,
        citation_map: dict[int, dict[str, Any]],
    ) -> list[Citation]:
        """Extract citation markers from LLM response and map to sources.

        Args:
            content: LLM response text
            citation_map: Map from citation number to source metadata

        Returns:
            List of Citation objects for citations actually used in the response
        """
        # Find all [N] citation markers in the response
        pattern = r"\[(\d+)\]"
        matches = re.findall(pattern, content)
        used_numbers = {int(n) for n in matches}

        citations = []
        for num in sorted(used_numbers):
            if num in citation_map:
                source = citation_map[num]
                citations.append(
                    Citation(
                        citation_number=num,
                        source_type=CitationSourceType(
                            self._normalize_source_type(source["source_type"])
                        ),
                        source_id=source["source_id"],
                        navigation_target=CitationNavigationTarget(
                            source["navigation_target"]
                        ),
                        display_text=source["display_text"],
                    )
                )

        return citations

    def _normalize_source_type(self, source_type: str) -> str:
        """Normalize source type to CitationSourceType enum value."""
        if source_type in ("ifrs", "ifrs_s1", "ifrs_s2"):
            return "ifrs_paragraph"
        return source_type
