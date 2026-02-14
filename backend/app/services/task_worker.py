"""Background task worker for PDF parsing and claims extraction.

Implements FRD 2 (PDF Upload & Ingestion) Section 5 and FRD 3 (Claims Agent) Section 6.

A lightweight Redis-based task queue that processes PDF parsing
and claims extraction jobs asynchronously. Uses BRPOP for blocking dequeue.
"""

import asyncio
import logging
from typing import TYPE_CHECKING
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.models.report import Report
from app.services.pdf_parser import PDFParseError, PDFParserService

if TYPE_CHECKING:
    from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

# Redis queue keys
PARSE_PDF_QUEUE = "sibyl:tasks:parse_pdf"
EXTRACT_CLAIMS_QUEUE = "sibyl:tasks:extract_claims"

# Legacy alias for backwards compatibility
TASK_QUEUE_KEY = PARSE_PDF_QUEUE


class TaskWorker:
    """Background worker that processes PDF parsing and claims extraction tasks from Redis.

    Polls the Redis queues using BRPOP and processes tasks sequentially.
    Designed to run as an asyncio.Task within the FastAPI lifespan.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        """Initialize the task worker.

        Args:
            redis_client: Async Redis client for queue operations
            session_factory: SQLAlchemy session factory for database access
        """
        self.redis = redis_client
        self.session_factory = session_factory
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the background worker loop."""
        self._running = True
        logger.info(
            "Task worker started, listening on queues: %s, %s",
            PARSE_PDF_QUEUE,
            EXTRACT_CLAIMS_QUEUE,
        )

        while self._running:
            try:
                # BRPOP blocks until a task is available (with 5s timeout for graceful shutdown)
                # Listen on both queues
                result = await self.redis.brpop(
                    [PARSE_PDF_QUEUE, EXTRACT_CLAIMS_QUEUE], timeout=5
                )

                if result is None:
                    # Timeout, check if we should continue
                    continue

                queue_name, report_id_bytes = result
                queue_name = (
                    queue_name.decode("utf-8")
                    if isinstance(queue_name, bytes)
                    else queue_name
                )
                report_id = report_id_bytes.decode("utf-8")

                logger.info("Dequeued task from %s for report: %s", queue_name, report_id)

                # Route to appropriate handler
                if queue_name == PARSE_PDF_QUEUE:
                    await self.process_parse_task(report_id)
                elif queue_name == EXTRACT_CLAIMS_QUEUE:
                    await self.process_extract_claims_task(report_id)
                else:
                    logger.warning("Unknown queue: %s", queue_name)

            except asyncio.CancelledError:
                logger.info("Task worker cancelled")
                break
            except Exception:
                logger.exception("Error in task worker loop")
                # Brief pause before retrying to avoid tight error loops
                await asyncio.sleep(1)

        logger.info("Task worker stopped")

    async def stop(self) -> None:
        """Gracefully stop the worker."""
        logger.info("Stopping task worker...")
        self._running = False

    async def process_parse_task(self, report_id: str) -> None:
        """Parse a PDF and embed its content.

        Pipeline:
        1. Fetch the report from the database
        2. Update status to 'parsing'
        3. Parse the PDF using PDFParserService
        4. Store parsed content and content structure
        5. Call RAGService.ingest_report() for embedding
        6. Update status to 'parsed' (or 'analyzing' if AUTO_START_ANALYSIS is True)

        On error: Update status to 'error' with descriptive message.
        """
        async with self.session_factory() as db:
            try:
                # Fetch the report
                stmt = select(Report).where(Report.id == UUID(report_id))
                result = await db.execute(stmt)
                report = result.scalar_one_or_none()

                if report is None:
                    logger.error("Report not found: %s", report_id)
                    return

                if report.pdf_binary is None:
                    logger.error("Report has no PDF binary: %s", report_id)
                    await self._set_error(db, report, "Report PDF binary is missing.")
                    return

                # Update status to parsing
                report.status = "parsing"
                await db.commit()
                logger.info("Set report %s status to 'parsing'", report_id)

                # Parse the PDF
                parser = PDFParserService()
                parse_result = await parser.parse_pdf(report.pdf_binary)

                # Store parsed content
                report.parsed_content = parse_result.markdown
                report.page_count = parse_result.page_count
                report.content_structure = parse_result.content_structure.model_dump()
                await db.commit()
                logger.info(
                    "Stored parsed content for report %s: %d pages",
                    report_id,
                    parse_result.page_count,
                )

                # Update status to embedding
                report.status = "embedding"
                await db.commit()
                logger.info("Set report %s status to 'embedding'", report_id)

                # Embed the content via RAG service
                # Import here to avoid circular imports
                from app.services.embedding_service import EmbeddingService
                from app.services.rag_service import RAGService

                embedding_service = EmbeddingService()
                try:
                    rag_service = RAGService(db, embedding_service)

                    # Convert page boundaries to the format expected by RAG service
                    page_metadata = [
                        {
                            "page_number": pb.page_number,
                            "start_char": pb.char_start,
                        }
                        for pb in parse_result.page_boundaries
                    ]

                    chunk_count = await rag_service.ingest_report(
                        report_id=report_id,
                        markdown_content=parse_result.markdown,
                        page_metadata=page_metadata,
                    )
                    logger.info(
                        "Embedded %d chunks for report %s", chunk_count, report_id
                    )
                finally:
                    await embedding_service.close()

                # Check if we should auto-start analysis
                if settings.AUTO_START_ANALYSIS:
                    # Set status to analyzing and enqueue claims extraction
                    report.status = "analyzing"
                    await db.commit()
                    await self.redis.lpush(EXTRACT_CLAIMS_QUEUE, report_id)
                    logger.info(
                        "Auto-started claims extraction for report %s", report_id
                    )
                else:
                    # Update status to parsed
                    report.status = "parsed"
                    await db.commit()
                    logger.info("Report %s parsing complete", report_id)

            except PDFParseError as e:
                logger.warning("PDF parse error for report %s: %s", report_id, e)
                # Re-fetch report in case session state is stale
                stmt = select(Report).where(Report.id == UUID(report_id))
                result = await db.execute(stmt)
                report = result.scalar_one_or_none()
                if report:
                    await self._set_error(db, report, str(e))

            except Exception:
                logger.exception("Unexpected error processing report %s", report_id)
                # Re-fetch report
                stmt = select(Report).where(Report.id == UUID(report_id))
                result = await db.execute(stmt)
                report = result.scalar_one_or_none()
                if report:
                    await self._set_error(
                        db,
                        report,
                        "An unexpected error occurred while processing the document. "
                        "Please try again.",
                    )

    async def process_extract_claims_task(self, report_id: str) -> None:
        """Extract claims from a parsed report.

        Pipeline:
        1. Fetch the report from the database
        2. Verify status is 'analyzing'
        3. Run claims extraction via the Claims Agent
        4. Update status to 'completed'

        On error: Update status to 'error' with descriptive message.
        """
        async with self.session_factory() as db:
            try:
                # Fetch the report
                stmt = select(Report).where(Report.id == UUID(report_id))
                result = await db.execute(stmt)
                report = result.scalar_one_or_none()

                if report is None:
                    logger.error("Report not found: %s", report_id)
                    return

                if report.status != "analyzing":
                    logger.warning(
                        "Report %s is not in 'analyzing' status (current: %s), skipping",
                        report_id,
                        report.status,
                    )
                    return

                if report.parsed_content is None:
                    logger.error("Report has no parsed content: %s", report_id)
                    await self._set_error(
                        db, report, "Report content is missing. Please re-upload the PDF."
                    )
                    return

                logger.info("Starting claims extraction for report: %s", report_id)

                # Run claims extraction
                from app.agents.claims_agent import run_claims_extraction

                claims = await run_claims_extraction(report_id, db)

                logger.info(
                    "Extracted %d claims for report %s", len(claims), report_id
                )

                # Update status to completed
                report.status = "completed"
                await db.commit()
                logger.info("Report %s claims extraction complete", report_id)

            except Exception as e:
                logger.exception(
                    "Error during claims extraction for report %s", report_id
                )
                # Re-fetch report
                stmt = select(Report).where(Report.id == UUID(report_id))
                result = await db.execute(stmt)
                report = result.scalar_one_or_none()
                if report:
                    await self._set_error(
                        db,
                        report,
                        f"Claims extraction failed: {str(e)[:200]}",
                    )

    async def _set_error(
        self, db: AsyncSession, report: Report, error_message: str
    ) -> None:
        """Set report status to error with the given message."""
        report.status = "error"
        report.error_message = error_message
        await db.commit()
        logger.info("Set report %s status to 'error': %s", report.id, error_message)
