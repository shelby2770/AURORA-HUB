"""Env-selected provider construction for each authoring role."""
from __future__ import annotations

from app.core.config import Settings, settings as default_settings
from app.llm.base import LLMError, LLMProvider


def _build(name: str, model: str, s: Settings) -> LLMProvider:
    if name == "claude":
        from app.llm.claude import ClaudeProvider

        return ClaudeProvider(s.anthropic_api_key, model)
    if name == "gemini":
        from app.llm.gemini import GeminiProvider

        return GeminiProvider(s.gemini_api_key, model, s.gemini_embedding_model)
    raise LLMError(f"Unknown LLM provider: {name!r}")


def _model_for(name: str, role: str, s: Settings) -> str:
    if name == "claude":
        return (
            s.claude_verifier_model
            if role == "verifier"
            else s.claude_generation_model
        )
    return s.gemini_generation_model


def get_generator(s: Settings | None = None) -> LLMProvider:
    s = s or default_settings
    return _build(s.llm_generator_provider, _model_for(s.llm_generator_provider, "generator", s), s)


def get_verifier(s: Settings | None = None) -> LLMProvider:
    s = s or default_settings
    return _build(s.llm_verifier_provider, _model_for(s.llm_verifier_provider, "verifier", s), s)


def get_embedder(s: Settings | None = None) -> LLMProvider:
    s = s or default_settings
    name = s.llm_embedding_provider
    model = s.gemini_embedding_model if name == "gemini" else ""
    return _build(name, model, s)
