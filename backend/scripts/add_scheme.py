#!/usr/bin/env python3
"""Add a real government scheme PDF to the corpus and re-ingest.

    python backend/scripts/add_scheme.py --pdf ~/Downloads/pmay.pdf --scheme-id pmay_u \
        --name "PM Awas Yojana (Urban)" --lang en --level central \
        --url https://pmay-urban.gov.in --date 2024-06-01 --alias "pmay urban" --alias "awas yojana"

* The PDF is copied to data/raw/pdfs/<scheme-id>.<lang>.pdf and registered in data/raw/manifest.json.
* Scanned / legacy-font pages are detected and OCR'd automatically (Hindi/Marathi need tesseract data;
  run scripts/setup_tessdata.sh once).
* Use the real source URL and publication date. If the date is unknown, omit --date (stored as unavailable).
* Re-run per language (--lang hi / --lang mr) to add translations of the same scheme.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", type=Path, required=True)
    ap.add_argument("--scheme-id", required=True, help="stable id, e.g. pmay_u")
    ap.add_argument("--name", required=True, help="scheme name in the document's language")
    ap.add_argument("--lang", choices=["en", "hi", "mr"], required=True)
    ap.add_argument("--level", choices=["central", "state"], required=True)
    ap.add_argument("--url", required=True, help="official source URL of the document")
    ap.add_argument("--date", default=None, help="publication date YYYY-MM-DD (omit if unknown)")
    ap.add_argument("--doc-ref", default=None, help="e.g. GR number")
    ap.add_argument("--alias", action="append", default=[], help="alternative names/romanisations (repeatable)")
    ap.add_argument("--no-ingest", action="store_true")
    a = ap.parse_args()
    if not a.pdf.exists():
        sys.exit(f"PDF not found: {a.pdf}")

    pdf_dir = ROOT / "data/raw/pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{a.scheme_id}.{a.lang}.pdf"
    shutil.copy2(a.pdf, pdf_dir / fname)
    mpath = ROOT / "data/raw/manifest.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else []
    manifest = [m for m in manifest if m["file"] != fname]
    manifest.append({"file": fname, "scheme_id": a.scheme_id, "scheme_name": a.name, "level": a.level, "language": a.lang,
                     "source_url": a.url, "publication_date": a.date, "doc_ref": a.doc_ref or fname,
                     "data_status": "official_document"})
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    if a.alias:  # extend the lexicon so romanised / alternative names resolve to the scheme
        lpath = ROOT / "data/raw/lexicon.json"
        lex = json.loads(lpath.read_text(encoding="utf-8")) if lpath.exists() else {"groups": []}
        gid = f"scheme:{a.scheme_id}"
        grp = next((g for g in lex["groups"] if g["id"] == gid), None)
        if grp is None:
            grp = {"id": gid, "triggers": [], "terms": [], "en": []}
            lex["groups"].append(grp)
        grp["triggers"] = sorted(set(grp["triggers"] + a.alias + [a.name]))
        grp["terms"] = sorted(set(grp["terms"] + [a.name]))
        if a.lang == "en":
            grp["en"] = [a.name]
        lpath.write_text(json.dumps(lex, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"registered {fname}")
    if not a.no_ingest:
        subprocess.run([sys.executable, "-I", str(Path(__file__).parent / "ingest.py")], check=True)
        print("Restart the API (or POST nothing - it loads chunks at startup) to serve the new scheme.")


if __name__ == "__main__":
    main()
