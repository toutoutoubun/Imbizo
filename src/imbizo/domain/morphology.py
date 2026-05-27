"""Morphology assistance models."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(slots=True)
class MorphemeDictionaryEntry:
    """Editable local morphology dictionary entry."""

    id: str
    language_id: str
    surface: str
    category: str
    gloss: str = ""
    notes: str = ""
    source: str = "default"
    is_active: bool = True


@dataclass(slots=True)
class Morpheme:
    """One morpheme inside a token split."""

    id: str
    split_id: str
    sort_order: int
    surface: str
    gloss: str = ""
    category: str = "other"
    language_id: str | None = None
    dictionary_entry_id: str | None = None


@dataclass(slots=True)
class MorphemeSplit:
    """A manual or suggested token-level morpheme segmentation."""

    id: str
    token_id: str
    source: str
    status: str
    split_text: str
    morphemes: list[Morpheme] = field(default_factory=list)
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""


def parse_split_text(split_text: str) -> list[str]:
    """Parse researcher-entered split text into morpheme surfaces."""

    return [part for part in re.split(r"\s*\+\s*|\s*-\s*", split_text.strip()) if part]
