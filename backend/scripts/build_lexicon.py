#!/usr/bin/env python3
"""Build data/raw/lexicon.json: the bilingual dictionary used for query expansion and for the
offline lexicon "translator". Scheme groups are generated from scheme names/aliases; concept
groups (eligibility, apply, documents, ...) are written by hand below.

The lexicon is generic domain vocabulary. It is NOT derived from the evaluation questions.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from sample_data.content import SCHEMES  # noqa: E402

# id, triggers (any language / romanised), terms to add (all languages), english terms
CONCEPTS: list[tuple[str, list[str], str, str]] = [
    ("eligibility", ["eligible", "eligibility", "who can", "qualify", "qualifies", "पात्र", "पात्रता", "patra", "patrata", "pratra", "paatra", "kon patra"],
     "eligible eligibility पात्र पात्रता", "eligible eligibility"),
    ("benefits", ["benefit", "benefits", "how much", "amount", "money", "get per", "लाभ", "कितना", "कितने", "कितनी", "किती", "फायदा", "फायदे", "labh", "kiti milte", "rakkam", "paise", "kitna"],
     "benefits amount लाभ राशि रक्कम", "benefits amount per year month"),
    ("documents", ["document", "documents", "papers", "required papers", "दस्तावेज", "कागदपत्र", "कागद", "kagadpatre", "kagadpatra", "dastavej", "dastavez", "kaagadpatre"],
     "documents required आवश्यक दस्तावेज कागदपत्रे", "documents required"),
    ("apply", ["apply", "application", "register", "registration", "enrol", "enroll", "आवेदन", "अर्ज", "पंजीकरण", "नोंदणी", "nondani", "arj", "avedan", "karaycha", "bharaycha", "kaise", "kasa", "kase", "form"],
     "apply application register आवेदन अर्ज पंजीकरण नोंदणी", "apply application register"),
    ("age", ["age", "years old", "वय", "आयु", "उम्र", "vay", "umar"], "age years आयु वर्ष वर्षे वय", "age years"),
    ("income", ["income", "आय", "उत्पन्न", "आमदनी", "utpanna", "utpann"], "income उत्पन्न आय", "income"),
    ("bank", ["bank", "बैंक", "बँक", "khate", "khata", "खाता", "खाते"], "bank account बैंक बँक खाता खाते", "bank account"),
    ("instalment", ["instalment", "installment", "instalments", "किस्त", "हप्ता", "हप्त्या", "hapta", "kist"], "instalments किस्त हप्त्यांमध्ये", "instalments"),
    ("online", ["online", "portal", "app", "ऑनलाइन", "पोर्टल", "ॲप", "ऐप"], "online portal ऑनलाइन पोर्टल", "online portal app"),
    ("pension", ["pension", "पेंशन", "पेन्शन", "निवृत्तिवेतन"], "pension पेंशन पेन्शन", "pension"),
    ("loan", ["loan", "कर्ज", "ऋण", "karj", "loan"], "loan collateral-free कर्ज ऋण", "loan collateral-free"),
    ("insurance", ["insurance", "insured", "premium", "बीमा", "विमा", "प्रीमियम", "bima", "vima"], "insurance premium बीमा विमा प्रीमियम", "insurance premium"),
    ("girl", ["girl", "daughter", "बेटी", "बालिका", "मुलगी", "mulgi", "beti"], "girl child बालिका मुलगी", "girl child"),
    ("farmer", ["farmer", "farmers", "किसान", "शेतकरी", "shetkari", "kisan"], "farmer farmers किसान शेतकरी", "farmer farmers"),
    ("women", ["woman", "women", "महिला", "बहीण", "बहिण", "mahila", "bahin", "bahini"], "women woman महिला बहीण", "women woman"),
    ("house", ["house", "housing", "home", "आवास", "घर", "gharkul", "ghar"], "house pucca housing आवास घर", "house pucca housing"),
    ("lpg", ["gas", "lpg", "cylinder", "गैस", "सिलेंडर", "सिलिंडर"], "LPG connection गैस कनेक्शन", "LPG gas connection"),
]


def main() -> None:
    groups: list[dict] = []
    for sch in SCHEMES:
        names = list(sch["names"].values())
        groups.append({
            "id": f"scheme:{sch['id']}",
            "triggers": list(dict.fromkeys(sch["aliases"] + names)),
            "terms": names,
            "en": [sch["names"]["en"]],
        })
    for gid, triggers, terms, en in CONCEPTS:
        groups.append({"id": f"concept:{gid}", "triggers": triggers, "terms": terms.split(), "en": en.split()})
    out = ROOT / "data" / "raw" / "lexicon.json"
    out.write_text(json.dumps({"groups": groups}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(groups)} groups -> {out}")


if __name__ == "__main__":
    main()
