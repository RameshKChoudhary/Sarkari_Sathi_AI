"""Citation verification: every factual sentence must carry [n] markers that point to a
retrieved passage, and the sentence must be lexically supported by those passages (all numbers
present, enough content words in common). Unsupported sentences are removed.

This is a deterministic *lexical* check: it catches invented numbers, wrong citation ids and
uncited claims. It cannot catch a fluent but semantically wrong paraphrase."""
from __future__ import annotations

import re

from ..models.schemas import VerificationReport
from ..retrieval.tokenize import normalize_for_match, stem_match, word_tokens

_MARK = re.compile(r"\[(\d+)\]")
_NUM = re.compile(r"\d+(?:\.\d+)?")
# split after sentence punctuation, or after a citation marker, but never between a sentence and
# its own trailing "[n]" marker
_SPLIT = re.compile(r"(?<=[.!?।])\s+(?=[^\s\[])|(?<=\])\s+(?=[^\s\[|])|\n+")


def split_units(text: str) -> list[str]:
    return [u.strip() for u in _SPLIT.split(text) if u and u.strip()]


def strip_markers(s: str) -> str:
    return re.sub(r"\s*\[\d+\]", "", s).strip()


def support_score(sentence: str, passage: str) -> tuple[float, bool]:
    """(content-word coverage in [0,1], all numbers present?)"""
    sent = strip_markers(sentence)
    nums = set(_NUM.findall(normalize_for_match(sent)))
    pass_norm = normalize_for_match(passage)
    pnums = set(_NUM.findall(pass_norm))
    nums_ok = nums <= pnums
    stoks = [t for t in word_tokens(sent) if len(t) > 1 and not t.isdigit()]
    ptoks = word_tokens(passage)
    if not stoks:
        return 1.0, nums_ok
    hit = sum(1 for t in stoks if any(stem_match(t, p) for p in ptoks))
    return hit / len(stoks), nums_ok


def is_heading(unit: str) -> bool:
    u = unit.strip()
    return u.startswith("**") or u.endswith(":") or u.startswith("[TABLE]") or u.startswith("|") or u.startswith("[/TABLE]")


def verify_answer(answer: str, passages: dict[int, str], min_support: float = 0.5) -> tuple[str, VerificationReport]:
    """`passages` maps citation id -> passage text."""
    rep = VerificationReport()
    kept: list[str] = []
    for unit in split_units(answer):
        ids = [int(i) for i in _MARK.findall(unit)]
        if is_heading(unit) and not ids:
            kept.append(unit)
            continue
        rep.checked_sentences += 1
        bad = [i for i in ids if i not in passages]
        if bad:
            rep.invalid_citations.extend(bad)
        good = [i for i in ids if i in passages]
        if not good:
            rep.removed.append(unit)
            rep.notes.append("removed: no valid citation")
            continue
        text = " ".join(passages[i] for i in good)
        cov, nums_ok = support_score(unit, text)
        if cov < min_support or not nums_ok:
            rep.removed.append(unit)
            rep.notes.append(f"removed: unsupported (coverage {cov:.2f}, numbers_ok={nums_ok})")
            continue
        kept.append(unit)
        rep.kept_sentences += 1
    rep.ok = rep.kept_sentences > 0
    return "\n".join(kept), rep


def cited_ids(answer: str) -> set[int]:
    return {int(i) for i in _MARK.findall(answer)}
