#!/usr/bin/env python3
"""One command to (re)build everything derived from the sample fixtures:

  sample PDFs -> lexicon -> ingestion (OCR fallback, cleaning, chunking) -> golden set -> validation

    python backend/scripts/setup_data.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
STEPS = ["build_sample_pdfs.py", "build_lexicon.py", "ingest.py", "build_golden.py", "validate_golden.py"]

if __name__ == "__main__":
    for step in STEPS:
        print(f"\n=== {step} ===", flush=True)
        r = subprocess.run([sys.executable, "-I", str(HERE / step)])
        if r.returncode != 0:
            sys.exit(f"{step} failed (exit {r.returncode})")
    print("\nAll done. Start the API: cd backend && uvicorn app.main:app --reload")
