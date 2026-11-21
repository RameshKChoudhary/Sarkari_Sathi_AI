#!/usr/bin/env python3
"""Render the SAMPLE FIXTURE schemes (scripts/sample_data/content.py) into real PDFs.

Why PDFs? So the ingestion pipeline (PyMuPDF extraction, header/footer removal, table
preservation, structure-aware chunking) is exercised end-to-end exactly as it would be with
real government PDFs. One PDF per (scheme, language); each has two pages with a repeating
running header/footer so header/footer removal is tested.

Output:  data/raw/pdfs/<scheme>.<lang>.pdf   +   data/raw/manifest.json
Needs:   playwright + chromium (``pip install playwright && playwright install chromium``)
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).parent))

from app.models.schemas import LANGUAGES, SECTION_LABELS  # noqa: E402
from sample_data.content import NOTICE, SCHEMES, SECTION_ORDER  # noqa: E402

LANG_TITLES = {"en": "Scheme fact sheet", "hi": "योजना तथ्य-पत्र", "mr": "योजना माहितीपत्रक"}
META_LABELS = {
    "en": ("Level", "Language", "Official portal"),
    "hi": ("स्तर", "भाषा", "आधिकारिक पोर्टल"),
    "mr": ("स्तर", "भाषा", "अधिकृत पोर्टल"),
}
LEVEL_NAMES = {
    "en": {"central": "Central scheme", "state": "State scheme (Maharashtra)"},
    "hi": {"central": "केंद्रीय योजना", "state": "राज्य योजना (महाराष्ट्र)"},
    "mr": {"central": "केंद्रीय योजना", "state": "राज्य योजना (महाराष्ट्र)"},
}
LANG_NAMES = {"en": "English", "hi": "हिंदी", "mr": "मराठी"}
FONT = "'FreeSerif','FreeSans','Noto Sans Devanagari','Mangal',serif"


def render_html(scheme: dict, lang: str) -> str:
    labels = SECTION_LABELS[lang]
    lv, lg, url = META_LABELS[lang]
    parts = [
        "<html><head><meta charset='utf-8'><style>",
        f"body{{font-family:{FONT};font-size:13pt;line-height:1.55;margin:0}}",
        "h1{font-size:20pt;margin:0 0 6pt}h2{font-size:15pt;margin:16pt 0 4pt;border-bottom:1px solid #999}",
        "p{margin:4pt 0}.meta{font-size:10.5pt;color:#333}",
        "table{border-collapse:collapse;margin:8pt 0}td,th{border:1px solid #000;padding:4pt 8pt}",
        ".pb{break-before:page}",
        "</style></head><body>",
        f"<h1>{html.escape(scheme['names'][lang])}</h1>",
        f"<p class='meta'>{LANG_TITLES[lang]}</p>",
        f"<p class='meta'>{lv}: {LEVEL_NAMES[lang][scheme['level']]}</p>",
        f"<p class='meta'>{lg}: {LANG_NAMES[lang]}</p>",
        f"<p class='meta'>{url}: {html.escape(scheme['url'])}</p>",
    ]
    for sec in SECTION_ORDER:
        cls = " class='pb'" if sec == "documents" else ""
        parts.append(f"<h2{cls}>{html.escape(labels[sec])}</h2>")
        parts.append(f"<p>{html.escape(scheme['sections'][sec][lang])}</p>")
        table = scheme.get("tables", {}).get(sec, {}).get(lang)
        if table:
            rows = "".join(
                "<tr>" + "".join(f"<{'th' if i == 0 else 'td'}>{html.escape(c)}</{'th' if i == 0 else 'td'}>" for c in r) + "</tr>"
                for i, r in enumerate(table)
            )
            parts.append(f"<table>{rows}</table>")
    parts.append("</body></html>")
    return "".join(parts)


def main() -> None:
    from playwright.sync_api import sync_playwright

    out_dir = ROOT / "data" / "raw" / "pdfs"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        for scheme in SCHEMES:
            for lang in LANGUAGES:
                page.set_content(render_html(scheme, lang))
                fname = f"{scheme['id']}.{lang}.pdf"
                header = (f"<div style=\"font-family:FreeSans;font-size:8px;width:100%;text-align:center;color:#555\">"
                          f"{html.escape(NOTICE[lang])}</div>")
                footer = ("<div style=\"font-family:FreeSans;font-size:8px;width:100%;text-align:center;color:#555\">"
                          "Page <span class='pageNumber'></span></div>")
                page.pdf(path=str(out_dir / fname), format="A4", print_background=True,
                         display_header_footer=True, header_template=header, footer_template=footer,
                         margin={"top": "22mm", "bottom": "20mm", "left": "18mm", "right": "18mm"})
                manifest.append({
                    "file": fname, "scheme_id": scheme["id"], "scheme_name": scheme["names"][lang],
                    "level": scheme["level"], "language": lang, "source_url": scheme["url"],
                    "publication_date": None,  # unavailable: fixtures have no real publication date
                    "doc_ref": f"SAMPLE-FIXTURE/{scheme['id']}/{lang}",
                    "data_status": "sample_fixture",
                })
        browser.close()
    (ROOT / "data" / "raw" / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(manifest)} PDFs to {out_dir}")


if __name__ == "__main__":
    main()
