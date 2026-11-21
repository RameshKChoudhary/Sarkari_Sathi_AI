#!/usr/bin/env python3
"""Sanity-check the golden set against the ingested corpus:
* counts / unanswerable share / ids unique
* every answerable question has gold passages in en, hi and mr
* every key fact (any alternative) occurs in the gold passage of EVERY language, so a correct
  answer in any language can score full correctness.
Exit code 1 if something is wrong."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.ingestion.pipeline import read_chunks  # noqa: E402
from app.retrieval.tokenize import normalize_for_match  # noqa: E402


def main() -> int:
    golden = json.loads((ROOT / "data/evaluation/golden.json").read_text(encoding="utf-8"))
    chunks = [c for c in read_chunks(ROOT / "data/processed/chunks_structure.jsonl") if c.section_type != "overview"]
    by = {(c.scheme_id, c.section_type, c.language): c for c in chunks}
    errors: list[str] = []
    ids = [g["id"] for g in golden]
    if len(ids) != len(set(ids)):
        errors.append("duplicate ids")
    n_un = sum(not g["answerable"] for g in golden)
    print(f"{len(golden)} questions, {n_un} unanswerable ({n_un / len(golden):.1%})")
    if not 150 <= len(golden) <= 200:
        errors.append("question count outside 150-200")
    if not 0.15 <= n_un / len(golden) <= 0.20:
        errors.append("unanswerable share outside 15-20%")
    for g in golden:
        if not g["answerable"]:
            continue
        for lang in ("en", "hi", "mr"):
            c = by.get((g["gold"]["scheme_id"], g["gold"]["section"], lang))
            if c is None:
                errors.append(f"{g['id']}: no gold passage in {lang}")
                continue
            text = normalize_for_match(c.text)
            for fact in g["key_facts"]:
                if not any(normalize_for_match(a) in text for a in fact):
                    errors.append(f"{g['id']}: fact {fact} missing from {c.chunk_id}")
    for e in errors:
        print("ERROR", e)
    print("OK" if not errors else f"{len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
