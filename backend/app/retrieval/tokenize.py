"""Tokenisers for English / Hindi / Marathi.

Python's `\\w` does NOT match Devanagari vowel signs (matras) because they are combining
marks, so a naive regex tokeniser splits Marathi words into fragments. We use explicit
Unicode ranges instead.
"""
from __future__ import annotations

import re
import unicodedata

_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_STRIP_JOINERS = dict.fromkeys([0x200C, 0x200D, 0x200B, 0xFEFF, 0x00AD], None)
_NUM_COMMA = re.compile(r"(?<=\d),(?=\d)")
_TOKEN = re.compile(r"[a-z]+|\d+(?:\.\d+)?|[ऀ-ॣ॰-ॿ]+")

STOPWORDS: frozenset[str] = frozenset(
    # English
    "a an the of for to in on at and or is are was be by with this that it as from can do does did "
    "i my me we you your what who whom which how when where why get gets there any under".split()
    # Hindi
    + "है हैं था थे का के की को से में पर तक भी और या यह वह इस उस क्या कैसे कौन कौनसे कितना कितनी कहां कब "
      "मुझे मैं लिए नहीं कर करें करना सकता सकती सकते होता होती होते जाता जाती जाते तो ही".split()
    # Marathi
    + "आहे आहेत होता होते आणि व या ही हे तो ती ते का काय मला मी तर पण किंवा साठी कसा कशी कसे कोण कोणती "
      "कोणता कोणत्या किती कुठे कधी करायचा करायची करायचे शकतो शकते शकतात नाही त्या त्यांना यांना".split()
)


def normalize_for_match(text: str) -> str:
    """NFC, lowercase, drop joiners, ASCII digits, '6,000' -> '6000'."""
    text = unicodedata.normalize("NFC", text).translate(_STRIP_JOINERS).translate(_DEV_DIGITS).lower()
    return _NUM_COMMA.sub("", text)


def word_tokens(text: str, stop: bool = True) -> list[str]:
    toks = _TOKEN.findall(normalize_for_match(text))
    return [t for t in toks if not (stop and t in STOPWORDS)]


def char_ngram_tokens(text: str, n_min: int = 3, n_max: int = 5, stop: bool = True) -> list[str]:
    """Character n-grams per word with boundary markers. Helps agglutinative Marathi where
    'योजनेचा', 'योजनेसाठी', 'योजनेमध्ये' share a root but differ as whole words."""
    grams: list[str] = []
    for tok in word_tokens(text, stop=stop):
        padded = f"#{tok}#"
        if len(tok) <= 2:
            grams.append(padded)
            continue
        for n in range(n_min, n_max + 1):
            if len(padded) < n:
                break
            grams.extend(padded[i : i + n] for i in range(len(padded) - n + 1))
    return grams


def stem_match(a: str, b: str, prefix: int = 4) -> bool:
    """Cheap suffix-tolerant token match used for coverage / support heuristics: tokens match
    if equal or if both are at least `prefix` chars and share that prefix."""
    if a == b:
        return True
    return min(len(a), len(b)) >= prefix and a[:prefix] == b[:prefix]
