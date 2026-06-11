"""Groq provider (OpenAI-compatible chat completions over open models).

Used by default as the cross-check VERIFIER — a different provider from the
Gemini generator, so the independent re-solve isn't the same model grading its
own work. Pick a reasoning-capable model (e.g. a Llama-3.3-70B or gpt-oss
variant) for verification. Groq has no embeddings API; `embed` raises.
"""
from __future__ import annotations

import asyncio

from app.llm.base import LLMError, LLMProvider

_TRANSIENT = ("429", "rate", "limit", "503", "502", "500", "overloaded", "timeout")


def _is_transient(err: Exception) -> bool:
    msg = str(err).lower()
    return any(tok in msg for tok in _TRANSIENT)


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, api_key: str, model: str) -> None:
        try:
            from groq import AsyncGroq
        except ImportError as e:  # pragma: no cover - exercised only live
            raise LLMError(
                "groq SDK not installed; `pip install -e '.[llm]'`"
            ) from e
        if not api_key:
            raise LLMError("GROQ_API_KEY is not set")
        self._client = AsyncGroq(api_key=api_key)
        self._model = model

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
        extra = {"response_format": {"type": "json_object"}} if json_mode else {}
        delay = 2.0
        for attempt in range(5):
            try:
                resp = await self._client.chat.completions.create(
                    model=self._model,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    **extra,
                )
                return resp.choices[0].message.content or ""
            except Exception as e:  # pragma: no cover - exercised only live
                if _is_transient(e) and attempt < 4:
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                raise LLMError(f"Groq request failed: {e}") from e

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise LLMError(
            "Groq has no embeddings API; set LLM_EMBEDDING_PROVIDER=gemini"
        )
