"""Answer composition: LLM prompt (grounded, cited) and the offline extractive composer."""
from __future__ import annotations

import re
from typing import Optional

from ..models.schemas import Chunk, SECTION_LABELS, SearchHit, SourceCard
from ..retrieval.tokenize import stem_match, word_tokens
from .i18n import CROSS_LANG_NOTE, LANG_NAME, LANG_NAME_NATIVE
from .verify import split_units, strip_markers

NOT_FOUND = "NOT_FOUND"

SYSTEM_PROMPT = """You are SarkariSathi AI, an assistant that explains Indian government schemes.
Rules (follow strictly):
1. Answer ONLY from the numbered passages below. Never use outside knowledge.
2. Cite every sentence with the passage number in square brackets, e.g. [1] or [1][2].
3. Never invent eligibility rules, income limits, ages, amounts, dates or deadlines. Copy numbers exactly.
4. If the passages do not contain the answer, reply with exactly: NOT_FOUND
5. Write the whole answer in {lang_name} ({lang_native}), using {script}. Keep scheme names and numbers as in the passages. If the user wrote {lang_name} in Latin letters, still answer in {script}.
6. Be concise: at most 5 short sentences or bullet points. No preamble."""


def build_system_prompt(lang: str) -> str:
    script = "English" if lang == "en" else "Devanagari script"
    return SYSTEM_PROMPT.format(lang_name=LANG_NAME[lang], lang_native=LANG_NAME_NATIVE[lang], script=script)


def build_user_prompt(query: str, cards: list[SourceCard]) -> str:
    blocks = [
        f"[{c.id}] {c.scheme_name} — {SECTION_LABELS[c.language][c.section_type]} ({LANG_NAME[c.language]})\n{c.text}"
        for c in cards
    ]
    return "Passages:\n\n" + "\n\n".join(blocks) + f"\n\nQuestion: {query}\nAnswer:"


def passage_units(text: str) -> list[str]:
    """Split a passage into citable units; a [TABLE]..[/TABLE] block stays whole."""
    units: list[str] = []
    for part in re.split(r"(\[TABLE\].*?\[/TABLE\])", text, flags=re.S):
        part = part.strip()
        if not part:
            continue
        if part.startswith("[TABLE]"):
            rows = [ln for ln in part.splitlines() if ln.startswith("|")]
            units.append("\n".join(rows))
        else:
            units.extend(split_units(part))
    return units


def best_sentence(passage: str, reference: str) -> Optional[str]:
    """Sentence of `passage` that overlaps most with `reference` (used for highlighting)."""
    ref = [t for t in word_tokens(reference) if len(t) > 1]
    best, best_score = None, 0.0
    for u in passage_units(passage):
        if u.startswith("|"):
            continue
        toks = [t for t in word_tokens(u) if len(t) > 1]
        if not toks or not ref:
            continue
        score = sum(1 for t in ref if any(stem_match(t, p) for p in toks)) / len(ref)
        if score > best_score:
            best, best_score = u, score
    return best


def extractive_answer(
    lang: str, hits: list[SearchHit], sibling: dict[tuple[str, str, str], Chunk], max_passages: int = 2, score_ratio: float = 0.0,
) -> tuple[str, list[Chunk]]:
    """Offline answer without an LLM: verbatim sentences of the best passage(s), each with a
    citation id. If the passage exists in the user's language (parallel corpus) that version
    is used, otherwise the original passage is quoted with a note. Returns (answer, chunks
    in citation order; ids are assigned later by the caller)."""
    chosen: list[Chunk] = []
    top = hits[0].chunk
    for h in hits:
        if h.chunk.scheme_id != top.scheme_id:
            continue
        if chosen and h.score < score_ratio * hits[0].score:
            continue
        c = sibling.get((h.chunk.scheme_id, h.chunk.section_type, lang), h.chunk)
        if c.chunk_id not in {x.chunk_id for x in chosen}:
            chosen.append(c)
        if len(chosen) >= max_passages:
            break
    lines: list[str] = []
    for idx, c in enumerate(chosen, start=1):
        label = SECTION_LABELS[c.language][c.section_type]
        lines.append(f"**{c.scheme_name} — {label}**")
        units = passage_units(c.text)
        for u in units:
            lines.append(f"{u} [{idx}]")
        if c.language != lang:
            lines.append(CROSS_LANG_NOTE[lang].format(src=LANG_NAME[c.language]))
    return "\n".join(lines), chosen


def clean_llm_text(text: str) -> str:
    return re.sub(r"^\s*(answer|उत्तर)\s*:\s*", "", text.strip(), flags=re.I)


def answer_text_for_display(answer: str) -> str:
    """Answer shown to the user keeps [n] markers (they link to the source cards)."""
    return answer.strip()
