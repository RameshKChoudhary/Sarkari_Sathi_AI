"""FastAPI application factory.  Run: uvicorn app.main:app --reload  (from backend/)."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..core.config import get_settings
from ..core.logging import setup_logging
from ..services.rag_service import CorpusNotReady, RagService
from .routes import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    setup_logging(s.log_level)
    app.state.service = None
    try:
        app.state.service = RagService(s)
    except CorpusNotReady as exc:
        app.state.startup_error = str(exc)
        logger.error("%s", exc)
    yield


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title=f"{s.app_name} API", version="1.0.0", lifespan=lifespan,
                  description="Multilingual (English/Hindi/Marathi) RAG over Indian government schemes.")
    app.add_middleware(CORSMiddleware, allow_origins=s.cors_list, allow_methods=["*"], allow_headers=["*"])
    app.include_router(router)

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error")
        return JSONResponse(status_code=500, content={"detail": f"internal error: {exc.__class__.__name__}"})

    static = Path(s.static_dir) if s.static_dir and str(s.static_dir) not in ("", ".") else None
    if static and (static / "index.html").is_file():  # serve the built React app (single-container deploys)
        if (static / "assets").is_dir():
            app.mount("/assets", StaticFiles(directory=static / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str) -> FileResponse:
            f = static / path
            return FileResponse(f if path and f.is_file() else static / "index.html")

    return app