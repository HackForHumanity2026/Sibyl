"""Background task worker for PDF parsing.

Implements FRD 2 (PDF Upload & Ingestion) Section 5.

A lightweight Redis-based task queue that processes PDF parsing
jobs asynchronously. Uses BRPOP for blocking dequeue.
"""

import asyncio
import logging
from typing import TYPE_CHECKING
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.report import Report
from app.services.pdf_parser import PDFParseError, PDFParserService

if TYPE_CHECKING:
    from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

# Redis queue key
TASK_QUEUE_KEY = "sibyl:tasks:parse_pdf"


class TaskWorker:
    """Background worker that processes PDF parsing tasks from Redis.

    Polls the Redis queue using BRPOP and processes tasks sequentially.
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
        logger.info("Task worker started, listening on queue: %s", TASK_QUEUE_KEY)

        while self._running:
            try:
                # BRPOP blocks until a task is available (with 5s timeout for graceful shutdown)
                result = await self.redis.brpop(TASK_QUEUE_KEY, timeout=5)

                if result is None:
                    # Timeout, check if we should continue
                    continue

                _, report_id_bytes = result
                report_id = report_id_bytes.decode("utf-8")

                logger.info("Dequeued parse task for report: %s", report_id)
                await self.process_parse_task(report_id)

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
        6. Update status to 'parsed'

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

            except Exception as e:
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

    async def _set_error(
        self, db: AsyncSession, report: Report, error_message: str
    ) -> None:
        """Set report status to error with the given message."""
        report.status = "error"
        report.error_message = error_message
        await db.commit()
        logger.info("Set report %s status to 'error': %s", report.id, error_message)
