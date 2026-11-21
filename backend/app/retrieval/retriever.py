"""Configurable retriever: BM25 / char-n-gram BM25 / dense / hybrid (RRF) / reranking, with the
four cross-lingual strategies (A native, B translate query, C translate docs, D index both)."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from ..models.schemas import Chunk, Filters, SearchHit
from .dense import DenseIndex, Embedder
from .expansion import QueryExpander
from .fusion import rrf
from .lexical import ngram_bm25, word_bm25
from .rerank import Reranker
from .translate import Translator

logger = logging.getLogger(__name__)

MODE_COMPONENTS: dict[str, list[str]] = {
    "bm25": ["bm25"],
    "ngram": ["ngram"],
    "dense": ["dense"],
    "hybrid": ["bm25", "ngram", "dense"],
    "hybrid_lex": ["bm25", "ngram"],
}


@dataclass
class RetrievalConfig:
    mode: str = "hybrid_lex"
    strategy: str = "native"  # tokens joined by '+': native | translate_query | translate_docs | index_both
    expand_query: bool = False
    rerank: bool = False
    top_k: int = 5
    candidate_k: int = 30
    rrf_k: int = 60
    section_boost: float = 0.0  # extra RRF 'votes' for chunks of the section the question asks about

    @property
    def components(self) -> list[str]:
        return MODE_COMPONENTS[self.mode]

    @property
    def translate_query(self) -> bool:
        return "translate_query" in self.strategy.split("+")

    @property
    def doc_variant(self) -> str:
        toks = self.strategy.split("+")
        if "index_both" in toks:
            return "both"
        if "translate_docs" in toks:
            return "translated"
        return "original"


@dataclass
class _Item:
    chunk: Chunk
    text: str
    variant: str  # original | translated


class RetrieverError(RuntimeError):
    pass


class Retriever:
    def __init__(
        self,
        chunks: list[Chunk],
        config: RetrievalConfig,
        embedder: Optional[Embedder] = None,
        reranker: Optional[Reranker] = None,
        translator: Optional[Translator] = None,
        expander: Optional[QueryExpander] = None,
    ) -> None:
        self.chunks = chunks
        self.cfg = config
        self.embedder = embedder
        self.reranker = reranker
        self.translator = translator
        self.expander = expander
        if "dense" in config.components and embedder is None:
            raise RetrieverError(f"mode {config.mode!r} needs an embedder")
        if config.rerank and reranker is None:
            raise RetrieverError("rerank=True needs a reranker")
        if config.section_boost > 0 and expander is None:
            raise RetrieverError("section_boost needs a QueryExpander")
        if config.expand_query and expander is None:
            raise RetrieverError("expand_query=True needs a QueryExpander")
        if (config.translate_query or config.doc_variant != "original") and translator is None:
            raise RetrieverError(f"strategy {config.strategy!r} needs a translator")
        self.items = self._build_items()
        texts = [it.text for it in self.items]
        self._word = word_bm25(texts) if "bm25" in config.components else None
        self._ngram = ngram_bm25(texts) if "ngram" in config.components else None
        self._dense: Optional[DenseIndex] = None
        if "dense" in config.components:
            assert embedder is not None
            self._dense = DenseIndex(embedder.encode_passages(texts))

    # ------------------------------------------------------------------ build
    def _build_items(self) -> list[_Item]:
        variant = self.cfg.doc_variant
        items: list[_Item] = []
        for c in self.chunks:
            if variant in ("original", "both"):
                items.append(_Item(c, c.retrieval_text, "original"))
            if variant in ("translated", "both"):
                assert self.translator is not None
                en = c.retrieval_text if c.language == "en" else self.translator.translate(c.retrieval_text, c.language, "en")
                if variant == "both" and c.language == "en":
                    continue  # identical to the original item
                items.append(_Item(c, en, "translated"))
        return items

    def _mask(self, filters: Optional[Filters]) -> np.ndarray:
        if filters is None or filters.is_empty:
            return np.ones(len(self.items), dtype=bool)
        return np.array([filters.matches(it.chunk) for it in self.items], dtype=bool)

    @staticmethod
    def _rank(scores: np.ndarray, mask: np.ndarray, limit: int, positive_only: bool) -> list[int]:
        idx = np.where(mask & ((scores > 0) if positive_only else True))[0]
        if idx.size == 0:
            return []
        order = idx[np.argsort(-scores[idx], kind="stable")]
        return [int(i) for i in order[:limit]]

    # ----------------------------------------------------------------- search
    def prepare_query(self, query: str, query_lang: Optional[str]) -> tuple[str, str]:
        """Return (lexical_query, dense_query)."""
        q = query
        if self.cfg.translate_query and query_lang not in (None, "en"):
            assert self.translator is not None
            q = self.translator.translate(query, query_lang, "en")
        lex = self.expander.expand(q) if (self.cfg.expand_query and self.expander) else q
        return lex, q

    def search(self, query: str, k: Optional[int] = None, filters: Optional[Filters] = None,
               query_lang: Optional[str] = None) -> list[SearchHit]:
        k = k or self.cfg.top_k
        lex_q, dense_q = self.prepare_query(query, query_lang)
        mask = self._mask(filters)
        limit = len(self.items) if (filters and not filters.is_empty) else max(self.cfg.candidate_k, k)
        raw: dict[str, np.ndarray] = {}
        rankings: dict[str, list[int]] = {}
        if self._word is not None:
            raw["bm25"] = self._word.scores(lex_q)
            rankings["bm25"] = self._rank(raw["bm25"], mask, limit, True)
        if self._ngram is not None:
            raw["ngram"] = self._ngram.scores(lex_q)
            rankings["ngram"] = self._rank(raw["ngram"], mask, limit, True)
        if self._dense is not None:
            assert self.embedder is not None
            raw["dense"] = self._dense.scores(self.embedder.encode_queries([dense_q])[0])
            rankings["dense"] = self._rank(raw["dense"], mask, limit, False)

        fused = rrf([r for r in rankings.values() if r], k=self.cfg.rrf_k)
        if self.cfg.section_boost > 0 and self.expander is not None:
            intents = self.expander.intent_sections(query)
            if intents:
                bonus = self.cfg.section_boost / (self.cfg.rrf_k + 1)
                fused = sorted(
                    ((i, s + (bonus if self.items[int(i)].chunk.section_type in intents else 0.0)) for i, s in fused),  # type: ignore[arg-type]
                    key=lambda kv: -kv[1])
        hits: list[SearchHit] = []
        seen: set[str] = set()
        for item_idx, score in fused:
            chunk = self.items[int(item_idx)].chunk  # type: ignore[arg-type]
            if chunk.chunk_id in seen:
                continue
            seen.add(chunk.chunk_id)
            hits.append(SearchHit(chunk=chunk, score=float(score), rank=len(hits) + 1))
        # attach raw per-component scores/ranks (best variant of each chunk)
        by_chunk: dict[str, list[int]] = {}
        for i, it in enumerate(self.items):
            by_chunk.setdefault(it.chunk.chunk_id, []).append(i)
        for h in hits:
            ids = by_chunk[h.chunk.chunk_id]
            for comp, arr in raw.items():
                h.scores[comp] = float(max(arr[i] for i in ids))
                rk = [rankings[comp].index(i) + 1 for i in ids if i in rankings[comp]]
                if rk:
                    h.ranks[comp] = min(rk)
        pool = hits[: self.cfg.candidate_k]
        if self.cfg.rerank and self.reranker is not None:
            return self.reranker.rerank(query, pool, k)
        return pool[:k]
