"""OpenRouter API client wrapper for unified LLM access.

Provides a single interface for all LLM calls in Sibyl through the OpenRouter gateway.
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class Models:
    """OpenRouter model identifiers."""

    # Gemini models (use the latest available versions on OpenRouter)
    GEMINI_FLASH = "google/gemini-2.5-flash"  # Fast, cheap reasoning model
    GEMINI_PRO = "google/gemini-2.5-pro"
    # Claude models
    CLAUDE_SONNET = "anthropic/claude-3.5-sonnet"
    CLAUDE_HAIKU = "anthropic/claude-3.5-haiku"  # Fast, cheap for classification tasks
    CLAUDE_OPUS = "anthropic/claude-3-opus"
    # OpenAI models
    GPT4O_MINI = "openai/gpt-4o-mini"  # Best JSON compliance, fast, cheap
    # Other models
    DEEPSEEK = "deepseek/deepseek-chat"
    EMBEDDING = "openai/text-embedding-3-small"


class OpenRouterClient:
    """
    Async HTTP client for OpenRouter API.

    Features:
    - Retry logic with exponential backoff for transient failures
    - Request/response logging
    - Consistent headers (Authorization, Referer, X-Title)
    """

    # HTTP status codes that trigger retry
    RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAYS = [1.0, 2.0, 4.0]  # seconds

    def __init__(self) -> None:
        """Initialize the OpenRouter client."""
        self._client = httpx.AsyncClient(
            base_url=settings.OPENROUTER_BASE_URL,
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://sibyl.dev",
                "X-Title": "Sibyl",
            },
            timeout=httpx.Timeout(180.0),  # Large reports may need 60-120s of generation
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """
        Send a chat completion request to OpenRouter.

        Args:
            model: OpenRouter model identifier (e.g., Models.CLAUDE_SONNET)
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens in response (optional)
            response_format: Optional structured output format

        Returns:
            The assistant's response content as a string

        Raises:
            httpx.HTTPStatusError: On non-retryable HTTP errors
            Exception: On exhausted retries or other failures
        """
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        if response_format is not None:
            payload["response_format"] = response_format

        last_exception: Exception | None = None

        for attempt in range(self.MAX_RETRIES):
            try:
                logger.debug(
                    "OpenRouter request: model=%s, messages=%d, attempt=%d",
                    model,
                    len(messages),
                    attempt + 1,
                )

                response = await self._client.post("/chat/completions", json=payload)

                if response.status_code in self.RETRY_STATUS_CODES:
                    delay = self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]
                    logger.warning(
                        "OpenRouter returned %d, retrying in %.1fs (attempt %d/%d)",
                        response.status_code,
                        delay,
                        attempt + 1,
                        self.MAX_RETRIES,
                    )
                    import asyncio
                    await asyncio.sleep(delay)
                    continue

                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                finish_reason = data["choices"][0].get("finish_reason", "unknown")

                # Log token usage and finish reason (WARNING level to bypass default config)
                usage = data.get("usage", {})
                logger.warning(
                    "OpenRouter response: model=%s, finish_reason=%s, "
                    "prompt_tokens=%s, completion_tokens=%s, "
                    "response_length=%d chars",
                    model,
                    finish_reason,
                    usage.get("prompt_tokens", "N/A"),
                    usage.get("completion_tokens", "N/A"),
                    len(content) if content else 0,
                )

                # Warn on potential issues
                if not content:
                    logger.warning(
                        "OpenRouter returned empty content! finish_reason=%s",
                        finish_reason,
                    )
                if finish_reason == "length":
                    logger.warning(
                        "OpenRouter response truncated (finish_reason=length). "
                        "Output hit max_tokens limit."
                    )

                return content

            except httpx.HTTPStatusError as e:
                if e.response.status_code in self.RETRY_STATUS_CODES:
                    last_exception = e
                    delay = self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]
                    logger.warning(
                        "OpenRouter HTTP error %d, retrying in %.1fs",
                        e.response.status_code,
                        delay,
                    )
                    import asyncio
                    await asyncio.sleep(delay)
                    continue
                # Log the error response body for debugging
                try:
                    error_body = e.response.json()
                    logger.error("OpenRouter error response: %s", error_body)
                except Exception:
                    logger.error("OpenRouter error response (text): %s", e.response.text[:500])
                logger.error("OpenRouter non-retryable error: %s", e)
                raise

            except Exception as e:
                last_exception = e
                logger.error("OpenRouter unexpected error: %s", e)
                raise

        # Exhausted retries
        msg = f"OpenRouter request failed after {self.MAX_RETRIES} attempts"
        logger.error(msg)
        if last_exception:
            raise Exception(msg) from last_exception
        raise Exception(msg)

    async def stream_chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream a chat completion response from OpenRouter.

        Yields individual text tokens as they arrive, enabling real-time display.
        Uses Server-Sent Events (SSE) format from OpenRouter's streaming API.

        Args:
            model: OpenRouter model identifier (e.g., Models.GEMINI_FLASH)
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens in response (optional)

        Yields:
            str: Individual text tokens from the response

        Raises:
            httpx.HTTPStatusError: On HTTP errors
            Exception: On connection errors
        """
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        logger.debug(
            "OpenRouter streaming request: model=%s, messages=%d",
            model,
            len(messages),
        )

        async with self._client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()

            buffer = ""
            async for chunk in response.aiter_text():
                buffer += chunk
                
                # Process complete SSE lines
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    if line.startswith("data: "):
                        data_str = line[6:]
                        
                        # Check for stream end
                        if data_str == "[DONE]":
                            logger.debug("OpenRouter stream completed")
                            return
                        
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            logger.warning("Failed to parse SSE data: %s", data_str[:100])
                            continue


# Singleton client instance
openrouter_client = OpenRouterClient()
