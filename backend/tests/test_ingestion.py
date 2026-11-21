import pymupdf
import pytest

from app.ingestion.chunking import DocMeta, chunk_fixed, chunk_structure, unwrap_lines
from app.ingestion.cleaning import normalize_text, remove_repeated_lines
from app.ingestion.legacy_fonts import font_names_suggest_legacy, garbage_score
from app.ingestion.pdf_extract import extract_pdf
from app.ingestion.sections import detect_heading, split_sections

META = DocMeta(doc_id="t.en", scheme_id="t", scheme_name="Test", level="central", language="en",
               source_url="https://x", publication_date=None, doc_ref="r")


def test_normalize_nfc_and_duplicate_marks():
    assert normalize_text("क्षेेत्रात") == "क्षेत्रात"  # Chromium-style doubled vowel sign collapsed
    assert normalize_text("A B  C") == "A B C"


def test_repeated_header_footer_removed():
    pages = ["HEADER\nbody one\nPage 1", "HEADER\nbody two\nPage 2", "HEADER\nbody three\nPage 3"]
    cleaned, removed = remove_repeated_lines(pages)
    assert all("HEADER" not in p and "Page" not in p for p in cleaned)
    assert cleaned[1] == "body two" and removed


def test_single_page_is_untouched():
    cleaned, removed = remove_repeated_lines(["HEADER\nbody"])
    assert cleaned == ["HEADER\nbody"] and removed == []


@pytest.mark.parametrize("line,sec", [("Eligibility", "eligibility"), ("पात्रता", "eligibility"),
                                      ("आवश्यक कागदपत्रे", "documents"), ("अर्ज कसा करावा", "how_to_apply"),
                                      ("आवेदन कैसे करें", "how_to_apply"), ("Benefits", "benefits")])
def test_heading_detection(line, sec):
    assert detect_heading(line) == sec


def test_structure_chunking_follows_sections():
    text = "Title\n\nEligibility\nAll farmers can join.\n\nBenefits\nRs 6000 per year.\n\nHow to Apply\nVisit the CSC."
    chunks = chunk_structure(text, META)
    secs = [c.section_type for c in chunks]
    assert secs == ["overview", "eligibility", "benefits", "how_to_apply"] or secs[-3:] == ["eligibility", "benefits", "how_to_apply"]
    assert all(c.scheme_id == "t" and c.source_url == "https://x" and c.chunking == "structure" for c in chunks)
    assert [c for c in chunks if c.section_type == "benefits"][0].text.endswith("6000 per year.")


def test_fixed_chunking_overlaps_and_covers():
    text = " ".join(f"word{i}" for i in range(200))
    chunks = chunk_fixed(text, META, size=200, overlap=40)
    assert len(chunks) > 3 and all(len(c.text) <= 260 for c in chunks)
    assert chunks[0].chunking == "fixed"


def test_unwrap_keeps_tables():
    t = "line one\nline two\n\n[TABLE]\n| a | b |\n| 1 | 2 |\n[/TABLE]"
    out = unwrap_lines(t)
    assert "line one line two" in out and "| a | b |\n| 1 | 2 |" in out


def test_legacy_font_and_garbage_detection():
    assert font_names_suggest_legacy(["KrutiDev010", "Arial"])
    assert not font_names_suggest_legacy(["Arial", "Mangal"])
    assert garbage_score("ekuuh; eq[;ea=h y kM+dh cgu ;kstuk ds fy, ik= gSa", "hi").is_garbage
    assert garbage_score("(cid:12)(cid:45)(cid:77)  �� text", "hi").score > 0.3
    assert not garbage_score("पीएम किसान योजना के लिए पात्र किसान परिवार", "hi").is_garbage
    assert not garbage_score("Farmers receive income support every year.", "en").is_garbage


def make_pdf(path, pages, with_table=False):
    doc = pymupdf.open()
    for i, body in enumerate(pages, 1):
        p = doc.new_page()
        p.insert_text((72, 40), "GOVT SAMPLE HEADER", fontsize=9)
        p.insert_text((72, 100), body, fontsize=11)
        p.insert_text((72, 800), f"Page {i}", fontsize=9)
    doc.save(path)


def test_extract_text_pdf_removes_boilerplate(tmp_path):
    pdf = tmp_path / "a.pdf"
    make_pdf(pdf, ["Eligibility\nAll farmers.", "Benefits\nRs 6000 per year."])
    pages = extract_pdf(pdf, "en", ocr=None, mode="off")
    assert len(pages) == 2 and pages[0].method == "text"
    cleaned, removed = remove_repeated_lines([p.text for p in pages])
    assert "HEADER" not in "\n".join(cleaned) and removed


def test_scanned_pdf_triggers_ocr_backend(tmp_path):
    class FakeOCR:
        def ocr_png(self, png, language):
            return "Eligibility OCR TEXT recovered from the scanned page with enough characters"
    doc = pymupdf.open()
    page = doc.new_page()
    page.draw_rect(pymupdf.Rect(50, 50, 200, 200), fill=(0, 0, 0))  # no text layer at all
    pdf = tmp_path / "scan.pdf"
    doc.save(pdf)
    pages = extract_pdf(pdf, "en", ocr=FakeOCR(), mode="auto")
    assert pages[0].method == "ocr_scanned" and "OCR TEXT" in pages[0].text
    assert any("no text layer" in f for f in pages[0].flags)


def test_sample_pdf_table_is_preserved(corpus_ready):
    from pathlib import Path
    pdf = Path(__file__).resolve().parents[2] / "data/raw/pdfs/mudra.en.pdf"
    if not pdf.exists():
        pytest.skip("sample PDFs not built")
    text = "\n".join(p.text for p in extract_pdf(pdf, "en", ocr=None, mode="off"))
    assert "[TABLE]" in text and "Shishu" in text and "50,000" in text
