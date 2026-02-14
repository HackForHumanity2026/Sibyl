"""Claims Agent - extracts verifiable sustainability claims from reports.

Implements FRD 3.

Uses Map-Reduce architecture to handle large documents:
1. Split document into overlapping chunks (10 pages each, 2-page overlap)
2. Process chunks concurrently with Claude Sonnet
3. Merge results and deduplicate using embedding similarity + Claude Haiku confirmation
"""

import asyncio
import json
import logging
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import Claim as StateClaim
from app.agents.state import SibylState, StreamEvent
from app.core.database import generate_uuid7
from app.models.claim import Claim
from app.models.report import Report
from app.services.embedding_service import embedding_service
from app.services.openrouter_client import Models, openrouter_client

logger = logging.getLogger(__name__)


# ============================================================================
# Map-Reduce Configuration
# ============================================================================

# Chunking configuration
CHUNK_SIZE_PAGES = 10  # Pages per chunk
CHUNK_OVERLAP_PAGES = 2  # Overlap between adjacent chunks
MAX_CONCURRENT_CHUNKS = 3  # Parallel LLM calls (respects Sonnet rate limits)

# Deduplication configuration
SIMILARITY_THRESHOLD = 0.85  # Cosine similarity threshold for candidate duplicates


@dataclass
class DocumentChunk:
    """A chunk of the document for processing."""

    content: str
    start_page: int
    end_page: int
    chunk_index: int
    total_chunks: int
    total_pages: int


# ============================================================================
# Extraction Schemas
# ============================================================================


class ExtractedClaim(BaseModel):
    """A single claim extracted from the document by the LLM."""

    claim_text: str = Field(description="The verbatim or closely paraphrased claim text")
    claim_type: Literal[
        "geographic", "quantitative", "legal_governance", "strategic", "environmental"
    ] = Field(description="Category of the claim")
    source_page: int = Field(description="Page number where the claim appears")
    source_context: str = Field(
        description="Surrounding text (1-2 sentences) for location anchoring"
    )
    priority: Literal["high", "medium", "low"] = Field(
        description="Materiality and verifiability priority"
    )
    reasoning: str = Field(description="Why this is a verifiable claim")
    preliminary_ifrs: list[str] = Field(
        default_factory=list,
        description="List of likely IFRS paragraph IDs (e.g., S2.29(a)(iii))",
    )


class ClaimsExtractionResult(BaseModel):
    """Complete extraction result from the LLM."""

    claims: list[ExtractedClaim] = Field(default_factory=list)
    total_pages_analyzed: int = Field(default=0)
    extraction_summary: str = Field(
        default="", description="Brief summary of the document and claim landscape"
    )


# ============================================================================
# Document Chunking
# ============================================================================


