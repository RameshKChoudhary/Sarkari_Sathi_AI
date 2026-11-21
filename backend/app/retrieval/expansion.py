"""Lexicon-based query expansion (bilingual dictionary CLIR + romanised-term handling).

The lexicon (data/raw/lexicon.json) maps trigger strings (romanised, English, Hindi, Marathi)
to expansion terms in all three languages. This is a classic dictionary-based cross-lingual
IR technique, deliberately kept separate from the "native" baseline so its effect is measured
as its own ablation, not hidden inside the baseline.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from .tokenize import normalize_for_match

logger = logging.getLogger(__name__)


# lexicon concept group -> document section it asks about (generic question intents)
INTENT_SECTIONS: dict[str, str] = {
    "concept:eligibility": "eligibility", "concept:age": "eligibility", "concept:income": "eligibility",
    "concept:benefits": "benefits", "concept:instalment": "benefits",
    "concept:documents": "documents",
    "concept:apply": "how_to_apply", "concept:online": "how_to_apply",
}


class QueryExpander:
    def __init__(self, groups: list[dict]) -> None:
        self.groups = []
        self.english: dict[str, str] = {}
        for g in groups:
            triggers = [normalize_for_match(t) for t in g.get("triggers", []) if t.strip()]
            terms = " ".join(g.get("terms", []))
            self.groups.append((triggers, terms, g.get("id", "")))
            self.english[g.get("id", "")] = " ".join(g.get("en", []))

    @classmethod
    def from_file(cls, path: Path) -> "QueryExpander":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(data["groups"])

    @staticmethod
    def _hit(trigger: str, q: str) -> bool:
        if re.search(r"[ऀ-ॿ]", trigger):
            return trigger in q  # suffixes attach in Devanagari: substring match
        return re.search(rf"(?<![a-z0-9]){re.escape(trigger)}(?![a-z0-9])", q) is not None

    def matched_groups(self, query: str) -> list[str]:
        q = normalize_for_match(query)
        return [gid for triggers, _t, gid in self.groups if any(self._hit(t, q) for t in triggers)]

    def expand(self, query: str) -> str:
        q = normalize_for_match(query)
        extra: list[str] = []
        for triggers, terms, _gid in self.groups:
            if any(self._hit(t, q) for t in triggers):
                extra.append(terms)
        return query if not extra else query + " " + " ".join(extra)

    def english_terms(self, query: str) -> str:
        """English side of every matching group, in lexicon order (used by LexiconTranslator)."""
        return " ".join(self.english[g] for g in self.matched_groups(query) if self.english.get(g))

    def matched_trigger_tokens(self, query: str) -> set[str]:
        """Word tokens of every trigger phrase that fired: these are known domain words
        (e.g. 'apply', 'kasa', 'karaycha') and are not requests for new information."""
        from .tokenize import word_tokens

        q = normalize_for_match(query)
        out: set[str] = set()
        for triggers, _terms, _gid in self.groups:
            for t in triggers:
                if self._hit(t, q):
                    out.update(word_tokens(t, stop=False))
        return out

    def intent_sections(self, query: str) -> set[str]:
        """Sections the question seems to ask about (eligibility / benefits / documents /
        how_to_apply), from the concept groups that fire."""
        return {INTENT_SECTIONS[g] for g in self.matched_groups(query) if g in INTENT_SECTIONS}
