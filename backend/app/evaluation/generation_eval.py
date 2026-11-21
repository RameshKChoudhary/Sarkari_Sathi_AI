"""End-to-end (retrieval + LangGraph + verification) evaluation and language-detection accuracy."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Optional

from ..models.schemas import ChatRequest
from ..retrieval.lang import detect_language
from .golden import GoldenItem
from .metrics import key_fact_recall, mean

_STRIP = re.compile(r"\[\d+\]|https?://\S+|\*\*|\|")


def run_generation(service, items: list[GoldenItem]) -> list[dict]:
    rows: list[dict] = []
    for q in items:
        service.cache._d.clear()
        resp = service.chat(ChatRequest(query=q.question, top_k=5))
        cited = [s for s in resp.sources if s.cited]
        gold_ok = [bool(q.gold and s.scheme_id == q.gold.scheme_id and s.section_type == q.gold.section) for s in cited]
        ans_clean = _STRIP.sub(" ", resp.answer)
        rows.append({
            "id": q.id, "group": q.group_id, "language": q.language, "split": q.split, "answerable": q.answerable,
            "abstained": resp.abstained,
            "correctness": key_fact_recall(resp.answer, q.key_facts) if (q.answerable and not resp.abstained) else (0.0 if q.answerable else None),
            "citation_precision": (sum(gold_ok) / len(gold_ok)) if (q.answerable and cited) else None,
            "faithfulness": resp.pipeline.get("first_pass_support") if not resp.abstained else None,
            "language_match": detect_language(ans_clean).language == q.query_lang,
            "coverage": (resp.pipeline.get("relevance") or {}).get("coverage"),
            "generator": resp.pipeline.get("generator"),
            "latency_ms": resp.timings_ms.get("total"),
        })
    return rows


def summarize(rows: list[dict]) -> dict:
    ans = [r for r in rows if r["answerable"]]
    un = [r for r in rows if not r["answerable"]]
    tp = sum(1 for r in un if r["abstained"])  # correctly abstained
    fn = sum(1 for r in ans if r["abstained"])  # wrongly abstained
    return {
        "n": len(rows), "n_answerable": len(ans), "n_unanswerable": len(un),
        "abstention_accuracy": mean([float(r["abstained"] == (not r["answerable"])) for r in rows]),
        "abstain_recall_on_unanswerable": tp / len(un) if un else None,
        "false_abstain_rate_on_answerable": fn / len(ans) if ans else None,
        "answer_correctness": mean([r["correctness"] for r in ans if r["correctness"] is not None]),
        "answer_correctness_when_answered": mean([r["correctness"] for r in ans if not r["abstained"]]),
        "citation_accuracy": mean([r["citation_precision"] for r in ans if r["citation_precision"] is not None]),
        "faithfulness_proxy": mean([r["faithfulness"] for r in rows if r["faithfulness"] is not None]),
        "language_match_rate": mean([float(r["language_match"]) for r in rows]),
        "latency_ms_mean": mean([r["latency_ms"] for r in rows if r["latency_ms"] is not None]),
    }


def summarize_by(rows: list[dict], key: str) -> dict:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[r[key]].append(r)
    return {k: summarize(v) for k, v in sorted(groups.items())}


def sweep_coverage_threshold(coverages: list[tuple[float, bool]], grid: Optional[list[float]] = None) -> list[tuple[float, float]]:
    """coverages: (coverage, answerable). Abstain iff coverage < t. Returns (t, abstention accuracy)."""
    grid = grid or [round(0.1 * i, 2) for i in range(1, 11)]
    out = []
    for t in grid:
        acc = mean([float((cov < t) == (not ans)) for cov, ans in coverages])
        out.append((t, acc))
    return out


def language_detection_report(items: list[GoldenItem]) -> dict:
    conf: dict[str, Counter] = defaultdict(Counter)
    for q in items:
        info = detect_language(q.question)
        got = f"{info.language}{'_roman' if info.romanized else ''}"
        want = "mr_roman" if q.language == "mr_roman" else q.language
        conf[want][got.replace("mr_roman", "mr_roman")] += 1
    acc = {k: v[k if k != "mr_roman" else "mr_roman"] / sum(v.values()) for k, v in conf.items()}
    total = sum(sum(v.values()) for v in conf.values())
    correct = sum(v[k] for k, v in conf.items())
    return {"accuracy": correct / total, "per_label_accuracy": acc, "confusion": {k: dict(v) for k, v in conf.items()}}