def _split_document_into_chunks(document_content: str) -> list[DocumentChunk]:
    """Split document by PAGE markers into overlapping chunks.

    Uses <!-- PAGE N --> markers from pdf_parser.py to identify page boundaries.
    Creates chunks of CHUNK_SIZE_PAGES with CHUNK_OVERLAP_PAGES overlap.

    Args:
        document_content: Full document with PAGE markers

    Returns:
        List of DocumentChunk objects with page ranges and content
    """
    # Find all page markers and their positions
    page_pattern = re.compile(r"<!-- PAGE (\d+) -->")
    page_matches = list(page_pattern.finditer(document_content))

    if not page_matches:
        # No page markers found - treat entire document as one chunk
        logger.warning("No PAGE markers found in document, treating as single chunk")
        return [
            DocumentChunk(
                content=document_content,
                start_page=1,
                end_page=1,
                chunk_index=0,
                total_chunks=1,
                total_pages=1,
            )
        ]

    # Build page boundaries: list of (page_num, start_pos, end_pos)
    page_boundaries: list[tuple[int, int, int]] = []
    for i, match in enumerate(page_matches):
        page_num = int(match.group(1))
        start_pos = match.start()
        # End position is either the start of next page or end of document
        end_pos = page_matches[i + 1].start() if i + 1 < len(page_matches) else len(document_content)
        page_boundaries.append((page_num, start_pos, end_pos))

    total_pages = len(page_boundaries)
    logger.info("Document has %d pages, creating chunks of %d pages with %d overlap",
                total_pages, CHUNK_SIZE_PAGES, CHUNK_OVERLAP_PAGES)

    # Calculate number of chunks needed
    # With overlap, each chunk advances by (CHUNK_SIZE_PAGES - CHUNK_OVERLAP_PAGES)
    step = CHUNK_SIZE_PAGES - CHUNK_OVERLAP_PAGES
    if step <= 0:
        step = 1  # Safety: ensure we make progress

    chunks: list[DocumentChunk] = []
    chunk_index = 0
    start_idx = 0

    while start_idx < total_pages:
        # Determine end index for this chunk
        end_idx = min(start_idx + CHUNK_SIZE_PAGES, total_pages)

        # Extract content for these pages
        chunk_start_pos = page_boundaries[start_idx][1]
        chunk_end_pos = page_boundaries[end_idx - 1][2]
        chunk_content = document_content[chunk_start_pos:chunk_end_pos]

        # Get actual page numbers (1-indexed as they appear in markers)
        start_page = page_boundaries[start_idx][0]
        end_page = page_boundaries[end_idx - 1][0]

        chunks.append(
            DocumentChunk(
                content=chunk_content,
                start_page=start_page,
                end_page=end_page,
                chunk_index=chunk_index,
                total_chunks=0,  # Will update after we know total
                total_pages=total_pages,
            )
        )

        chunk_index += 1
        start_idx += step

        # Don't create tiny final chunks
        if start_idx < total_pages and (total_pages - start_idx) < CHUNK_OVERLAP_PAGES:
            # Extend the last chunk instead of creating a tiny one
            break

    # Update total_chunks in all chunks
    for chunk in chunks:
        chunk.total_chunks = len(chunks)

    logger.info("Created %d chunks from %d pages", len(chunks), total_pages)
    for i, chunk in enumerate(chunks):
        logger.debug("Chunk %d: pages %d-%d (%d chars)",
                     i, chunk.start_page, chunk.end_page, len(chunk.content))

    return chunks


# ============================================================================
# System Prompt (from FRD 3 Appendix A)
# ============================================================================

CLAIMS_EXTRACTION_SYSTEM_PROMPT = """You are a structured data extraction API. You output ONLY valid JSON. No prose, no markdown, no commentary.

You will receive a full sustainability report. You must extract EVERY verifiable claim from EVERY page — page by page, from the first page to the last page. Do NOT provide a sample. Do NOT stop early. Do NOT ask follow-up questions. Your output must be the complete, exhaustive extraction.

## What is a verifiable claim?

A statement asserting a fact, metric, commitment, or condition checkable against external evidence (satellite imagery, news, academic literature, regulatory filings) or internal consistency (math, benchmarks).

## Claim types (assign exactly ONE):

- geographic: Facility locations, land use, regional water usage, physical risk exposure at specific locations
- quantitative: Emission figures (Scope 1/2/3), percentage targets, financial impacts, year-over-year comparisons, intensity metrics, energy/waste numbers
- legal_governance: Board oversight, committee responsibilities, compliance assertions, policy commitments, remuneration-climate links
- strategic: Transition plans, net-zero commitments, future targets, investment commitments, timeline assertions, scenario analysis, SBTi alignment
- environmental: Biodiversity, waste management, resource efficiency, renewable energy, water stewardship, circular economy, certifications

## Priority (assign exactly ONE):

- high: Specific numerical claims central to the sustainability narrative; core IFRS S2 metrics; claims that would be material greenwashing if false
- medium: Qualitative claims with verifiable elements; governance processes; strategic commitments with timelines
- low: General assertions with limited verifiability

## IFRS mapping reference:

S1: Governance (S1.26-27), Strategy (S1.28-35), Risk Management (S1.38-42), Metrics & Targets (S1.43-53)
S2: Governance (S2.5-7), Strategy (S2.8-22), Risk Management (S2.24-26), Metrics (S2.27-31, S2.33-36)
GHG specifics: Scope 1 = S2.29(a)(i), Scope 2 = S2.29(a)(ii), Scope 3 = S2.29(a)(iii)

## Extraction procedure:

1. Read page 1 through the last page sequentially using <!-- PAGE N --> markers
2. On EACH page, identify every verifiable claim
3. For each claim: extract verbatim text (paraphrase only if >300 chars), categorize, assign priority, note the source page, provide 1-2 sentences of surrounding context, assign preliminary IFRS paragraph IDs
4. Split compound statements into separate claims
5. Skip: boilerplate, table of contents, methodology definitions, disclaimers, generic industry context
6. Target: 50-200 claims for a typical report. Claims MUST come from throughout the entire document, not just the first few pages.

## Output schema (raw JSON only, no wrapping):

{"claims":[{"claim_text":"...","claim_type":"quantitative","source_page":45,"source_context":"...","priority":"high","reasoning":"...","preliminary_ifrs":["S2.29(a)(i)"]}],"total_pages_analyzed":87,"extraction_summary":"..."}"""


