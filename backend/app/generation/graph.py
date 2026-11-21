"""LangGraph workflow:

  detect_language -> retrieve -> grade_relevance --(insufficient)--> abstain -> END
                                       |
                                    (relevant)
                                       v
                                   generate -> verify_citations --(nothing verified)--> abstain
                                                      |
                                                  finalize -> END

Every node records its latency in state["timings_ms"]."""
from __future__ import annotations

import logging
import time
from typing import Any, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from ..models.schemas import ChatResponse, Filters, SearchHit, SourceCard, VerificationReport
from ..retrieval.lang import LangInfo, detect_language
from .answer import (NOT_FOUND, best_sentence, build_system_prompt, build_user_prompt, clean_llm_text,
                     extractive_answer)
from .context import RagContext
from .i18n import ABSTAIN, DISCLAIMER
from .llm import LLMError
from .relevance import Grade, grade_relevance
from .verify import cited_ids, verify_answer

logger = logging.getLogger(__name__)


class GraphState(TypedDict, total=False):
    query: str
    ui_language: Optional[str]
    filters: Optional[Filters]
    top_k: int
    lang: LangInfo
    hits: list[SearchHit]
    grade: Grade
    cards: list[SourceCard]
    raw_answer: str
    answer_mode: str  # llm | extractive
    answer: str
    abstained: bool
    abstain_reason: Optional[str]
    verification: Optional[VerificationReport]
    timings_ms: dict[str, float]
    pipeline: dict[str, Any]
    llm_usage: dict[str, int]


def _timed(name: str, state: GraphState, t0: float) -> dict[str, float]:
    t = dict(state.get("timings_ms", {}))
    t[name] = round((time.perf_counter() - t0) * 1000, 1)
    return t


def _card(i: int, hit_chunk, score: float) -> SourceCard:
    c = hit_chunk
    return SourceCard(
        id=i, chunk_id=c.chunk_id, scheme_id=c.scheme_id, scheme_name=c.scheme_name, level=c.level,
        language=c.language, section_type=c.section_type, source_url=c.source_url,
        publication_date=c.publication_date, doc_ref=c.doc_ref, text=c.text, score=round(score, 5),
        data_status=c.data_status, extraction_method=c.extraction_method,
    )


