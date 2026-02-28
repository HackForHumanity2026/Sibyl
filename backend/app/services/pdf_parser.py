"""PDF parsing service using PyMuPDF4LLM.

Implements FRD 2 (PDF Upload & Ingestion).

Converts PDF documents to structured markdown with:
- Table preservation
- Heading extraction
- Page number references
- Content structure analysis
"""

import logging
import re
from typing import Any

import pymupdf
import pymupdf4llm
from pydantic import BaseModel

from app.core.sanitize import sanitize_string

logger = logging.getLogger(__name__)


class PDFParseError(Exception):
    """Raised when PDF parsing fails."""

    pass


class SectionInfo(BaseModel):
    """A section detected in the document."""

    title: str
    level: int  # Heading level (1 = H1, 2 = H2, etc.)
    page_start: int
    page_end: int | None = None
    children: list["SectionInfo"] = []


class ContentStructure(BaseModel):
    """Structural summary of the parsed document."""

    sections: list[SectionInfo]
    table_count: int
    page_count: int
    estimated_word_count: int


class PageBoundary(BaseModel):
    """Maps page numbers to character positions in the markdown output."""

    page_number: int
    char_start: int
    char_end: int


class ParseResult(BaseModel):
    """Result of PDF parsing."""

    markdown: str
    page_count: int
    content_structure: ContentStructure
    page_boundaries: list[PageBoundary]