CLAIMS_EXTRACTION_USER_PROMPT = """Process the following sustainability report page by page from start to finish. Extract every verifiable claim from every page. Output raw JSON only.

<report>
{document_content}
</report>"""


# Chunk-specific prompt includes page range context
CLAIMS_EXTRACTION_CHUNK_PROMPT = """Extract ALL verifiable claims from this document section.
This is pages {start_page}-{end_page} of {total_pages} total pages (chunk {chunk_index}/{total_chunks}).

Process each page in this section thoroughly. Extract EVERY claim - do not provide samples or summaries.

<report_section>
{chunk_content}
</report_section>"""


# Prefill forces the model to begin outputting JSON immediately,
# preventing any conversational preamble or markdown wrapping.
CLAIMS_EXTRACTION_PREFILL = '{  "claims": ['


# ============================================================================
# Deduplication Prompt (Claude Haiku)
# ============================================================================

DEDUP_SYSTEM_PROMPT = """You compare two sustainability claims to determine if they are semantic duplicates.

Two claims are DUPLICATES if they assert the same fact, even if worded differently.
Two claims are NOT duplicates if they contain different metrics, dates, or assertions.

Respond with ONLY a JSON object:
{"is_duplicate": true/false, "keep": 1 or 2, "reason": "brief explanation"}

If duplicates, "keep" indicates which claim has richer context or more detail."""


# ============================================================================
# Helper Functions
# ============================================================================


def _get_pillar_for_paragraph(paragraph_id: str) -> str:
    """Determine the IFRS pillar for a paragraph ID."""
    if not paragraph_id:
        return "unknown"

    pid = paragraph_id.upper()

    # S1 mappings
    if pid.startswith("S1.26") or pid.startswith("S1.27"):
        return "governance"
    if pid.startswith("S1.28") or pid.startswith("S1.29") or pid.startswith("S1.30"):
        return "strategy"
    if pid.startswith("S1.31") or pid.startswith("S1.32") or pid.startswith("S1.33"):
        return "strategy"
    if pid.startswith("S1.34") or pid.startswith("S1.35"):
        return "strategy"
    if pid.startswith("S1.36") or pid.startswith("S1.37"):
        return "strategy"
    if pid.startswith("S1.38") or pid.startswith("S1.39") or pid.startswith("S1.40"):
        return "risk_management"
    if pid.startswith("S1.41") or pid.startswith("S1.42"):
        return "risk_management"
    if pid.startswith("S1.43") or pid.startswith("S1.44") or pid.startswith("S1.45"):
        return "metrics_targets"
    if pid.startswith("S1.46") or pid.startswith("S1.47") or pid.startswith("S1.48"):
        return "metrics_targets"
    if pid.startswith("S1.49") or pid.startswith("S1.50") or pid.startswith("S1.51"):
        return "metrics_targets"
    if pid.startswith("S1.52") or pid.startswith("S1.53"):
        return "metrics_targets"

    # S2 mappings
    if pid.startswith("S2.5") or pid.startswith("S2.6") or pid.startswith("S2.7"):
        return "governance"
    if pid.startswith("S2.8") or pid.startswith("S2.9") or pid.startswith("S2.10"):
        return "strategy"
    if pid.startswith("S2.11") or pid.startswith("S2.12") or pid.startswith("S2.13"):
        return "strategy"
    if pid.startswith("S2.14") or pid.startswith("S2.15") or pid.startswith("S2.16"):
        return "strategy"
    if pid.startswith("S2.17") or pid.startswith("S2.18") or pid.startswith("S2.19"):
        return "strategy"
    if pid.startswith("S2.20") or pid.startswith("S2.21") or pid.startswith("S2.22"):
        return "strategy"
    if pid.startswith("S2.24") or pid.startswith("S2.25") or pid.startswith("S2.26"):
        return "risk_management"
    if pid.startswith("S2.27") or pid.startswith("S2.28") or pid.startswith("S2.29"):
        return "metrics_targets"
    if pid.startswith("S2.30") or pid.startswith("S2.31"):
        return "metrics_targets"
    if pid.startswith("S2.33") or pid.startswith("S2.34") or pid.startswith("S2.35"):
        return "metrics_targets"
    if pid.startswith("S2.36"):
        return "metrics_targets"

    return "unknown"


