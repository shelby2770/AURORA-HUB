"""Deterministic in-memory provider for tests and offline runs."""
from __future__ import annotations

import hashlib
from collections.abc import Callable

from app.llm.base import LLMProvider


def _hash_embedding(text: str, dims: int = 16) -> list[float]:
    """Stable pseudo-embedding from a hash — deterministic, no network."""
    h = hashlib.sha256(text.encode("utf-8")).digest()
    raw = [h[i % len(h)] / 255.0 for i in range(dims)]
    norm = sum(v * v for v in raw) ** 0.5 or 1.0
    return [v / norm for v in raw]


class MockProvider(LLMProvider):
    name = "mock"

    def __init__(
        self,
        *,
        responses: list[str] | None = None,
        complete_fn: Callable[[str, str], str] | None = None,
        embed_dims: int = 16,
    ) -> None:
        self._responses = list(responses or [])
        self._complete_fn = complete_fn
        self._embed_dims = embed_dims
        self.calls: list[dict] = []

    async def complete(
        self,
        *,
        system: str,
        prompt: str,
        thinking: bool = True,
        effort: str = "high",
        max_tokens: int = 8000,
    ) -> str:
        self.calls.append({"system": system, "prompt": prompt})
        if self._complete_fn is not None:
            return self._complete_fn(system, prompt)
        if self._responses:
            return self._responses.pop(0)
        raise AssertionError("MockProvider had no scripted response")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [_hash_embedding(t, self._embed_dims) for t in texts]
