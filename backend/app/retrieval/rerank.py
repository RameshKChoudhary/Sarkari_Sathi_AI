"""Cross-encoder reranking (bge-reranker-v2-m3)."""
from __future__ import annotations

import logging
from typing import Protocol

from ..models.schemas import SearchHit
from .dense import EmbedderUnavailable

logger = logging.getLogger(__name__)


class Reranker(Protocol):
    name: str

    def rerank(self, query: str, hits: list[SearchHit], top_k: int) -> list[SearchHit]: ...


class CrossEncoderReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", device: str | None = None) -> None:
        self.name = model_name
        try:
            from sentence_transformers import CrossEncoder

            self.model = CrossEncoder(model_name, device=device)
        except Exception as exc:
            raise EmbedderUnavailable(f"cannot load reranker {model_name}: {exc}") from exc

    def rerank(self, query: str, hits: list[SearchHit], top_k: int) -> list[SearchHit]:
        if not hits:
            return hits
        pairs = [(query, h.chunk.retrieval_text) for h in hits]
        scores = self.model.predict(pairs, show_progress_bar=False)
        rescored = []
        for h, s in zip(hits, scores):
            h2 = h.model_copy(deep=True)
            h2.scores["rerank"] = float(s)
            h2.score = float(s)
            rescored.append(h2)
        rescored.sort(key=lambda h: -h.score)
        for i, h in enumerate(rescored, 1):
            h.rank = i
        return rescored[:top_k]


def create_reranker(name: str) -> Reranker:
    return CrossEncoderReranker(name)
