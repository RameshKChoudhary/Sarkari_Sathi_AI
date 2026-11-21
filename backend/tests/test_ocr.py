"""OCR smoke test: skipped when Tesseract or its Hindi model is not installed."""
import shutil

import pytest

pytesseract = pytest.importorskip("pytesseract")


def _has_hin() -> bool:
    if not shutil.which("tesseract"):
        return False
    try:
        return "hin" in pytesseract.get_languages(config="")
    except Exception:
        return False


@pytest.mark.skipif(not _has_hin(), reason="tesseract 'hin' model not installed")
def test_ocr_reads_rendered_hindi():
    from PIL import Image, ImageDraw, ImageFont
    import glob
    fonts = glob.glob("/usr/share/fonts/**/FreeSerif.ttf", recursive=True)
    if not fonts:
        pytest.skip("no Devanagari-capable font available")
    img = Image.new("L", (900, 160), 255)
    ImageDraw.Draw(img).text((20, 40), "किसान सम्मान निधि", font=ImageFont.truetype(fonts[0], 64), fill=0)
    text = pytesseract.image_to_string(img, lang="hin")
    assert "किसान" in text
