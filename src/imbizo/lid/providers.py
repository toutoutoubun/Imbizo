"""Language identifier provider protocols."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol, Sequence


class LidLayer(StrEnum):
    """Local LID layers."""

    LAYER1_BASELINE = "layer1_baseline"
    LAYER2_AFROLID = "layer2_afrolid"
    LAYER3_MASKLID = "layer3_masklid"


@dataclass(slots=True)
class LidProgress:
    """One local LID progress update.

    Local LID can touch thousands of tokens in a long interview. This progress
    object keeps GUI feedback offline and explicit without coupling service
    code to PySide6.
    """

    current: int
    total: int
    message: str


LidProgressCallback = Callable[[LidProgress], None]


@dataclass(slots=True)
class LidOptions:
    """Options for local LID."""

    max_languages: int = 3
    min_confidence: float = 0.25
    use_optional_afrolid: bool = False
    progress_callback: LidProgressCallback | None = None


@dataclass(slots=True)
class LanguageScore:
    """A language code and confidence score from a provider."""

    language_code: str
    confidence: float
    evidence: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class LidSuggestionDraft:
    """Suggestion before persistence."""

    token_id: str | None
    segment_id: str | None
    language_id: str | None
    layer: LidLayer
    rank: int
    confidence: float | None
    evidence: dict[str, object] = field(default_factory=dict)


class LanguageIdentifier(Protocol):
    """Local language identification provider."""

    @property
    def name(self) -> str:
        """Return provider name."""

    @property
    def version(self) -> str:
        """Return provider version or resource version."""

    def predict(self, texts: Sequence[str], options: LidOptions) -> list[list[LanguageScore]]:
        """Return ranked language scores for each input text."""
