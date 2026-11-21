"""Application service: loads the corpus, builds the configured retriever (degrading
gracefully when optional models are unavailable), runs the LangGraph pipeline, and caches."""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Optional

from ..core.config import Settings
from ..generation.context import RagContext
import time
from typing import Iterator

from ..generation.graph import build_graph, run_chat, state_to_response
from ..generation.llm import create_llm
from ..ingestion.pipeline import read_chunks
from ..models.schemas import (ChatRequest, ChatResponse, Chunk, Filters, RetrieveRequest, SchemeSummary, SearchHit)
from ..retrieval.dense import EmbedderUnavailable, create_embedder
from ..retrieval.expansion import QueryExpander
from ..retrieval.rerank import create_reranker
from ..retrieval.retriever import RetrievalConfig, Retriever
from ..retrieval.translate import LexiconTranslator, LLMTranslator
from .cache import TTLCache

logger = logging.getLogger(__name__)


class CorpusNotReady(RuntimeError):
    pass


class RagService:
    def __init__(self, settings: Settings) -> None:
        self.s = settings
        path = settings.processed_dir / f"chunks_{settings.chunking}.jsonl"
        if not path.exists():
            raise CorpusNotReady(f"{path} not found. Run: python backend/scripts/setup_data.py (or ingest.py)")
        all_chunks = read_chunks(path)
        # 'overview' chunks (title block / metadata) feed the scheme catalog only; they are
        # not retrieval targets because they would match every query that names the scheme.
        self.chunks: list[Chunk] = [c for c in all_chunks if c.section_type != "overview"]
        lex = settings.raw_dir / "lexicon.json"
        self.expander = QueryExpander.from_file(lex) if lex.exists() else None
        self.degraded: list[str] = []
        self.llm = create_llm(settings)
        self._retrievers: dict[tuple, Retriever] = {}
        self._lock = threading.Lock()
        self._embedder = None
        self._reranker = None
        self.default_cfg = self._config_from_settings()
        self.cache = TTLCache(settings.cache_ttl_s)
        self.ctx = RagContext(settings, self.chunks, lambda: self.get_retriever(self.default_cfg), self.llm,
                              self.expander, self.degraded)
        self.graph = build_graph(self.ctx)
        self.catalog: list[SchemeSummary] = self._load_catalog()
        self.get_retriever(self.default_cfg)  # build eagerly so the first request is fast
        logger.info("RagService ready: %d chunks, mode=%s, llm=%s, degraded=%s", len(self.chunks),
                    self.default_cfg.mode, self.s.resolved_llm_provider if self.llm else "extractive", self.degraded)

    # ---------------------------------------------------------------- config
    def _config_from_settings(self) -> RetrievalConfig:
        s = self.s
        mode = s.retrieval_mode
        if "dense" in mode or mode == "hybrid":
            try:
                self._embedder = create_embedder(s.embed_model, cache_dir=s.processed_dir / "embeddings")
            except EmbedderUnavailable as exc:
                fallback = "hybrid_lex" if mode == "hybrid" else "ngram"
                self.degraded.append(f"embedding model '{s.embed_model}' unavailable ({exc}); using '{fallback}'")
                logger.warning(self.degraded[-1])
                mode = fallback
        rerank = s.use_reranker
        if rerank:
            try:
                self._reranker = create_reranker(s.reranker_model)
            except EmbedderUnavailable as exc:
                self.degraded.append(f"reranker unavailable ({exc}); reranking disabled")
                logger.warning(self.degraded[-1])
                rerank = False
        expand = s.query_expansion and self.expander is not None
        return RetrievalConfig(mode=mode, strategy=s.translation_strategy, expand_query=expand, rerank=rerank,
                               section_boost=s.section_boost if self.expander is not None else 0.0, top_k=s.top_k, candidate_k=s.candidate_k, rrf_k=s.rrf_k)

    def _translator(self, cfg: RetrievalConfig):
        if not (cfg.translate_query or cfg.doc_variant != "original"):
            return None
        if self.llm is not None:
            return LLMTranslator(self.llm, self.s.processed_dir / "translation_cache.json")
        if self.expander is not None and cfg.doc_variant == "original":
            return LexiconTranslator(self.expander)
        raise RuntimeError("translating documents needs an LLM (set GROQ_API_KEY) - no offline document translator")

    def get_retriever(self, cfg: RetrievalConfig) -> Retriever:
        key = (cfg.mode, cfg.strategy, cfg.expand_query, cfg.rerank, cfg.section_boost, cfg.top_k, cfg.candidate_k)
        with self._lock:
            if key not in self._retrievers:
                emb = self._embedder if "dense" in cfg.components else None
                if "dense" in cfg.components and emb is None:
                    emb = create_embedder(self.s.embed_model, cache_dir=self.s.processed_dir / "embeddings")
                self._retrievers[key] = Retriever(
                    self.chunks, cfg, embedder=emb, reranker=self._reranker if cfg.rerank else None,
                    translator=self._translator(cfg),
                    expander=self.expander if (cfg.expand_query or cfg.section_boost > 0) else None)
            return self._retrievers[key]

    # ------------------------------------------------------------------ API
    def chat(self, req: ChatRequest) -> ChatResponse:
        key = (req.query.strip().lower(), req.ui_language, req.top_k,
               req.filters.model_dump_json() if req.filters else None)
        cached = self.cache.get(key)
        if cached is not None:
            out = cached.model_copy(deep=True)
            out.pipeline["cache"] = "hit"
            return out
        resp = run_chat(self.graph, self.ctx, req.query, req.ui_language, req.filters, req.top_k)
        resp.pipeline["cache"] = "miss"
        self.cache.set(key, resp)
        return resp

    def chat_stream(self, req: ChatRequest) -> Iterator[dict]:
        """Yield pipeline events (one per LangGraph node), then the verified answer in small
        pieces, then the full response. The answer is only released after citation
        verification, so this is progressive *delivery* of a verified answer, not token
        streaming straight from the model."""
        t0 = time.perf_counter()
        state: dict = {"query": req.query, "ui_language": req.ui_language, "filters": req.filters,
                       "top_k": req.top_k, "timings_ms": {}, "pipeline": {}}
        cached = self.cache.get((req.query.strip().lower(), req.ui_language, req.top_k,
                                 req.filters.model_dump_json() if req.filters else None))
        if cached is None:
            for update in self.graph.stream(state, stream_mode="updates"):
                for node, delta in update.items():
                    state.update(delta)
                    yield {"event": "stage", "data": {"stage": node, "ms": state["timings_ms"].get(node)}}
            resp = state_to_response(state, self.ctx, (time.perf_counter() - t0) * 1000)
            resp.pipeline["cache"] = "miss"
            self.cache.set((req.query.strip().lower(), req.ui_language, req.top_k,
                            req.filters.model_dump_json() if req.filters else None), resp)
        else:
            resp = cached.model_copy(deep=True)
            resp.pipeline["cache"] = "hit"
            yield {"event": "stage", "data": {"stage": "cache", "ms": 0}}
        yield {"event": "meta", "data": {"language": resp.language, "romanized": resp.romanized, "abstained": resp.abstained}}
        yield {"event": "sources", "data": [x.model_dump() for x in resp.sources]}
        words = resp.answer.split(" ")
        for i in range(0, len(words), 4):
            yield {"event": "token", "data": {"text": " ".join(words[i:i + 4]) + (" " if i + 4 < len(words) else "")}}
            time.sleep(0.015)
        yield {"event": "done", "data": resp.model_dump()}

    def retrieve(self, req: RetrieveRequest) -> list[SearchHit]:
        cfg = RetrievalConfig(**{**self.default_cfg.__dict__, "top_k": req.top_k})
        if req.mode:
            cfg.mode = req.mode
        if req.expand_query is not None:
            cfg.expand_query = req.expand_query and self.expander is not None
        from ..retrieval.lang import detect_language
        lang = detect_language(req.query).language
        return self.get_retriever(cfg).search(req.query, k=req.top_k, filters=req.filters, query_lang=lang)

    def _load_catalog(self) -> list[SchemeSummary]:
        p = self.s.processed_dir / "schemes.json"
        if not p.exists():
            return []
        return [SchemeSummary.model_validate(x) for x in json.loads(p.read_text(encoding="utf-8"))]

    def scheme_detail(self, scheme_id: str) -> Optional[dict]:
        summ = next((c for c in self.catalog if c.scheme_id == scheme_id), None)
        if summ is None:
            return None
        sections: dict[str, dict[str, Chunk]] = {}
        for c in self.chunks:
            if c.scheme_id == scheme_id and c.section_type != "overview":
                sections.setdefault(c.section_type, {})[c.language] = c
        return {"summary": summ.model_dump(),
                "sections": {sec: {lang: ch.model_dump() for lang, ch in by.items()} for sec, by in sections.items()}}

    def health(self) -> dict:
        return {
            "status": "degraded" if self.degraded else "ok", "chunks": len(self.chunks), "schemes": len(self.catalog),
            "retrieval_mode": self.default_cfg.mode, "embed_model": self.s.embed_model if self._embedder else None,
            "llm": (self.s.resolved_llm_provider + ":" + self.s.llm_model) if self.llm else "extractive (offline)",
            "reranker": bool(self._reranker), "degraded": self.degraded, "cache": self.cache.stats(),
            "data_status": sorted({c.data_status for c in self.chunks}),
        }
