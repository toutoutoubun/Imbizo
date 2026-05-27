"""Exporter protocols and packages."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from imbizo.domain.annotations import Annotation
from imbizo.domain.languages import LanguageTag
from imbizo.domain.metrics import MetricResult
from imbizo.domain.project import ProjectMetadata
from imbizo.domain.transcripts import Token, TranscriptDocument, TranscriptSegment


@dataclass(slots=True)
class ExportOptions:
    """Options for local export."""

    include_auto: bool = True
    include_memos: bool = True
    document_id: str | None = None


@dataclass(slots=True)
class ExportPackage:
    """Domain data prepared for an exporter."""

    metadata: ProjectMetadata
    languages: list[LanguageTag]
    documents: list[TranscriptDocument]
    segments: list[TranscriptSegment]
    tokens: list[Token]
    annotations: list[Annotation]
    metrics: list[MetricResult] = field(default_factory=list)


@dataclass(slots=True)
class ExportedFile:
    """A written local export file."""

    path: Path
    format_name: str


class Exporter(Protocol):
    """Writer for one local export format."""

    @property
    def format_name(self) -> str:
        """Return a stable export format name."""

    def export(self, package: ExportPackage, destination: Path, options: ExportOptions) -> ExportedFile:
        """Write a local export file."""
