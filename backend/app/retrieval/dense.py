"""Dense retrieval: embedders (BGE-M3, multilingual-E5, LaBSE, offline LSA) + FAISS index."""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Protocol

import numpy as np

logger = logging.getLogger(__name__)


class EmbedderUnavailable(RuntimeError):
    """Raised when a model cannot be loaded (package missing, no network, no weights)."""


class Embedder(Protocol):
    name: str

    def encode_queries(self, texts: list[str]) -> np.ndarray: ...
    def encode_passages(self, texts: list[str]) -> np.ndarray: ...


# name -> (huggingface id, query prefix, passage prefix)
MODEL_REGISTRY: dict[str, tuple[str, str, str]] = {
    "bge-m3": ("BAAI/bge-m3", "", ""),
    "multilingual-e5": ("intfloat/multilingual-e5-base", "query: ", "passage: "),
    "multilingual-e5-large": ("intfloat/multilingual-e5-large", "query: ", "passage: "),
    "labse": ("sentence-transformers/LaBSE", "", ""),
}


def _normalize(m: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(m, axis=1, keepdims=True)
    return m / np.clip(n, 1e-12, None)


class SentenceTransformerEmbedder:
    def __init__(self, name: str, device: Optional[str] = None, batch_size: int = 16,
                 cache_dir: Optional[Path] = None) -> None:
        if name not in MODEL_REGISTRY:
            raise EmbedderUnavailable(f"unknown embedding model {name!r}; choose from {sorted(MODEL_REGISTRY)}")
        self.name = name
        self.hf_id, self.q_prefix, self.p_prefix = MODEL_REGISTRY[name]
        self.batch_size = batch_size
        self.cache_dir = cache_dir
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(self.hf_id, device=device)
        except Exception as exc:
            raise EmbedderUnavailable(f"cannot load {self.hf_id}: {exc}") from exc

    def _encode(self, texts: list[str]) -> np.ndarray:
        v = self.model.encode(texts, batch_size=self.batch_size, show_progress_bar=False, convert_to_numpy=True)
        return _normalize(np.asarray(v, dtype="float32"))

    def encode_queries(self, texts: list[str]) -> np.ndarray:
        return self._encode([self.q_prefix + t for t in texts])

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        """Passage encoding with an on-disk cache keyed by (model, text)."""
        prefixed = [self.p_prefix + t for t in texts]
        if not self.cache_dir:
            return self._encode(prefixed)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        idx_f, vec_f = self.cache_dir / f"{self.name}.json", self.cache_dir / f"{self.name}.npy"
        keys = [hashlib.sha1(t.encode("utf-8")).hexdigest() for t in prefixed]
        cache: dict[str, int] = json.loads(idx_f.read_text()) if idx_f.exists() else {}
        mat = np.load(vec_f) if vec_f.exists() else np.zeros((0, 1), dtype="float32")
        missing = [i for i, k in enumerate(keys) if k not in cache]
        if missing:
            new = self._encode([prefixed[i] for i in missing])
            if mat.shape[0] == 0:
                mat = new
            else:
                mat = np.vstack([mat, new])
            base = len(cache)
            for j, i in enumerate(missing):
                cache[keys[i]] = base + j
            np.save(vec_f, mat)
            idx_f.write_text(json.dumps(cache))
        return mat[[cache[k] for k in keys]]


class OfflineLSAEmbedder:
    """NOT a semantic cross-lingual model. TF-IDF over character n-grams + truncated SVD (LSA).
    Exists so that the dense/FAISS/RRF plumbing can be run and measured with no model download.
    Because it only sees surface forms it cannot bridge Latin and Devanagari scripts."""

    name = "offline-lsa"

    def __init__(self, dim: int = 128) -> None:
        self.dim = dim
        self._vec = None
        self._svd = None

    def _fit(self, texts: list[str]) -> None:
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer

        from .tokenize import normalize_for_match

        self._vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True,
                                    preprocessor=normalize_for_match, min_df=1)
        x = self._vec.fit_transform(texts)
        k = max(2, min(self.dim, x.shape[0] - 1, x.shape[1] - 1))
        self._svd = TruncatedSVD(n_components=k, random_state=0)
        self._svd.fit(x)

    def _project(self, texts: list[str]) -> np.ndarray:
        assert self._vec is not None and self._svd is not None
        return _normalize(np.asarray(self._svd.transform(self._vec.transform(texts)), dtype="float32"))

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        self._fit(texts)
        return self._project(texts)

    def encode_queries(self, texts: list[str]) -> np.ndarray:
        if self._vec is None:
            raise RuntimeError("encode_passages must be called first")
        return self._project(texts)


def create_embedder(name: str, cache_dir: Optional[Path] = None) -> Embedder:
    if name == "offline-lsa":
        return OfflineLSAEmbedder()
    return SentenceTransformerEmbedder(name, cache_dir=cache_dir)


class DenseIndex:
    """Exact inner-product search (cosine, vectors are L2-normalised) using FAISS."""

    def __init__(self, vectors: np.ndarray) -> None:
        self.vectors = np.ascontiguousarray(vectors, dtype="float32")
        self.n = self.vectors.shape[0]
        try:
            import faiss

            self._index = faiss.IndexFlatIP(self.vectors.shape[1])
            self._index.add(self.vectors)
            self.backend = "faiss"
        except Exception:  # pragma: no cover - faiss missing
            self._index = None
            self.backend = "numpy"

    def scores(self, qvec: np.ndarray) -> np.ndarray:
        """Cosine score for every indexed item (corpus is small; exact search over all)."""
        q = np.ascontiguousarray(qvec.reshape(1, -1), dtype="float32")
        if self._index is not None:
            sims, ids = self._index.search(q, self.n)
            out = np.full(self.n, -1.0, dtype="float32")
            out[ids[0]] = sims[0]
            return out
        return (self.vectors @ q.T).ravel()
