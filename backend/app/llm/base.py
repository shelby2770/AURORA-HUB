"""Pluggable LLM provider interface.

Authoring-plane only — never imported on the serving hot path. The generator
and the cross-check verifier can be different providers (env-selected). Concrete
providers import their SDK lazily so this module is importable without the SDK
or any API key (tests use MockProvider).
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMError(Exception):
    """Raised for provider/transport failures."""


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
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
        """Return the model's text response.

        `thinking=True` requests reasoning (used for generation/verification);
        `thinking=False` is the cheap path (categorize/parse). `json_mode=True`
        asks the provider to emit strict JSON (guaranteed well-escaped) where it
        supports it. Providers map these to their own knobs and ignore ones they
        don't support.
        """

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text (dedup only)."""
