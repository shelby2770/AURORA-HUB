"""Google Gemini provider (generation + embeddings).

Uses the unified google-genai SDK. Default embedding backend for the project
since Claude can't embed.
"""
from __future__ import annotations

from app.llm.base import LLMError, LLMProvider


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
    ) -> str:
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
        )
        try:
            resp = await self._client.aio.models.generate_content(
                model=self._model, contents=prompt, config=config
            )
        except Exception as e:  # pragma: no cover - exercised only live
            raise LLMError(f"Gemini request failed: {e}") from e
        return resp.text or ""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not self._embedding_model:
            raise LLMError("Gemini embedding model not configured")
        try:
            resp = await self._client.aio.models.embed_content(
                model=self._embedding_model, contents=texts
            )
        except Exception as e:  # pragma: no cover - exercised only live
            raise LLMError(f"Gemini embedding failed: {e}") from e
        return [list(e.values) for e in resp.embeddings]
