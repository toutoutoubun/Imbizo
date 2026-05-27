"""Structured JSON transcript importer."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from imbizo.domain.transcripts import SegmentLevel, SourceFormat, TranscriptDocument, TranscriptSegment, split_tokens_preserving_offsets
from imbizo.importers.base import ImportedBundle, ImportOptions


def _segments_from_json(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        if isinstance(data.get("segments"), list):
            return [item for item in data["segments"] if isinstance(item, dict)]
        if isinstance(data.get("utterances"), list):
            return [item for item in data["utterances"] if isinstance(item, dict)]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


class JsonTranscriptImporter:
    """Import structured transcript JSON."""

    name = "json"

    def can_import(self, path: Path) -> bool:
        """Return whether this importer can parse a copied local file."""

        return path.suffix.lower() == ".json"

    def import_file(self, path: Path, options: ImportOptions) -> ImportedBundle:
        """Parse JSON transcript data into segments and tokens."""

        data = json.loads(path.read_text(encoding=options.encoding))
        document = TranscriptDocument(
            id=str(uuid.uuid4()),
            name=path.stem,
            source_format=SourceFormat.JSON,
            media_asset_id=options.linked_media_asset_id,
            relative_path=str(path),
            original_filename=path.name,
        )
        segments: list[TranscriptSegment] = []
        tokens = []
        for order, item in enumerate(_segments_from_json(data), start=1):
            text = str(item.get("text") or item.get("transcript") or item.get("utterance") or "").strip()
            if not text:
                continue
            segment = TranscriptSegment(
                id=str(uuid.uuid4()),
                transcript_document_id=document.id,
                media_asset_id=options.linked_media_asset_id,
                segment_level=SegmentLevel.UTTERANCE,
                sort_order=int(item.get("sort_order") or order),
                text_original=text,
                start_ms=item.get("start_ms"),
                end_ms=item.get("end_ms"),
                external_ref=str(item.get("id") or ""),
            )
            segments.append(segment)
            tokens.extend(split_tokens_preserving_offsets(segment.id, text))
        return ImportedBundle(document=document, segments=segments, tokens=tokens, report={"segments": len(segments), "tokens": len(tokens)})
