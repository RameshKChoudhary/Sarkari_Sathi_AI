"""Detection of legacy-font (non-Unicode) Indic text and other garbled extraction.

Many Marathi/Hindi government PDFs were typeset with fonts such as Kruti Dev, DevLys or
Shusha that map Devanagari glyphs onto Latin code points. PyMuPDF then returns text like
"çk/kkuea=h" instead of Devanagari. We score extracted text with several independent
signals and fall back to OCR when the score is high.

NOTE: the heuristics are validated on synthetic strings in the unit tests; they have not
been validated on a corpus of real legacy-font government PDFs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

LEGACY_FONT_HINTS = (
    "kruti", "krutidev", "devlys", "shusha", "shivaji", "chanakya", "walkman",
    "apsdv", "aps-dv", "sulekha", "akruti", "dvb-tt", "dv-tt", "dvbw", "dvw-tt",
)
_DEV = re.compile(r"[ऀ-ॿ]")
_LATIN = re.compile(r"[A-Za-z]")
_PUA = re.compile(r"[-�]")
_LATIN_EXT = re.compile(r"[À-ɏ]")
_SYMBOLS = re.compile(r"[/\\;~^`\[\]{}|<>@#$%&*=+]")
# dependent vowel signs, virama, anusvara etc. at the start of a token or after a digit
_ORPHAN_MARK = re.compile(r"(?:(?<=\s)|^)[ऀ-ःऺऻ़ा-ॏ]")


@dataclass
class GarbageReport:
    score: float
    reasons: list[str] = field(default_factory=list)

    @property
    def is_garbage(self) -> bool:
        return self.score >= 0.5


def font_names_suggest_legacy(font_names: list[str]) -> bool:
    joined = " ".join(font_names).lower().replace(" ", "").replace("_", "")
    return any(h.replace(" ", "") in joined for h in LEGACY_FONT_HINTS)


def garbage_score(text: str, expected_lang: str = "en") -> GarbageReport:
    """Return a 0..1 score that the text is corrupted / legacy-encoded."""
    chars = [c for c in text if not c.isspace()]
    n = len(chars)
    if n < 15:
        return GarbageReport(0.0, ["too short to judge"])
    reasons: list[str] = []
    score = 0.0

    pua = len(_PUA.findall(text)) / n
    if pua > 0.02:
        score += 0.6
        reasons.append(f"private-use/replacement chars {pua:.1%}")

    n_dev = len(_DEV.findall(text))
    n_lat = len(_LATIN.findall(text))
    letters = max(n_dev + n_lat, 1)
    dev_ratio = n_dev / letters

    if expected_lang in ("hi", "mr"):
        sym = len(_SYMBOLS.findall(text)) / max(n_lat, 1)
        ext = len(_LATIN_EXT.findall(text)) / n
        if dev_ratio < 0.2 and sym > 0.08:
            score += 0.5
            reasons.append(f"Latin text with dense symbols ({sym:.2f}/letter) in a Devanagari document")
        if dev_ratio < 0.2 and ext > 0.12:
            score += 0.4
            reasons.append(f"extended-Latin characters {ext:.1%} typical of Kruti-style mapping")

    if n_dev >= 20:
        orphans = len(_ORPHAN_MARK.findall(text)) / n_dev
        if orphans > 0.03:
            score += 0.5
            reasons.append(f"orphan combining marks {orphans:.1%}")

    return GarbageReport(min(score, 1.0), reasons)
