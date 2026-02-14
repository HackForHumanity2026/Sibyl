"""Embedding service for generating text embeddings via OpenRouter.

Implements FRD 1 (RAG Pipeline) Section 1 - Embedding Service.

Provides:
- Single text embedding via embed_text()
- Batch text embedding via embed_batch() with token-aware batching
- Retry logic for transient failures
- Token estimation for batch sizing
"""

import asyncio
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Raised when embedding generation fails after all retries."""


class EmbeddingService:
    """
    Service for generating text embeddings via OpenRouter API.

    Uses OpenAI text-embedding-3-small model (1536 dimensions) through OpenRouter.
    Implements batching with token-aware grouping and retry logic.
    """

    # Model configuration
    MODEL = "openai/text-embedding-3-small"
    EMBEDDING_DIMENSION = 1536

    # Batching configuration
    # OpenAI embeddings API accepts up to 2048 inputs per request.
    # text-embedding-3-small supports 8191 tokens per individual input.
    # We set a generous per-batch token budget so that the text count
    # limit (100) is typically the binding constraint, not tokens.
    MAX_TEXTS_PER_BATCH = 100
    MAX_TOKENS_PER_BATCH = 50_000
    CHARS_PER_TOKEN = 4  # Approximate for English text
    MAX_TEXT_CHARS = 32000  # ~8000 tokens, truncate texts exceeding this

    # Concurrency configuration
    MAX_CONCURRENT_BATCHES = 5

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAYS = [1.0, 2.0, 4.0]  # seconds
    RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(self) -> None:
        """Initialize the embedding service with an HTTP client."""
        self._client = httpx.AsyncClient(
            base_url=settings.OPENROUTER_BASE_URL,
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://sibyl.dev",
                "X-Title": "Sibyl",
            },
            timeout=httpx.Timeout(120.0),  # Embeddings can take longer for large batches
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for a text string.

        Uses a simple heuristic of characters / 4 for English text.
        This is used only for batch sizing - the API handles exact counts.
        """
        return len(text) // self.CHARS_PER_TOKEN

    def _truncate_text(self, text: str) -> str:
        """Truncate text if it exceeds the maximum character limit.

        Returns the original text if within limits, otherwise truncates
        and logs a warning.
        """
        if len(text) <= self.MAX_TEXT_CHARS:
            return text

        logger.warning(
            "Truncating text from %d to %d characters (estimated %d to %d tokens)",
            len(text),
            self.MAX_TEXT_CHARS,
            self._estimate_tokens(text),
            self.MAX_TOKENS_PER_BATCH,
        )
        return text[: self.MAX_TEXT_CHARS]

    def _create_batches(self, texts: list[str]) -> list[list[str]]:
        """Group texts into batches respecting token and count limits.

        Each batch contains at most MAX_TEXTS_PER_BATCH texts and
        approximately MAX_TOKENS_PER_BATCH total tokens.
        """
        batches: list[list[str]] = []
        current_batch: list[str] = []
        current_tokens = 0

        for text in texts:
            # Truncate if needed
            text = self._truncate_text(text)
            text_tokens = self._estimate_tokens(text)

            # Check if adding this text would exceed limits
            would_exceed_count = len(current_batch) >= self.MAX_TEXTS_PER_BATCH
            would_exceed_tokens = (
                current_tokens + text_tokens > self.MAX_TOKENS_PER_BATCH
                and len(current_batch) > 0
            )

            if would_exceed_count or would_exceed_tokens:
                # Start a new batch
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0

            current_batch.append(text)
            current_tokens += text_tokens

        # Add the last batch if not empty
        if current_batch:
            batches.append(current_batch)

        return batches

    async def _call_embedding_api(self, texts: list[str]) -> list[list[float]]:
        """Call the OpenRouter embeddings API with retry logic.

        Args:
            texts: List of text strings to embed (already batched)

        Returns:
            List of embedding vectors in the same order as input

        Raises:
            EmbeddingError: If all retries fail
        """
        payload: dict[str, Any] = {
            "model": self.MODEL,
            "input": texts,
        }

        last_exception: Exception | None = None

        for attempt in range(self.MAX_RETRIES):
            try:
                logger.debug(
                    "Embedding API request: texts=%d, attempt=%d",
                    len(texts),
                    attempt + 1,
                )

                response = await self._client.post("/embeddings", json=payload)

                if response.status_code in self.RETRY_STATUS_CODES:
                    delay = self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]
                    logger.warning(
                        "Embedding API returned %d, retrying in %.1fs (attempt %d/%d)",
                        response.status_code,
                        delay,
                        attempt + 1,
                        self.MAX_RETRIES,
                    )
                    await asyncio.sleep(delay)
                    continue

                response.raise_for_status()

                data = response.json()

                # Extract embeddings in order (API returns them with index)
                embedding_data = data.get("data", [])
                # Sort by index to ensure correct order
                embedding_data.sort(key=lambda x: x.get("index", 0))
                embeddings = [item["embedding"] for item in embedding_data]

                # Log usage if available
                if "usage" in data:
                    usage = data["usage"]
                    logger.info(
                        "Embedding API response: texts=%d, total_tokens=%d",
                        len(texts),
                        usage.get("total_tokens", 0),
                    )

                return embeddings

            except httpx.HTTPStatusError as e:
                if e.response.status_code in self.RETRY_STATUS_CODES:
                    last_exception = e
                    delay = self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]
                    logger.warning(
                        "Embedding API HTTP error %d, retrying in %.1fs",
                        e.response.status_code,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                logger.error("Embedding API non-retryable error: %s", e)
                raise EmbeddingError(f"Embedding API error: {e}") from e

            except Exception as e:
                last_exception = e
                logger.error("Embedding API unexpected error: %s", e)
                raise EmbeddingError(f"Embedding API error: {e}") from e

        # Exhausted retries
        msg = f"Embedding API request failed after {self.MAX_RETRIES} attempts"
        logger.error(msg)
        raise EmbeddingError(msg) from last_exception

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string.

        Args:
            text: The text to embed

        Returns:
            A 1536-dimensional float vector

        Raises:
            EmbeddingError: If embedding fails after all retries
        """
        text = self._truncate_text(text)
        embeddings = await self._call_embedding_api([text])
        return embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple text strings with batching and concurrency.

        Groups texts into batches respecting token limits and processes
        them concurrently (up to MAX_CONCURRENT_BATCHES at a time) to
        minimize wall-clock time while avoiding rate-limit storms.

        Args:
            texts: List of text strings to embed

        Returns:
            List of 1536-dimensional float vectors in the same order as input

        Raises:
            EmbeddingError: If embedding fails after all retries
        """
        if not texts:
            return []

        # Create batches
        batches = self._create_batches(texts)
        logger.info(
            "Embedding %d texts in %d batches (concurrency=%d)",
            len(texts),
            len(batches),
            self.MAX_CONCURRENT_BATCHES,
        )

        # Process batches concurrently with a semaphore to cap parallelism
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_BATCHES)

        async def _process_batch(batch_idx: int, batch: list[str]) -> list[list[float]]:
            async with semaphore:
                logger.debug(
                    "Processing batch %d/%d (%d texts)",
                    batch_idx + 1,
                    len(batches),
                    len(batch),
                )
                return await self._call_embedding_api(batch)

        tasks = [
            _process_batch(i, batch) for i, batch in enumerate(batches)
        ]
        batch_results = await asyncio.gather(*tasks)

        # Flatten results in order
        all_embeddings: list[list[float]] = []
        for batch_embeddings in batch_results:
            all_embeddings.extend(batch_embeddings)

        return all_embeddings


# Singleton service instance
embedding_service = EmbeddingService()
