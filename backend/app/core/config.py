"""Application settings, loaded from environment variables / .env (never hardcode secrets)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]  # repo root (backend/app/core/config.py -> ../../..)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", str(ROOT / ".env")), env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "SarkariSathi AI"
    data_dir: Path = ROOT / "data"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    static_dir: Path | None = None

    # LLM
    llm_provider: Literal["auto", "groq", "openai_compat", "extractive"] = "auto"
    groq_api_key: str = ""
    llm_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_timeout_s: float = 45.0
    llm_query_rewrite: bool = True

    # Retrieval
    retrieval_mode: Literal["bm25", "ngram", "dense", "hybrid", "hybrid_lex"] = "hybrid"
    embed_model: str = "bge-m3"
    translation_strategy: str = "native"
    query_expansion: bool = True
    section_boost: float = 0.25  # needs the lexicon; boosts the section the question asks about
    use_reranker: bool = False
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    chunking: Literal["structure", "fixed"] = "structure"
    top_k: int = Field(5, ge=1, le=10)
    candidate_k: int = 30
    rrf_k: int = 60

    # Extractive (offline) answer composer
    extractive_passages: int = Field(1, ge=1, le=3)  # 1 = most precise citations (chosen on dev split)
    extractive_score_ratio: float = 0.0  # extra passage must score >= ratio x top passage

    # Relevance gate (heuristic, used when no LLM / reranker is available)
    min_query_coverage: float = 0.34
    rerank_relevance_threshold: float = 0.0  # bge-reranker logits; > 0 means "probably relevant"

    # OCR
    tessdata_dir: Path | None = None
    ocr_dpi: int = 300

    cache_ttl_s: int = 600

    @property
    def resolved_llm_provider(self) -> str:
        if self.llm_provider == "auto":
            return "groq" if self.groq_api_key else "extractive"
        return self.llm_provider

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def eval_dir(self) -> Path:
        return self.data_dir / "evaluation"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