class PDFParserService:
    """Service for parsing PDF files into structured markdown.

    Uses PyMuPDF4LLM to extract content while preserving:
    - Tables as markdown tables
    - Headings with proper hierarchy
    - Page number boundaries
    """

    async def parse_pdf(self, pdf_bytes: bytes) -> ParseResult:
        """Parse a PDF binary into structured markdown.

        Args:
            pdf_bytes: Raw PDF file content.

        Returns:
            ParseResult with markdown content, page count, and content structure.

        Raises:
            PDFParseError: If the PDF cannot be parsed.
        """
        try:
            # Open PDF from bytes using pymupdf
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")

            # Extract markdown with page chunks for page boundary tracking
            page_chunks = pymupdf4llm.to_markdown(
                doc,
                page_chunks=True,
                write_images=False,
                show_progress=False,
            )

            if not page_chunks:
                raise PDFParseError(
                    "The uploaded PDF could not be parsed. The file may be corrupt."
                )

            # Process page chunks and build full markdown with page markers
            markdown_parts: list[str] = []
            page_boundaries: list[PageBoundary] = []
            char_pos = 0

            for i, chunk in enumerate(page_chunks):
                page_num = i + 1
                page_text = self._extract_page_text(chunk)

                # Insert page marker
                page_marker = f"<!-- PAGE {page_num} -->\n\n"
                markdown_parts.append(page_marker)

                char_start = char_pos + len(page_marker)
                markdown_parts.append(page_text)

                if not page_text.endswith("\n"):
                    markdown_parts.append("\n")

                char_end = char_start + len(page_text)
                page_boundaries.append(
                    PageBoundary(
                        page_number=page_num,
                        char_start=char_start,
                        char_end=char_end,
                    )
                )

                char_pos = char_end + 1  # +1 for trailing newline

            full_markdown = "".join(markdown_parts)
            page_count = len(page_chunks)

            # Sanitize extracted text to remove PostgreSQL-incompatible characters
            # (null bytes, unpaired surrogates) that may come from corrupted PDFs
            full_markdown = sanitize_string(full_markdown)

            # Check for image-only / scanned PDFs
            text_content = re.sub(r"\s+", "", full_markdown)
            text_content = re.sub(r"<!--.*?-->", "", text_content)
            if len(text_content) < 100:
                raise PDFParseError(
                    "This PDF appears to contain only scanned images. "
                    "Text-based PDFs are required for analysis."
                )

            # Build content structure
            content_structure = self._build_content_structure(
                full_markdown, page_count, page_boundaries
            )

            logger.info(
                "Parsed PDF: %d pages, %d sections, %d tables, ~%d words",
                page_count,
                len(content_structure.sections),
                content_structure.table_count,
                content_structure.estimated_word_count,
            )

            return ParseResult(
                markdown=full_markdown,
                page_count=page_count,
                content_structure=content_structure,
                page_boundaries=page_boundaries,
            )

        except PDFParseError:
            raise
        except Exception as e:
            error_msg = str(e).lower()
            if "password" in error_msg or "encrypted" in error_msg:
                raise PDFParseError(
                    "This PDF is password-protected. "
                    "Please upload an unprotected version."
                ) from e
            if "corrupt" in error_msg or "invalid" in error_msg:
                raise PDFParseError(
                    "The uploaded PDF could not be parsed. The file may be corrupt."
                ) from e
            logger.exception("Unexpected error parsing PDF")
            raise PDFParseError(
                "An unexpected error occurred while parsing the PDF."
            ) from e

    def _extract_page_text(self, chunk: Any) -> str:
        """Extract text from a page chunk.

        PyMuPDF4LLM returns either a dict with 'text' key or a string directly.
        """
        if isinstance(chunk, dict):
            return chunk.get("text", "")
        return str(chunk)

    def _build_content_structure(
        self,
        markdown: str,
        page_count: int,
        page_boundaries: list[PageBoundary],
    ) -> ContentStructure:
        """Build hierarchical content structure from markdown.

        Extracts sections from headings, counts tables, estimates word count.
        """
        # Extract sections from headings
        sections = self._extract_sections(markdown, page_boundaries)

        # Count tables (markdown tables have |---| separators)
        table_count = len(re.findall(r"\|[\s\-:]+\|", markdown))

        # Estimate word count (strip markdown syntax, split on whitespace)
        text_only = re.sub(r"<!--.*?-->", "", markdown)  # Remove comments
        text_only = re.sub(r"\|", " ", text_only)  # Tables
        text_only = re.sub(r"[#*_`\[\]()]", "", text_only)  # Markdown syntax
        words = text_only.split()
        estimated_word_count = len(words)

        return ContentStructure(
            sections=sections,
            table_count=table_count,
            page_count=page_count,
            estimated_word_count=estimated_word_count,
        )

    def _extract_sections(
        self,
        markdown: str,
        page_boundaries: list[PageBoundary],
    ) -> list[SectionInfo]:
        """Extract hierarchical section structure from markdown headings."""
        # Find all headings with their positions
        heading_pattern = r"^(#{1,6})\s+(.+)$"
        headings: list[tuple[int, int, str, int]] = []  # (char_pos, level, title, line_num)

        for match in re.finditer(heading_pattern, markdown, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            char_pos = match.start()
            headings.append((char_pos, level, title, char_pos))

        if not headings:
            return []

        # Helper to find page number for a character position
        def get_page_for_pos(char_pos: int) -> int:
            for boundary in page_boundaries:
                if boundary.char_start <= char_pos <= boundary.char_end:
                    return boundary.page_number
            # Default to last page if position is beyond all boundaries
            return page_boundaries[-1].page_number if page_boundaries else 1

        # Build hierarchical structure
        root_sections: list[SectionInfo] = []
        section_stack: list[tuple[int, SectionInfo]] = []  # (level, section)

        for i, (char_pos, level, title, _) in enumerate(headings):
            page_start = get_page_for_pos(char_pos)

            # Determine page_end (start of next heading or end of document)
            if i + 1 < len(headings):
                next_char_pos = headings[i + 1][0]
                page_end = get_page_for_pos(next_char_pos - 1)
            else:
                page_end = page_boundaries[-1].page_number if page_boundaries else page_start

            section = SectionInfo(
                title=title,
                level=level,
                page_start=page_start,
                page_end=page_end,
                children=[],
            )

            # Find parent section (most recent section with lower level)
            while section_stack and section_stack[-1][0] >= level:
                section_stack.pop()

            if section_stack:
                # Add as child of parent
                parent = section_stack[-1][1]
                parent.children.append(section)
            else:
                # Top-level section
                root_sections.append(section)

            section_stack.append((level, section))

        return root_sections
