"""PDF -> per-page text. Handles normal text PDFs, scanned PDFs, legacy-font PDFs and tables."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

import pymupdf

from .cleaning import normalize_text
from .legacy_fonts import font_names_suggest_legacy, garbage_score
from .ocr import OcrBackend, OcrUnavailable

logger = logging.getLogger(__name__)

OcrMode = Literal["auto", "force", "off"]
MIN_TEXT_CHARS = 25  # fewer non-space characters than this on a page => treat as scanned


@dataclass
class PageResult:
    page_no: int  # 1-based
    text: str
    method: str  # text | ocr_scanned | ocr_legacy_font
    garbage_score: float = 0.0
    flags: list[str] = field(default_factory=list)


def _table_to_text(page: pymupdf.Page, table) -> str:
    """Render a detected table as a [TABLE] block.

    Cell text is read with a clipped `get_text` (logical stream order) instead of
    `Table.extract()`, because `extract()` orders glyphs left-to-right and scrambles
    Devanagari conjuncts / vowel signs (e.g. 'श्रेणी' -> 'शरेणी ्')."""
    out = ["[TABLE]"]
    for row in table.rows:
        cells: list[str] = []
        for bbox in row.cells:
            if bbox is None:
                cells.append("")
                continue
            txt = page.get_text("text", clip=pymupdf.Rect(bbox))
            cells.append(" ".join(normalize_text(txt).split()))
        if any(cells):
            out.append("| " + " | ".join(cells) + " |")
    out.append("[/TABLE]")
    return "\n".join(out)


def _overlap_fraction(a: pymupdf.Rect, b: pymupdf.Rect) -> float:
    inter = a & b
    if inter.is_empty or a.get_area() == 0:
        return 0.0
    return inter.get_area() / a.get_area()


def page_text_with_tables(page: pymupdf.Page) -> str:
    """Text in reading order; tables are emitted as [TABLE] blocks instead of being
    flattened into scrambled lines (income limits often live in tables)."""
    tables = []
    try:
        tables = list(page.find_tables().tables)
    except Exception:  # very old PyMuPDF or odd page
        logger.debug("find_tables unavailable", exc_info=True)
    items: list[tuple[float, str]] = []
    table_rects = [pymupdf.Rect(t.bbox) for t in tables]
    for x0, y0, x1, y1, txt, _no, btype in page.get_text("blocks", sort=True):
        if btype != 0:
            continue
        rect = pymupdf.Rect(x0, y0, x1, y1)
        if any(_overlap_fraction(rect, tr) > 0.5 for tr in table_rects):
            continue
        items.append((y0, txt.strip()))
    for t in tables:
        try:
            items.append((t.bbox[1], _table_to_text(page, t)))
        except Exception:
            logger.debug("table extract failed", exc_info=True)
    items.sort(key=lambda it: it[0])
    return "\n".join(txt for _, txt in items if txt)


def _ocr_page(page: pymupdf.Page, ocr: OcrBackend, language: str, dpi: int) -> str:
    png = page.get_pixmap(dpi=dpi).tobytes("png")
    return ocr.ocr_png(png, language)


def extract_pdf(
    path: Path,
    language: str,
    ocr: Optional[OcrBackend] = None,
    mode: OcrMode = "auto",
    dpi: int = 300,
) -> list[PageResult]:
    """Extract every page. In `auto` mode OCR is used when a page has (almost) no text layer
    (scanned) or when the text layer looks corrupted (legacy font / garbage)."""
    results: list[PageResult] = []
    with pymupdf.open(path) as doc:
        for i, page in enumerate(doc, start=1):
            flags: list[str] = []
            raw = normalize_text(page_text_with_tables(page)) if mode != "force" else ""
            n_chars = len("".join(raw.split()))
            fonts = [f[3] for f in page.get_fonts()]
            legacy_font = font_names_suggest_legacy(fonts)
            report = garbage_score(raw, language)
            need_ocr, method = False, "text"
            if mode == "force":
                need_ocr, method = True, "ocr_scanned"
            elif mode == "auto":
                if n_chars < MIN_TEXT_CHARS:
                    need_ocr, method = True, "ocr_scanned"
                    flags.append("no text layer")
                elif report.is_garbage or (legacy_font and report.score >= 0.3):
                    need_ocr, method = True, "ocr_legacy_font"
                    flags.append("corrupted text layer: " + "; ".join(report.reasons or ["legacy font"]))
            text = raw
            if need_ocr:
                if ocr is None:
                    flags.append("OCR needed but no OCR backend configured")
                    method = "text"
                else:
                    try:
                        text = normalize_text(_ocr_page(page, ocr, language, dpi))
                        if method == "ocr_legacy_font" and garbage_score(text, language).is_garbage:
                            flags.append("OCR output also looks corrupted")
                    except OcrUnavailable as exc:
                        flags.append(f"OCR failed: {exc}")
                        method = "text"
                        text = raw
            results.append(PageResult(i, text, method, report.score, flags))
    return results
