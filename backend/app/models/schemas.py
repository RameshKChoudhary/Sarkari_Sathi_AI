"""Pydantic models shared by ingestion, retrieval, generation and the API."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

Language = Literal["en", "hi", "mr"]
SectionType = Literal["overview", "eligibility", "benefits", "documents", "how_to_apply"]
Level = Literal["central", "state"]

SECTION_TYPES: list[str] = ["overview", "eligibility", "benefits", "documents", "how_to_apply"]
LANGUAGES: list[str] = ["en", "hi", "mr"]

SECTION_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "overview": "Overview",
        "eligibility": "Eligibility",
        "benefits": "Benefits",
        "documents": "Documents Required",
        "how_to_apply": "How to Apply",
    },
    "hi": {
        "overview": "परिचय",
        "eligibility": "पात्रता",
        "benefits": "लाभ",
        "documents": "आवश्यक दस्तावेज़",
        "how_to_apply": "आवेदन कैसे करें",
    },
    "mr": {
        "overview": "परिचय",
        "eligibility": "पात्रता",
        "benefits": "लाभ",
        "documents": "आवश्यक कागदपत्रे",
        "how_to_apply": "अर्ज कसा करावा",
    },
}


class Chunk(BaseModel):
    """One retrievable passage plus the metadata required by the project spec."""

    chunk_id: str
    doc_id: str
    scheme_id: str
    scheme_name: str
    level: Level
    language: Language
    source_url: str
    publication_date: Optional[str] = None  # None => unavailable (shown as such in the UI)
    section_type: SectionType
    doc_ref: str  # original document reference (file name / GR number)
    text: str  # passage body as shown to the user
    char_start: int = 0
    char_end: int = 0
    page: Optional[int] = None
    extraction_method: str = "text"  # text | ocr_scanned | ocr_legacy_font
    chunking: Literal["structure", "fixed"] = "structure"
    contextual_header: bool = True
    data_status: str = "sample_fixture"  # sample_fixture | official | unverified

    @property
    def chunk_key(self) -> str:
        return f"{self.scheme_id}#{self.section_type}"

    @property
    def retrieval_text(self) -> str:
        """Text used for indexing: body, optionally prefixed with 'Scheme - Section'."""
        if self.contextual_header:
            label = SECTION_LABELS[self.language][self.section_type]
            return f"{self.scheme_name} — {label}\n{self.text}"
        return self.text


class Filters(BaseModel):
    scheme_ids: Optional[list[str]] = None
    levels: Optional[list[Level]] = None
    section_types: Optional[list[SectionType]] = None
    languages: Optional[list[Language]] = None

    @property
    def is_empty(self) -> bool:
        return not any([self.scheme_ids, self.levels, self.section_types, self.languages])

    def matches(self, c: Chunk) -> bool:
        if self.scheme_ids and c.scheme_id not in self.scheme_ids:
            return False
        if self.levels and c.level not in self.levels:
            return False
        if self.section_types and c.section_type not in self.section_types:
            return False
        if self.languages and c.language not in self.languages:
            return False
        return True


class SearchHit(BaseModel):
    chunk: Chunk
    score: float
    rank: int = 0
    scores: dict[str, float] = Field(default_factory=dict)  # raw per-component scores
    ranks: dict[str, int] = Field(default_factory=dict)  # per-component ranks (1-based)


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    ui_language: Optional[Language] = None
    filters: Optional[Filters] = None
    top_k: int = Field(5, ge=1, le=10)


class SourceCard(BaseModel):
    id: int
    chunk_id: str
    scheme_id: str
    scheme_name: str
    level: Level
    language: Language
    section_type: SectionType
    source_url: str
    publication_date: Optional[str] = None
    doc_ref: str
    text: str
    highlight: Optional[str] = None
    score: float
    cited: bool = False
    data_status: str = "sample_fixture"
    extraction_method: str = "text"


class VerificationReport(BaseModel):
    ok: bool = True
    checked_sentences: int = 0
    kept_sentences: int = 0
    removed: list[str] = Field(default_factory=list)
    invalid_citations: list[int] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    language: Language
    script: str
    romanized: bool = False
    abstained: bool
    abstain_reason: Optional[str] = None
    sources: list[SourceCard] = Field(default_factory=list)
    disclaimer: str
    verification: Optional[VerificationReport] = None
    timings_ms: dict[str, float] = Field(default_factory=dict)
    pipeline: dict[str, Any] = Field(default_factory=dict)


class SchemeSummary(BaseModel):
    scheme_id: str
    names: dict[str, str]
    level: Level
    languages: list[str]
    sections: list[str]
    official_url: str
    data_status: str
    publication_date: Optional[str] = None
    n_chunks: int = 0


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    mode: Optional[Literal["bm25", "ngram", "dense", "hybrid", "hybrid_lex"]] = None
    top_k: int = Field(5, ge=1, le=20)
    expand_query: Optional[bool] = None
    filters: Optional[Filters] = None
