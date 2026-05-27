"""Annotation data model and SQLite persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from imbizo.domain.annotations import (
    Annotation,
    AnnotationDraft,
    AnnotationSource,
    AnnotationStatus,
    LinguisticStatus,
    SwitchType,
    Tag,
    choose_effective_annotation,
    validate_annotation_target,
)
from imbizo.persistence.repositories import AnnotationRepository, TagRepository
from imbizo.services.annotation_service import AnnotationEditorState, AnnotationRow, AnnotationService

__all__ = [
    "Annotation",
    "AnnotationDraft",
    "AnnotationEditorState",
    "AnnotationRepository",
    "AnnotationRow",
    "AnnotationService",
    "AnnotationSource",
    "AnnotationStatus",
    "LinguisticStatus",
    "SwitchType",
    "Tag",
    "TagRepository",
    "Token",
    "choose_effective_annotation",
    "token_from_mapping",
    "validate_annotation_target",
]


@dataclass(slots=True)
class Token:
    """Small token contract used by local v1.5 advisory modules."""

    id: str
    surface: str
    utterance_id: str | None = None
    position: int = 0
    language: str | None = None
    normalized: str | None = None
    speaker_id: str | None = None
    nc_class: int | None = None
    nc_prefix: str | None = None
    four_m_type: str | None = None
    sister_lang_confidence: float | None = None
    sister_lang_evidence: str | None = None
    trigger_role: str | None = None
    mixed_code_variety: str | None = None
    phon_integration_score: float | None = None
    metadata: dict[str, Any] | None = None

    @property
    def text_for_matching(self) -> str:
        """Return normalized text if available, otherwise the original surface."""

        return self.normalized or self.surface


def token_from_mapping(data: dict[str, Any]) -> Token:
    """Create a token contract object from a SQLite row or JSON-like mapping."""

    fields = {field for field in Token.__dataclass_fields__}
    return Token(**{key: value for key, value in data.items() if key in fields})
