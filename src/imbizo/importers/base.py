"""Importer protocols and result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from imbizo.domain.media import MediaAsset
from imbizo.domain.transcripts import Token, TranscriptDocument, TranscriptSegment


@dataclass(slots=True)
class ImportOptions:
    """Options used while importing a copied local file."""

    linked_media_asset_id: str | None = None
    encoding: str = "utf-8"


@dataclass(slots=True)
class ImportedBundle:
    """Parsed import output before persistence."""

    document: TranscriptDocument | None = None
    segments: list[TranscriptSegment] = field(default_factory=list)
    tokens: list[Token] = field(default_factory=list)
    media_assets: list[MediaAsset] = field(default_factory=list)
    report: dict[str, object] = field(default_factory=dict)


class Importer(Protocol):
    """Parser for one or more local import formats."""

    @property
    def name(self) -> str:
        """Return a stable importer name."""

    def can_import(self, path: Path) -> bool:
        """Return whether this importer can parse a copied local file."""

    def import_file(self, path: Path, options: ImportOptions) -> ImportedBundle:
        """Parse a copied local file into domain objects."""
