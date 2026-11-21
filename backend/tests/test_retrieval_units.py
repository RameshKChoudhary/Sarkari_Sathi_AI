import numpy as np
import pytest

from app.models.schemas import Chunk, Filters
from app.retrieval.dense import DenseIndex, OfflineLSAEmbedder
from app.retrieval.expansion import QueryExpander
from app.retrieval.fusion import rrf
from app.retrieval.lexical import ngram_bm25, word_bm25
from app.retrieval.retriever import RetrievalConfig, Retriever
from app.retrieval.translate import DictTranslator


def mk(i, text, lang="en", sec="benefits", scheme="s1"):
    return Chunk(chunk_id=f"{scheme}.{lang}:{i}", doc_id=f"{scheme}.{lang}", scheme_id=scheme, scheme_name=scheme.upper(),
                 level="central", language=lang, source_url="https://x", publication_date=None, doc_ref="ref",
                 section_type=sec, text=text, char_start=0, char_end=len(text), chunking="structure")


CHUNKS = [
    mk(1, "Farmers receive 6000 rupees per year in three instalments", "en", "benefits", "kisan"),
    mk(2, "Women aged 21 to 65 years are eligible", "en", "eligibility", "bahin"),
    mk(3, "किसानों को हर साल 6000 रुपये मिलते हैं", "hi", "benefits", "kisan"),
    mk(4, "शेतकऱ्यांना दरवर्षी ६००० रुपये मिळतात", "mr", "benefits", "kisan"),
]


def test_rrf_orders_and_is_deterministic():
    out = rrf([["a", "b", "c"], ["b", "a", "d"]], k=60)
    assert [x for x, _ in out][:2] == ["a", "b"] or [x for x, _ in out][:2] == ["b", "a"]
    assert out == rrf([["a", "b", "c"], ["b", "a", "d"]], k=60)
    assert dict(out)["a"] == pytest.approx(1 / 61 + 1 / 62)


def test_bm25_prefers_matching_doc():
    idx = word_bm25([c.retrieval_text for c in CHUNKS])
    assert int(np.argmax(idx.scores("women eligible"))) == 1


def test_ngram_bm25_handles_inflection():
    idx = ngram_bm25([c.retrieval_text for c in CHUNKS])
    assert int(np.argmax(idx.scores("शेतकऱ्यांना रुपये"))) == 3


def test_dense_lsa_roundtrip():
    emb = OfflineLSAEmbedder(dim=8)
    vecs = emb.encode_passages([c.retrieval_text for c in CHUNKS])
    di = DenseIndex(vecs)
    assert di.scores(emb.encode_queries(["women eligible 21 65"])[0]).argmax() == 1


def test_retriever_modes_and_filters():
    for mode in ("bm25", "ngram", "hybrid_lex"):
        r = Retriever(CHUNKS, RetrievalConfig(mode=mode))
        hits = r.search("farmers 6000 per year", k=2, query_lang="en")
        assert hits[0].chunk.scheme_id == "kisan"
    r = Retriever(CHUNKS, RetrievalConfig(mode="hybrid_lex"))
    hits = r.search("6000", k=5, filters=Filters(languages=["hi"]), query_lang="en")
    assert hits and all(h.chunk.language == "hi" for h in hits)


def test_translate_query_strategy_uses_translator():
    tr = DictTranslator({"किसान को कितना मिलता है": "farmers receive 6000 rupees per year"})
    r = Retriever(CHUNKS, RetrievalConfig(mode="bm25", strategy="translate_query"), translator=tr)
    hits = r.search("किसान को कितना मिलता है", k=1, filters=Filters(languages=["en"]), query_lang="hi")
    assert hits[0].chunk.chunk_id == "kisan.en:1"


def test_translate_strategy_without_translator_fails_loudly():
    with pytest.raises(Exception):
        Retriever(CHUNKS, RetrievalConfig(mode="bm25", strategy="translate_query"))


def test_expander_and_intents(tmp_path):
    import json
    p = tmp_path / "lex.json"
    p.write_text(json.dumps({"groups": [
        {"id": "concept:apply", "triggers": ["apply", "अर्ज"], "terms": ["apply", "अर्ज"], "en": ["apply"]},
        {"id": "scheme:x", "triggers": ["ladki bahin"], "terms": ["लाडकी बहीण"], "en": ["Ladki Bahin"]}]}), encoding="utf-8")
    ex = QueryExpander.from_file(p)
    assert "scheme:x" in ex.matched_groups("ladki bahin yojana sathi apply kasa karaycha?")
    assert ex.intent_sections("how to apply") == {"how_to_apply"}
    assert "लाडकी बहीण" in ex.expand("ladki bahin")


def test_fake_dense_embedder_with_hybrid():
    class Fake:
        name = "fake"
        def encode_queries(self, t): return self._e(t)
        def encode_passages(self, t): return self._e(t)
        @staticmethod
        def _e(texts):
            m = np.array([[1.0 if "6000" in x else 0.0, 1.0 if "21" in x else 0.0] for x in texts]) + 1e-3
            return m / np.linalg.norm(m, axis=1, keepdims=True)
    r = Retriever(CHUNKS, RetrievalConfig(mode="hybrid"), embedder=Fake())
    assert r.search("6000", k=1, query_lang="en")[0].chunk.scheme_id == "kisan"