def _deduplicate_claims(claims: list[ExtractedClaim]) -> list[ExtractedClaim]:
    """Remove duplicate claims (same text and same page).

    This is a fast text-based deduplication used before LLM-assisted dedup.
    """
    seen = set()
    unique_claims = []

    for claim in claims:
        # Create a key based on normalized text and page
        key = (claim.claim_text.strip().lower(), claim.source_page)
        if key not in seen:
            seen.add(key)
            unique_claims.append(claim)

    return unique_claims


# ============================================================================
# Map-Reduce Functions
# ============================================================================


async def _extract_claims_from_chunk(chunk: DocumentChunk) -> list[ExtractedClaim]:
    """Extract claims from a single document chunk using Claude Sonnet.

    Args:
        chunk: DocumentChunk with content and page metadata

    Returns:
        List of ExtractedClaim objects from this chunk
    """
    # Build chunk-specific prompt
    user_prompt = CLAIMS_EXTRACTION_CHUNK_PROMPT.format(
        start_page=chunk.start_page,
        end_page=chunk.end_page,
        total_pages=chunk.total_pages,
        chunk_index=chunk.chunk_index + 1,  # 1-indexed for display
        total_chunks=chunk.total_chunks,
        chunk_content=chunk.content,
    )

    # Log chunk info (WARNING level to ensure visibility)
    prompt_chars = len(CLAIMS_EXTRACTION_SYSTEM_PROMPT) + len(user_prompt)
    logger.warning(
        "Processing chunk %d/%d (pages %d-%d): %d chars (~%d tokens)",
        chunk.chunk_index + 1,
        chunk.total_chunks,
        chunk.start_page,
        chunk.end_page,
        prompt_chars,
        prompt_chars // 4,
    )

    try:
        response = await openrouter_client.chat_completion(
            model=Models.CLAUDE_SONNET,
            messages=[
                {"role": "system", "content": CLAIMS_EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": CLAIMS_EXTRACTION_PREFILL},
            ],
            temperature=0.0,
            max_tokens=16000,
        )

        # Reconstruct full JSON by prepending the prefill
        full_response = CLAIMS_EXTRACTION_PREFILL + response

        logger.warning(
            "Chunk %d response: %d chars, first 200: %s",
            chunk.chunk_index + 1,
            len(full_response),
            repr(full_response[:200]),
        )

        # Parse the response
        try:
            result_data = json.loads(full_response)
            extraction_result = ClaimsExtractionResult(**result_data)
            logger.info(
                "Chunk %d extracted %d claims",
                chunk.chunk_index + 1,
                len(extraction_result.claims),
            )
            return extraction_result.claims
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(
                "Failed to parse chunk %d response: %s",
                chunk.chunk_index + 1,
                e,
            )
            # Attempt lenient parsing
            result = _parse_lenient_response(full_response)
            return result.claims

    except Exception as e:
        logger.error(
            "Error processing chunk %d (pages %d-%d): %s",
            chunk.chunk_index + 1,
            chunk.start_page,
            chunk.end_page,
            e,
        )
        return []


# ============================================================================
# LLM-Assisted Deduplication Functions
# ============================================================================


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def _find_candidate_duplicates(
    claims: list[ExtractedClaim],
    embeddings: list[list[float]],
) -> list[tuple[int, int, float]]:
    """Find claim pairs with high embedding similarity from overlap regions.

    Only compares claims from nearby pages (within CHUNK_OVERLAP_PAGES + 1)
    to reduce comparisons and focus on likely duplicates from chunk overlaps.

    Args:
        claims: List of extracted claims
        embeddings: Corresponding embedding vectors

    Returns:
        List of (index_i, index_j, similarity) tuples for candidate duplicates
    """
    candidates = []
    n = len(claims)

    for i in range(n):
        for j in range(i + 1, n):
            # Only compare if pages are within overlap range
            page_diff = abs(claims[i].source_page - claims[j].source_page)
            if page_diff > CHUNK_OVERLAP_PAGES + 1:
                continue

            sim = _cosine_similarity(embeddings[i], embeddings[j])
            if sim >= SIMILARITY_THRESHOLD:
                candidates.append((i, j, sim))

    logger.info(
        "Found %d candidate duplicate pairs from %d claims",
        len(candidates),
        n,
    )
    return candidates


async def _confirm_duplicates_with_llm(
    candidates: list[tuple[int, int, float]],
    claims: list[ExtractedClaim],
) -> list[tuple[int, int, int]]:
    """Use Claude Haiku to confirm which candidate pairs are true duplicates.

    Args:
        candidates: List of (i, j, similarity) candidate pairs
        claims: The full claims list

    Returns:
        List of (i, j, keep_index) for confirmed duplicates
    """
    if not candidates:
        return []

    confirmed: list[tuple[int, int, int]] = []

    for i, j, sim in candidates:
        try:
            response = await openrouter_client.chat_completion(
                model=Models.CLAUDE_HAIKU,
                messages=[
                    {"role": "system", "content": DEDUP_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"""Claim 1 (page {claims[i].source_page}):
{claims[i].claim_text}

Claim 2 (page {claims[j].source_page}):
{claims[j].claim_text}""",
                    },
                ],
                temperature=0.0,
                max_tokens=100,
            )

            try:
                result = json.loads(response)
                if result.get("is_duplicate"):
                    keep = result.get("keep", 1)
                    keep_index = i if keep == 1 else j
                    confirmed.append((i, j, keep_index))
                    logger.debug(
                        "Confirmed duplicate: claims %d and %d (keep %d): %s",
                        i,
                        j,
                        keep_index,
                        result.get("reason", ""),
                    )
            except json.JSONDecodeError:
                # If parsing fails, treat as not duplicate (conservative)
                logger.debug("Failed to parse Haiku response for pair %d-%d", i, j)

        except Exception as e:
            logger.warning("Error confirming duplicate pair %d-%d: %s", i, j, e)
            # Continue with other pairs

    logger.info(
        "Confirmed %d duplicates from %d candidates",
        len(confirmed),
        len(candidates),
    )
    return confirmed


def _build_unique_set(
    claims: list[ExtractedClaim],
    duplicates: list[tuple[int, int, int]],
) -> list[ExtractedClaim]:
    """Build unique claim set by removing confirmed duplicates.

    Args:
        claims: Full list of claims
        duplicates: List of (i, j, keep_index) for confirmed duplicates

    Returns:
        List of unique claims with duplicates removed
    """
    to_remove: set[int] = set()
    for i, j, keep_index in duplicates:
        # Remove the claim we're NOT keeping
        remove_index = j if keep_index == i else i
        to_remove.add(remove_index)

    unique = [c for idx, c in enumerate(claims) if idx not in to_remove]
    logger.info(
        "Built unique set: %d claims (removed %d duplicates)",
        len(unique),
        len(to_remove),
    )
    return unique


async def _deduplicate_claims_llm_assisted(
    claims: list[ExtractedClaim],
) -> list[ExtractedClaim]:
    """Deduplicate claims using embedding similarity + LLM confirmation.

    This is the main deduplication function that:
    1. First applies fast text-based deduplication
    2. Embeds all claim texts
    3. Finds candidate duplicates via cosine similarity
    4. Confirms duplicates with Claude Haiku
    5. Builds the final unique set

    Args:
        claims: List of claims to deduplicate

    Returns:
        List of unique claims
    """
    if len(claims) <= 1:
        return claims

    # Step 0: Fast text-based deduplication first
    claims = _deduplicate_claims(claims)
    if len(claims) <= 1:
        return claims

    logger.info("Starting LLM-assisted deduplication for %d claims", len(claims))

    # Step 1: Embed all claim texts
    claim_texts = [c.claim_text for c in claims]
    logger.info("Embedding %d claim texts...", len(claim_texts))
    embeddings = await embedding_service.embed_batch(claim_texts)

    # Step 2: Find candidate duplicate pairs
    candidates = _find_candidate_duplicates(claims, embeddings)

    if not candidates:
        logger.info("No candidate duplicates found, returning all claims")
        return claims

    # Step 3: Confirm duplicates with Claude Haiku
    confirmed = await _confirm_duplicates_with_llm(candidates, claims)

    # Step 4: Build unique set
    unique_claims = _build_unique_set(claims, confirmed)

    return unique_claims


async def _validate_ifrs_mappings_via_rag(
    claims: list[ExtractedClaim], db: AsyncSession
) -> list[ExtractedClaim]:
    """Validate and enhance IFRS mappings using RAG retrieval.

    Groups claims by type and performs batched RAG queries to validate
    the LLM's preliminary IFRS mappings.
    """
    from app.services.embedding_service import EmbeddingService
    from app.services.rag_service import RAGService

    embedding_service = EmbeddingService()
    try:
        rag_service = RAGService(db, embedding_service)

        # Group claims by type for efficient querying
        claims_by_type: dict[str, list[ExtractedClaim]] = {}
        for claim in claims:
            if claim.claim_type not in claims_by_type:
                claims_by_type[claim.claim_type] = []
            claims_by_type[claim.claim_type].append(claim)

        # Process each type group
        for claim_type, type_claims in claims_by_type.items():
            # Take a representative sample of claims for batch querying
            # Query with up to 5 claims per type to get relevant paragraphs
            sample_size = min(5, len(type_claims))
            sample_claims = type_claims[:sample_size]

            # Build a combined query from sample claims
            combined_query = f"{claim_type} claims: " + " | ".join(
                [c.claim_text[:100] for c in sample_claims]
            )

            try:
                # Search IFRS corpus
                results = await rag_service.search(
                    query=combined_query,
                    top_k=5,
                    mode="hybrid",
                    source_types=["ifrs_s1", "ifrs_s2"],
                )

                # Extract paragraph IDs from results
                rag_paragraph_ids = []
                for result in results:
                    if result.metadata and "paragraph_id" in result.metadata:
                        rag_paragraph_ids.append(result.metadata["paragraph_id"])

                # Update claims in this group with validated/enhanced mappings
                for claim in type_claims:
                    # Keep existing mappings but add any new ones from RAG
                    existing_ids = set(claim.preliminary_ifrs)
                    for pid in rag_paragraph_ids:
                        if pid and pid not in existing_ids:
                            claim.preliminary_ifrs.append(pid)

            except Exception as e:
                logger.warning(
                    "RAG validation failed for %s claims: %s", claim_type, e
                )
                # Continue with LLM-provided mappings

        return claims

    finally:
        await embedding_service.close()


# ============================================================================
# Main Extraction Functions
# ============================================================================


async def extract_claims(state: SibylState) -> dict:
    """
    Extract verifiable sustainability claims from the parsed document.

    Uses Map-Reduce architecture to handle large documents:
    1. Split document into overlapping chunks (10 pages each, 2-page overlap)
    2. Process chunks concurrently with Claude Sonnet (max 3 parallel)
    3. Merge all extracted claims
    4. Deduplicate using embedding similarity + Claude Haiku confirmation

    Categorizes each claim by type (geographic, quantitative, legal_governance,
    strategic, environmental) and tags with source page, preliminary IFRS mapping,
    and priority.

    Args:
        state: Current pipeline state with document content

    Returns:
        Partial state update with extracted claims and events
    """
    events: list[StreamEvent] = []

    # Emit start event
    events.append(
        StreamEvent(
            event_type="agent_started",
            agent_name="claims",
            data={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )

    # Emit thinking event
    events.append(
        StreamEvent(
            event_type="agent_thinking",
            agent_name="claims",
            data={"message": "Analyzing document structure..."},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )

    try:
        # ================================================================
        # Phase 1: Split document into chunks
        # ================================================================
        chunks = _split_document_into_chunks(state.document_content)

        logger.warning(
            "Map-Reduce extraction: %d chunks, %d pages, concurrency=%d",
            len(chunks),
            chunks[0].total_pages if chunks else 0,
            MAX_CONCURRENT_CHUNKS,
        )

        # Emit thinking event
        events.append(
            StreamEvent(
                event_type="agent_thinking",
                agent_name="claims",
                data={
                    "message": f"Processing {len(chunks)} document chunks concurrently..."
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

        # ================================================================
        # Phase 2: Process chunks concurrently (Map phase)
        # ================================================================
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_CHUNKS)

        async def _process_chunk_with_semaphore(chunk: DocumentChunk) -> list[ExtractedClaim]:
            async with semaphore:
                return await _extract_claims_from_chunk(chunk)

        tasks = [_process_chunk_with_semaphore(chunk) for chunk in chunks]
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

        # ================================================================
        # Phase 3: Merge all claims
        # ================================================================
        all_claims: list[ExtractedClaim] = []
        chunk_errors = 0

        for i, result in enumerate(chunk_results):
            if isinstance(result, Exception):
                logger.error("Chunk %d failed: %s", i + 1, result)
                chunk_errors += 1
            elif isinstance(result, list):
                all_claims.extend(result)
                logger.info("Chunk %d contributed %d claims", i + 1, len(result))

        logger.warning(
            "Map phase complete: %d total claims from %d chunks (%d errors)",
            len(all_claims),
            len(chunks),
            chunk_errors,
        )

        # Emit thinking event
        events.append(
            StreamEvent(
                event_type="agent_thinking",
                agent_name="claims",
                data={
                    "message": f"Extracted {len(all_claims)} raw claims. Deduplicating with LLM assistance..."
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

        # ================================================================
        # Phase 4: Deduplicate claims (Reduce phase)
        # ================================================================
        unique_claims = await _deduplicate_claims_llm_assisted(all_claims)

        logger.warning(
            "Reduce phase complete: %d unique claims (removed %d duplicates)",
            len(unique_claims),
            len(all_claims) - len(unique_claims),
        )

        # Emit thinking event
        events.append(
            StreamEvent(
                event_type="agent_thinking",
                agent_name="claims",
                data={
                    "message": f"Identified {len(unique_claims)} unique claims."
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

        # ================================================================
        # Phase 5: Convert to state format
        # ================================================================
        state_claims: list[StateClaim] = []
        for claim in unique_claims:
            # Build IFRS paragraphs with pillar info
            ifrs_paragraphs = []
            for pid in claim.preliminary_ifrs:
                ifrs_paragraphs.append(pid)

            state_claims.append(
                StateClaim(
                    claim_id=str(generate_uuid7()),
                    text=claim.claim_text,
                    page_number=claim.source_page,
                    claim_type=claim.claim_type,
                    ifrs_paragraphs=ifrs_paragraphs,
                    priority=claim.priority,
                    source_location={"source_context": claim.source_context},
                    agent_reasoning=claim.reasoning,
                )
            )

        # Count by type and priority
        by_type: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        for claim in state_claims:
            by_type[claim.claim_type] = by_type.get(claim.claim_type, 0) + 1
            by_priority[claim.priority] = by_priority.get(claim.priority, 0) + 1

        # Log page coverage
        pages_covered = sorted(set(c.page_number for c in state_claims))
        logger.warning(
            "Claims extracted from %d unique pages: %s",
            len(pages_covered),
            pages_covered[:20] if len(pages_covered) > 20 else pages_covered,
        )

        # Emit completion event
        events.append(
            StreamEvent(
                event_type="agent_completed",
                agent_name="claims",
                data={
                    "claim_count": len(state_claims),
                    "by_type": by_type,
                    "by_priority": by_priority,
                    "chunks_processed": len(chunks),
                    "pages_covered": len(pages_covered),
                },
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

        return {"claims": state_claims, "events": events}

    except Exception as e:
        logger.exception("Error during claims extraction")
        events.append(
            StreamEvent(
                event_type="error",
                agent_name="claims",
                data={"message": str(e)},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )
        return {"claims": [], "events": events}


def _parse_lenient_response(response: str) -> ClaimsExtractionResult:
    """Attempt to parse a malformed LLM response leniently."""
    # Try to find JSON in the response
    import re

    # Look for JSON object
    json_match = re.search(r"\{[\s\S]*\}", response)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return ClaimsExtractionResult(**data)
        except Exception:
            pass

    # Return empty result if parsing fails
    logger.warning("Could not parse LLM response leniently")
    return ClaimsExtractionResult(
        claims=[],
        total_pages_analyzed=0,
        extraction_summary="Failed to extract claims due to parsing error",
    )


async def run_claims_extraction(
    report_id: str, db: AsyncSession
) -> list[Claim]:
    """Run the Claims Agent standalone (without the full LangGraph pipeline).

    Used by the background task worker until FRD 5 delivers the full pipeline.

    Args:
        report_id: UUID of the report to process
        db: Database session

    Returns:
        List of persisted Claim models
    """
    # Load the report
    stmt = select(Report).where(Report.id == UUID(report_id))
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if report is None:
        raise ValueError(f"Report not found: {report_id}")

    if report.parsed_content is None:
        raise ValueError(f"Report has no parsed content: {report_id}")

    # Build minimal state
    state = SibylState(
        report_id=report_id,
        document_content=report.parsed_content,
    )

    # Run extraction
    result_dict = await extract_claims(state)
    state_claims: list[StateClaim] = result_dict.get("claims", [])

    # Validate IFRS mappings via RAG
    extracted_claims = []
    for sc in state_claims:
        extracted_claims.append(
            ExtractedClaim(
                claim_text=sc.text,
                claim_type=sc.claim_type,  # type: ignore
                source_page=sc.page_number,
                source_context=sc.source_location.get("source_context", "") if sc.source_location else "",
                priority=sc.priority,  # type: ignore
                reasoning=sc.agent_reasoning or "",
                preliminary_ifrs=sc.ifrs_paragraphs,
            )
        )

    # Run RAG validation
    validated_claims = await _validate_ifrs_mappings_via_rag(extracted_claims, db)

    # Persist claims to database
    db_claims: list[Claim] = []
    for extracted in validated_claims:
        # Build IFRS paragraphs with full metadata
        ifrs_paragraphs = []
        for pid in extracted.preliminary_ifrs:
            pillar = _get_pillar_for_paragraph(pid)
            ifrs_paragraphs.append(
                {
                    "paragraph_id": pid,
                    "pillar": pillar,
                    "relevance": "Preliminary mapping based on claim content",
                }
            )

        claim = Claim(
            id=generate_uuid7(),
            report_id=UUID(report_id),
            claim_text=extracted.claim_text,
            claim_type=extracted.claim_type,
            source_page=extracted.source_page,
            source_location={"source_context": extracted.source_context},
            ifrs_paragraphs=ifrs_paragraphs,
            priority=extracted.priority,
            agent_reasoning=extracted.reasoning,
        )
        db.add(claim)
        db_claims.append(claim)

    await db.commit()

    logger.info(
        "Persisted %d claims for report %s", len(db_claims), report_id
    )

    return db_claims
