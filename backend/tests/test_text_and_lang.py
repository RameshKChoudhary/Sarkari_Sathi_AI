from app.retrieval.lang import detect_language
from app.retrieval.tokenize import char_ngram_tokens, normalize_for_match, stem_match, word_tokens


def test_nfc_and_digit_normalisation():
    assert "6000" in normalize_for_match("₹६,०००")  # Devanagari digits + comma -> ASCII
    assert normalize_for_match("ऩ") == normalize_for_match("ऩ")


def test_word_tokens_keep_devanagari_marks():
    toks = word_tokens("लाडकी बहीण योजनेसाठी", stop=False)
    assert "बहीण" in toks and "योजनेसाठी" in toks  # matras must not split words


def test_char_ngrams_and_stem():
    assert any(len(t) == 3 for t in char_ngram_tokens("kisan", stop=False))
    assert stem_match("योजनेसाठी", "योजना")
    assert not stem_match("पेंशन", "किसान")


def test_language_detection():
    assert detect_language("What are the eligibility criteria for PM Kisan?").language == "en"
    assert detect_language("पीएम किसान योजना के लिए कौन पात्र है?").language == "hi"
    assert detect_language("मला लाडकी बहीण योजनेसाठी अर्ज कसा करायचा?").language == "mr"
    info = detect_language("ladki bahin yojana sathi apply kasa karaycha?")
    assert info.language == "mr" and info.romanized and info.script == "latin"


def test_language_hint_breaks_ties_only():
    assert detect_language("योजना", hint="mr").language in ("mr", "hi")
    assert detect_language("What is the capital of France?", hint="mr").language == "en"
