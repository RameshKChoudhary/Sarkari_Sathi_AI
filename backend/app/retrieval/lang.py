"""Language / script detection for en, hi, mr and romanised queries.

Method: Unicode-script ratio first. For Devanagari, Hindi vs Marathi is decided by marker
words and Marathi's attached postpositions (योजनेचा, योजनेसाठी). For Latin script, a small
lexicon of romanised Marathi/Hindi function words decides between English and romanised
Indic. This is a transparent rule-based classifier, not a trained model; its accuracy on the
golden set is reported by `scripts/run_eval.py` (suite `lang`).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

_DEV = re.compile(r"[ऀ-ॿ]")
_LAT = re.compile(r"[A-Za-z]")
_WORD = re.compile(r"[a-z]+|[ऀ-ॿ]+")

MR_DEV = set("आहे आहेत नाही आणि मला मी काय कसा कशी कसे कोण कोणती कोणत्या किती कुठे कधी करायचा करायची करायचे "
             "शकतो शकते शकतात मिळू मिळते मिळतात मिळेल लागतात लागते येते मध्ये आधी पासून".split())
HI_DEV = set("है हैं नहीं और मुझे मैं क्या कैसे कौन कौनसे कितना कितनी कितने कहां कब करें करना सकता सकती सकते "
             "मिलता मिलती मिलते चाहिए में के लिए".split())
MR_DEV_SUFFIX = ("साठी", "चा", "ची", "चे", "चं", "ांना", "ाला", "ात")
HI_DEV_SUFFIX: tuple[str, ...] = ()

MR_ROMAN = set("kasa kashi kase karaycha karaychi karaychay kay mala mi sathi ahe aahe ahet nahi milel milte "
               "milatat kiti kuthe kon konti konta lagtat shakto shakte shaktat kadhaiche kadhaycha "
               "yojanesathi yojanecha yojanechi yojanet nondani arj tapasayche sadar ughadnyasathi "
               "dar mahina kimaan kamal thev vayomarya".split())
HI_ROMAN = set("kaise kya hai hain mujhe kaun kitna kitni kitne kahan kab karna karein milta milti milte chahiye "
               "aur ke liye nahi avedan".split())
ROMAN_MR_SUFFIX = ("aycha", "aychi", "ayche", "sathi", "madhe", "yojanecha", "yojanechi", "yojanet")


@dataclass
class LangInfo:
    language: str  # en | hi | mr
    script: str  # latin | devanagari
    romanized: bool
    confidence: float
    scores: dict[str, float] = field(default_factory=dict)


def detect_language(text: str, hint: Optional[str] = None) -> LangInfo:
    t = unicodedata.normalize("NFC", text)
    n_dev, n_lat = len(_DEV.findall(t)), len(_LAT.findall(t))
    total = max(n_dev + n_lat, 1)
    words = _WORD.findall(t.lower())

    if n_dev / total >= 0.3:
        mr = sum(2 for w in words if w in MR_DEV) + sum(1 for w in words if w.endswith(MR_DEV_SUFFIX) and len(w) > 4)
        hi = sum(2 for w in words if w in HI_DEV)
        if mr == hi:
            lang = hint if hint in ("hi", "mr") else "hi"
            conf = 0.5
        else:
            lang = "mr" if mr > hi else "hi"
            conf = min(1.0, abs(mr - hi) / max(mr + hi, 1) + 0.3)
        return LangInfo(lang, "devanagari", False, conf, {"mr": mr, "hi": hi})

    lat_words = [w for w in words if w.isascii()]
    mr = sum(1 for w in lat_words if w in MR_ROMAN or w.endswith(ROMAN_MR_SUFFIX))
    hi = sum(1 for w in lat_words if w in HI_ROMAN)
    n = max(len(lat_words), 1)
    if (mr + hi) / n >= 0.15 and (mr + hi) >= 1:
        lang = "mr" if mr >= hi else "hi"
        return LangInfo(lang, "latin", True, min(1.0, (mr + hi) / n + 0.3), {"mr": mr, "hi": hi})
    return LangInfo("en", "latin", False, 0.9 if n >= 3 else 0.6, {"mr": mr, "hi": hi})
