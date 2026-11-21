import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))


@pytest.fixture(scope="session")
def corpus_ready() -> bool:
    return (ROOT / "data/processed/chunks_structure.jsonl").exists()


@pytest.fixture(scope="session")
def service():
    """Real RagService on the ingested sample corpus, offline/extractive mode."""
    if not (ROOT / "data/processed/chunks_structure.jsonl").exists():
        pytest.skip("run `python backend/scripts/setup_data.py` first")
    from app.core.config import Settings
    from app.services.rag_service import RagService

    return RagService(Settings(retrieval_mode="hybrid_lex", query_expansion=True, use_reranker=False,
                               llm_provider="extractive", min_query_coverage=0.6))
