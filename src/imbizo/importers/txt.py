"""Plain text transcript importer."""

from __future__ import annotations

import uuid
from pathlib import Path

from imbizo.domain.transcripts import (
    SegmentLevel,
    SourceFormat,
    TranscriptDocument,
    TranscriptSegment,
    split_tokens_preserving_offsets,
)
from imbizo.importers.base import ImportedBundle, ImportOptions


class TxtImporter:
    """Import TXT transcripts while preserving original line text."""

    name = "txt"

    def can_import(self, path: Path) -> bool:
        """Return whether this importer can parse a copied local file."""

        return path.suffix.lower() == ".txt"

    def import_file(self, path: Path, options: ImportOptions) -> ImportedBundle:
        """Parse a TXT transcript into utterance segments and tokens."""

        document = TranscriptDocument(
            id=str(uuid.uuid4()),
            name=path.stem,
            source_format=SourceFormat.TXT,
            media_asset_id=options.linked_media_asset_id,
            relative_path=str(path),
            original_filename=path.name,
        )
        segments: list[TranscriptSegment] = []
        tokens = []
        text = path.read_text(encoding=options.encoding)
        for order, line in enumerate([line.rstrip("\n") for line in text.splitlines() if line.strip()], start=1):
            segment = TranscriptSegment(
                id=str(uuid.uuid4()),
                transcript_document_id=document.id,
                media_asset_id=options.linked_media_asset_id,
                segment_level=SegmentLevel.UTTERANCE,
                sort_order=order,
                text_original=line,
            )
            segments.append(segment)
            tokens.extend(split_tokens_preserving_offsets(segment.id, line))
        return ImportedBundle(
            document=document,
            segments=segments,
            tokens=tokens,
            report={"segments": len(segments), "tokens": len(tokens)},
        )
