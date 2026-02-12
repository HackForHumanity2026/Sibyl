"""Chunking strategies for different corpus types.

Implements FRD 1 (RAG Pipeline) Section 2 - Chunking Strategies.

Provides three distinct chunking strategies:
- IFRS paragraph-level chunking (S1/S2 standards)
- SASB topic-level chunking (industry standards)
- Report hierarchical chunking (uploaded sustainability reports)
"""

import re
from dataclasses import dataclass
from typing import TypedDict


class ChunkingConfig:
    """Configuration constants for chunking strategies.

    These are tunable parameters that control chunk sizing.
    """

    # IFRS / SASB paragraph chunking
    PARAGRAPH_MAX_TOKENS: int = 1500

    # Report hierarchical chunking
    REPORT_CHUNK_TARGET_TOKENS: int = 600
    REPORT_CHUNK_MIN_TOKENS: int = 200
    REPORT_CHUNK_MAX_TOKENS: int = 800
    REPORT_CHUNK_OVERLAP_TOKENS: int = 100

    # Token estimation
    CHARS_PER_TOKEN: int = 4  # Approximate for English text


# Pillar mappings for IFRS standards
IFRS_PILLAR_SECTIONS = {
    "governance": ["governance", "oversight", "board", "management role"],
    "strategy": [
        "strategy",
        "decision-making",
        "business model",
        "financial effects",
        "resilience",
        "risks and opportunities",
        "transition plan",
    ],
    "risk_management": ["risk management", "risk identification", "risk assessment"],
    "metrics_targets": ["metrics", "targets", "ghg emissions", "performance"],
}


class IFRSChunkMetadata(TypedDict, total=False):
    """Metadata schema for IFRS chunks."""

    paragraph_id: str
    standard: str  # "S1" or "S2"
    pillar: str  # governance | strategy | risk_management | metrics_targets
    section: str
    sub_requirements: list[str]
    s1_counterpart: str | None


class SASBChunkMetadata(TypedDict, total=False):
    """Metadata schema for SASB chunks."""

    industry_sector: str
    disclosure_topic: str
    metric_codes: list[str]
    standard_code: str


class ReportChunkMetadata(TypedDict, total=False):
    """Metadata schema for report chunks."""

    page_start: int
    page_end: int
    section_path: list[str]
    has_table: bool
    chunk_index: int


@dataclass
class ChunkResult:
    """Result of chunking a document."""

    text: str  # The chunk text including context header
    metadata: dict  # Corpus-specific metadata


