"""RAG retrieval tool for LangGraph agents.

Implements FRD 1 (RAG Pipeline) Section 6 - RAG Lookup Tool.

Provides retrieval from the pgvector knowledge base for:
- Legal Agent (FRD 6)
- Claims Agent (FRD 3)
- Chatbot (FRD 14)

Corpus:
- IFRS S1/S2 standard text
- SASB industry standards
- Uploaded report content
"""

import logging
from typing import Annotated

from langchain_core.tools import tool

from app.core.database import async_session_maker
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RAGResult, RAGService

logger = logging.getLogger(__name__)


def _format_result(result: RAGResult, index: int) -> str:
    """Format a single RAG result for LLM consumption."""
    # Build metadata line based on source type
    metadata = result.metadata
    source_type = result.source_type

    if source_type in ("ifrs_s1", "ifrs_s2"):
        # IFRS chunk - show paragraph, pillar, section
        para_id = metadata.get("paragraph_id", "unknown")
        pillar = metadata.get("pillar", "").replace("_", " ").title()
        section = metadata.get("section", "")
        s1_counterpart = metadata.get("s1_counterpart")

        meta_parts = [f"Paragraph: {para_id}"]
        if pillar:
            meta_parts.append(f"Pillar: {pillar}")
        if section:
            meta_parts.append(f"Section: {section}")
        if s1_counterpart:
            meta_parts.append(f"S1 Counterpart: {s1_counterpart}")
        meta_line = " | ".join(meta_parts)

    elif source_type == "sasb":
        # SASB chunk - show industry, topic
        industry = metadata.get("industry_sector", "")
        topic = metadata.get("disclosure_topic", "")
        codes = metadata.get("metric_codes", [])

        meta_parts = []
        if industry:
            meta_parts.append(f"Industry: {industry}")
        if topic:
            meta_parts.append(f"Topic: {topic}")
        if codes:
            meta_parts.append(f"Metrics: {', '.join(codes[:3])}")
        meta_line = " | ".join(meta_parts) if meta_parts else "SASB Standard"

    elif source_type == "report":
        # Report chunk - show pages, section path
        page_start = metadata.get("page_start", 0)
        page_end = metadata.get("page_end", 0)
        section_path = metadata.get("section_path", [])
        has_table = metadata.get("has_table", False)

        meta_parts = []
        if page_start == page_end:
            meta_parts.append(f"Page: {page_start}")
        else:
            meta_parts.append(f"Pages: {page_start}-{page_end}")
        if section_path:
            meta_parts.append(f"Section: {' > '.join(section_path)}")
        if has_table:
            meta_parts.append("Contains table")
        meta_line = " | ".join(meta_parts) if meta_parts else "Report Content"

    else:
        meta_line = f"Source: {source_type}"

    # Format the full result
    return f"""--- Result {index} (source: {source_type}, score: {result.score:.2f}) ---
[{meta_line}]

{result.chunk_text}
"""


def _format_results(results: list[RAGResult]) -> str:
    """Format RAG results as structured text for LLM consumption."""
    if not results:
        return "--- No results found ---"

    formatted = []
    for i, result in enumerate(results, 1):
        formatted.append(_format_result(result, i))

    formatted.append("--- No more results ---")
    return "\n".join(formatted)


@tool
async def rag_lookup(
    query: str,
    source_types: Annotated[
        list[str] | None,
        "Optional filter for corpus type(s). Valid values: 'ifrs_s1', 'ifrs_s2', 'sasb', 'report'. If omitted, searches all.",
    ] = None,
    top_k: Annotated[
        int,
        "Number of results to return (default: 5).",
    ] = 5,
    paragraph_id: Annotated[
        str | None,
        "If provided, retrieves the exact IFRS paragraph by ID (e.g., 'S2.14(a)(iv)'). When set, query and source_types are ignored.",
    ] = None,
) -> str:
    """Search the RAG knowledge base for relevant IFRS standards, SASB guidance, or report content.

    Use this tool to retrieve authoritative information from:
    - IFRS S1/S2 sustainability disclosure standards
    - SASB industry-specific standards
    - Content from the uploaded sustainability report

    Args:
        query: Natural language search query describing what information you need
            (e.g., "transition plan requirements", "Scope 3 emissions disclosure").
        source_types: Optional filter for corpus type(s). Valid values:
            "ifrs_s1", "ifrs_s2", "sasb", "report". If omitted, searches all.
        top_k: Number of results to return (default: 5).
        paragraph_id: If provided, retrieves the exact IFRS paragraph by ID
            (e.g., "S2.14(a)(iv)"). When set, query and source_types are ignored.

    Returns:
        Formatted text with retrieved passages and their source metadata.
    """
    logger.info(
        "RAG lookup: query=%s, source_types=%s, top_k=%d, paragraph_id=%s",
        query[:50] if query else None,
        source_types,
        top_k,
        paragraph_id,
    )

    # Create a fresh database session for the tool
    async with async_session_maker() as db:
        embedding_service = EmbeddingService()
        try:
            rag_service = RAGService(db, embedding_service)

            if paragraph_id:
                # Exact paragraph lookup
                result = await rag_service.get_paragraph(paragraph_id)
                if result:
                    return _format_results([result])
                else:
                    return f"--- Paragraph '{paragraph_id}' not found ---"

            # Regular search
            results = await rag_service.search(
                query=query,
                top_k=top_k,
                mode="hybrid",
                source_types=source_types,
            )

            return _format_results(results)

        finally:
            await embedding_service.close()


@tool
async def rag_lookup_report(
    query: str,
    report_id: Annotated[
        str,
        "UUID of the report to search within.",
    ],
    top_k: Annotated[
        int,
        "Number of results to return (default: 5).",
    ] = 5,
) -> str:
    """Search within a specific uploaded report's content.

    Use this tool to find specific information within the sustainability report
    being analyzed. This searches only the report content, not IFRS/SASB standards.

    Args:
        query: Natural language search query describing what information you need.
        report_id: UUID of the report to search within.
        top_k: Number of results to return (default: 5).

    Returns:
        Formatted text with retrieved passages and their source metadata.
    """
    logger.info(
        "RAG lookup report: query=%s, report_id=%s, top_k=%d",
        query[:50],
        report_id,
        top_k,
    )

    async with async_session_maker() as db:
        embedding_service = EmbeddingService()
        try:
            rag_service = RAGService(db, embedding_service)

            results = await rag_service.search(
                query=query,
                top_k=top_k,
                mode="hybrid",
                source_types=["report"],
                report_id=report_id,
            )

            return _format_results(results)

        finally:
            await embedding_service.close()
