"""Step 3 of the graph: is the retrieved evidence sufficient to answer?

Two gates:
* cross-encoder score, when a reranker is configured (bge-reranker logit > threshold);
* otherwise a query-coverage heuristic: the share of the question's content words that are
  either known domain vocabulary (lexicon triggers) or appear in the top passages. Words the
  corpus never mentions ("capital", "France", "2027") stay uncovered and push coverage down.

The heuristic is deliberately simple and transparent; its abstention accuracy on the golden set
is measured and reported (it is not perfect, notably for in-domain questions about facts that
are simply missing from the documents)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..models.schemas import SearchHit
from ..retrieval.expansion import QueryExpander
from ..retrieval.tokenize import stem_match, word_tokens


@dataclass
class Grade:
    relevant: bool
    coverage: float
    method: str
    top_rerank_score: Optional[float] = None
    uncovered: list[str] = field(default_factory=list)


def query_coverage(query: str, hits: list[SearchHit], expander: Optional[QueryExpander], top_n: int = 3) -> tuple[float, list[str]]:
    toks = [t for t in dict.fromkeys(word_tokens(query)) if len(t) > 1]
    if not toks or not hits:
        return 0.0, toks
    known = expander.matched_trigger_tokens(query) if expander else set()
    ptoks: list[str] = []
    for h in hits[:top_n]:
        ptoks.extend(word_tokens(h.chunk.retrieval_text, stop=False))
    uncovered = [t for t in toks if t not in known and not any(stem_match(t, p) for p in ptoks)]
    return (len(toks) - len(uncovered)) / len(toks), uncovered


def grade_relevance(query: str, hits: list[SearchHit], expander: Optional[QueryExpander],
                    min_coverage: float, rerank_threshold: float) -> Grade:
    if not hits:
        return Grade(False, 0.0, "no_hits")
    cov, unc = query_coverage(query, hits, expander)
    if "rerank" in hits[0].scores:
        top = hits[0].scores["rerank"]
        return Grade(top > rerank_threshold, cov, "reranker", top, unc)
    return Grade(cov >= min_coverage, cov, "coverage", None, unc)
