"""OCR backends. Tesseract (hin/mar/eng) is implemented; the Protocol is the extension point
for alternatives such as Surya (not implemented here)."""
from __future__ import annotations

import io
import logging
import os
from pathlib import Path
from typing import Optional, Protocol

logger = logging.getLogger(__name__)


class OcrBackend(Protocol):
    name: str

    def ocr_png(self, png_bytes: bytes, language: str) -> str: ...


class OcrUnavailable(RuntimeError):
    pass


class TesseractOCR:
    name = "tesseract"

    def __init__(self, tessdata_dir: Optional[Path] = None, psm: int = 3) -> None:
        self.psm = psm
        self.tessdata_dir = self._resolve_dir(tessdata_dir)
        self._langs: Optional[set[str]] = None

    @staticmethod
    def _resolve_dir(explicit: Optional[Path]) -> Optional[Path]:
        if explicit and Path(explicit).exists():
            return Path(explicit)
        env = os.environ.get("TESSDATA_PREFIX")
        return Path(env) if env else None

    def _config(self) -> str:
        cfg = f"--psm {self.psm}"
        if self.tessdata_dir:
            cfg += f' --tessdata-dir "{self.tessdata_dir}"'
        return cfg

    def available_langs(self) -> set[str]:
        if self._langs is None:
            try:
                import pytesseract

                self._langs = set(pytesseract.get_languages(config=self._config()))
            except Exception as exc:  # tesseract binary missing, etc.
                raise OcrUnavailable(f"Tesseract not usable: {exc}") from exc
        return self._langs

    def lang_string(self, doc_language: str) -> str:
        """Map document language -> tesseract model string, with a documented fallback:
        Marathi uses the Devanagari-capable Hindi model if `mar` data is missing."""
        langs = self.available_langs()
        primary = {"en": "eng", "hi": "hin", "mr": "mar"}.get(doc_language, "eng")
        if primary not in langs:
            fallback = "hin" if doc_language == "mr" and "hin" in langs else "eng"
            logger.warning("tesseract model %r missing; falling back to %r", primary, fallback)
            primary = fallback
        parts = [primary] + (["eng"] if primary != "eng" and "eng" in langs else [])
        return "+".join(parts)

    def ocr_png(self, png_bytes: bytes, language: str) -> str:
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(io.BytesIO(png_bytes))
            return pytesseract.image_to_string(
                img, lang=self.lang_string(language), config=self._config()
            )
        except OcrUnavailable:
            raise
        except Exception as exc:
            raise OcrUnavailable(f"OCR failed: {exc}") from exc
