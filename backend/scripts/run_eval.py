#!/usr/bin/env python3
"""Run the evaluation suites and write REAL measured results.

    python scripts/run_eval.py --suite all        # language, retrieval (matrix + ablations), generation
    python scripts/run_eval.py --suite retrieval
    python scripts/run_eval.py --suite generation

Outputs: data/evaluation/results/*.json and docs/RESULTS.md. Experiments that need models that
cannot be loaded here (BGE-M3, E5, LaBSE, bge-reranker) are written as NOT RUN with the reason;
nothing is estimated. On a machine with Hugging Face access and `pip install -r
backend/requirements-ml.txt` the same command runs them.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import Settings  # noqa: E402
from app.core.logging import setup_logging  # noqa: E402
from app.evaluation.ablations import SPECS, Builder, NotRun  # noqa: E402
from app.evaluation.generation_eval import (language_detection_report, run_generation, summarize,  # noqa: E402
                                            summarize_by, sweep_coverage_threshold)
from app.evaluation.golden import load_golden  # noqa: E402
from app.evaluation.retrieval_eval import QUERY_LANGS, build_spans, fmt, matrix, matrix_markdown, overall  # noqa: E402
from app.ingestion.pipeline import read_chunks  # noqa: E402
from app.retrieval.expansion import QueryExpander  # noqa: E402

MATRIX_SPECS = ["BM25 (words)", "Char n-gram BM25 (3-5)", "BM25 + n-gram BM25 (RRF)", "A + lexicon query expansion",
                "B: translate query (lexicon translator)", "B: translate query (ORACLE = gold English question)",
                "Dense: BGE-M3", "Hybrid: BM25 + n-gram + BGE-M3 (RRF)", "Hybrid (BM25+n-gram+BGE-M3) + bge-reranker-v2-m3"]


def pct(x) -> str:
    return "n/a" if x is None else f"{100 * x:.1f}%"


def run_retrieval(cfg: Settings, out: Path) -> dict:
    items = load_golden(cfg.eval_dir / "golden.json")
    sets = {
        "structure": [c for c in read_chunks(cfg.processed_dir / "chunks_structure.jsonl") if c.section_type != "overview"],
        "fixed": read_chunks(cfg.processed_dir / "chunks_fixed.jsonl"),
    }
    builder = Builder(sets, QueryExpander.from_file(cfg.raw_dir / "lexicon.json"), items, cfg.processed_dir / "embeddings")
    spans = build_spans(sets["structure"])
    results: list[dict] = []
    for spec in SPECS:
        entry = {"name": spec.name, "group": spec.group, "note": spec.note, "status": "ok"}
        t0 = time.perf_counter()
        try:
            retriever, chunks = builder.build(spec)
            entry["overall"] = overall(retriever, items, chunks, spans)
            if spec.name in MATRIX_SPECS:
                entry["matrix"] = matrix(retriever, items, chunks, spans)
        except NotRun as exc:
            entry.update(status="NOT RUN", reason=str(exc))
        entry["seconds"] = round(time.perf_counter() - t0, 1)
        print(f"{entry['status']:8s} {spec.name}")
        results.append(entry)
    (out / "retrieval.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"results": results}


def run_generation_suite(cfg: Settings, out: Path) -> dict:
    from app.services.rag_service import RagService

    items = load_golden(cfg.eval_dir / "golden.json")
    base = dict(retrieval_mode="hybrid_lex", query_expansion=True, use_reranker=False, chunking="structure", llm_provider="extractive")
    # 1) tune the coverage threshold on the DEV split only
    probe = RagService(Settings(**base, min_query_coverage=0.0))
    probe_rows = run_generation(probe, items)
    dev = [(r["coverage"] or 0.0, r["answerable"]) for r in probe_rows if r["split"] == "dev"]
    sweep = sweep_coverage_threshold(dev)
    best_t = max(sweep, key=lambda x: (x[1], -x[0]))[0]
    # 2) evaluate everything with the chosen threshold
    svc = RagService(Settings(**base, min_query_coverage=best_t))
    rows = run_generation(svc, items)
    res = {
        "generator": "extractive (offline, no LLM)", "chosen_coverage_threshold": best_t,
        "threshold_sweep_dev": sweep, "overall": summarize(rows), "test_split": summarize([r for r in rows if r["split"] == "test"]),
        "dev_split": summarize([r for r in rows if r["split"] == "dev"]),
        "by_language": summarize_by(rows, "language"),
        "false_answers": [r["id"] for r in rows if not r["answerable"] and not r["abstained"]],
        "false_abstains": [r["id"] for r in rows if r["answerable"] and r["abstained"]],
        "rows": rows,
    }
    (out / "generation.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


def write_report(cfg: Settings, lang_rep: dict | None, ret: dict | None, gen: dict | None, path: Path) -> None:
    items = load_golden(cfg.eval_dir / "golden.json")
    n_un = sum(not q.answerable for q in items)
    L: list[str] = [
        "# Evaluation results (measured)", "",
        f"_Generated by `scripts/run_eval.py` on {time.strftime('%Y-%m-%d %H:%M')} · Python {platform.python_version()} · CPU only._", "",
        "## Read this first (limitations)", "",
        f"* **Corpus**: 10 schemes x 3 languages = 30 PDFs, 120 retrievable sections. All are *sample fixtures* written by the project author (AI assistant) from general knowledge - **not official documents**. Numbers below measure this small fixture corpus; they do not predict performance on real government PDFs.",
        f"* **Golden set**: {len(items)} questions ({n_un} unanswerable = {n_un / len(items):.1%}) in English, Hindi, Marathi and romanised Marathi, {len({q.group_id for q in items})} question groups. Questions were AI-written and **not yet verified by a native Hindi/Marathi speaker** (see `data/evaluation/golden_review.csv`).",
        "* **Parallel corpus**: every section exists in en/hi/mr, so a Marathi query always has a same-language gold passage when searching the pooled corpus. The matrix therefore restricts the search to one document language at a time to measure true cross-lingual retrieval.",
        "* **Not run here**: neural embedding models (BGE-M3, multilingual-E5, LaBSE), the bge-reranker-v2-m3 cross-encoder and an LLM (Groq) - the build sandbox cannot reach Hugging Face or Groq. Those rows are marked `NOT RUN`; run the same script locally to fill them.",
        "* **ORACLE rows** use human-written parallel text as the 'translation'. They are upper bounds for machine translation, not a measurement of any MT system.",
        "* **Relevance**: a retrieved chunk is relevant if it is the gold section (structure chunks) or overlaps the gold section by >= half of the smaller of the two (fixed-size chunks). In the *pooled* columns the three language versions of the gold section all count as relevant, so pooled nDCG rewards retrieving the sibling passages in other languages; the per-document-language columns do not.",
        "* Small sample: with ~45 questions per language a single question moves a metric by ~2 points; differences of a few points are not significant.", ""]
    if lang_rep:
        L += ["## Language detection (rule-based)", "", f"Overall accuracy on the golden questions: **{pct(lang_rep['accuracy'])}**", "",
              "| Label | Accuracy |", "|---|---|"] + [f"| {k} | {pct(v)} |" for k, v in lang_rep["per_label_accuracy"].items()]
        L += ["", f"The romanised-Marathi marker list was written while looking at these same questions, so this number is **optimistic**; treat it as a smoke test, not a generalisation estimate. Confusion (true -> predicted): `{json.dumps(lang_rep['confusion'], ensure_ascii=False)}`", ""]
    if ret:
        res = {e["name"]: e for e in ret["results"]}
        L += ["## Retrieval matrix: query language x document language", ""]
        for name in MATRIX_SPECS:
            e = res.get(name)
            if e is None:
                continue
            if e["status"] != "ok":
                L += [f"**{name}** - NOT RUN: {e.get('reason', '')}", ""]
            else:
                L += [matrix_markdown(e["matrix"], name), ""]
        L += ["## Ablations (pooled corpus, all answerable questions)", "",
              "Cells: Recall@5 / MRR / nDCG@10. Pooled search over all three document languages.", ""]
        for group, title in [("method", "BM25 vs n-gram BM25 vs dense vs hybrid"), ("embedding", "Embedding models"),
                             ("rerank", "With / without reranker"), ("strategy", "Cross-lingual strategies A-D"),
                             ("chunking", "Fixed-size vs structure-aware chunking")]:
            L += [f"### {title}", "", "| Configuration | All | English q | Hindi q | Marathi q | Romanised Marathi q |", "|---|---|---|---|---|---|"]
            for e in ret["results"]:
                if e["group"] != group:
                    continue
                if e["status"] != "ok":
                    L.append(f"| {e['name']} | NOT RUN - {e.get('reason', '')[:90]} | | | | |")
                else:
                    o = e["overall"]
                    note = f" _({e['note']})_" if e["note"] else ""
                    L.append(f"| {e['name']}{note} | " + " | ".join(fmt(o[k]) for k in ["all"] + QUERY_LANGS) + " |")
            L.append("")
    if gen:
        o, t = gen["overall"], gen["test_split"]
        L += ["## Generation / abstention (end-to-end LangGraph pipeline)", "",
              f"Generator: **{gen['generator']}**. Faithfulness and answer correctness are only meaningful for an LLM generator; here answers are verbatim passage sentences, so they are high *by construction*. Language-match, citation accuracy and abstention reflect the actual pipeline behaviour.", "",
              f"Coverage threshold for the relevance gate was chosen on the **dev split only** (sweep: `{gen['threshold_sweep_dev']}`) -> **{gen['chosen_coverage_threshold']}**. Test split is held out.", "",
              "| Metric | All | Dev | Test (held out) |", "|---|---|---|---|"]
        for k, lab in [("abstention_accuracy", "Abstention accuracy"), ("abstain_recall_on_unanswerable", "Abstained on unanswerable"),
                       ("false_abstain_rate_on_answerable", "False abstain on answerable"), ("answer_correctness", "Answer correctness (key-fact recall)"),
                       ("citation_accuracy", "Citation accuracy (cited passage = gold section)"), ("faithfulness_proxy", "Faithfulness proxy (verified sentences)"),
                       ("language_match_rate", "Language-match rate")]:
            L.append(f"| {lab} | {pct(o[k])} | {pct(gen['dev_split'][k])} | {pct(t[k])} |")
        L += ["", f"n = {o['n']} (answerable {o['n_answerable']}, unanswerable {o['n_unanswerable']}); test n = {t['n']} (unanswerable {t['n_unanswerable']}).", "",
              "By question language:", "", "| Language | Abstention acc. | Correctness | Citation acc. | Language match |", "|---|---|---|---|---|"]
        for k, v in gen["by_language"].items():
            L.append(f"| {k} | {pct(v['abstention_accuracy'])} | {pct(v['answer_correctness'])} | {pct(v['citation_accuracy'])} | {pct(v['language_match_rate'])} |")
        L += ["", f"Unanswerable questions that were answered anyway: `{gen['false_answers']}`", "",
              f"Answerable questions that were wrongly refused: `{gen['false_abstains']}`", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--suite", choices=["all", "lang", "retrieval", "generation"], default="all")
    args = ap.parse_args()
    cfg = Settings()
    setup_logging("WARNING")
    out = cfg.eval_dir / "results"
    out.mkdir(parents=True, exist_ok=True)
    lang_rep = ret = gen = None
    items = load_golden(cfg.eval_dir / "golden.json")
    if args.suite in ("all", "lang"):
        lang_rep = language_detection_report(items)
        (out / "language_detection.json").write_text(json.dumps(lang_rep, ensure_ascii=False, indent=1), encoding="utf-8")
    if args.suite in ("all", "retrieval"):
        ret = run_retrieval(cfg, out)
    if args.suite in ("all", "generation"):
        gen = run_generation_suite(cfg, out)
    # re-load whatever was not run in this invocation so the report is always complete
    def load(name):
        p = out / name
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    lang_rep = lang_rep or load("language_detection.json")
    ret = ret or ({"results": load("retrieval.json")} if load("retrieval.json") else None)
    gen = gen or load("generation.json")
    write_report(cfg, lang_rep, ret, gen, ROOT / "docs" / "RESULTS.md")
    print("wrote docs/RESULTS.md")


if __name__ == "__main__":
    main()
