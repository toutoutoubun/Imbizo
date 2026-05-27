"""CSV and TSV transcript importer."""

from __future__ import annotations

import csv
import uuid
from pathlib import Path

from imbizo.domain.transcripts import SegmentLevel, SourceFormat, TranscriptDocument, TranscriptSegment, split_tokens_preserving_offsets
from imbizo.importers.base import ImportedBundle, ImportOptions


def _to_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


class CsvTranscriptImporter:
    """Import CSV or TSV transcript rows."""

    name = "csv_tsv"

    def can_import(self, path: Path) -> bool:
        """Return whether this importer can parse a copied local file."""

        return path.suffix.lower() in {".csv", ".tsv"}

    def import_file(self, path: Path, options: ImportOptions) -> ImportedBundle:
        """Parse CSV/TSV rows into segments and tokens."""

        delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
        document = TranscriptDocument(
            id=str(uuid.uuid4()),
            name=path.stem,
            source_format=SourceFormat.TSV if delimiter == "\t" else SourceFormat.CSV,
            media_asset_id=options.linked_media_asset_id,
            relative_path=str(path),
            original_filename=path.name,
        )
        segments: list[TranscriptSegment] = []
        tokens = []
        with path.open("r", encoding=options.encoding, newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            if not reader.fieldnames:
                return ImportedBundle(document=document, report={"warning": "No rows found."})
            for order, row in enumerate(reader, start=1):
                text = row.get("text") or row.get("transcript") or row.get("utterance") or ""
                if not text.strip():
                    continue
                segment = TranscriptSegment(
                    id=str(uuid.uuid4()),
                    transcript_document_id=document.id,
                    media_asset_id=options.linked_media_asset_id,
                    segment_level=SegmentLevel.UTTERANCE,
                    sort_order=order,
                    text_original=text,
                    start_ms=_to_int(row.get("start_ms") or row.get("start")),
                    end_ms=_to_int(row.get("end_ms") or row.get("end")),
                    external_ref=row.get("id") or "",
                )
                segments.append(segment)
                tokens.extend(split_tokens_preserving_offsets(segment.id, text))
        return ImportedBundle(document=document, segments=segments, tokens=tokens, report={"segments": len(segments), "tokens": len(tokens)})
