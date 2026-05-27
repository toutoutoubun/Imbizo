"""Annotation data model and SQLite persistence."""

from __future__ import annotations

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
    "choose_effective_annotation",
    "validate_annotation_target",
]