def _estimate_tokens(text: str) -> int:
    """Estimate token count using characters / 4 heuristic."""
    return len(text) // ChunkingConfig.CHARS_PER_TOKEN


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences at common boundaries."""
    # Split on sentence-ending punctuation followed by space or newline
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def _identify_pillar(section_text: str) -> str:
    """Identify the IFRS pillar from section text."""
    section_lower = section_text.lower()
    for pillar, keywords in IFRS_PILLAR_SECTIONS.items():
        if any(kw in section_lower for kw in keywords):
            return pillar
    return "governance"  # Default fallback


def _extract_paragraph_id(text: str) -> str | None:
    """Extract IFRS paragraph ID from text (e.g., S1.26, S2.14(a)(iv))."""
    # Match patterns like S1.26, S2.14, S1.27(a), S2.14(a)(iv)
    pattern = r"\b(S[12]\.\d+(?:\([a-z]+\))*(?:\([ivx]+\))*)"
    match = re.search(pattern, text)
    return match.group(1) if match else None


def _extract_sub_requirements(text: str, main_id: str) -> list[str]:
    """Extract sub-requirement IDs from paragraph text."""
    sub_reqs = []
    # Look for patterns like (a), (b), (i), (ii) within the text
    # that extend the main paragraph ID
    base_pattern = re.escape(main_id)
    sub_pattern = rf"{base_pattern}\([a-z]+\)(?:\([ivx]+\))?"
    matches = re.findall(sub_pattern, text)
    sub_reqs.extend(matches)
    return list(set(sub_reqs))


def _extract_metric_codes(text: str) -> list[str]:
    """Extract SASB metric codes from text (e.g., EM-EP-110a.1)."""
    # SASB codes follow pattern like XX-YY-NNNa.N
    pattern = r"\b([A-Z]{2}-[A-Z]{2}-\d{3}[a-z]?\.\d+)\b"
    matches = re.findall(pattern, text)
    return list(set(matches))


def _extract_standard_code(filename: str) -> str:
    """Extract SASB standard code from filename."""
    # Map common industry names to SASB codes
    code_map = {
        "oil_and_gas": "EM-EP",
        "oil_gas": "EM-EP",
        "banking": "FN-CB",
        "banking_and_finance": "FN-CB",
        "utilities": "IF-EU",
        "electric_utilities": "IF-EU",
        "transportation": "TR-RO",
        "materials": "EM-MM",
        "materials_and_mining": "EM-MM",
        "mining": "EM-MM",
        "technology": "TC-SI",
        "healthcare": "HC-DY",
        "real_estate": "IF-RE",
        "agriculture": "FB-AG",
        "food": "FB-PF",
    }

    # Clean filename and try to match
    clean_name = filename.lower().replace(".md", "").replace("-", "_").replace(" ", "_")
    for key, code in code_map.items():
        if key in clean_name:
            return code
    return "XX-XX"  # Unknown


def chunk_ifrs(content: str, standard: str) -> list[ChunkResult]:
    """Chunk IFRS standard text at paragraph boundaries.

    Implements FRD 1 Section 2.2 - IFRS Paragraph-Level Chunking.

    Args:
        content: Full markdown content of the IFRS standard
        standard: "S1" or "S2"

    Returns:
        List of ChunkResult with text and IFRS metadata
    """
    chunks: list[ChunkResult] = []

    # Track current section context
    current_sections: list[str] = []
    current_pillar = "governance"

    # Split content into lines for processing
    lines = content.split("\n")

    # Buffer for accumulating paragraph content
    para_buffer: list[str] = []
    current_para_id: str | None = None

    def flush_paragraph():
        """Flush the current paragraph buffer as a chunk."""
        nonlocal para_buffer, current_para_id
        if not para_buffer:
            return

        para_text = "\n".join(para_buffer).strip()
        if not para_text:
            para_buffer = []
            current_para_id = None
            return

        # Build context header
        section_path = " > ".join(current_sections) if current_sections else standard
        para_id = current_para_id or _extract_paragraph_id(para_text) or "unknown"
        context_header = f"[IFRS {standard} > {section_path} > {para_id}]"

        full_text = f"{context_header}\n\n{para_text}"

        # Check if paragraph is too long
        tokens = _estimate_tokens(full_text)
        if tokens > ChunkingConfig.PARAGRAPH_MAX_TOKENS:
            # Split at sentence boundaries
            sentences = _split_sentences(para_text)
            sub_chunks = _split_long_paragraph(sentences, context_header)
            for i, sub_text in enumerate(sub_chunks, 1):
                part_indicator = f" [Part {i}/{len(sub_chunks)}]" if len(sub_chunks) > 1 else ""
                metadata: IFRSChunkMetadata = {
                    "paragraph_id": f"{para_id}{part_indicator}",
                    "standard": standard,
                    "pillar": current_pillar,
                    "section": current_sections[-1] if current_sections else "",
                    "sub_requirements": _extract_sub_requirements(para_text, para_id),
                    "s1_counterpart": None,
                }
                chunks.append(ChunkResult(text=sub_text, metadata=dict(metadata)))
        else:
            metadata = {
                "paragraph_id": para_id,
                "standard": standard,
                "pillar": current_pillar,
                "section": current_sections[-1] if current_sections else "",
                "sub_requirements": _extract_sub_requirements(para_text, para_id),
                "s1_counterpart": None,
            }
            chunks.append(ChunkResult(text=full_text, metadata=metadata))

        para_buffer = []
        current_para_id = None

    def _split_long_paragraph(
        sentences: list[str], context_header: str
    ) -> list[str]:
        """Split a long paragraph into smaller chunks at sentence boundaries."""
        sub_chunks = []
        current_chunk: list[str] = []
        current_tokens = _estimate_tokens(context_header + "\n\n")

        for sentence in sentences:
            sentence_tokens = _estimate_tokens(sentence)
            if current_tokens + sentence_tokens > ChunkingConfig.PARAGRAPH_MAX_TOKENS and current_chunk:
                # Flush current chunk
                chunk_text = f"{context_header}\n\n" + " ".join(current_chunk)
                sub_chunks.append(chunk_text)
                current_chunk = []
                current_tokens = _estimate_tokens(context_header + "\n\n")

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        if current_chunk:
            chunk_text = f"{context_header}\n\n" + " ".join(current_chunk)
            sub_chunks.append(chunk_text)

        return sub_chunks

    for line in lines:
        stripped = line.strip()

        # Check for section headers
        if stripped.startswith("# "):
            flush_paragraph()
            current_sections = [stripped[2:].strip()]
            current_pillar = _identify_pillar(stripped)
        elif stripped.startswith("## "):
            flush_paragraph()
            section_name = stripped[3:].strip()
            current_sections = current_sections[:1] + [section_name]
            current_pillar = _identify_pillar(section_name)
        elif stripped.startswith("### "):
            flush_paragraph()
            section_name = stripped[4:].strip()
            current_sections = current_sections[:2] + [section_name]
            # Check for paragraph ID in heading (e.g., "### S2.14 Strategy and Decision-Making")
            para_id = _extract_paragraph_id(section_name)
            if para_id:
                current_para_id = para_id
        elif stripped.startswith("#### "):
            # Sub-heading, might contain paragraph reference
            section_name = stripped[5:].strip()
            para_id = _extract_paragraph_id(section_name)
            if para_id:
                flush_paragraph()
                current_para_id = para_id
            para_buffer.append(stripped)
        elif stripped:
            # Check if line starts with a new paragraph ID
            line_para_id = _extract_paragraph_id(stripped)
            if line_para_id and line_para_id != current_para_id:
                flush_paragraph()
                current_para_id = line_para_id
            para_buffer.append(stripped)
        elif para_buffer:
            # Empty line - check if we should flush
            # Keep empty lines within a paragraph for formatting
            para_buffer.append("")

    # Flush any remaining content
    flush_paragraph()

    return chunks


def chunk_sasb(content: str, filename: str) -> list[ChunkResult]:
    """Chunk SASB industry standard at topic boundaries.

    Implements FRD 1 Section 2.3 - SASB Topic-Level Chunking.

    Args:
        content: Full markdown content of the SASB standard
        filename: Original filename (used to extract industry/code)

    Returns:
        List of ChunkResult with text and SASB metadata
    """
    chunks: list[ChunkResult] = []

    # Extract industry info from filename
    industry_sector = (
        filename.replace(".md", "")
        .replace("_", " ")
        .replace("-", " ")
        .title()
    )
    standard_code = _extract_standard_code(filename)

    # Track current topic
    current_topic: str | None = None
    topic_buffer: list[str] = []

    def flush_topic():
        """Flush the current topic buffer as a chunk."""
        nonlocal topic_buffer, current_topic
        if not topic_buffer or not current_topic:
            topic_buffer = []
            return

        topic_text = "\n".join(topic_buffer).strip()
        if not topic_text:
            topic_buffer = []
            return

        # Build context header
        context_header = f"[SASB > {industry_sector} > {current_topic}]"
        full_text = f"{context_header}\n\n{topic_text}"

        # Extract metric codes from content
        metric_codes = _extract_metric_codes(topic_text)

        # Check if too long
        tokens = _estimate_tokens(full_text)
        if tokens > ChunkingConfig.PARAGRAPH_MAX_TOKENS:
            # Split at sub-topic or natural boundaries
            sub_chunks = _split_long_sasb_topic(topic_text, context_header)
            for sub_text in sub_chunks:
                metadata: SASBChunkMetadata = {
                    "industry_sector": industry_sector,
                    "disclosure_topic": current_topic,
                    "metric_codes": _extract_metric_codes(sub_text),
                    "standard_code": standard_code,
                }
                chunks.append(ChunkResult(text=sub_text, metadata=dict(metadata)))
        else:
            metadata = {
                "industry_sector": industry_sector,
                "disclosure_topic": current_topic,
                "metric_codes": metric_codes,
                "standard_code": standard_code,
            }
            chunks.append(ChunkResult(text=full_text, metadata=metadata))

        topic_buffer = []

    def _split_long_sasb_topic(topic_text: str, context_header: str) -> list[str]:
        """Split a long SASB topic into smaller chunks."""
        sub_chunks = []
        paragraphs = topic_text.split("\n\n")
        current_chunk: list[str] = []
        current_tokens = _estimate_tokens(context_header + "\n\n")

        for para in paragraphs:
            para_tokens = _estimate_tokens(para)
            if current_tokens + para_tokens > ChunkingConfig.PARAGRAPH_MAX_TOKENS and current_chunk:
                chunk_text = f"{context_header}\n\n" + "\n\n".join(current_chunk)
                sub_chunks.append(chunk_text)
                current_chunk = []
                current_tokens = _estimate_tokens(context_header + "\n\n")

            current_chunk.append(para)
            current_tokens += para_tokens

        if current_chunk:
            chunk_text = f"{context_header}\n\n" + "\n\n".join(current_chunk)
            sub_chunks.append(chunk_text)

        return sub_chunks

    lines = content.split("\n")

    for line in lines:
        stripped = line.strip()

        # Check for topic headers (H2 or H3)
        if stripped.startswith("## ") or stripped.startswith("### "):
            flush_topic()
            if stripped.startswith("## "):
                current_topic = stripped[3:].strip()
            else:
                current_topic = stripped[4:].strip()
        elif stripped or topic_buffer:
            # Add content to current topic
            if current_topic:
                topic_buffer.append(line)

    flush_topic()

    return chunks


def chunk_report(
    content: str, page_metadata: list[dict] | None = None
) -> list[ChunkResult]:
    """Chunk uploaded report content with hierarchical structure.

    Implements FRD 1 Section 2.4 - Report Hierarchical Chunking.

    Args:
        content: Markdown content from PyMuPDF4LLM parsing
        page_metadata: Optional list of page info dicts with 'page_number' and 'start_char' keys

    Returns:
        List of ChunkResult with text and report metadata
    """
    chunks: list[ChunkResult] = []

    # Track section hierarchy
    section_path: list[str] = []

    # Page tracking
    def get_page_for_position(char_pos: int) -> int:
        """Get page number for a character position."""
        if not page_metadata:
            return 1
        for i, page_info in enumerate(page_metadata):
            start = page_info.get("start_char", 0)
            next_start = (
                page_metadata[i + 1].get("start_char", float("inf"))
                if i + 1 < len(page_metadata)
                else float("inf")
            )
            if start <= char_pos < next_start:
                return page_info.get("page_number", i + 1)
        return 1

    # Parse content into sections
    sections: list[dict] = []
    current_section: dict = {"path": [], "content": [], "start_char": 0}
    char_pos = 0

    lines = content.split("\n")
    for line in lines:
        stripped = line.strip()
        line_len = len(line) + 1  # +1 for newline

        # Check for headers
        header_level = 0
        header_text = ""
        if stripped.startswith("# "):
            header_level = 1
            header_text = stripped[2:].strip()
        elif stripped.startswith("## "):
            header_level = 2
            header_text = stripped[3:].strip()
        elif stripped.startswith("### "):
            header_level = 3
            header_text = stripped[4:].strip()
        elif stripped.startswith("#### "):
            header_level = 4
            header_text = stripped[5:].strip()

        if header_level > 0:
            # Save current section
            if current_section["content"]:
                sections.append(current_section)

            # Update section path
            section_path = section_path[: header_level - 1] + [header_text]

            # Start new section
            current_section = {
                "path": section_path.copy(),
                "content": [],
                "start_char": char_pos,
            }
        else:
            current_section["content"].append(line)

        char_pos += line_len

    # Save final section
    if current_section["content"]:
        sections.append(current_section)

    # Chunk each section with overlap
    chunk_index = 0
    min_chars = ChunkingConfig.REPORT_CHUNK_MIN_TOKENS * ChunkingConfig.CHARS_PER_TOKEN
    max_chars = ChunkingConfig.REPORT_CHUNK_MAX_TOKENS * ChunkingConfig.CHARS_PER_TOKEN
    overlap_chars = ChunkingConfig.REPORT_CHUNK_OVERLAP_TOKENS * ChunkingConfig.CHARS_PER_TOKEN

    for section in sections:
        section_text = "\n".join(section["content"]).strip()
        if not section_text:
            continue

        section_path = section["path"]
        section_start_char = section["start_char"]

        # Build context header
        path_str = " > ".join(section_path) if section_path else "Document"
        context_header = f"[Report > {path_str}]"

        # Check for tables
        has_table = "|" in section_text and "---" in section_text

        # If section is small enough, keep as single chunk
        section_chars = len(section_text)
        if section_chars <= max_chars:
            full_text = f"{context_header}\n\n{section_text}"
            page_num = get_page_for_position(section_start_char)
            metadata: ReportChunkMetadata = {
                "page_start": page_num,
                "page_end": page_num,
                "section_path": section_path,
                "has_table": has_table,
                "chunk_index": chunk_index,
            }
            chunks.append(ChunkResult(text=full_text, metadata=dict(metadata)))
            chunk_index += 1
            continue

        # Split into paragraphs
        paragraphs = section_text.split("\n\n")
        current_chunk: list[str] = []
        current_chars = 0
        chunk_start_char = section_start_char

        for para in paragraphs:
            para_chars = len(para)

            # Check if adding this paragraph would exceed max
            if current_chars + para_chars > max_chars and current_chunk:
                # Flush current chunk
                chunk_text = "\n\n".join(current_chunk)
                full_text = f"{context_header}\n\n{chunk_text}"

                page_start = get_page_for_position(chunk_start_char)
                page_end = get_page_for_position(chunk_start_char + len(chunk_text))

                metadata = {
                    "page_start": page_start,
                    "page_end": page_end,
                    "section_path": section_path,
                    "has_table": "|" in chunk_text and "---" in chunk_text,
                    "chunk_index": chunk_index,
                }
                chunks.append(ChunkResult(text=full_text, metadata=metadata))
                chunk_index += 1

                # Apply overlap - keep last paragraph(s) up to overlap_chars
                overlap_content: list[str] = []
                overlap_total = 0
                for prev_para in reversed(current_chunk):
                    if overlap_total + len(prev_para) <= overlap_chars:
                        overlap_content.insert(0, prev_para)
                        overlap_total += len(prev_para)
                    else:
                        break

                current_chunk = overlap_content
                current_chars = overlap_total
                chunk_start_char += len(chunk_text) - overlap_total

            current_chunk.append(para)
            current_chars += para_chars

        # Flush remaining content
        if current_chunk and current_chars >= min_chars:
            chunk_text = "\n\n".join(current_chunk)
            full_text = f"{context_header}\n\n{chunk_text}"

            page_start = get_page_for_position(chunk_start_char)
            page_end = get_page_for_position(chunk_start_char + len(chunk_text))

            metadata = {
                "page_start": page_start,
                "page_end": page_end,
                "section_path": section_path,
                "has_table": "|" in chunk_text and "---" in chunk_text,
                "chunk_index": chunk_index,
            }
            chunks.append(ChunkResult(text=full_text, metadata=metadata))
            chunk_index += 1
        elif current_chunk and chunks:
            # Append to last chunk if too small
            last_chunk = chunks[-1]
            separator = "\n\n"
            last_chunk.text += separator + "\n\n".join(current_chunk)
            # Update page_end
            last_chunk.metadata["page_end"] = get_page_for_position(
                chunk_start_char + len("\n\n".join(current_chunk))
            )

    return chunks
