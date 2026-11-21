"""LLM access. One thin client for any OpenAI-compatible chat endpoint (Groq, OpenRouter,
Together, a local vLLM/Ollama server...). Keys come from the environment only."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

import httpx

from ..core.config import Settings

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    pass


@dataclass
class LLMResult:
    text: str
    model: str
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0


class OpenAICompatClient:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 45.0, retries: int = 2) -> None:
        if not api_key:
            raise LLMError("no API key configured (set GROQ_API_KEY or LLM_API_KEY in .env)")
        self.base_url, self.api_key, self.model = base_url.rstrip("/"), api_key, model
        self.timeout, self.retries = timeout, retries

    def chat(self, system: str, user: str, temperature: float = 0.0, max_tokens: int = 700) -> LLMResult:
        payload = {
            "model": self.model, "temperature": temperature, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        last: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            t0 = time.perf_counter()
            try:
                r = httpx.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=self.timeout)
                if r.status_code in (429, 500, 502, 503, 504) and attempt < self.retries:
                    wait = float(r.headers.get("retry-after", 1.5 * (attempt + 1)))
                    logger.warning("LLM HTTP %s, retrying in %.1fs", r.status_code, wait)
                    time.sleep(min(wait, 10))
                    continue
                r.raise_for_status()
                data = r.json()
                usage = data.get("usage") or {}
                return LLMResult(
                    text=data["choices"][0]["message"]["content"] or "", model=self.model,
                    latency_ms=(time.perf_counter() - t0) * 1000,
                    prompt_tokens=int(usage.get("prompt_tokens", 0)), completion_tokens=int(usage.get("completion_tokens", 0)),
                )
            except (httpx.HTTPError, KeyError, ValueError) as exc:
                last = exc
                if attempt < self.retries:
                    time.sleep(1.0 * (attempt + 1))
        raise LLMError(f"LLM request failed: {last}")


def create_llm(settings: Settings) -> Optional[OpenAICompatClient]:
    """Return a client, or None when running in offline/extractive mode."""
    provider = settings.resolved_llm_provider
    if provider == "extractive":
        return None
    key = settings.groq_api_key if provider == "groq" else (settings.llm_api_key or settings.groq_api_key)
    try:
        return OpenAICompatClient(settings.llm_base_url, key, settings.llm_model, settings.llm_timeout_s)
    except LLMError as exc:
        logger.warning("LLM disabled: %s", exc)
        return None
