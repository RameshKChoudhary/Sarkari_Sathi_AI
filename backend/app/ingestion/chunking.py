"""Chunking: structure-aware (by section) and a fixed-window baseline for the ablation."""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..models.schemas import Chunk
from .sections import Section, split_sections

_SENT = re.compile(r"[^.!?।\n]+(?:[.!?।]+|\n|$)\s*")


@dataclass
class DocMeta:
    doc_id: str
    scheme_id: str
    scheme_name: str
    level: str
    language: str
    source_url: str
    publication_date: str | None
    doc_ref: str
    data_status: str = "sample_fixture"
    extraction_method: str = "text"


def unwrap_lines(text: str) -> str:
    """Undo hard line wraps inside paragraphs (PDFs break lines at the page width), keeping
    paragraph breaks and [TABLE] blocks intact."""
    out: list[str] = []
    for part in re.split(r"(\[TABLE\].*?\[/TABLE\])", text, flags=re.S):
        if part.startswith("[TABLE]"):
            out.append(part)
        else:
            paras = [" ".join(p.split()) for p in re.split(r"\n\s*\n", part)]
            out.append("\n\n".join(p for p in paras if p))
    joined = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", joined).replace("\n\n[TABLE]", "\n[TABLE]")


def _make_chunk(meta: DocMeta, idx: int, text: str, start: int, end: int, section_type: str,
                chunking: str, header: bool, page: int | None = None) -> Chunk:
    return Chunk(
        chunk_id=f"{meta.doc_id}:{chunking[0]}{idx:03d}",
        doc_id=meta.doc_id, scheme_id=meta.scheme_id, scheme_name=meta.scheme_name,
        level=meta.level, language=meta.language, source_url=meta.source_url,  # type: ignore[arg-type]
        publication_date=meta.publication_date, section_type=section_type,  # type: ignore[arg-type]
        doc_ref=meta.doc_ref, text=unwrap_lines(text), char_start=start, char_end=end, page=page,
        extraction_method=meta.extraction_method, chunking=chunking,  # type: ignore[arg-type]
        contextual_header=header, data_status=meta.data_status,
    )


def _paragraph_spans(text: str, lo: int, hi: int) -> list[tuple[int, int]]:
    """Paragraph spans inside text[lo:hi]; a [TABLE]...[/TABLE] block is one atomic paragraph."""
    spans: list[tuple[int, int]] = []
    pos = lo
    for block in text[lo:hi].split("\n\n"):
        start = pos + (len(block) - len(block.lstrip()))
        end = pos + len(block.rstrip())
        if block.strip():
            spans.append((start, end))
        pos += len(block) + 2
    return spans


def _sentence_spans(text: str, lo: int, hi: int) -> list[tuple[int, int]]:
    return [(lo + m.start(), lo + m.end()) for m in _SENT.finditer(text[lo:hi]) if m.group().strip()]


def _pack(text: str, spans: list[tuple[int, int]], max_chars: int) -> list[tuple[int, int]]:
    packed: list[tuple[int, int]] = []
    cur: tuple[int, int] | None = None
    for s, e in spans:
        if cur is None:
            cur = (s, e)
        elif e - cur[0] <= max_chars:
            cur = (cur[0], e)
        else:
            packed.append(cur)
            cur = (s, e)
    if cur:
        packed.append(cur)
    return [(s, len(text[:e].rstrip())) for s, e in packed]


def chunk_structure(text: str, meta: DocMeta, max_chars: int = 900) -> list[Chunk]:
    """One chunk per section; sections longer than `max_chars` are split on paragraph, then
    sentence boundaries. Tables are never split."""
    chunks: list[Chunk] = []
    for sec in split_sections(text):
        paras = _paragraph_spans(text, sec.start, sec.end)
        pieces: list[tuple[int, int]] = []
        for ps, pe in paras:
            if pe - ps > max_chars and "[TABLE]" not in text[ps:pe]:
                pieces.extend(_sentence_spans(text, ps, pe))
            else:
                pieces.append((ps, pe))
        for s, e in _pack(text, pieces, max_chars):
            chunks.append(_make_chunk(meta, len(chunks), text[s:e].strip(), s, e, sec.type, "structure", True))
    return chunks


def _dominant_section(sections: list[Section], start: int, end: int) -> str:
    best, best_len = "overview", 0
    for s in sections:
        ov = min(end, s.end) - max(start, s.start)
        if ov > best_len:
            best, best_len = s.type, ov
    return best


def chunk_fixed(text: str, meta: DocMeta, size: int = 350, overlap: int = 60) -> list[Chunk]:
    """Naive sliding window baseline (no section awareness, no contextual header).
    `section_type` = section covering most of the window so that retrieval can still be scored
    against section-level gold passages."""
    sections = split_sections(text)
    chunks: list[Chunk] = []
    n, start = len(text), 0
    while start < n:
        end = min(start + size, n)
        if end < n:  # snap to whitespace
            snap = text.rfind(" ", start + size // 2, end)
            snap_nl = text.rfind("\n", start + size // 2, end)
            end = max(snap, snap_nl) if max(snap, snap_nl) > start else end
        piece = text[start:end].strip()
        if piece:
            sec = _dominant_section(sections, start, end)
            chunks.append(_make_chunk(meta, len(chunks), piece, start, end, sec, "fixed", False))
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks
