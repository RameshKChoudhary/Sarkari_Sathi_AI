"""Golden-set loading."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class Gold(BaseModel):
    scheme_id: str
    section: str


class GoldenItem(BaseModel):
    id: str
    group_id: str
    language: str  # en | hi | mr | mr_roman
    question: str
    question_en: str
    answerable: bool
    gold: Optional[Gold] = None
    key_facts: list[list[str]] = []
    kind: str = "answerable"
    split: str = "test"
    verification: dict = {}

    @property
    def query_lang(self) -> str:
        return "mr" if self.language == "mr_roman" else self.language


def load_golden(path: Path) -> list[GoldenItem]:
    items = [GoldenItem.model_validate(x) for x in json.loads(path.read_text(encoding="utf-8"))]
    return [i for i in items if i.verification.get("status") != "rejected"]  # rejected by a reviewer
