"""Anthropic Claude provider.

Targets Opus 4.8 by default. Opus 4.8 accepts adaptive thinking only — it
rejects `temperature`/`top_p`/`top_k` and `budget_tokens` with a 400 — so we
never send sampling params, and gate adaptive thinking + effort behind the
`thinking` flag (older/cheaper models don't support them).

Anthropic has no embeddings API; `embed` raises. Configure the embedding
provider as gemini (or another embeddings backend).
"""
from __future__ import annotations

from app.llm.base import LLMError, LLMProvider


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self, api_key: str, model: str) -> None:
        try:
            from anthropic import AsyncAnthropic
        except ImportError as e:  # pragma: no cover - exercised only live
            raise LLMError(
                "anthropic SDK not installed; `pip install -e '.[llm]'`"
            ) from e
        if not api_key:
            raise LLMError("ANTHROPIC_API_KEY is not set")
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def complete(
        self,
        *,
        system: str,
        prompt: str,
        thinking: bool = True,
        effort: str = "high",
        max_tokens: int = 8000,
    ) -> str:
        kwargs: dict = {
            "model": self._model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
        if thinking:
            # Adaptive thinking + effort (Opus 4.8). No sampling params.
            kwargs["thinking"] = {"type": "adaptive"}
            kwargs["output_config"] = {"effort": effort}
        try:
            resp = await self._client.messages.create(**kwargs)
        except Exception as e:  # pragma: no cover - exercised only live
            raise LLMError(f"Claude request failed: {e}") from e
        return "".join(b.text for b in resp.content if b.type == "text")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise LLMError(
            "Anthropic has no embeddings API; set LLM_EMBEDDING_PROVIDER=gemini"
        )
