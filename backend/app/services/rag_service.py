"""RAG (Retrieval-Augmented Generation) service.

Implements FRD 1 (RAG Pipeline).

Provides:
- Document chunking with hierarchical structure
- Embedding generation via OpenAI text-embedding-3-small
- pgvector storage and retrieval
- Hybrid search (semantic + full-text) with RRF re-ranking
- Corpus ingestion for IFRS, SASB, and report content
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.embedding import Embedding
from app.services.chunking import chunk_ifrs, chunk_report, chunk_sasb
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

# Data directory paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
IFRS_DIR = DATA_DIR / "ifrs"
SASB_DIR = DATA_DIR / "sasb"


class RAGResult(BaseModel):
    """A single retrieval result from the RAG pipeline."""

    chunk_id: str
    chunk_text: str
    metadata: dict
    source_type: str  # ifrs_s1 | ifrs_s2 | sasb | report
    report_id: str | None
    score: float
    search_method: str  # semantic | keyword | hybrid


class RAGServiceError(Exception):
    """Raised when RAG service operations fail."""


class RAGService:
    """Central API for all RAG operations.

    Provides ingestion of IFRS, SASB, and report content, and hybrid
    retrieval combining semantic (pgvector) and keyword (full-text) search.
    """

    # Default RRF constant
    DEFAULT_RRF_K = 60

    def __init__(self, db: AsyncSession, embedding_service: EmbeddingService):
        """Initialize the RAG service.

        Args:
            db: Async SQLAlchemy session
            embedding_service: Service for generating embeddings
        """
        self.db = db
        self.embedding_service = embedding_service

    # -------------------------------------------------------------------------
    # Ingestion Methods
    # -------------------------------------------------------------------------

    async def ingest_ifrs_corpus(self) -> dict:
        """Ingest IFRS S1 and S2 standard texts.

        Reads markdown files from data/ifrs/, chunks them, generates embeddings,
        and stores them in the database.

        Returns:
            Dict with ingestion stats (chunk counts, duration)

        Raises:
            RAGServiceError: If ingestion fails
        """
        start_time = time.time()
        stats = {"ifrs_s1_chunks": 0, "ifrs_s2_chunks": 0}

        # Check if already ingested
        existing = await self._count_by_source_type("ifrs_s1")
        if existing > 0:
            logger.info("IFRS S1 corpus already ingested (%d chunks)", existing)
            stats["ifrs_s1_chunks"] = existing
            existing_s2 = await self._count_by_source_type("ifrs_s2")
            stats["ifrs_s2_chunks"] = existing_s2
            stats["already_ingested"] = True
            return stats

        # Load S1/S2 mapping for enriching S2 chunks
        s1_s2_mapping = await self._load_s1_s2_mapping()

        # Ingest S1
        s1_path = IFRS_DIR / "s1_full.md"
        if s1_path.exists():
            logger.info("Ingesting IFRS S1 from %s", s1_path)
            content = s1_path.read_text(encoding="utf-8")
            chunks = chunk_ifrs(content, "S1")
            await self._store_chunks(chunks, "ifrs_s1")
            stats["ifrs_s1_chunks"] = len(chunks)
            logger.info("Ingested %d IFRS S1 chunks", len(chunks))
        else:
            logger.warning("IFRS S1 file not found: %s", s1_path)

        # Ingest S2
        s2_path = IFRS_DIR / "s2_full.md"
        if s2_path.exists():
            logger.info("Ingesting IFRS S2 from %s", s2_path)
            content = s2_path.read_text(encoding="utf-8")
            chunks = chunk_ifrs(content, "S2")

            # Enrich S2 chunks with S1 counterpart mapping
            if s1_s2_mapping:
                chunks = self._enrich_s2_chunks(chunks, s1_s2_mapping)

            await self._store_chunks(chunks, "ifrs_s2")
            stats["ifrs_s2_chunks"] = len(chunks)
            logger.info("Ingested %d IFRS S2 chunks", len(chunks))
        else:
            logger.warning("IFRS S2 file not found: %s", s2_path)

        stats["duration_seconds"] = round(time.time() - start_time, 2)
        return stats

    async def ingest_sasb_corpus(self) -> dict:
        """Ingest SASB industry standards.

        Reads all markdown files from data/sasb/, chunks them, generates
        embeddings, and stores them in the database.

        Returns:
            Dict with ingestion stats

        Raises:
            RAGServiceError: If ingestion fails
        """
        start_time = time.time()
        stats = {"sasb_chunks": 0, "files_processed": 0}

        # Check if already ingested
        existing = await self._count_by_source_type("sasb")
        if existing > 0:
            logger.info("SASB corpus already ingested (%d chunks)", existing)
            stats["sasb_chunks"] = existing
            stats["already_ingested"] = True
            return stats

        if not SASB_DIR.exists():
            logger.warning("SASB directory not found: %s", SASB_DIR)
            return stats

        # Process each SASB file
        all_chunks = []
        for sasb_file in SASB_DIR.glob("*.md"):
            logger.info("Processing SASB file: %s", sasb_file.name)
            content = sasb_file.read_text(encoding="utf-8")
            chunks = chunk_sasb(content, sasb_file.name)
            all_chunks.extend(chunks)
            stats["files_processed"] += 1

        if all_chunks:
            await self._store_chunks(all_chunks, "sasb")
            stats["sasb_chunks"] = len(all_chunks)
            logger.info("Ingested %d SASB chunks from %d files", len(all_chunks), stats["files_processed"])

        stats["duration_seconds"] = round(time.time() - start_time, 2)
        return stats

    async def ingest_report(
        self,
        report_id: str,
        markdown_content: str,
        page_metadata: list[dict] | None = None,
    ) -> int:
        """Chunk, embed, and store report content.

        Args:
            report_id: UUID of the parent report
            markdown_content: Parsed markdown from PyMuPDF4LLM
            page_metadata: Optional page info for tracking page numbers

        Returns:
            Number of chunks created

        Raises:
            RAGServiceError: If ingestion fails
        """
        # Delete existing embeddings for this report (idempotent re-ingestion)
        await self.delete_report_embeddings(report_id)

        # Chunk the content
        chunks = chunk_report(markdown_content, page_metadata)
        logger.info("Created %d chunks for report %s", len(chunks), report_id)

        if not chunks:
            return 0

        # Store chunks with report_id
        await self._store_chunks(chunks, "report", report_id=report_id)

        return len(chunks)

    async def delete_corpus(self, source_type: str) -> int:
        """Delete all embeddings for a source type.

        Args:
            source_type: The corpus type to delete (ifrs_s1, ifrs_s2, sasb, report)

        Returns:
            Number of embeddings deleted
        """
        stmt = delete(Embedding).where(Embedding.source_type == source_type)
        result = await self.db.execute(stmt)
        await self.db.commit()
        count = result.rowcount
        logger.info("Deleted %d embeddings for source_type=%s", count, source_type)
        return count

    async def delete_report_embeddings(self, report_id: str) -> int:
        """Delete all embeddings for a specific report.

        Args:
            report_id: UUID of the report

        Returns:
            Number of embeddings deleted
        """
        stmt = delete(Embedding).where(Embedding.report_id == UUID(report_id))
        result = await self.db.execute(stmt)
        await self.db.commit()
        count = result.rowcount
        if count > 0:
            logger.info("Deleted %d embeddings for report_id=%s", count, report_id)
        return count

    # -------------------------------------------------------------------------
    # Retrieval Methods
    # -------------------------------------------------------------------------

    async def search(
        self,
        query: str,
        top_k: int = 10,
        mode: Literal["semantic", "keyword", "hybrid"] = "hybrid",
        source_types: list[str] | None = None,
        report_id: str | None = None,
        rrf_k: int = DEFAULT_RRF_K,
    ) -> list[RAGResult]:
        """Perform a search and return ranked results.

        Args:
            query: Search query text
            top_k: Maximum number of results to return
            mode: Search mode (semantic, keyword, or hybrid)
            source_types: Optional filter by corpus type(s)
            report_id: Optional filter to a specific report's chunks
            rrf_k: RRF constant for hybrid mode (default: 60)

        Returns:
            List of RAGResult sorted by relevance
        """
        if mode == "semantic":
            return await self._semantic_search(query, top_k, source_types, report_id)
        elif mode == "keyword":
            return await self._keyword_search(query, top_k, source_types, report_id)
        else:  # hybrid
            return await self._hybrid_search(query, top_k, source_types, report_id, rrf_k)

    async def _semantic_search(
        self,
        query: str,
        top_k: int,
        source_types: list[str] | None,
        report_id: str | None,
    ) -> list[RAGResult]:
        """Perform semantic search using pgvector cosine similarity."""
        # Embed the query
        query_embedding = await self.embedding_service.embed_text(query)

        # Build the query using raw SQL for pgvector operations
        # The <=> operator calculates cosine distance (1 - similarity)
        sql = """
            SELECT
                id,
                chunk_text,
                chunk_metadata,
                source_type,
                report_id,
                1 - (embedding <=> :query_vector) AS similarity_score
            FROM embeddings
            WHERE 1=1
        """
        params: dict = {"query_vector": str(query_embedding)}

        if source_types:
            sql += " AND source_type = ANY(:source_types)"
            params["source_types"] = source_types

        if report_id:
            sql += " AND report_id = :report_id"
            params["report_id"] = UUID(report_id)

        sql += " ORDER BY embedding <=> :query_vector LIMIT :top_k"
        params["top_k"] = top_k

        result = await self.db.execute(text(sql), params)
        rows = result.fetchall()

        return [
            RAGResult(
                chunk_id=str(row.id),
                chunk_text=row.chunk_text,
                metadata=row.chunk_metadata or {},
                source_type=row.source_type,
                report_id=str(row.report_id) if row.report_id else None,
                score=float(row.similarity_score),
                search_method="semantic",
            )
            for row in rows
        ]

    async def _keyword_search(
        self,
        query: str,
        top_k: int,
        source_types: list[str] | None,
        report_id: str | None,
    ) -> list[RAGResult]:
        """Perform keyword search using PostgreSQL full-text search."""
        sql = """
            SELECT
                id,
                chunk_text,
                chunk_metadata,
                source_type,
                report_id,
                ts_rank_cd(ts_content, query) AS rank_score
            FROM embeddings, plainto_tsquery('english', :query_text) AS query
            WHERE ts_content @@ query
        """
        params: dict = {"query_text": query}

        if source_types:
            sql += " AND source_type = ANY(:source_types)"
            params["source_types"] = source_types

        if report_id:
            sql += " AND report_id = :report_id"
            params["report_id"] = UUID(report_id)

        sql += " ORDER BY rank_score DESC LIMIT :top_k"
        params["top_k"] = top_k

        result = await self.db.execute(text(sql), params)
        rows = result.fetchall()

        return [
            RAGResult(
                chunk_id=str(row.id),
                chunk_text=row.chunk_text,
                metadata=row.chunk_metadata or {},
                source_type=row.source_type,
                report_id=str(row.report_id) if row.report_id else None,
                score=float(row.rank_score),
                search_method="keyword",
            )
            for row in rows
        ]

    async def _hybrid_search(
        self,
        query: str,
        top_k: int,
        source_types: list[str] | None,
        report_id: str | None,
        rrf_k: int,
    ) -> list[RAGResult]:
        """Perform hybrid search combining semantic and keyword with RRF re-ranking."""
        # Run both searches in parallel
        semantic_task = self._semantic_search(query, top_k * 2, source_types, report_id)
        keyword_task = self._keyword_search(query, top_k * 2, source_types, report_id)

        semantic_results, keyword_results = await asyncio.gather(
            semantic_task, keyword_task
        )

        # Build RRF scores
        # RRF_score(d) = Σ 1 / (k + rank_i(d))
        rrf_scores: dict[str, float] = {}
        chunk_data: dict[str, RAGResult] = {}

        # Process semantic results
        for rank, result in enumerate(semantic_results, start=1):
            chunk_id = result.chunk_id
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (rrf_k + rank)
            chunk_data[chunk_id] = result

        # Process keyword results
        for rank, result in enumerate(keyword_results, start=1):
            chunk_id = result.chunk_id
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (rrf_k + rank)
            if chunk_id not in chunk_data:
                chunk_data[chunk_id] = result

        # Sort by RRF score descending
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        # Build final results
        results = []
        for chunk_id in sorted_ids[:top_k]:
            result = chunk_data[chunk_id]
            results.append(
                RAGResult(
                    chunk_id=result.chunk_id,
                    chunk_text=result.chunk_text,
                    metadata=result.metadata,
                    source_type=result.source_type,
                    report_id=result.report_id,
                    score=rrf_scores[chunk_id],
                    search_method="hybrid",
                )
            )

        return results

    async def get_paragraph(self, paragraph_id: str) -> RAGResult | None:
        """Retrieve a specific IFRS paragraph by its identifier.

        Args:
            paragraph_id: The IFRS paragraph ID (e.g., "S2.14(a)(iv)")

        Returns:
            RAGResult if found, None otherwise
        """
        sql = """
            SELECT id, chunk_text, chunk_metadata, source_type, report_id
            FROM embeddings
            WHERE chunk_metadata->>'paragraph_id' = :paragraph_id
              AND source_type IN ('ifrs_s1', 'ifrs_s2')
            LIMIT 1
        """
        result = await self.db.execute(text(sql), {"paragraph_id": paragraph_id})
        row = result.fetchone()

        if not row:
            return None

        return RAGResult(
            chunk_id=str(row.id),
            chunk_text=row.chunk_text,
            metadata=row.chunk_metadata or {},
            source_type=row.source_type,
            report_id=str(row.report_id) if row.report_id else None,
            score=1.0,  # Exact match
            search_method="paragraph_lookup",
        )

    async def corpus_stats(self) -> dict:
        """Return counts of embeddings by source type."""
        sql = """
            SELECT source_type, COUNT(*) as count
            FROM embeddings
            GROUP BY source_type
        """
        result = await self.db.execute(text(sql))
        rows = result.fetchall()

        stats = {row.source_type: row.count for row in rows}
        stats["total"] = sum(stats.values())
        return stats

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    async def _count_by_source_type(self, source_type: str) -> int:
        """Count embeddings for a given source type."""
        stmt = select(func.count()).select_from(Embedding).where(
            Embedding.source_type == source_type
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _load_s1_s2_mapping(self) -> dict | None:
        """Load the S1/S2 cross-reference mapping from JSON."""
        mapping_path = IFRS_DIR / "s1_s2_mapping.json"
        if not mapping_path.exists():
            logger.warning("S1/S2 mapping file not found: %s", mapping_path)
            return None

        try:
            with open(mapping_path, encoding="utf-8") as f:
                data = json.load(f)
            return data
        except (OSError, json.JSONDecodeError) as e:
            logger.error("Failed to load S1/S2 mapping: %s", e)
            return None

    def _enrich_s2_chunks(self, chunks: list, mapping: dict) -> list:
        """Enrich S2 chunks with S1 counterpart from the mapping."""
        # Build a lookup from S2 paragraph ranges to S1 counterparts
        s2_to_s1: dict[str, str] = {}

        for entry in mapping.get("mappings", []):
            s2_paras = entry.get("s2_paragraphs", "")
            s1_paras = entry.get("s1_paragraphs", "")

            # Handle ranges like "S2.5-7" or single paragraphs like "S2.14"
            if "-" in s2_paras:
                # Parse range
                match = s2_paras.replace("S2.", "")
                parts = match.split("-")
                if len(parts) == 2:
                    try:
                        start, end = int(parts[0]), int(parts[1])
                        for num in range(start, end + 1):
                            s2_to_s1[f"S2.{num}"] = s1_paras
                    except ValueError:
                        s2_to_s1[s2_paras] = s1_paras
            else:
                s2_to_s1[s2_paras] = s1_paras

        # Enrich chunks
        for chunk in chunks:
            para_id = chunk.metadata.get("paragraph_id", "")
            # Try exact match first
            if para_id in s2_to_s1:
                chunk.metadata["s1_counterpart"] = s2_to_s1[para_id]
            else:
                # Try base paragraph (e.g., S2.14 for S2.14(a)(iv))
                base_match = para_id.split("(")[0] if "(" in para_id else para_id
                if base_match in s2_to_s1:
                    chunk.metadata["s1_counterpart"] = s2_to_s1[base_match]

        return chunks

    async def _store_chunks(
        self,
        chunks: list,
        source_type: str,
        report_id: str | None = None,
    ) -> None:
        """Embed and store chunks in the database."""
        if not chunks:
            return

        # Extract texts for batch embedding
        texts = [chunk.text for chunk in chunks]

        # Generate embeddings
        logger.info("Generating embeddings for %d chunks...", len(texts))
        embeddings = await self.embedding_service.embed_batch(texts)

        # Create embedding records
        for chunk, embedding in zip(chunks, embeddings):
            # Create the embedding record
            # ts_content is set via raw SQL to use to_tsvector
            embedding_record = Embedding(
                report_id=UUID(report_id) if report_id else None,
                source_type=source_type,
                chunk_text=chunk.text,
                chunk_metadata=chunk.metadata,
                embedding=embedding,
            )
            self.db.add(embedding_record)

        # Flush to get IDs assigned
        await self.db.flush()

        # Update ts_content for all new records using raw SQL
        # This uses to_tsvector to generate the tsvector from chunk_text
        sql = """
            UPDATE embeddings
            SET ts_content = to_tsvector('english', chunk_text)
            WHERE ts_content IS NULL
        """
        await self.db.execute(text(sql))
        await self.db.commit()

        logger.info("Stored %d embeddings with source_type=%s", len(chunks), source_type)


# CLI entry point
if __name__ == "__main__":
    import argparse
    import sys

    from app.core.database import async_session_maker
    from app.services.embedding_service import EmbeddingService

    async def run_cli(cli_args: argparse.Namespace) -> None:
        """Run CLI commands."""
        async with async_session_maker() as db:
            embedding_svc = EmbeddingService()
            rag_svc = RAGService(db, embedding_svc)

            try:
                if cli_args.command == "ingest":
                    if cli_args.corpus in ("all", "ifrs"):
                        print("Ingesting IFRS corpus...")
                        stats = await rag_svc.ingest_ifrs_corpus()
                        print(f"  IFRS S1: {stats.get('ifrs_s1_chunks', 0)} chunks")
                        print(f"  IFRS S2: {stats.get('ifrs_s2_chunks', 0)} chunks")

                    if cli_args.corpus in ("all", "sasb"):
                        print("Ingesting SASB corpus...")
                        stats = await rag_svc.ingest_sasb_corpus()
                        print(f"  SASB: {stats.get('sasb_chunks', 0)} chunks")

                elif cli_args.command == "stats":
                    stats = await rag_svc.corpus_stats()
                    print("Corpus Statistics:")
                    for source_type, count in stats.items():
                        print(f"  {source_type}: {count}")

                elif cli_args.command == "delete":
                    if not cli_args.source_type:
                        print("Error: --source-type required for delete command")
                        sys.exit(1)
                    count = await rag_svc.delete_corpus(cli_args.source_type)
                    print(f"Deleted {count} embeddings for {cli_args.source_type}")

            finally:
                await embedding_svc.close()

    parser = argparse.ArgumentParser(description="RAG Service CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest corpus data")
    ingest_parser.add_argument(
        "--corpus",
        choices=["all", "ifrs", "sasb"],
        default="all",
        help="Which corpus to ingest",
    )

    # Stats command
    subparsers.add_parser("stats", help="Show corpus statistics")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete corpus data")
    delete_parser.add_argument(
        "--source-type",
        choices=["ifrs_s1", "ifrs_s2", "sasb", "report"],
        help="Source type to delete",
    )

    args = parser.parse_args()

    asyncio.run(run_cli(args))
