import pytest

from app.evaluation.metrics import key_fact_recall, ndcg_at_k, recall_at_k, reciprocal_rank
from app.generation.relevance import query_coverage
from app.generation.verify import cited_ids, verify_answer


def test_ranking_metrics():
    assert recall_at_k([False, False, True], 5) == 1.0
    assert recall_at_k([False, False, True], 2) == 0.0
    assert reciprocal_rank([False, True]) == 0.5
    assert reciprocal_rank([False] * 10) == 0.0
    assert ndcg_at_k([True, False, False], 10, 1) == pytest.approx(1.0)
    assert ndcg_at_k([False, True], 10, 1) == pytest.approx(1 / 1.5849625, rel=1e-3)
    assert ndcg_at_k([True], 10, 3) < 1.0


def test_key_fact_recall_normalises_numbers_and_scripts():
    assert key_fact_recall("दरवर्षी ₹६,००० मिळतात", [["6000"]]) == 1.0
    assert key_fact_recall("Rs 6,000 in 3 parts", [["6000"], ["aadhaar"]]) == 0.5
    assert key_fact_recall("anything", []) == 1.0


PASSAGES = {1: "Farmers receive Rs 6,000 per year in three instalments of Rs 2,000.", 2: "Apply at the Common Service Centre."}


def test_verify_keeps_supported_and_drops_invented():
    ans = ("Farmers receive Rs 6,000 per year in three instalments. [1]\n"
           "Farmers also receive Rs 9,000 as a bonus. [1]\n"          # invented number
           "They can apply at the Common Service Centre. [2]\n"
           "Payment is made every Monday. [7]\n"                       # bad citation id
           "The scheme was launched in 1999.")                         # uncited claim
    cleaned, rep = verify_answer(ans, PASSAGES)
    assert "6,000" in cleaned and "Common Service Centre" in cleaned
    assert "9,000" not in cleaned and "Monday" not in cleaned and "1999" not in cleaned
    assert rep.ok and rep.kept_sentences == 2 and 7 in rep.invalid_citations and len(rep.removed) == 3


def test_verify_all_unsupported_is_not_ok():
    _, rep = verify_answer("The moon is made of cheese. [1]", PASSAGES)
    assert not rep.ok


def test_marker_after_period_is_not_split_off():
    cleaned, rep = verify_answer("Apply at the Common Service Centre. [2]", PASSAGES)
    assert rep.ok and cited_ids(cleaned) == {2}


def test_query_coverage_penalises_unknown_words():
    from app.models.schemas import Chunk, SearchHit
    c = Chunk(chunk_id="a", doc_id="d", scheme_id="s", scheme_name="PM Kisan", level="central", language="en",
              source_url="u", publication_date=None, doc_ref="r", section_type="benefits",
              text="Farmers receive 6000 rupees per year", char_start=0, char_end=10, chunking="structure")
    hits = [SearchHit(chunk=c, score=1.0, scores={})]
    full, _ = query_coverage("farmers receive 6000 per year", hits, None)
    off, unc = query_coverage("capital of France", hits, None)
    assert full > 0.9 and off < 0.2 and "france" in unc
