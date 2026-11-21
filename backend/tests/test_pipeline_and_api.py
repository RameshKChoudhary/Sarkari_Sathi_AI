import pytest
from fastapi.testclient import TestClient

from app.models.schemas import ChatRequest


def test_end_to_end_answers_in_user_language(service):
    cases = {
        "What are the eligibility criteria for PM Kisan?": "en",
        "पीएम किसान योजना के लिए कौन पात्र है?": "hi",
        "मला लाडकी बहीण योजनेसाठी अर्ज कसा करायचा?": "mr",
        "ladki bahin yojana sathi apply kasa karaycha?": "mr",
    }
    for q, lang in cases.items():
        r = service.chat(ChatRequest(query=q))
        assert r.language == lang and not r.abstained, q
        assert r.sources and any(s.cited for s in r.sources)
        assert r.disclaimer and r.verification and r.verification.ok
        cited = [s for s in r.sources if s.cited][0]
        assert cited.language == lang and cited.source_url.startswith("https://")


def test_marathi_apply_answer_cites_ladki_bahin_how_to_apply(service):
    r = service.chat(ChatRequest(query="मला लाडकी बहीण योजनेसाठी अर्ज कसा करायचा?"))
    cited = [s for s in r.sources if s.cited][0]
    assert (cited.scheme_id, cited.section_type) == ("ladki_bahin", "how_to_apply")
    assert "नारी शक्ती" in r.answer and "[" in r.answer


def test_abstains_when_out_of_scope(service):
    for q in ["What is the capital of France?", "फ्रांस की राजधानी क्या है?"]:
        r = service.chat(ChatRequest(query=q))
        assert r.abstained and r.sources == [] and r.abstain_reason
    assert "फ्रांस" not in r.answer or "नहीं" in r.answer


def test_scheme_filter_restricts_sources(service):
    from app.models.schemas import Filters
    r = service.chat(ChatRequest(query="How can I apply?", filters=Filters(scheme_ids=["mudra"])))
    assert all(s.scheme_id == "mudra" for s in r.sources)


def test_cache_hit_flag(service):
    q = ChatRequest(query="How much does Atal Pension Yojana pay?")
    service.chat(q)
    assert service.chat(q).pipeline["cache"] == "hit"


def test_api_endpoints(service):
    from app.main import create_app
    app = create_app()
    with TestClient(app) as c:
        app.state.service = service
        assert c.get("/api/health").json()["chunks"] == len(service.chunks)
        r = c.post("/api/chat", json={"query": "पीक विमा योजनेत खरीप पिकांसाठी किती प्रीमियम?"}).json()
        assert r["language"] == "mr" and "answer" in r and "sources" in r
        assert c.post("/api/chat", json={"query": ""}).status_code == 422
        assert c.post("/api/chat", json={"query": "x" * 5000}).status_code == 422
        schemes = c.get("/api/schemes").json()
        assert len(schemes) == 10 and {s["level"] for s in schemes} == {"central", "state"}
        assert c.get("/api/schemes?level=state").json() and c.get("/api/schemes/mudra").status_code == 200
        assert c.get("/api/schemes/nope").status_code == 404
        assert c.get("/api/suggestions?lang=hi").json()
        d = c.post("/api/detect-language", json={"text": "ladki bahin yojana sathi apply kasa karaycha?"}).json()
        assert d["romanized"] and d["language"] == "mr"
        hits = c.post("/api/retrieve", json={"query": "pension", "top_k": 3, "mode": "bm25"}).json()
        assert len(hits) == 3
        with c.stream("POST", "/api/chat/stream", json={"query": "What documents are needed for Sukanya Samriddhi?"}) as s:
            events = [l.split(": ", 1)[1] for l in s.iter_lines() if l.startswith("event:")]
        assert events[0] == "stage" and "sources" in events and events[-1] == "done"


def test_api_reports_missing_corpus(tmp_path, monkeypatch):
    from app.core import config
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    config.get_settings.cache_clear()
    from app.main import create_app
    with TestClient(create_app()) as c:
        assert c.get("/api/health").json()["status"] == "error"
        assert c.post("/api/chat", json={"query": "hello"}).status_code == 503
    config.get_settings.cache_clear()