def build_graph(ctx: RagContext):
    s = ctx.settings

    def detect_node(state: GraphState) -> dict:
        t0 = time.perf_counter()
        info = detect_language(state["query"], hint=state.get("ui_language"))
        return {"lang": info, "timings_ms": _timed("detect_language", state, t0)}

    def retrieve_node(state: GraphState) -> dict:
        t0 = time.perf_counter()
        retriever = ctx.retriever_for()
        hits = retriever.search(state["query"], k=state.get("top_k") or s.top_k, filters=state.get("filters"),
                                query_lang=state["lang"].language)
        cards = [_card(i, h.chunk, h.score) for i, h in enumerate(hits, start=1)]
        return {"hits": hits, "cards": cards, "timings_ms": _timed("retrieve", state, t0)}

    def grade_node(state: GraphState) -> dict:
        t0 = time.perf_counter()
        g = grade_relevance(state["query"], state["hits"], ctx.expander, s.min_query_coverage, s.rerank_relevance_threshold)
        return {"grade": g, "timings_ms": _timed("grade_relevance", state, t0)}

    def route_after_grade(state: GraphState) -> str:
        return "generate" if state["grade"].relevant else "abstain"

    def abstain_node(state: GraphState) -> dict:
        lang = state["lang"].language
        g = state.get("grade")
        reason = state.get("abstain_reason") or (
            f"insufficient evidence ({g.method}: coverage={g.coverage:.2f})" if g else "insufficient evidence")
        return {"answer": ABSTAIN[lang], "abstained": True, "abstain_reason": reason, "cards": []}

    def _llm_answer(state: GraphState) -> Optional[str]:
        lang = state["lang"].language
        res = ctx.llm.chat(build_system_prompt(lang), build_user_prompt(state["query"], state["cards"]),
                           temperature=0.0, max_tokens=600)
        text = clean_llm_text(res.text)
        usage = {"prompt_tokens": res.prompt_tokens, "completion_tokens": res.completion_tokens}
        state_usage = dict(state.get("llm_usage", {}))
        for k, v in usage.items():
            state_usage[k] = state_usage.get(k, 0) + v
        state["llm_usage"] = state_usage  # type: ignore[typeddict-item]
        if NOT_FOUND in text[:40]:
            return None
        # one retry if the model answered in the wrong language
        got = detect_language(text).language
        if got != lang:
            logger.info("language mismatch (%s != %s); retrying once", got, lang)
            res = ctx.llm.chat(build_system_prompt(lang) + f"\nIMPORTANT: your last reply was not in {lang}. Reply in the required language only.",
                               build_user_prompt(state["query"], state["cards"]), temperature=0.0, max_tokens=600)
            text = clean_llm_text(res.text)
            if NOT_FOUND in text[:40]:
                return None
        return text

    def generate_node(state: GraphState) -> dict:
        t0 = time.perf_counter()
        lang = state["lang"].language
        pipeline = dict(state.get("pipeline", {}))
        if ctx.llm is not None:
            try:
                text = _llm_answer(state)
                if text is None:
                    return {"abstained": True, "abstain_reason": "LLM reported the passages do not contain the answer",
                            "answer": ABSTAIN[lang], "cards": [], "timings_ms": _timed("generate", state, t0),
                            "llm_usage": state.get("llm_usage", {})}
                pipeline["generator"] = f"llm:{ctx.llm.model}"
                return {"raw_answer": text, "answer_mode": "llm", "pipeline": pipeline,
                        "llm_usage": state.get("llm_usage", {}), "timings_ms": _timed("generate", state, t0)}
            except LLMError as exc:
                logger.warning("LLM failed, using extractive fallback: %s", exc)
                pipeline["llm_error"] = str(exc)
        pipeline["generator"] = "extractive"
        return {"answer_mode": "extractive", "pipeline": pipeline, "raw_answer": "", "timings_ms": _timed("generate", state, t0)}

    def route_after_generate(state: GraphState) -> str:
        return "end" if state.get("abstained") else "verify"

    def _compose_extractive(state: GraphState) -> tuple[str, list[SourceCard]]:
        lang = state["lang"].language
        text, chosen = extractive_answer(lang, state["hits"], ctx.sibling, s.extractive_passages, s.extractive_score_ratio)
        cards = list(state["cards"])
        order: list[SourceCard] = []
        for c in chosen:  # reuse the retrieved card if present, else append the language sibling
            card = next((k for k in cards if k.chunk_id == c.chunk_id), None)
            if card is None:
                card = _card(len(cards) + 1, c, 0.0)
                cards.append(card)
            order.append(card)
        # citation numbers in `text` are 1..n by `chosen` order -> remap to real card ids
        for idx, card in enumerate(order, start=1):
            text = text.replace(f"[{idx}]", f"[§{card.id}]")
        return text.replace("[§", "["), cards

    def verify_node(state: GraphState) -> dict:
        t0 = time.perf_counter()
        pipeline = dict(state.get("pipeline", {}))
        cards = list(state["cards"])
        answer = state.get("raw_answer", "")
        if state.get("answer_mode") == "extractive":
            answer, cards = _compose_extractive(state)
        passages = {c.id: c.text for c in cards}
        cleaned, rep = verify_answer(answer, passages)
        # share of sentences of the first-pass answer that survived verification (faithfulness proxy)
        pipeline["first_pass_support"] = round(rep.kept_sentences / max(rep.checked_sentences, 1), 3)
        if not rep.ok and state.get("answer_mode") == "llm":
            logger.info("LLM answer failed verification; falling back to extractive")
            pipeline["generator"] = "extractive (LLM answer failed verification)"
            answer, cards = _compose_extractive(state)
            passages = {c.id: c.text for c in cards}
            cleaned, rep = verify_answer(answer, passages)
        out: dict[str, Any] = {"verification": rep, "pipeline": pipeline, "cards": cards,
                               "timings_ms": _timed("verify_citations", state, t0)}
        if rep.ok:
            out["answer"] = cleaned
        else:
            lang = state["lang"].language
            out.update({"answer": ABSTAIN[lang], "abstained": True, "cards": [],
                        "abstain_reason": "no sentence could be verified against the retrieved passages"})
        return out

    def finalize_node(state: GraphState) -> dict:
        ids = cited_ids(state["answer"])
        cards = []
        for c in state["cards"]:
            c = c.model_copy()
            c.cited = c.id in ids
            ref = state["answer"] if c.cited else state["query"]
            c.highlight = best_sentence(c.text, ref)
            cards.append(c)
        cards.sort(key=lambda k: (not k.cited, k.id))
        return {"cards": cards}

    g = StateGraph(GraphState)
    g.add_node("detect_language", detect_node)
    g.add_node("retrieve", retrieve_node)
    g.add_node("grade_relevance", grade_node)
    g.add_node("abstain", abstain_node)
    g.add_node("generate", generate_node)
    g.add_node("verify_citations", verify_node)
    g.add_node("finalize", finalize_node)
    g.add_edge(START, "detect_language")
    g.add_edge("detect_language", "retrieve")
    g.add_edge("retrieve", "grade_relevance")
    g.add_conditional_edges("grade_relevance", route_after_grade, {"generate": "generate", "abstain": "abstain"})
    g.add_conditional_edges("generate", route_after_generate, {"verify": "verify_citations", "end": END})
    g.add_edge("verify_citations", "finalize")
    g.add_edge("finalize", END)
    g.add_edge("abstain", END)
    return g.compile()


def run_chat(graph, ctx: RagContext, query: str, ui_language: Optional[str] = None,
             filters: Optional[Filters] = None, top_k: Optional[int] = None) -> ChatResponse:
    t0 = time.perf_counter()
    st: GraphState = graph.invoke({"query": query, "ui_language": ui_language, "filters": filters,
                                   "top_k": top_k or ctx.settings.top_k, "timings_ms": {}, "pipeline": {}})
    return state_to_response(st, ctx, (time.perf_counter() - t0) * 1000)


def state_to_response(st: GraphState, ctx: RagContext, total_ms: float) -> ChatResponse:
    info: LangInfo = st["lang"]
    lang = info.language
    abstained = bool(st.get("abstained"))
    timings = dict(st.get("timings_ms", {}))
    timings["total"] = round(total_ms, 1)
    g: Optional[Grade] = st.get("grade")
    pipeline = dict(st.get("pipeline", {}))
    pipeline.update({
        "retrieval_mode": ctx.settings.retrieval_mode, "embed_model": ctx.settings.embed_model,
        "translation_strategy": ctx.settings.translation_strategy, "reranker": ctx.settings.use_reranker,
        "chunking": ctx.settings.chunking, "relevance": ({"method": g.method, "coverage": round(g.coverage, 3),
                                                         "uncovered": g.uncovered} if g else None),
        "llm_usage": st.get("llm_usage", {}), "degraded": ctx.degraded,
    })
    return ChatResponse(
        answer=st["answer"], language=lang, script=info.script, romanized=info.romanized, abstained=abstained,
        abstain_reason=st.get("abstain_reason"), sources=st.get("cards", []), disclaimer=DISCLAIMER[lang],
        verification=st.get("verification"), timings_ms=timings, pipeline=pipeline,
    )
