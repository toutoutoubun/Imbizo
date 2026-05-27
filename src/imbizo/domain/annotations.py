"""Annotation models and effective annotation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Sequence


class AnnotationSource(StrEnum):
    """Origin of an annotation record."""

    MANUAL = "manual"
    AUTO = "auto"
    IMPORTED = "imported"


class AnnotationStatus(StrEnum):
    """Lifecycle state for annotations and suggestions."""

    ACTIVE = "active"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class SwitchType(StrEnum):
    """Code-switch type labels used by the annotation model."""

    INTRA_SENTENTIAL = "intra_sentential"
    INTER_SENTENTIAL = "inter_sentential"
    EXTRA_SENTENTIAL = "extra_sentential"


class LinguisticStatus(StrEnum):
    """MLF-compatible linguistic status labels."""

    BORROWING = "borrowing"
    INSERTION = "insertion"
    ALTERNATION = "alternation"


@dataclass(slots=True)
class Annotation:
    """Manual, automatic, or imported linguistic annotation."""

    id: str
    source: AnnotationSource
    status: AnnotationStatus = AnnotationStatus.ACTIVE
    token_id: str | None = None
    segment_id: str | None = None
    language_id: str | None = None
    matrix_language_id: str | None = None
    embedded_language_id: str | None = None
    switch_type: SwitchType | None = None
    linguistic_status: LinguisticStatus | None = None
    trigger_text: str = ""
    direction_from_language_id: str | None = None
    direction_to_language_id: str | None = None
    researcher_confidence: int | None = None
    auto_confidence: float | None = None
    memo: str = ""
    tag_ids: list[str] = field(default_factory=list)
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class AnnotationDraft:
    """Editable annotation input before storage assigns an ID."""

    language_id: str | None = None
    matrix_language_id: str | None = None
    embedded_language_id: str | None = None
    switch_type: SwitchType | None = None
    linguistic_status: LinguisticStatus | None = None
    trigger_text: str = ""
    direction_from_language_id: str | None = None
    direction_to_language_id: str | None = None
    researcher_confidence: int | None = None
    memo: str = ""
    tag_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Tag:
    """A user-defined tag that can be attached to annotations."""

    id: str
    name: str
    color_hex: str = "#808080"
    description: str = ""


def validate_annotation_target(token_id: str | None, segment_id: str | None) -> None:
    """Require exactly one token or segment target."""

    if (token_id is None and segment_id is None) or (token_id is not None and segment_id is not None):
        raise ValueError("An annotation must target exactly one token or one segment.")


def choose_effective_annotation(annotations: Sequence[Annotation]) -> Annotation | None:
    """Apply the effective annotation rule for one token or segment."""

    active = [item for item in annotations if item.status == AnnotationStatus.ACTIVE]
    for source in (AnnotationSource.MANUAL, AnnotationSource.IMPORTED, AnnotationSource.AUTO):
        candidates = [item for item in active if item.source == source]
        if candidates:
            return sorted(candidates, key=lambda item: item.updated_at or item.created_at)[-1]
    return None
