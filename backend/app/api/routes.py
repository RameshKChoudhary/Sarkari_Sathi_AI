"""HTTP routes. All responses are Pydantic models, so the OpenAPI schema is exact."""
from __future__ import annotations

import json
from typing import Iterator, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..models.schemas import ChatRequest, ChatResponse, SchemeSummary, SearchHit, RetrieveRequest
from ..retrieval.lang import detect_language
from ..services.rag_service import RagService

router = APIRouter(prefix="/api")


def svc(request: Request) -> RagService:
    service = getattr(request.app.state, "service", None)
    if service is None:
        raise HTTPException(503, detail=getattr(request.app.state, "startup_error", "service not ready"))
    return service


class DetectRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class DetectResponse(BaseModel):
    language: str
    script: str
    romanized: bool
    confidence: float


@router.get("/health")
def health(request: Request) -> dict:
    service = getattr(request.app.state, "service", None)
    if service is None:
        return {"status": "error", "detail": getattr(request.app.state, "startup_error", "not ready")}
    return service.health()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request) -> ChatResponse:
    return svc(request).chat(req)


@router.post("/chat/stream")
def chat_stream(req: ChatRequest, request: Request) -> StreamingResponse:
    service = svc(request)

    def gen() -> Iterator[str]:
        try:
            for ev in service.chat_stream(req):
                yield f"event: {ev['event']}\ndata: {json.dumps(ev['data'], ensure_ascii=False)}\n\n"
        except Exception as exc:  # surface errors to the client instead of cutting the stream
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/retrieve", response_model=list[SearchHit])
def retrieve(req: RetrieveRequest, request: Request) -> list[SearchHit]:
    """Debug endpoint: raw retrieval with a selectable mode (bm25 | ngram | dense | hybrid | hybrid_lex)."""
    try:
        return svc(request).retrieve(req)
    except Exception as exc:
        raise HTTPException(400, detail=str(exc)) from exc


@router.post("/detect-language", response_model=DetectResponse)
def detect(req: DetectRequest) -> DetectResponse:
    i = detect_language(req.text)
    return DetectResponse(language=i.language, script=i.script, romanized=i.romanized, confidence=round(i.confidence, 3))


@router.get("/schemes", response_model=list[SchemeSummary])
def schemes(request: Request, level: Optional[str] = Query(None, pattern="^(central|state)$"),
            q: Optional[str] = None) -> list[SchemeSummary]:
    out = svc(request).catalog
    if level:
        out = [s for s in out if s.level == level]
    if q:
        ql = q.lower()
        out = [s for s in out if any(ql in n.lower() for n in s.names.values())]
    return out


@router.get("/schemes/{scheme_id}")
def scheme(scheme_id: str, request: Request) -> dict:
    d = svc(request).scheme_detail(scheme_id)
    if d is None:
        raise HTTPException(404, detail=f"unknown scheme '{scheme_id}'")
    return d


SUGGESTED = {
    "en": ["What are the eligibility criteria for PM Kisan?", "How do I apply for Ladki Bahin Yojana?",
           "What documents are needed for Sukanya Samriddhi?", "How much health cover does Ayushman Bharat give?"],
    "hi": ["पीएम किसान योजना के लिए कौन पात्र है?", "आयुष्मान भारत में कितना स्वास्थ्य कवर मिलता है?",
           "अटल पेंशन योजना में कितनी पेंशन मिलती है?", "उज्ज्वला योजना के लिए आवेदन कैसे करें?"],
    "mr": ["मला लाडकी बहीण योजनेचा लाभ मिळू शकतो का?", "लाडकी बहीण योजनेसाठी अर्ज कसा करायचा?",
           "पीक विमा योजनेत शेतकऱ्याला किती प्रीमियम भरावा लागतो?", "नमो शेतकरी योजनेत किती रक्कम मिळते?"],
}


@router.get("/suggestions")
def suggestions(lang: str = Query("en", pattern="^(en|hi|mr)$")) -> list[str]:
    return SUGGESTED[lang]
