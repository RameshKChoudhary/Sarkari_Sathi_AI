"""Unicode normalisation and PDF text clean-up (NFC, artefact repair, header/footer removal)."""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

_REMOVE = dict.fromkeys(map(ord, "​﻿­⁠"), None)
# Identical combining marks repeated (e.g. "पर्यंंत") never occur in valid Devanagari;
# some PDF producers emit them. Collapse to a single mark.
_REPEATED_MARK = re.compile(r"([ऀ-ःऺ़ा-ॏ॑-ॗॢॣ])\1+")
_LATIN_HYPHEN_BREAK = re.compile(r"([A-Za-z])-\n([a-z])")


def normalize_text(text: str) -> str:
    """NFC-normalise and repair common extraction artefacts. Keeps line structure."""
    text = unicodedata.normalize("NFC", text)
    text = text.translate(_REMOVE).replace(" ", " ").replace("\r", "\n")
    text = _REPEATED_MARK.sub(r"\1", text)
    text = _LATIN_HYPHEN_BREAK.sub(r"\1\2", text)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.split("\n")]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _line_key(line: str) -> str:
    """Key used to recognise the same header/footer on different pages (digits masked)."""
    k = unicodedata.normalize("NFC", line).lower().strip()
    k = re.sub(r"[0-9०-९]+", "#", k)
    return re.sub(r"\s+", " ", k)


def remove_repeated_lines(
    pages: list[str], edge: int = 3, min_ratio: float = 0.6
) -> tuple[list[str], list[str]]:
    """Remove running headers/footers: lines near the top/bottom of a page that repeat
    on most pages (page numbers are masked). Needs at least 2 pages. Returns
    (cleaned_pages, removed_line_keys)."""
    n = len(pages)
    if n < 2:
        return pages, []
    split = [p.split("\n") for p in pages]
    counts: Counter[str] = Counter()
    for lines in split:
        nonempty = [ln for ln in lines if ln.strip()]
        cands = nonempty[:edge] + nonempty[-edge:]
        for key in {_line_key(ln) for ln in cands}:
            counts[key] += 1
    threshold = max(2, math.ceil(min_ratio * n))
    bad = {k for k, c in counts.items() if c >= threshold and k}
    cleaned: list[str] = []
    for lines in split:
        nonempty_idx = [i for i, ln in enumerate(lines) if ln.strip()]
        edge_idx = set(nonempty_idx[:edge] + nonempty_idx[-edge:])
        kept = [ln for i, ln in enumerate(lines) if not (i in edge_idx and _line_key(ln) in bad)]
        cleaned.append("\n".join(kept).strip())
    return cleaned, sorted(bad)
