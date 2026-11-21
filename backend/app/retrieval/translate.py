"""Translation to English for strategies B (translate query), C (translate docs), D (index both)."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, Protocol

logger = logging.getLogger(__name__)

LANG_NAMES = {"en": "English", "hi": "Hindi", "mr": "Marathi"}


class Translator(Protocol):
    name: str

    def translate(self, text: str, source_lang: str, target_lang: str = "en") -> str: ...


class LLMTranslator:
    """Translate with any chat LLM (Groq Llama 3.3 70B by default). Results are cached on disk
    so that document translation (strategy C/D) is paid for once."""

    def __init__(self, llm, cache_path: Optional[Path] = None) -> None:  # llm: LLMClient
        self.llm = llm
        self.name = f"llm:{getattr(llm, 'model', '?')}"
        self.cache_path = cache_path
        self._cache: dict[str, str] = {}
        if cache_path and cache_path.exists():
            self._cache = json.loads(cache_path.read_text(encoding="utf-8"))

    def translate(self, text: str, source_lang: str, target_lang: str = "en") -> str:
        if source_lang == target_lang:
            return text
        key = f"{source_lang}>{target_lang}|{text}"
        if key in self._cache:
            return self._cache[key]
        system = (
            f"Translate the user's {LANG_NAMES.get(source_lang, source_lang)} text into "
            f"{LANG_NAMES.get(target_lang, target_lang)}. Keep every number, amount, age and proper "
            "noun exact. Output only the translation."
        )
        out = self.llm.chat(system, text, temperature=0.0, max_tokens=600).text.strip()
        self._cache[key] = out
        if self.cache_path:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps(self._cache, ensure_ascii=False), encoding="utf-8")
        return out


class DictTranslator:
    """Lookup translator. Used for unit tests and for the ORACLE upper-bound experiments in the
    evaluation (translations come from human-written parallel text, not from MT)."""

    def __init__(self, mapping: dict[str, str], name: str = "dict") -> None:
        self.mapping = mapping
        self.name = name

    def translate(self, text: str, source_lang: str, target_lang: str = "en") -> str:
        if source_lang == target_lang:
            return text
        return self.mapping.get(text, text)


class LexiconTranslator:
    """Offline query "translator": replaces the query with the English side of every matched
    lexicon group, keeping Latin-script tokens that were already English. This is a dictionary
    translation (no MT model), so it only covers the lexicon's domain vocabulary."""

    name = "lexicon"

    def __init__(self, expander) -> None:  # QueryExpander
        self.expander = expander

    def translate(self, text: str, source_lang: str, target_lang: str = "en") -> str:
        if source_lang == target_lang:
            return text
        latin = " ".join(w for w in text.split() if w.isascii())
        return (self.expander.english_terms(text) + " " + latin).strip() or text
