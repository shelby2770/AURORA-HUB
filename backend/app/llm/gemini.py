"""Google Gemini provider (generation + embeddings).

Uses the unified google-genai SDK. Default embedding backend for the project
since Claude can't embed.
"""
from __future__ import annotations

import asyncio

from app.llm.base import LLMError, LLMProvider

# Transient server-side conditions worth retrying with backoff.
_TRANSIENT = ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "500", "INTERNAL")


def _is_transient(err: Exception) -> bool:
    msg = str(err)
    return any(tok in msg for tok in _TRANSIENT)


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(
        self, api_key: str, model: str, embedding_model: str | None = None
    ) -> None:
        try:
            from google import genai
        except ImportError as e:  # pragma: no cover - exercised only live
            raise LLMError(
                "google-genai SDK not installed; `pip install -e '.[llm]'`"
            ) from e
        if not api_key:
            raise LLMError("GEMINI_API_KEY is not set")
        self._genai = genai
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._embedding_model = embedding_model

    async def complete(
        self,
        *,
        system: str,
        prompt: str,
        thinking: bool = True,
        effort: str = "high",
        max_tokens: int = 8000,
        json_mode: bool = False,
    ) -> str:
        from google.genai import types

        # Gemini 2.5 models "think" by default, consuming the output-token
        # budget before the answer is produced (which truncates JSON). Disable
        # thinking on the cheap path; allow dynamic thinking otherwise.
        thinking_config = types.ThinkingConfig(thinking_budget=0 if not thinking else -1)
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            thinking_config=thinking_config,
            # Native JSON mode returns guaranteed well-escaped JSON (no fences,
            # no literal control chars / unescaped quotes) — robust parsing.
            response_mime_type="application/json" if json_mode else None,
        )
        return await self._with_retry(
            lambda: self._client.aio.models.generate_content(
                model=self._model, contents=prompt, config=config
            ),
            what="request",
        )

    async def _with_retry(self, call, *, what: str, retries: int = 4):
        delay = 2.0
        for attempt in range(retries):
            try:
                resp = await call()
                return resp.text or ""
            except Exception as e:  # pragma: no cover - exercised only live
                if _is_transient(e) and attempt < retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                raise LLMError(f"Gemini {what} failed: {e}") from e

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not self._embedding_model:
            raise LLMError("Gemini embedding model not configured")
        delay = 2.0
        for attempt in range(4):
            try:
                resp = await self._client.aio.models.embed_content(
                    model=self._embedding_model, contents=texts
                )
                return [list(e.values) for e in resp.embeddings]
            except Exception as e:  # pragma: no cover - exercised only live
                if _is_transient(e) and attempt < 3:
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                raise LLMError(f"Gemini embedding failed: {e}") from e
