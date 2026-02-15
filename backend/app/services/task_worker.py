"""Background task worker for PDF parsing, claims extraction, and pipeline execution.

Implements FRD 2 (PDF Upload & Ingestion), FRD 3 (Claims Agent), and FRD 5 (Pipeline).

A lightweight Redis-based task queue that processes PDF parsing,
claims extraction, and full pipeline jobs asynchronously.

Uses rpoplpush for at-least-once delivery: tasks are atomically moved from
the main queue to a processing queue, then removed only after successful
completion. If the worker crashes, orphaned tasks are recovered on startup.
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

# Redis queue keys (main task queues)
PARSE_PDF_QUEUE = "sibyl:tasks:parse_pdf"
EXTRACT_CLAIMS_QUEUE = "sibyl:tasks:extract_claims"
RUN_PIPELINE_QUEUE = "sibyl:tasks:run_pipeline"  # FRD 5: Full pipeline

# Redis processing queues (tasks currently being worked on)
PARSE_PDF_PROCESSING = "sibyl:processing:parse_pdf"
EXTRACT_CLAIMS_PROCESSING = "sibyl:processing:extract_claims"
RUN_PIPELINE_PROCESSING = "sibyl:processing:run_pipeline"  # FRD 5

# Legacy alias for backwards compatibility
TASK_QUEUE_KEY = PARSE_PDF_QUEUE


class TaskWorker:
    """Background worker that processes PDF parsing, claims extraction, and pipeline tasks.

    Uses rpoplpush for reliable at-least-once delivery:
    1. Tasks are atomically moved from the main queue to a processing queue
    2. After successful processing, the task is removed from the processing queue
    3. On startup, any orphaned tasks left in processing queues are recovered

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

        # Recover any orphaned tasks from a previous crash before processing new ones
        await self.recover_orphaned_tasks()

        logger.warning(
            "Task worker started, listening on queues: %s, %s, %s",
            PARSE_PDF_QUEUE,
            EXTRACT_CLAIMS_QUEUE,
            RUN_PIPELINE_QUEUE,
        )

        while self._running:
            try:
                task = await self._dequeue_task()
                if task is None:
                    # No tasks available, poll again after a brief sleep
                    await asyncio.sleep(1)
                    continue

                queue_name, task_payload = task
                logger.warning("Dequeued task from %s: %s", queue_name, task_payload)

                # Route to appropriate handler, then remove from processing queue on success
                if queue_name == PARSE_PDF_QUEUE:
                    await self.process_parse_task(task_payload)
                    await self.redis.lrem(PARSE_PDF_PROCESSING, 1, task_payload)
                elif queue_name == EXTRACT_CLAIMS_QUEUE:
                    await self.process_extract_claims_task(task_payload)
                    await self.redis.lrem(EXTRACT_CLAIMS_PROCESSING, 1, task_payload)
                elif queue_name == RUN_PIPELINE_QUEUE:
                    await self.process_run_pipeline_task(task_payload)
                    await self.redis.lrem(RUN_PIPELINE_PROCESSING, 1, task_payload)
                else:
                    logger.warning("Unknown queue: %s", queue_name)

            except asyncio.CancelledError:
                logger.warning("Task worker cancelled")
                break
            except Exception:
                logger.exception("Error in task worker loop")
                # Brief pause before retrying to avoid tight error loops
                await asyncio.sleep(1)

        logger.warning("Task worker stopped")

    async def _dequeue_task(self) -> tuple[str, str] | None:
        """Try to dequeue a task from each queue using rpoplpush.

        Atomically moves a task from the main queue to the corresponding
        processing queue. Returns (queue_name, task_payload) or None if
        all queues are empty.
        """
        # Check parse queue first
        result = await self.redis.rpoplpush(PARSE_PDF_QUEUE, PARSE_PDF_PROCESSING)
        if result is not None:
            payload = result.decode("utf-8") if isinstance(result, bytes) else result
            return (PARSE_PDF_QUEUE, payload)

        # Then check pipeline queue (FRD 5 - priority over legacy claims queue)
        result = await self.redis.rpoplpush(RUN_PIPELINE_QUEUE, RUN_PIPELINE_PROCESSING)
        if result is not None:
            payload = result.decode("utf-8") if isinstance(result, bytes) else result
            return (RUN_PIPELINE_QUEUE, payload)

        # Then check claims queue (legacy, for backwards compatibility)
        result = await self.redis.rpoplpush(EXTRACT_CLAIMS_QUEUE, EXTRACT_CLAIMS_PROCESSING)
        if result is not None:
            payload = result.decode("utf-8") if isinstance(result, bytes) else result
            return (EXTRACT_CLAIMS_QUEUE, payload)

        return None

    async def recover_orphaned_tasks(self) -> None:
        """Re-enqueue any tasks left in processing queues from a previous crash.

        Called on startup to ensure at-least-once delivery. Also checks the
        database for reports stuck in intermediate states (parsing, embedding,
        analyzing) and re-enqueues them.
        """
        recovered_count = 0

        # 1. Recover tasks from Redis processing queues
        for proc_queue, main_queue in [
            (PARSE_PDF_PROCESSING, PARSE_PDF_QUEUE),
            (EXTRACT_CLAIMS_PROCESSING, EXTRACT_CLAIMS_QUEUE),
            (RUN_PIPELINE_PROCESSING, RUN_PIPELINE_QUEUE),
        ]:
            while True:
                task = await self.redis.rpoplpush(proc_queue, main_queue)
                if task is None:
                    break
                payload = task.decode("utf-8") if isinstance(task, bytes) else task
                logger.warning(
                    "Recovered orphaned task: %s -> %s",
                    payload,
                    main_queue,
                )
                recovered_count += 1

        # 2. Recover reports stuck in intermediate DB states
        async with self.session_factory() as db:
            # Reports stuck in parsing/embedding -> re-enqueue for parse
            stuck_parse = await db.execute(
                select(Report).where(Report.status.in_(["parsing", "embedding"]))
            )
            for report in stuck_parse.scalars():
                logger.warning(
                    "Recovering stuck report %s (status=%s), re-enqueuing parse",
                    report.id,
                    report.status,
                )
                report.status = "uploaded"
                await db.commit()
                await self.redis.lpush(PARSE_PDF_QUEUE, str(report.id))
                recovered_count += 1

            # Reports stuck in analyzing -> re-enqueue for pipeline
            stuck_analyzing = await db.execute(
                select(Report).where(Report.status == "analyzing")
            )
            for report in stuck_analyzing.scalars():
                logger.warning(
                    "Recovering stuck report %s (status=analyzing), re-enqueuing pipeline",
                    report.id,
                )
                # FRD 5: Re-enqueue to pipeline queue instead of claims queue
                await self.redis.lpush(RUN_PIPELINE_QUEUE, str(report.id))
                recovered_count += 1

        if recovered_count > 0:
            logger.warning("Recovery complete: %d tasks re-enqueued", recovered_count)
        else:
            logger.warning("Recovery complete: no orphaned tasks found")

    async def stop(self) -> None:
        """Gracefully stop the worker."""
        logger.warning("Stopping task worker...")
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
                logger.warning("Set report %s status to 'parsing'", report_id)

                # Parse the PDF
                parser = PDFParserService()
                parse_result = await parser.parse_pdf(report.pdf_binary)

                # Store parsed content
                report.parsed_content = parse_result.markdown
                report.page_count = parse_result.page_count
                report.content_structure = parse_result.content_structure.model_dump()
                await db.commit()
                logger.warning(
                    "Stored parsed content for report %s: %d pages",
                    report_id,
                    parse_result.page_count,
                )

                # Update status to embedding
                report.status = "embedding"
                await db.commit()
                logger.warning("Set report %s status to 'embedding'", report_id)

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
                    logger.warning(
                        "Embedded %d chunks for report %s", chunk_count, report_id
                    )
                finally:
                    await embedding_service.close()

                # Check if we should auto-start analysis
                if settings.AUTO_START_ANALYSIS:
                    # Set status to analyzing and enqueue pipeline task
                    report.status = "analyzing"
                    await db.commit()
                    # FRD 5: Enqueue to pipeline queue instead of claims queue
                    await self.redis.lpush(RUN_PIPELINE_QUEUE, report_id)
                    logger.warning(
                        "Auto-started pipeline for report %s", report_id
                    )
                else:
                    # Update status to parsed
                    report.status = "parsed"
                    await db.commit()
                    logger.warning("Report %s parsing complete", report_id)

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
        """Extract claims from a parsed report (legacy queue handler).

        This is the FRD 3 standalone claims extraction. Kept for backwards
        compatibility. For FRD 5+, use process_run_pipeline_task instead.

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

                logger.warning("Starting claims extraction for report: %s", report_id)

                # Run claims extraction
                from app.agents.claims_agent import run_claims_extraction

                claims = await run_claims_extraction(report_id, db)

                logger.warning(
                    "Extracted %d claims for report %s", len(claims), report_id
                )

                # Update status to completed
                report.status = "completed"
                await db.commit()
                logger.warning("Report %s claims extraction complete", report_id)

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

    async def process_run_pipeline_task(self, task_payload: str) -> None:
        """Execute the full LangGraph analysis pipeline.

        FRD 5: This is the new pipeline execution handler that runs the
        complete analysis flow including claims extraction, orchestrator
        routing, specialist agents, judge, and report compilation.

        Task payload format:
        - "report_id" - Run full pipeline
        - "report_id:skip_claims" - Skip claims extraction, start from routing

        Pipeline:
        1. Parse task payload
        2. Fetch the report from the database
        3. Verify status is 'analyzing'
        4. Run the full LangGraph pipeline
        5. Status is updated by compile_report node

        On error: Update status to 'error' with descriptive message.
        """
        # Parse task payload
        skip_claims = False
        if ":skip_claims" in task_payload:
            report_id = task_payload.replace(":skip_claims", "")
            skip_claims = True
        else:
            report_id = task_payload

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

                logger.warning(
                    "Starting pipeline for report: %s (skip_claims=%s)",
                    report_id,
                    skip_claims,
                )

                # Run the full pipeline
                from app.agents.pipeline import run_pipeline, run_pipeline_skip_claims

                if skip_claims:
                    await run_pipeline_skip_claims(report_id, db)
                else:
                    await run_pipeline(report_id, db)

                logger.warning("Pipeline completed for report %s", report_id)

                # Note: Status is updated to "completed" by the compile_report node,
                # so we don't need to set it here

            except Exception as e:
                logger.exception(
                    "Error during pipeline execution for report %s", report_id
                )
                # Re-fetch report
                stmt = select(Report).where(Report.id == UUID(report_id))
                result = await db.execute(stmt)
                report = result.scalar_one_or_none()
                if report:
                    await self._set_error(
                        db,
                        report,
                        f"Pipeline execution failed: {str(e)[:200]}",
                    )

    async def _set_error(
        self, db: AsyncSession, report: Report, error_message: str
    ) -> None:
        """Set report status to error with the given message."""
        report.status = "error"
        report.error_message = error_message
        await db.commit()
        logger.warning("Set report %s status to 'error': %s", report.id, error_message)
