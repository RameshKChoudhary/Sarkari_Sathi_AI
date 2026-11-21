"""Shared runtime objects for the generation graph."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from ..core.config import Settings
from ..models.schemas import Chunk
from ..retrieval.expansion import QueryExpander
from ..retrieval.retriever import Retriever
from .llm import OpenAICompatClient


@dataclass
class RagContext:
    settings: Settings
    chunks: list[Chunk]
    retriever_for: Callable[[], Retriever]  # returns the configured default retriever
    llm: Optional[OpenAICompatClient] = None
    expander: Optional[QueryExpander] = None
    degraded: list[str] = field(default_factory=list)  # e.g. ["embedding model unavailable -> hybrid_lex"]

    def __post_init__(self) -> None:
        self.by_id = {c.chunk_id: c for c in self.chunks}
        self.sibling: dict[tuple[str, str, str], Chunk] = {}
        for c in self.chunks:
            self.sibling.setdefault((c.scheme_id, c.section_type, c.language), c)
