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
    if name == "groq":
        from app.llm.groq import GroqProvider

        return GroqProvider(s.groq_api_key, model)
    raise LLMError(f"Unknown LLM provider: {name!r}")


def _model_for(name: str, role: str, s: Settings) -> str:
    verifier = role == "verifier"
    if name == "claude":
        return s.claude_verifier_model if verifier else s.claude_generation_model
    if name == "groq":
        return s.groq_verifier_model if verifier else s.groq_generation_model
    return s.gemini_generation_model


def get_generator(s: Settings | None = None) -> LLMProvider:
    s = s or default_settings
    return _build(s.llm_generator_provider, _model_for(s.llm_generator_provider, "generator", s), s)


def get_verifier(s: Settings | None = None) -> LLMProvider:
    s = s or default_settings
    return _build(s.llm_verifier_provider, _model_for(s.llm_verifier_provider, "verifier", s), s)


def get_parser(s: Settings | None = None) -> LLMProvider:
    """Cheap categorize/parse provider for ingestion.

    Defaults to the generator, but `LLM_PARSER_PROVIDER` can override it (e.g.
    Groq, far more generous than Gemini's 20-requests/day free tier for bulk).
    """
    s = s or default_settings
    name = s.llm_parser_provider or s.llm_generator_provider
    return _build(name, _model_for(name, "generator", s), s)


def get_ondemand_generator(s: Settings | None = None) -> LLMProvider:
    """Generator for on-demand quiz generation: Gemini first, Groq fallback.

    Honors the product preference (Gemini priority) while staying usable when
    Gemini's free-tier daily quota is spent (falls through to Groq).
    """
    from app.llm.fallback import FallbackProvider

    s = s or default_settings
    return FallbackProvider([
        _build("gemini", _model_for("gemini", "generator", s), s),
        _build("groq", _model_for("groq", "generator", s), s),
    ])


def get_ondemand_verifier(s: Settings | None = None) -> LLMProvider:
    """Cross-check verifier: Groq first (independent of the Gemini generator),
    Gemini fallback. Keeps the re-solve on a different model when possible."""
    from app.llm.fallback import FallbackProvider

    s = s or default_settings
    return FallbackProvider([
        _build("groq", _model_for("groq", "verifier", s), s),
        _build("gemini", _model_for("gemini", "verifier", s), s),
    ])


def get_embedder(s: Settings | None = None) -> LLMProvider:
    s = s or default_settings
    name = s.llm_embedding_provider
    model = s.gemini_embedding_model if name == "gemini" else ""
    return _build(name, model, s)
