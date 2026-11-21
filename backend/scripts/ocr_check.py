#!/usr/bin/env python3
"""Measure OCR quality on rasterised (scanned-like) versions of the sample PDFs.

For each sample PDF the page images are re-wrapped into an image-only PDF (no text layer),
the ingestion pipeline's OCR fallback is run, and the character error rate (CER) is computed
against the original digital text layer. Needs the tesseract binary + language data.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.ingestion.cleaning import normalize_text  # noqa: E402
from app.ingestion.ocr import TesseractOCR  # noqa: E402
from app.ingestion.pdf_extract import extract_pdf  # noqa: E402


def levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def squash(s: str) -> str:
    return "".join(normalize_text(s).split())


def rasterise(src: Path, dst: Path, dpi: int = 200) -> None:
    out = pymupdf.open()
    with pymupdf.open(src) as doc:
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            p = out.new_page(width=page.rect.width, height=page.rect.height)
            p.insert_image(p.rect, pixmap=pix)
    out.save(dst)


def main() -> None:
    s = get_settings()
    ocr = TesseractOCR(s.tessdata_dir)
    print("tesseract languages:", sorted(ocr.available_langs()))
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, lang in [("pm_kisan.en", "en"), ("ladki_bahin.hi", "hi"), ("pmfby.hi", "hi"), ("ladki_bahin.mr", "mr"), ("pmfby.mr", "mr")]:
            src = ROOT / "data/raw/pdfs" / f"{name}.pdf"
            scanned = Path(tmp) / f"{name}.scan.pdf"
            rasterise(src, scanned)
            ref = squash("\n".join(p.text for p in extract_pdf(src, lang, ocr=None, mode="off")))
            res = extract_pdf(scanned, lang, ocr=ocr, mode="auto")
            got = squash("\n".join(p.text for p in res))
            cer = levenshtein(ref, got) / max(len(ref), 1)
            rows.append((name, lang, ocr.lang_string(lang), res[0].method, len(ref), cer))
            print(f"{name:18s} lang={lang} model={ocr.lang_string(lang):8s} method={res[0].method:12s} chars={len(ref):4d} CER={cer:.1%}")
    print(f"mean CER: {sum(r[-1] for r in rows) / len(rows):.1%}")


if __name__ == "__main__":
    main()
