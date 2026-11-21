"""End-to-end ingestion: manifest of PDFs -> cleaned text -> chunks (+ scheme catalog)."""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Optional

from pydantic import BaseModel

from ..models.schemas import Chunk, SchemeSummary
from .chunking import DocMeta, chunk_fixed, chunk_structure
from .cleaning import normalize_text, remove_repeated_lines
from .ocr import OcrBackend
from .pdf_extract import OcrMode, extract_pdf

logger = logging.getLogger(__name__)


class ManifestEntry(BaseModel):
    file: str  # path relative to the pdf root
    scheme_id: str
    scheme_name: str
    level: str
    language: str
    source_url: str
    publication_date: Optional[str] = None
    doc_ref: str = ""
    data_status: str = "sample_fixture"


class IngestedDoc(BaseModel):
    doc_id: str
    entry: ManifestEntry
    n_pages: int
    methods: list[str]
    flags: list[str]
    removed_header_footer: list[str]
    n_chars: int


def ingest_entry(
    entry: ManifestEntry, pdf_root: Path, ocr: Optional[OcrBackend] = None,
    ocr_mode: OcrMode = "auto", dpi: int = 300,
) -> tuple[IngestedDoc, list[Chunk], list[Chunk]]:
    path = pdf_root / entry.file
    pages = extract_pdf(path, entry.language, ocr=ocr, mode=ocr_mode, dpi=dpi)
    cleaned, removed = remove_repeated_lines([p.text for p in pages])
    # page markers are not kept in the text; join pages with a blank line
    text = normalize_text("\n\n".join(c for c in cleaned if c))
    doc_id = f"{entry.scheme_id}.{entry.language}"
    methods = sorted({p.method for p in pages})
    meta = DocMeta(
        doc_id=doc_id, scheme_id=entry.scheme_id, scheme_name=entry.scheme_name, level=entry.level,
        language=entry.language, source_url=entry.source_url, publication_date=entry.publication_date,
        doc_ref=entry.doc_ref or entry.file, data_status=entry.data_status,
        extraction_method=methods[0] if len(methods) == 1 else "+".join(methods),
    )
    structured = chunk_structure(text, meta)
    fixed = chunk_fixed(text, meta)
    doc = IngestedDoc(
        doc_id=doc_id, entry=entry, n_pages=len(pages), methods=methods,
        flags=[f"p{p.page_no}: {f}" for p in pages for f in p.flags],
        removed_header_footer=removed, n_chars=len(text),
    )
    logger.info("ingested %s: %d pages, %d structure chunks, %d fixed chunks", doc_id, len(pages), len(structured), len(fixed))
    return doc, structured, fixed


def build_catalog(entries: Iterable[ManifestEntry], chunks: list[Chunk]) -> list[SchemeSummary]:
    by_scheme: dict[str, list[ManifestEntry]] = defaultdict(list)
    for e in entries:
        by_scheme[e.scheme_id].append(e)
    n_chunks: dict[str, int] = defaultdict(int)
    sections: dict[str, set[str]] = defaultdict(set)
    for c in chunks:
        n_chunks[c.scheme_id] += 1
        if c.section_type != "overview":
            sections[c.scheme_id].add(c.section_type)
    out: list[SchemeSummary] = []
    for sid, es in by_scheme.items():
        out.append(SchemeSummary(
            scheme_id=sid, names={e.language: e.scheme_name for e in es}, level=es[0].level,  # type: ignore[arg-type]
            languages=sorted({e.language for e in es}), sections=sorted(sections[sid]),
            official_url=es[0].source_url,
            data_status=es[0].data_status,
            publication_date=es[0].publication_date, n_chunks=n_chunks[sid],
        ))
    return sorted(out, key=lambda s: s.names.get("en", s.scheme_id))


def write_jsonl(path: Path, rows: Iterable[BaseModel]) -> int:
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(r.model_dump_json() + "\n")
            n += 1
    return n


def read_chunks(path: Path) -> list[Chunk]:
    with path.open(encoding="utf-8") as f:
        return [Chunk.model_validate_json(line) for line in f if line.strip()]


def load_manifest(path: Path) -> list[ManifestEntry]:
    return [ManifestEntry.model_validate(x) for x in json.loads(path.read_text(encoding="utf-8"))]


def ingest_manifest(
    manifest_path: Path, pdf_root: Path, out_dir: Path, ocr: Optional[OcrBackend] = None,
    ocr_mode: OcrMode = "auto", dpi: int = 300,
) -> dict:
    """Ingest every PDF in the manifest and (re)write the processed artefacts."""
    entries = load_manifest(manifest_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    docs: list[IngestedDoc] = []
    structured: list[Chunk] = []
    fixed: list[Chunk] = []
    for e in entries:
        try:
            d, s, f = ingest_entry(e, pdf_root, ocr, ocr_mode, dpi)
        except Exception as exc:
            logger.error("failed to ingest %s: %s", e.file, exc)
            continue
        docs.append(d)
        structured += s
        fixed += f
    write_jsonl(out_dir / "chunks_structure.jsonl", structured)
    write_jsonl(out_dir / "chunks_fixed.jsonl", fixed)
    write_jsonl(out_dir / "docs.jsonl", docs)
    catalog = build_catalog([d.entry for d in docs], structured)
    (out_dir / "schemes.json").write_text(
        json.dumps([c.model_dump() for c in catalog], ensure_ascii=False, indent=2), encoding="utf-8")
    report = {
        "documents": len(docs), "structure_chunks": len(structured), "fixed_chunks": len(fixed),
        "ocr_used": [d.doc_id for d in docs if any(m.startswith("ocr") for m in d.methods)],
        "flags": {d.doc_id: d.flags for d in docs if d.flags},
    }
    (out_dir / "ingestion_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
