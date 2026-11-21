"""BM25 over words and over character n-grams."""
from __future__ import annotations

from typing import Callable

import numpy as np
from rank_bm25 import BM25Okapi

from .tokenize import char_ngram_tokens, word_tokens


class LexicalIndex:
    def __init__(self, texts: list[str], tokenizer: Callable[[str], list[str]], k1: float = 1.5, b: float = 0.75):
        self.tokenizer = tokenizer
        self.n = len(texts)
        docs = [tokenizer(t) or ["∅"] for t in texts]
        self._bm25 = BM25Okapi(docs, k1=k1, b=b)

    def scores(self, query: str) -> np.ndarray:
        q = self.tokenizer(query)
        if not q or self.n == 0:
            return np.zeros(self.n)
        return np.asarray(self._bm25.get_scores(q), dtype=float)


def word_bm25(texts: list[str]) -> LexicalIndex:
    return LexicalIndex(texts, word_tokens)


def ngram_bm25(texts: list[str], n_min: int = 3, n_max: int = 5) -> LexicalIndex:
    return LexicalIndex(texts, lambda t: char_ngram_tokens(t, n_min, n_max))
