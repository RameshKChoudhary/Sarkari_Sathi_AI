"""Section (Eligibility / Benefits / Documents / How to apply) detection in three languages."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

_RAW_PATTERNS: dict[str, list[str]] = {
    "eligibility": [
        r"eligibility", r"who (?:can apply|is eligible)", r"eligible (?:beneficiaries|persons)",
        r"पात्रता", r"कौन पात्र", r"कोण पात्र",
    ],
    "benefits": [
        r"benefits?", r"financial assistance", r"what you (?:get|receive)",
        r"लाभ", r"फायदे", r"फायदा",
    ],
    "documents": [
        r"documents? required", r"required documents", r"documents? needed",
        r"आवश्यक दस्तावेज़?", r"आवश्यक दस्तावेज", r"आवश्यक कागदपत्रे", r"कागदपत्रे",
    ],
    "how_to_apply": [
        r"how to apply", r"application (?:process|procedure)", r"apply(?: online)?",
        r"आवेदन कैसे करें", r"आवेदन प्रक्रिया", r"अर्ज कसा करावा", r"अर्ज प्रक्रिया", r"अर्ज कसा करायचा",
    ],
    "overview": [r"overview", r"about the scheme", r"परिचय", r"योजनेबद्दल", r"योजना के बारे में"],
}
_COMPILED: list[tuple[str, re.Pattern[str]]] = []
for _sec, _pats in _RAW_PATTERNS.items():
    for _p in _pats:
        _COMPILED.append((_sec, re.compile(r"^(?:\d+[.)]\s*)?" + unicodedata.normalize("NFC", _p) + r"\s*[:：-]?\s*$", re.I)))

MAX_HEADING_CHARS = 60


def detect_heading(line: str) -> Optional[str]:
    """Return the section type if the line is a section heading, else None."""
    s = unicodedata.normalize("NFC", line).strip()
    if not s or len(s) > MAX_HEADING_CHARS:
        return None
    for sec, pat in _COMPILED:
        if pat.match(s):
            return sec
    return None


@dataclass
class Section:
    type: str
    start: int  # char offset of section body in the document text
    end: int
    heading: str = ""


def split_sections(text: str) -> list[Section]:
    """Split document text into sections by heading lines. Text before the first heading
    (title block) becomes the 'overview'. Offsets index into `text`."""
    raw: list[tuple[str, int, int, str]] = []
    cur_type, cur_start, cur_heading = "overview", 0, ""
    pos = 0
    for line in text.split("\n"):
        line_end = pos + len(line)
        sec = detect_heading(line)
        if sec is not None:
            raw.append((cur_type, cur_start, pos, cur_heading))
            cur_type, cur_start, cur_heading = sec, line_end + 1, line.strip()
        pos = line_end + 1
    raw.append((cur_type, cur_start, len(text), cur_heading))
    out: list[Section] = []
    for typ, start, end, heading in raw:
        seg = text[start:end]
        body = seg.strip()
        if not body:
            continue
        lead = len(seg) - len(seg.lstrip())
        out.append(Section(typ, start + lead, start + lead + len(body), heading))
    return out
