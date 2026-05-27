"""Shared metric dataset helpers."""

from __future__ import annotations

from dataclasses import dataclass

from imbizo.domain.annotations import Annotation
from imbizo.domain.transcripts import Token, TranscriptSegment


@dataclass(slots=True)
class AnnotatedToken:
    """A token with its effective annotation and segment context."""

    token: Token
    segment: TranscriptSegment
    annotation: Annotation | None


@dataclass(slots=True)
class MetricsDataset:
    """Input data for metric calculators."""

    tokens: list[AnnotatedToken]
