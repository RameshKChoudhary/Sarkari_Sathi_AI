#!/usr/bin/env python3
"""Ingest PDFs listed in data/raw/manifest.json -> data/processed/*.jsonl (+ scheme catalog).

    python scripts/ingest.py                 # sample fixtures
    python scripts/ingest.py --ocr force     # force OCR on every page (needs tesseract)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.core.logging import setup_logging  # noqa: E402
from app.ingestion.ocr import TesseractOCR  # noqa: E402
from app.ingestion.pipeline import ingest_manifest  # noqa: E402


def main() -> None:
    s = get_settings()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, default=s.raw_dir / "manifest.json")
    ap.add_argument("--pdf-root", type=Path, default=s.raw_dir / "pdfs")
    ap.add_argument("--out", type=Path, default=s.processed_dir)
    ap.add_argument("--ocr", choices=["auto", "force", "off"], default="auto")
    args = ap.parse_args()
    setup_logging(s.log_level)
    ocr = None if args.ocr == "off" else TesseractOCR(s.tessdata_dir)
    report = ingest_manifest(args.manifest, args.pdf_root, args.out, ocr=ocr, ocr_mode=args.ocr, dpi=s.ocr_dpi)
    print(json.dumps({k: v for k, v in report.items() if k != "flags"}, ensure_ascii=False, indent=2))
    if report["flags"]:
        print("flags:", json.dumps(report["flags"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
