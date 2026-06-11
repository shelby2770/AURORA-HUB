"""Application settings, loaded from environment / backend/.env (Pydantic v2)."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "aurora_hub"

    # CORS
    cors_origins: str = "http://localhost:3000,capacitor://localhost,http://localhost"

    # LLM providers (authoring plane only). gemini | groq | claude.
    # Default stack: Gemini generates + embeds, Groq cross-checks (different
    # provider for an independent cold re-solve). Embeddings must be gemini —
    # neither Groq nor Claude exposes an embeddings API.
    llm_generator_provider: str = "gemini"
    llm_verifier_provider: str = "groq"
    llm_embedding_provider: str = "gemini"

    gemini_api_key: str = ""
    groq_api_key: str = ""
    anthropic_api_key: str = ""

    gemini_generation_model: str = "gemini-2.5-pro"
    gemini_embedding_model: str = "text-embedding-004"
    groq_generation_model: str = "llama-3.3-70b-versatile"
    groq_verifier_model: str = "llama-3.3-70b-versatile"
    claude_generation_model: str = "claude-opus-4-8"
    claude_verifier_model: str = "claude-opus-4-8"

    # Dedup
    dedup_similarity_threshold: float = 0.92

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
