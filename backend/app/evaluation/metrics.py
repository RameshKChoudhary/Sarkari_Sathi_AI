"""Ranking and answer metrics (pure functions, unit-tested)."""
from __future__ import annotations

import math
from typing import Sequence

from ..retrieval.tokenize import normalize_for_match


def recall_at_k(rels: Sequence[bool], k: int = 5) -> float:
    """1.0 if at least one relevant passage is in the top-k else 0.0 (every question has a
    single gold section, so recall@k equals hit-rate@k)."""
    return 1.0 if any(rels[:k]) else 0.0


def reciprocal_rank(rels: Sequence[bool], depth: int = 10) -> float:
    for i, r in enumerate(rels[:depth], start=1):
        if r:
            return 1.0 / i
    return 0.0


def ndcg_at_k(rels: Sequence[bool], k: int = 10, n_relevant: int | None = None) -> float:
    """Binary-relevance nDCG@k. `n_relevant` = number of relevant passages that exist (for the
    ideal ranking); defaults to the number seen in `rels`, capped at k."""
    dcg = sum(1.0 / math.log2(i + 2) for i, r in enumerate(rels[:k]) if r)
    n = n_relevant if n_relevant is not None else sum(bool(r) for r in rels)
    ideal = sum(1.0 / math.log2(i + 2) for i in range(min(max(n, 0), k)))
    return dcg / ideal if ideal > 0 else 0.0


def key_fact_recall(answer: str, key_facts: Sequence[Sequence[str]]) -> float:
    """Share of key facts present in the answer; a fact is a list of alternative strings."""
    if not key_facts:
        return 1.0
    text = normalize_for_match(answer)
    hit = sum(1 for alts in key_facts if any(normalize_for_match(a) in text for a in alts))
    return hit / len(key_facts)


def mean(xs: Sequence[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None
