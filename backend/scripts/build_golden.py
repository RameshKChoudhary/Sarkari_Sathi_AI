#!/usr/bin/env python3
"""Generate the golden evaluation set (data/evaluation/golden.json + golden_review.csv).

Design
* Every answerable question exists in English, Hindi and Marathi (same `group_id`, same gold
  passage), so results are directly comparable across languages; some groups also have a
  romanised-Marathi variant (`mr_roman`).
* Gold = (scheme_id, section). Because the sample corpus is parallel (every section exists in
  en/hi/mr), the gold passage in any document language is known -> the retrieval matrix can be
  computed per (query language, document language).
* ~18% of the questions are unanswerable (scheme not indexed, off-topic, or a fact the indexed
  text does not state) to test abstention.
* `key_facts`: list of facts; each fact is a list of alternative strings (any-of, matched after
  normalisation). Used for the answer-correctness metric.
* Questions were written by the project author (an AI assistant). Hindi/Marathi wording has NOT
  been verified by a native speaker: `verification` starts as "unverified". Review with
  golden_review.csv and merge with scripts/apply_review.py.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# (scheme, section, en, hi, mr, roman_mr | None, key_facts)
A = [
    ("pm_kisan", "eligibility", "What are the eligibility criteria for PM Kisan?", "पीएम किसान योजना के लिए कौन पात्र है?", "पीएम किसान योजनेसाठी कोण पात्र आहे?", "pm kisan yojanesathi kon patra ahe?", [["cultivable", "कृषि योग्य", "लागवडीयोग्य"]]),
    ("pm_kisan", "benefits", "How much money do farmers get every year under PM Kisan?", "पीएम किसान में किसानों को हर साल कितने रुपये मिलते हैं?", "पीएम किसान योजनेत शेतकऱ्यांना दरवर्षी किती रक्कम मिळते?", None, [["6000"]]),
    ("pm_kisan", "benefits", "In how many instalments is the PM Kisan amount paid?", "पीएम किसान की राशि कितनी किस्तों में दी जाती है?", "पीएम किसानची रक्कम किती हप्त्यांमध्ये दिली जाते?", None, [["2000"]]),
    ("pm_kisan", "eligibility", "Can an income tax payer get PM Kisan benefits?", "क्या आयकर देने वाला व्यक्ति पीएम किसान का लाभ ले सकता है?", "आयकर भरणारी व्यक्ती पीएम किसानचा लाभ घेऊ शकते का?", None, [["income tax", "आयकर"]]),
    ("pm_kisan", "documents", "Which documents are required to register for PM Kisan?", "पीएम किसान में पंजीकरण के लिए कौन से दस्तावेज़ चाहिए?", "पीएम किसानसाठी नोंदणी करण्यास कोणती कागदपत्रे लागतात?", None, [["aadhaar", "आधार"]]),
    ("pm_kisan", "how_to_apply", "How can a farmer register for PM Kisan?", "किसान पीएम किसान में पंजीकरण कैसे कर सकता है?", "शेतकरी पीएम किसानसाठी नोंदणी कशी करू शकतो?", None, [["farmers corner", "फार्मर्स कॉर्नर"]]),
    ("pmjay", "benefits", "How much health cover does Ayushman Bharat PM-JAY provide per family?", "आयुष्मान भारत पीएम-जेएवाई में प्रति परिवार कितना स्वास्थ्य कवर मिलता है?", "आयुष्मान भारत पीएम-जेएवाय मध्ये प्रति कुटुंब किती आरोग्य संरक्षण मिळते?", None, [["5 lakh", "5 लाख"]]),
    ("pmjay", "eligibility", "Who is eligible for Ayushman Bharat?", "आयुष्मान भारत के लिए कौन पात्र है?", "आयुष्मान भारतसाठी कोण पात्र आहे?", None, [["2011"]]),
    ("pmjay", "how_to_apply", "How do I get an Ayushman card?", "आयुष्मान कार्ड कैसे बनवाएं?", "आयुष्मान कार्ड कसे मिळवायचे?", "ayushman card kase milvayche?", [["ayushman mitra", "आयुष्मान मित्र"]]),
    ("pmjay", "documents", "What documents are used to verify a family for Ayushman Bharat?", "आयुष्मान भारत में परिवार के सत्यापन के लिए कौन से दस्तावेज़ उपयोग होते हैं?", "आयुष्मान भारतमध्ये कुटुंबाच्या पडताळणीसाठी कोणती कागदपत्रे वापरली जातात?", None, [["ration", "राशन", "रेशन"]]),
    ("ladki_bahin", "eligibility", "Who can get the benefit of Ladki Bahin Yojana?", "लाडकी बहीण योजना का लाभ किसे मिल सकता है?", "मला लाडकी बहीण योजनेचा लाभ मिळू शकतो का?", "ladki bahin yojanecha labh milu shakto ka?", [["21"], ["65"]]),
    ("ladki_bahin", "eligibility", "What is the family income limit for Ladki Bahin Yojana?", "लाडकी बहीण योजना के लिए पारिवारिक आय की सीमा क्या है?", "लाडकी बहीण योजनेसाठी कुटुंबाच्या उत्पन्नाची मर्यादा किती आहे?", None, [["2.5"]]),
    ("ladki_bahin", "benefits", "How much money per month does Ladki Bahin Yojana give?", "लाडकी बहीण योजना में हर महीने कितने रुपये मिलते हैं?", "लाडकी बहीण योजनेत दरमहा किती रुपये मिळतात?", "ladki bahin yojanet darmahaa kiti paise milatat?", [["1500"]]),
    ("ladki_bahin", "how_to_apply", "How do I apply for Ladki Bahin Yojana?", "लाडकी बहीण योजना के लिए आवेदन कैसे करें?", "मला लाडकी बहीण योजनेसाठी अर्ज कसा करायचा?", "ladki bahin yojana sathi apply kasa karaycha?", [["nari shakti", "नारी शक्ति", "नारी शक्ती"]]),
    ("ladki_bahin", "documents", "What documents are needed for Ladki Bahin Yojana?", "लाडकी बहीण योजना के लिए कौन से दस्तावेज़ चाहिए?", "लाडकी बहीण योजनेसाठी कोणती कागदपत्रे लागतात?", "ladki bahin yojanesathi konti kagadpatre lagtat?", [["aadhaar", "आधार"]]),
    ("pmayg", "eligibility", "Who is eligible for PMAY-G?", "पीएमएवाई-जी के लिए कौन पात्र है?", "पीएमएवाय-जी साठी कोण पात्र आहे?", None, [["gram sabha", "ग्राम सभा", "ग्रामसभा"]]),
    ("pmayg", "benefits", "How much assistance is given for building a house in plain areas under PMAY-G?", "पीएमएवाई-जी में मैदानी क्षेत्रों में घर बनाने के लिए कितनी सहायता मिलती है?", "पीएमएवाय-जी मध्ये सपाट प्रदेशात घर बांधण्यासाठी किती मदत मिळते?", None, [["1.2"]]),
    ("pmayg", "benefits", "How many days of MGNREGA work do PMAY-G beneficiaries get?", "पीएमएवाई-जी लाभार्थियों को मनरेगा में कितने दिन का काम मिलता है?", "पीएमएवाय-जी लाभार्थ्यांना मनरेगा अंतर्गत किती दिवस काम मिळते?", None, [["90"]]),
    ("pmayg", "how_to_apply", "How can a household find out whether it is on the Awaas Plus list?", "परिवार कैसे जान सकता है कि उसका नाम आवास प्लस सूची में है?", "कुटुंबाचे नाव आवास प्लस यादीत आहे का हे कसे कळेल?", None, [["gram panchayat", "ग्राम पंचायत", "ग्रामपंचायत"]]),
    ("pmayg", "documents", "What documents does a PMAY-G beneficiary need?", "पीएमएवाई-जी लाभार्थी को कौन से दस्तावेज़ चाहिए?", "पीएमएवाय-जी लाभार्थ्याला कोणती कागदपत्रे लागतात?", None, [["job card", "जॉब कार्ड"]]),
    ("pmayg", "benefits", "How much assistance does PMAY-G give in hilly areas?", "पीएमएवाई-जी में पहाड़ी क्षेत्रों में कितनी सहायता मिलती है?", "पीएमएवाय-जी मध्ये डोंगराळ प्रदेशात किती मदत मिळते?", None, [["1.3"]]),
    ("pmuy", "eligibility", "Who is eligible for the Ujjwala Yojana?", "उज्ज्वला योजना के लिए कौन पात्र है?", "उज्ज्वला योजनेसाठी कोण पात्र आहे?", "ujjwala yojanesathi kon patra ahe?", [["lpg", "एलपीजी"]]),
    ("pmuy", "benefits", "Is a security deposit needed for a new Ujjwala LPG connection?", "क्या उज्ज्वला के नए एलपीजी कनेक्शन के लिए सुरक्षा जमा राशि देनी पड़ती है?", "उज्ज्वलाच्या नवीन एलपीजी जोडणीसाठी सुरक्षा ठेव द्यावी लागते का?", None, [["deposit", "जमा", "ठेव"]]),
    ("pmuy", "documents", "What documents are required for an Ujjwala connection?", "उज्ज्वला कनेक्शन के लिए कौन से दस्तावेज़ चाहिए?", "उज्ज्वला जोडणीसाठी कोणती कागदपत्रे आवश्यक आहेत?", None, [["aadhaar", "आधार"]]),
    ("pmuy", "how_to_apply", "Where can I submit the Ujjwala application form?", "उज्ज्वला आवेदन फॉर्म कहां जमा करें?", "उज्ज्वलाचा अर्ज कुठे जमा करायचा?", None, [["distributor", "वितरक"]]),
    ("ssy", "eligibility", "What is the age limit for opening a Sukanya Samriddhi account?", "सुकन्या समृद्धि खाता खोलने की आयु सीमा क्या है?", "सुकन्या समृद्धी खाते उघडण्यासाठी वयाची मर्यादा काय आहे?", None, [["10"]]),
    ("ssy", "benefits", "What is the maximum yearly deposit in Sukanya Samriddhi?", "सुकन्या समृद्धि में एक वर्ष में अधिकतम कितनी जमा राशि हो सकती है?", "सुकन्या समृद्धीमध्ये एका वर्षात जास्तीत जास्त किती रक्कम जमा करता येते?", "sukanya samriddhi madhe varshala kamal kiti thev thevta yete?", [["1.5 lakh", "1.5 लाख"]]),
    ("ssy", "benefits", "After how many years does the Sukanya Samriddhi account mature?", "सुकन्या समृद्धि खाता कितने वर्षों बाद परिपक्व होता है?", "सुकन्या समृद्धी खाते किती वर्षांनी परिपक्व होते?", None, [["21"]]),
    ("ssy", "documents", "What documents are needed to open a Sukanya Samriddhi account?", "सुकन्या समृद्धि खाता खोलने के लिए कौन से दस्तावेज़ चाहिए?", "सुकन्या समृद्धी खाते उघडण्यासाठी कोणती कागदपत्रे लागतात?", None, [["birth certificate", "जन्म प्रमाणपत्र", "जन्म प्रमाण पत्र", "जन्माचा दाखला", "जन्म दाखला"]]),
    ("ssy", "how_to_apply", "Where can I open a Sukanya Samriddhi account?", "सुकन्या समृद्धि खाता कहां खोल सकते हैं?", "सुकन्या समृद्धी खाते कुठे उघडता येते?", None, [["post office", "डाकघर", "टपाल", "पोस्ट ऑफिस"]]),
    ("apy", "eligibility", "What is the age requirement for Atal Pension Yojana?", "अटल पेंशन योजना के लिए आयु की शर्त क्या है?", "अटल पेन्शन योजनेसाठी वयाची अट काय आहे?", None, [["18"], ["40"]]),
    ("apy", "benefits", "How much pension does Atal Pension Yojana give?", "अटल पेंशन योजना में कितनी पेंशन मिलती है?", "अटल पेन्शन योजनेत किती पेन्शन मिळते?", None, [["1000"], ["5000"]]),
    ("apy", "documents", "What do I need to enrol in Atal Pension Yojana?", "अटल पेंशन योजना में नामांकन के लिए क्या चाहिए?", "अटल पेन्शन योजनेत नोंदणीसाठी काय लागते?", None, [["mobile", "मोबाइल"]]),
    ("apy", "how_to_apply", "How do I enrol in Atal Pension Yojana?", "अटल पेंशन योजना में नामांकन कैसे करें?", "अटल पेन्शन योजनेत नोंदणी कशी करायची?", None, [["bank", "बैंक", "बँक"]]),
    ("mudra", "eligibility", "Who can apply for a Mudra loan?", "मुद्रा ऋण के लिए कौन आवेदन कर सकता है?", "मुद्रा कर्जासाठी कोण अर्ज करू शकतो?", None, [["10 lakh", "10 लाख"]]),
    ("mudra", "benefits", "What are the Mudra loan categories and amounts?", "मुद्रा ऋण की श्रेणियां और राशि क्या हैं?", "मुद्रा कर्जाच्या श्रेणी आणि रक्कम काय आहेत?", None, [["50000"], ["5 lakh", "5 लाख"]]),
    ("mudra", "benefits", "What is the Tarun category loan limit under Mudra?", "मुद्रा में तरुण श्रेणी की ऋण सीमा क्या है?", "मुद्रामध्ये तरुण श्रेणीची कर्ज मर्यादा किती आहे?", None, [["10 lakh", "10 लाख"]]),
    ("mudra", "documents", "What documents are needed for a Mudra loan?", "मुद्रा ऋण के लिए कौन से दस्तावेज़ चाहिए?", "मुद्रा कर्जासाठी कोणती कागदपत्रे लागतात?", None, [["address", "पते", "पत्त्याचा"]]),
    ("mudra", "how_to_apply", "Where can I apply for a Mudra loan?", "मुद्रा ऋण के लिए आवेदन कहां करें?", "मुद्रा कर्जासाठी अर्ज कुठे करायचा?", None, [["udyamimitra", "उद्यमिमित्र"]]),
    ("pmfby", "eligibility", "Who can enrol in the PM Fasal Bima Yojana?", "प्रधानमंत्री फसल बीमा योजना में कौन नामांकन कर सकता है?", "प्रधानमंत्री पीक विमा योजनेत कोण नोंदणी करू शकतो?", None, [["notified", "अधिसूचित"]]),
    ("pmfby", "benefits", "What premium do farmers pay for kharif crops under PMFBY?", "पीएमएफबीवाई में खरीफ फसलों के लिए किसान कितना प्रीमियम देते हैं?", "पीक विमा योजनेत खरीप पिकांसाठी शेतकऱ्याला किती प्रीमियम भरावा लागतो?", "pik vima yojanet kharip pikansathi shetkaryala kiti premium bharava lagto?", [["2 percent", "2%", "2 प्रतिशत", "2 टक्के"]]),
    ("pmfby", "documents", "What documents are required for crop insurance enrolment?", "फसल बीमा नामांकन के लिए कौन से दस्तावेज़ आवश्यक हैं?", "पीक विमा नोंदणीसाठी कोणती कागदपत्रे आवश्यक आहेत?", None, [["aadhaar", "आधार"]]),
    ("pmfby", "how_to_apply", "How can a farmer enrol for crop insurance?", "किसान फसल बीमा के लिए नामांकन कैसे करे?", "शेतकरी पीक विम्यासाठी नोंदणी कशी करू शकतो?", None, [["portal", "पोर्टल"]]),
    ("namo_shetkari", "eligibility", "Who is eligible for Namo Shetkari Mahasanman Nidhi?", "नमो शेतकरी महासन्मान निधि के लिए कौन पात्र है?", "नमो शेतकरी महासन्मान निधीसाठी कोण पात्र आहे?", None, [["pm-kisan", "पीएम-किसान"]]),
    ("namo_shetkari", "benefits", "How much additional money does Namo Shetkari give per year?", "नमो शेतकरी योजना में प्रति वर्ष कितनी अतिरिक्त राशि मिलती है?", "नमो शेतकरी योजनेत दरवर्षी किती अतिरिक्त रक्कम मिळते?", "namo shetkari yojanet daravarshi kiti rakkam milte?", [["6000"]]),
    ("namo_shetkari", "documents", "Which documents does Namo Shetkari use?", "नमो शेतकरी योजना में कौन से दस्तावेज़ उपयोग होते हैं?", "नमो शेतकरी योजनेत कोणती कागदपत्रे वापरली जातात?", None, [["aadhaar", "आधार"]]),
    ("namo_shetkari", "how_to_apply", "How do I apply for Namo Shetkari?", "नमो शेतकरी के लिए आवेदन कैसे करें?", "नमो शेतकरीसाठी अर्ज कसा करायचा?", None, [["pm-kisan", "पीएम-किसान"]]),
]

# (en, hi, mr, roman_mr | None, kind)
U = [
    ("What is the capital of France?", "फ्रांस की राजधानी क्या है?", "फ्रान्सची राजधानी कोणती आहे?", None, "off_topic"),
    ("What is the benefit amount under the PM Vishwakarma scheme?", "पीएम विश्वकर्मा योजना में कितनी राशि मिलती है?", "पीएम विश्वकर्मा योजनेत किती रक्कम मिळते?", "pm vishwakarma yojanet kiti rakkam milte?", "scheme_not_indexed"),
    ("How do I apply for Ladli Behna Yojana of Madhya Pradesh?", "मध्य प्रदेश की लाडली बहना योजना के लिए आवेदन कैसे करें?", "मध्य प्रदेशच्या लाडली बहना योजनेसाठी अर्ज कसा करायचा?", None, "scheme_not_indexed"),
    ("What is the last date to apply for PM Kisan in 2027?", "2027 में पीएम किसान के लिए आवेदन की अंतिम तारीख क्या है?", "२०२७ मध्ये पीएम किसानसाठी अर्ज करण्याची शेवटची तारीख कोणती आहे?", None, "fact_missing"),
    ("What is the helpline phone number of Ladki Bahin Yojana?", "लाडकी बहीण योजना का हेल्पलाइन फ़ोन नंबर क्या है?", "लाडकी बहीण योजनेचा हेल्पलाइन फोन नंबर काय आहे?", "ladki bahin yojanecha helpline number kay ahe?", "fact_missing"),
    ("What is the current interest rate of Sukanya Samriddhi?", "सुकन्या समृद्धि की वर्तमान ब्याज दर कितनी है?", "सुकन्या समृद्धीचा सध्याचा व्याजदर किती आहे?", None, "fact_missing"),
    ("How much monthly contribution is needed for a 5000 rupee pension at age 30 in Atal Pension Yojana?", "अटल पेंशन योजना में 30 वर्ष की आयु में ₹5000 पेंशन के लिए कितना मासिक अंशदान देना होगा?", "अटल पेन्शन योजनेत ३० वर्षे वयात ₹५००० पेन्शनसाठी दरमहा किती अंशदान भरावे लागेल?", None, "fact_missing"),
    ("Who won the cricket world cup in 2011?", "2011 का क्रिकेट विश्व कप किसने जीता?", "२०११ चा क्रिकेट विश्वचषक कोणी जिंकला?", None, "off_topic"),
    ("Which hospitals in Palghar accept Ayushman cards?", "पालघर में किन अस्पतालों में आयुष्मान कार्ड चलता है?", "पालघरमधील कोणत्या रुग्णालयांत आयुष्मान कार्ड चालते?", None, "fact_missing"),
    ("What is the interest rate on Mudra loans?", "मुद्रा ऋण की ब्याज दर क्या है?", "मुद्रा कर्जाचा व्याजदर किती आहे?", None, "fact_missing"),
    ("How much subsidy does PMAY-Urban give on home loan interest?", "पीएमएवाई-शहरी में होम लोन ब्याज पर कितनी सब्सिडी मिलती है?", "पीएमएवाय-शहरी मध्ये गृहकर्जाच्या व्याजावर किती अनुदान मिळते?", None, "scheme_not_indexed"),
]


def split_of(group_id: str) -> str:
    """Deterministic, stratified dev/test split (~40/60) by group (answerable and unanswerable
    groups are split separately) so all language variants of a question stay together."""
    n = int(group_id[1:])
    return "dev" if n % 5 in (0, 2) else "test"


def build() -> list[dict]:
    rows: list[dict] = []

    def add(group: str, lang: str, q: str, answerable: bool, gold, facts, kind: str, base_en: str) -> None:
        rows.append({
            "id": f"{group}.{lang}", "group_id": group, "language": lang, "question": q,
            "question_en": base_en, "answerable": answerable, "gold": gold, "key_facts": facts, "kind": kind,
            "split": split_of(group), "author": "ai_assistant",
            "verification": {"status": "unverified", "reviewer": None, "notes": ""},
        })

    for i, (sid, sec, en, hi, mr, rom, facts) in enumerate(A, start=1):
        g = f"A{i:02d}"
        gold = {"scheme_id": sid, "section": sec}
        for lang, q in (("en", en), ("hi", hi), ("mr", mr)):
            add(g, lang, q, True, gold, facts, "answerable", en)
        if rom:
            add(g, "mr_roman", rom, True, gold, facts, "answerable", en)
    for i, (en, hi, mr, rom, kind) in enumerate(U, start=1):
        g = f"U{i:02d}"
        for lang, q in (("en", en), ("hi", hi), ("mr", mr)):
            add(g, lang, q, False, None, [], kind, en)
        if rom:
            add(g, "mr_roman", rom, False, None, [], kind, en)
    return rows


def main() -> None:
    rows = build()
    out = ROOT / "data" / "evaluation"
    out.mkdir(parents=True, exist_ok=True)
    (out / "golden.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    with (out / "golden_review.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "language", "question", "english_reference", "answerable", "gold_scheme", "gold_section",
                    "review_status(ok|fix|reject)", "corrected_question", "reviewer", "notes"])
        for r in rows:
            if r["language"] in ("hi", "mr", "mr_roman"):
                g = r["gold"] or {}
                w.writerow([r["id"], r["language"], r["question"], r["question_en"], r["answerable"],
                            g.get("scheme_id", ""), g.get("section", ""), "", "", "", ""])
    n_un = sum(1 for r in rows if not r["answerable"])
    print(f"{len(rows)} questions ({n_un} unanswerable = {n_un / len(rows):.1%}); "
          f"{len({r['group_id'] for r in rows})} groups")


if __name__ == "__main__":
    main()
