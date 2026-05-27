"""Praat TextGrid importer."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from imbizo.domain.transcripts import SegmentLevel, SourceFormat, TranscriptDocument, TranscriptSegment, split_tokens_preserving_offsets
from imbizo.importers.base import ImportedBundle, ImportOptions


class TextGridImporter:
    """Import Praat TextGrid interval text as utterance segments."""

    name = "textgrid"

    def can_import(self, path: Path) -> bool:
        """Return whether this importer can parse a copied local file."""

        return path.suffix.lower() in {".textgrid", ".TextGrid".lower()}

    def import_file(self, path: Path, options: ImportOptions) -> ImportedBundle:
        """Parse simple Praat TextGrid intervals."""

        document = TranscriptDocument(
            id=str(uuid.uuid4()),
            name=path.stem,
            source_format=SourceFormat.TEXTGRID,
            media_asset_id=options.linked_media_asset_id,
            relative_path=str(path),
            original_filename=path.name,
        )
        content = path.read_text(encoding=options.encoding, errors="replace")
        pattern = re.compile(
            r"xmin\s*=\s*(?P<xmin>[0-9.]+)\s+"
            r"xmax\s*=\s*(?P<xmax>[0-9.]+)\s+"
            r"text\s*=\s*\"(?P<text>.*?)\"",
            re.DOTALL,
        )
        segments: list[TranscriptSegment] = []
        tokens = []
        for order, match in enumerate(pattern.finditer(content), start=1):
            text = match.group("text").replace('""', '"').strip()
            if not text:
                continue
            segment = TranscriptSegment(
                id=str(uuid.uuid4()),
                transcript_document_id=document.id,
                media_asset_id=options.linked_media_asset_id,
                segment_level=SegmentLevel.UTTERANCE,
                sort_order=order,
                text_original=text,
                start_ms=int(float(match.group("xmin")) * 1000),
                end_ms=int(float(match.group("xmax")) * 1000),
            )
            segments.append(segment)
            tokens.extend(split_tokens_preserving_offsets(segment.id, text))
        return ImportedBundle(document=document, segments=segments, tokens=tokens, report={"segments": len(segments), "tokens": len(tokens)})
