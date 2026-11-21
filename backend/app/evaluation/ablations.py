"""Experiment specifications for the ablations and how to build a Retriever for each."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..models.schemas import Chunk
from ..retrieval.dense import EmbedderUnavailable, create_embedder
from ..retrieval.expansion import QueryExpander
from ..retrieval.rerank import create_reranker
from ..retrieval.retriever import RetrievalConfig, Retriever
from ..retrieval.translate import DictTranslator, LexiconTranslator
from .golden import GoldenItem

logger = logging.getLogger(__name__)


@dataclass
class Spec:
    name: str
    group: str
    mode: str = "hybrid_lex"
    chunking: str = "structure"
    strategy: str = "native"
    expand: bool = False
    boost: float = 0.0
    embed: Optional[str] = None  # bge-m3 | multilingual-e5 | labse | offline-lsa
    rerank: bool = False
    translator: Optional[str] = None  # lexicon | oracle
    note: str = ""


SPECS: list[Spec] = [
    # --- BM25 vs char-n-gram BM25 vs dense vs hybrid (native multilingual, no translation)
    Spec("BM25 (words)", "method", mode="bm25"),
    Spec("Char n-gram BM25 (3-5)", "method", mode="ngram"),
    Spec("BM25 + n-gram BM25 (RRF)", "method", mode="hybrid_lex"),
    Spec("Dense: offline LSA (char n-gram, NOT neural)", "method", mode="dense", embed="offline-lsa",
         note="monolingual lexical baseline; cannot bridge scripts"),
    Spec("Hybrid: BM25 + n-gram + offline LSA (RRF)", "method", mode="hybrid", embed="offline-lsa"),
    # --- embedding models (need Hugging Face weights)
    Spec("Dense: BGE-M3", "embedding", mode="dense", embed="bge-m3"),
    Spec("Dense: multilingual-E5-base", "embedding", mode="dense", embed="multilingual-e5"),
    Spec("Dense: LaBSE", "embedding", mode="dense", embed="labse"),
    Spec("Hybrid: BM25 + n-gram + BGE-M3 (RRF)", "embedding", mode="hybrid", embed="bge-m3"),
    # --- reranking
    Spec("Hybrid (lexical) + bge-reranker-v2-m3", "rerank", mode="hybrid_lex", rerank=True),
    Spec("Hybrid (BM25+n-gram+BGE-M3) + bge-reranker-v2-m3", "rerank", mode="hybrid", embed="bge-m3", rerank=True),
    # --- cross-lingual strategies (A-D); reference = BM25 + n-gram, native
    Spec("A: native (reference)", "strategy", mode="hybrid_lex"),
    Spec("A + lexicon query expansion", "strategy", mode="hybrid_lex", expand=True),
    Spec("A + expansion + section-intent boost 0.25 (weight chosen on dev split)", "strategy", mode="hybrid_lex", expand=True, boost=0.25),
    Spec("B: translate query (lexicon translator)", "strategy", mode="hybrid_lex", strategy="translate_query", translator="lexicon"),
    Spec("B: translate query (ORACLE = gold English question)", "strategy", mode="hybrid_lex", strategy="translate_query", translator="oracle",
         note="upper bound for machine translation"),
    Spec("C: translate docs to English (ORACLE = English sibling passage)", "strategy", mode="hybrid_lex", strategy="translate_docs", translator="oracle",
         note="upper bound for machine translation"),
    Spec("D: index original + translated (ORACLE)", "strategy", mode="hybrid_lex", strategy="index_both", translator="oracle",
         note="upper bound for machine translation"),
    Spec("B+C: translate query and docs (ORACLE)", "strategy", mode="hybrid_lex", strategy="translate_query+translate_docs", translator="oracle",
         note="upper bound for machine translation"),
    # --- chunking
    Spec("Structure-aware chunks", "chunking", mode="hybrid_lex", chunking="structure"),
    Spec("Fixed-size chunks (350 chars, 60 overlap)", "chunking", mode="hybrid_lex", chunking="fixed"),
    Spec("Structure-aware chunks + n-gram only", "chunking", mode="ngram", chunking="structure"),
    Spec("Fixed-size chunks + n-gram only", "chunking", mode="ngram", chunking="fixed"),
]


class NotRun(RuntimeError):
    """Experiment could not run in this environment (reason in the message)."""


def oracle_translator(chunks: list[Chunk], items: list[GoldenItem]) -> DictTranslator:
    """Translations taken from the human-written parallel texts (NOT machine translation):
    query -> gold English question; non-English passage -> its English sibling."""
    en = {(c.scheme_id, c.section_type): c.retrieval_text for c in chunks if c.language == "en"}
    mapping = {q.question: q.question_en for q in items}
    for c in chunks:
        if c.language != "en" and (c.scheme_id, c.section_type) in en:
            mapping[c.retrieval_text] = en[(c.scheme_id, c.section_type)]
    return DictTranslator(mapping, name="oracle-parallel-text")


class Builder:
    def __init__(self, chunk_sets: dict[str, list[Chunk]], expander: QueryExpander, items: list[GoldenItem],
                 cache_dir: Optional[Path] = None) -> None:
        self.chunk_sets, self.expander, self.items, self.cache_dir = chunk_sets, expander, items, cache_dir
        self._embedders: dict[str, object] = {}
        self._rerankers: dict[str, object] = {}

    def _embedder(self, name: str):
        if name not in self._embedders:
            try:
                self._embedders[name] = create_embedder(name, cache_dir=self.cache_dir)
            except EmbedderUnavailable as exc:
                self._embedders[name] = exc
        v = self._embedders[name]
        if isinstance(v, Exception):
            raise NotRun(f"embedding model unavailable: {v}")
        return v

    def _reranker(self):
        if "r" not in self._rerankers:
            try:
                self._rerankers["r"] = create_reranker("BAAI/bge-reranker-v2-m3")
            except EmbedderUnavailable as exc:
                self._rerankers["r"] = exc
        v = self._rerankers["r"]
        if isinstance(v, Exception):
            raise NotRun(f"reranker unavailable: {v}")
        return v

    def build(self, spec: Spec) -> tuple[Retriever, list[Chunk]]:
        chunks = self.chunk_sets[spec.chunking]
        cfg = RetrievalConfig(mode=spec.mode, strategy=spec.strategy, expand_query=spec.expand, rerank=spec.rerank,
                              section_boost=spec.boost)
        translator = None
        if spec.translator == "lexicon":
            translator = LexiconTranslator(self.expander)
        elif spec.translator == "oracle":
            if spec.chunking != "structure":
                raise NotRun("oracle document translation needs parallel structure chunks")
            translator = oracle_translator(chunks, self.items)
        embedder = self._embedder(spec.embed) if spec.embed else None
        reranker = self._reranker() if spec.rerank else None
        r = Retriever(chunks, cfg, embedder=embedder, reranker=reranker, translator=translator,
                      expander=self.expander if (spec.expand or spec.boost > 0) else None)  # type: ignore[arg-type]
        return r, chunks
