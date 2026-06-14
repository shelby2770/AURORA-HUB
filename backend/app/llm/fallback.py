"""Provider that tries an ordered list of providers, falling through on failure.

Used by the on-demand generation path: Gemini first (per product preference),
Groq as fallback. Each underlying provider already does its own retry/backoff on
transient errors; this layer switches providers only when one gives up entirely
(raises LLMError) — e.g. Gemini's daily free-tier quota is exhausted.
"""
from __future__ import annotations

from app.llm.base import LLMError, LLMProvider


class FallbackProvider(LLMProvider):
    name = "fallback"

    def __init__(self, providers: list[LLMProvider]) -> None:
        if not providers:
            raise LLMError("FallbackProvider needs at least one provider")
        self._providers = providers
        # Records which provider served the last successful call (for reporting).
        self.last_used: str | None = None

    async def complete(self, **kwargs) -> str:
        errors: list[str] = []
        for p in self._providers:
            try:
                out = await p.complete(**kwargs)
                self.last_used = p.name
                return out
            except LLMError as e:  # provider gave up after its own retries
                errors.append(f"{p.name}: {e}")
        raise LLMError("all providers failed -> " + " | ".join(errors))

    async def embed(self, texts: list[str]) -> list[list[float]]:
        errors: list[str] = []
        for p in self._providers:
            try:
                out = await p.embed(texts)
                self.last_used = p.name
                return out
            except LLMError as e:
                errors.append(f"{p.name}: {e}")
        raise LLMError("all embedders failed -> " + " | ".join(errors))
