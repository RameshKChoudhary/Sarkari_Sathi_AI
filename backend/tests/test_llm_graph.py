"""LangGraph behaviour with a scripted fake LLM (no network)."""
import pytest

from app.generation.graph import build_graph, run_chat
from app.generation.llm import LLMError, LLMResult, OpenAICompatClient, create_llm


class ScriptedLLM:
    model = "fake"

    def __init__(self, replies):
        self.replies, self.calls = list(replies), 0

    def chat(self, system, user, temperature=0.0, max_tokens=700):
        self.calls += 1
        r = self.replies.pop(0) if self.replies else self.replies_last
        if isinstance(r, Exception):
            raise r
        self.replies_last = r
        return LLMResult(text=r, model="fake", latency_ms=1.0, prompt_tokens=10, completion_tokens=5)


def graph_with(service, llm):
    ctx = service.ctx
    old = ctx.llm
    ctx.llm = llm
    return build_graph(ctx), ctx, old


def test_llm_grounded_answer_is_kept(service):
    llm = ScriptedLLM(["Eligible women receive ₹1,500 per month through direct benefit transfer. [1]"])
    g, ctx, old = graph_with(service, llm)
    try:
        r = run_chat(g, ctx, "How much money per month does Ladki Bahin Yojana give?")
    finally:
        ctx.llm = old
    assert not r.abstained and r.pipeline["generator"].startswith("llm:") and r.pipeline["llm_usage"]["prompt_tokens"] == 10


def test_llm_hallucinated_numbers_trigger_extractive_fallback(service):
    llm = ScriptedLLM(["Women aged 18 to 99 get Rs 9,999 every week. [1]"] * 3)
    g, ctx, old = graph_with(service, llm)
    try:
        r = run_chat(g, ctx, "How much money per month does Ladki Bahin Yojana give?")
    finally:
        ctx.llm = old
    assert "9,999" not in r.answer and "generator" in r.pipeline and "extractive" in r.pipeline["generator"]
    assert r.verification.ok


def test_llm_not_found_means_abstain(service):
    llm = ScriptedLLM(["NOT_FOUND"])
    g, ctx, old = graph_with(service, llm)
    try:
        r = run_chat(g, ctx, "How much money per month does Ladki Bahin Yojana give?")
    finally:
        ctx.llm = old
    assert r.abstained and r.sources == []


def test_llm_error_falls_back_to_extractive(service):
    llm = ScriptedLLM([LLMError("boom")])
    g, ctx, old = graph_with(service, llm)
    try:
        r = run_chat(g, ctx, "How much money per month does Ladki Bahin Yojana give?")
    finally:
        ctx.llm = old
    assert not r.abstained and "llm_error" in r.pipeline


def test_client_requires_key_and_parses_response(monkeypatch):
    with pytest.raises(LLMError):
        OpenAICompatClient("https://x", "", "m")
    import httpx

    class R:
        status_code = 200
        headers = {}
        def raise_for_status(self): pass
        def json(self): return {"choices": [{"message": {"content": "hi"}}], "usage": {"prompt_tokens": 3, "completion_tokens": 1}}
    monkeypatch.setattr(httpx, "post", lambda *a, **k: R())
    res = OpenAICompatClient("https://x", "key", "m").chat("s", "u")
    assert res.text == "hi" and res.prompt_tokens == 3


def test_create_llm_is_none_without_key():
    from app.core.config import Settings
    assert create_llm(Settings(llm_provider="groq", groq_api_key="")) is None
    assert create_llm(Settings(llm_provider="extractive")) is None
