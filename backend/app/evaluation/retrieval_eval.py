"""Retrieval experiments: per-question ranking, the query-language x document-language matrix,
and the ablation configurations."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Optional

from ..models.schemas import Chunk, Filters
from ..retrieval.retriever import Retriever
from .golden import GoldenItem
from .metrics import mean, ndcg_at_k, recall_at_k, reciprocal_rank

logger = logging.getLogger(__name__)
QUERY_LANGS = ["en", "hi", "mr", "mr_roman"]
DOC_LANGS = ["en", "hi", "mr"]


@dataclass
class QResult:
    qid: str
    language: str
    doc_lang: Optional[str]
    rels: list[bool]
    n_relevant: int


Spans = dict[tuple[str, str], tuple[int, int]]  # (doc_id, section) -> character span in the document text


def build_spans(structure_chunks: list[Chunk]) -> Spans:
    """Gold section spans, taken from the structure-aware chunks (they follow section boundaries)."""
    spans: Spans = {}
    for c in structure_chunks:
        lo, hi = spans.get((c.doc_id, c.section_type), (c.char_start, c.char_end))
        spans[(c.doc_id, c.section_type)] = (min(lo, c.char_start), max(hi, c.char_end))
    return spans


def _is_rel(c: Chunk, q: GoldenItem, spans: Spans) -> bool:
    """Structure chunks: same scheme + section. Fixed-size chunks do not follow sections, so a
    chunk counts as relevant when it overlaps the gold section span by at least half of the
    smaller of (chunk, gold section) - i.e. it contains half the evidence or is mostly evidence."""
    if q.gold is None or c.scheme_id != q.gold.scheme_id:
        return False
    if c.chunking == "structure":
        return c.section_type == q.gold.section
    span = spans.get((c.doc_id, q.gold.section))
    if span is None:
        return False
    ov = min(c.char_end, span[1]) - max(c.char_start, span[0])
    return ov > 0 and ov / max(1, min(c.char_end - c.char_start, span[1] - span[0])) >= 0.5


def run_questions(retriever: Retriever, items: list[GoldenItem], chunks: list[Chunk], doc_lang: Optional[str],
                  spans: Spans, depth: int = 10) -> list[QResult]:
    """Retrieve for every answerable question. With `doc_lang`, the search is restricted to
    documents in that language (gold = the same section in that language)."""
    out: list[QResult] = []
    flt = Filters(languages=[doc_lang]) if doc_lang else None  # type: ignore[list-item]
    for q in items:
        if not q.answerable:
            continue
        hits = retriever.search(q.question, k=depth, filters=flt, query_lang=q.query_lang)
        rels = [_is_rel(h.chunk, q, spans) for h in hits]
        n_rel = sum(1 for c in chunks if _is_rel(c, q, spans) and (doc_lang is None or c.language == doc_lang))
        out.append(QResult(q.id, q.language, doc_lang, rels, n_rel))
    return out


def aggregate(results: list[QResult], k: int = 5) -> dict:
    return {
        "n": len(results),
        f"recall@{k}": mean([recall_at_k(r.rels, k) for r in results]),
        "mrr": mean([reciprocal_rank(r.rels, 10) for r in results]),
        "ndcg@10": mean([ndcg_at_k(r.rels, 10, r.n_relevant) for r in results]),
    }


def matrix(retriever: Retriever, items: list[GoldenItem], chunks: list[Chunk], spans: Spans) -> dict:
    """{query_lang: {doc_lang: metrics}} plus a pooled column ('all') searching every document."""
    out: dict = {}
    for dl in DOC_LANGS + [None]:
        res = run_questions(retriever, items, chunks, dl, spans)
        for ql in QUERY_LANGS:
            sub = [r for r in res if r.language == ql]
            out.setdefault(ql, {})[dl or "all"] = aggregate(sub)
    return out


def overall(retriever: Retriever, items: list[GoldenItem], chunks: list[Chunk], spans: Spans) -> dict:
    """Metrics over all answerable questions: pooled corpus (any language) and per query language."""
    res = run_questions(retriever, items, chunks, None, spans)
    d = {"all": aggregate(res)}
    for ql in QUERY_LANGS:
        d[ql] = aggregate([r for r in res if r.language == ql])
    return d


def fmt(m: dict) -> str:
    if not m or m.get("n", 0) == 0 or m["recall@5"] is None:
        return "n/a"
    return f"{m['recall@5']:.2f} / {m['mrr']:.2f} / {m['ndcg@10']:.2f}"


def matrix_markdown(mat: dict, title: str) -> str:
    lines = [f"**{title}** (cells: Recall@5 / MRR / nDCG@10; n = answerable questions per row)", "",
             "| Query language | English docs | Hindi docs | Marathi docs | All docs pooled |", "|---|---|---|---|---|"]
    names = {"en": "English", "hi": "Hindi", "mr": "Marathi", "mr_roman": "Marathi (romanised)"}
    for ql in QUERY_LANGS:
        row = mat.get(ql, {})
        n = row.get("en", {}).get("n", 0)
        lines.append(f"| {names[ql]} (n={n}) | " + " | ".join(fmt(row.get(dl, {})) for dl in DOC_LANGS + ["all"]) + " |")
    return "\n".join(lines)
