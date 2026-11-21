"""Reciprocal Rank Fusion."""
from __future__ import annotations

from collections import defaultdict
from typing import Hashable, Sequence


def rrf(rankings: Sequence[Sequence[Hashable]], k: int = 60, weights: Sequence[float] | None = None) -> list[tuple[Hashable, float]]:
    """score(d) = sum_i w_i / (k + rank_i(d)), ranks are 1-based. Returns items by descending score.
    Ties are broken by first appearance so the output is deterministic."""
    weights = weights or [1.0] * len(rankings)
    scores: dict[Hashable, float] = defaultdict(float)
    first_seen: dict[Hashable, int] = {}
    for w, ranking in zip(weights, rankings):
        for r, item in enumerate(ranking, start=1):
            scores[item] += w / (k + r)
            first_seen.setdefault(item, len(first_seen))
    return sorted(scores.items(), key=lambda kv: (-kv[1], first_seen[kv[0]]))
