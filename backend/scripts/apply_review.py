#!/usr/bin/env python3
"""Merge native-speaker review (golden_review.csv) back into golden.json.

Columns used: id, review_status (ok | fix | reject), corrected_question, reviewer, notes.
  ok     -> verification.status = "verified"
  fix    -> question text replaced by corrected_question, status = "verified"
  reject -> status = "rejected" (excluded from evaluation by --skip-rejected in run_eval)
Re-run scripts/run_eval.py afterwards. Hindi/Marathi rows start as "unverified".
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/evaluation/golden_review.csv"
    gpath = ROOT / "data/evaluation/golden.json"
    golden = {g["id"]: g for g in json.loads(gpath.read_text(encoding="utf-8"))}
    n = 0
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            status = (row.get("review_status(ok|fix|reject)") or "").strip().lower()
            g = golden.get(row["id"])
            if not g or status not in {"ok", "fix", "reject"}:
                continue
            if status == "fix" and row.get("corrected_question", "").strip():
                g["question"] = row["corrected_question"].strip()
            g["verification"] = {"status": "rejected" if status == "reject" else "verified",
                                 "reviewer": row.get("reviewer", "").strip() or None, "notes": row.get("notes", "")}
            n += 1
    gpath.write_text(json.dumps(list(golden.values()), ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"applied {n} reviews")


if __name__ == "__main__":
    main()
