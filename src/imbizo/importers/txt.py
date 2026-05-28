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
from imbizo.importers.base import ImportedBundle, ImportOptions, ImportProgress


FALLBACK_ENCODINGS = ("utf-8-sig", "utf-8", "cp932", "shift_jis", "latin-1")


def _emit_progress(options: ImportOptions, stage: str, message: str, current: int, total: int) -> None:
    """Notify a GUI or CLI progress observer when one is attached."""

    if options.progress_callback is not None:
        options.progress_callback(ImportProgress(stage=stage, message=message, current=current, total=total))


def _read_text_with_fallback(path: Path, preferred_encoding: str) -> tuple[str, str]:
    """Read text with offline fallbacks for files exported from local tools."""

    candidates = tuple(dict.fromkeys((preferred_encoding, *FALLBACK_ENCODINGS)))
    last_error: UnicodeDecodeError | None = None
    for encoding in candidates:
        try:
            return path.read_text(encoding=encoding), encoding
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    return path.read_text(encoding=preferred_encoding), preferred_encoding


class TxtImporter:
    """Import TXT transcripts while preserving original line text."""

    name = "txt"

    def can_import(self, path: Path) -> bool:
        """Return whether this importer can parse a copied local file."""

        return path.suffix.lower() == ".txt"

    def import_file(self, path: Path, options: ImportOptions) -> ImportedBundle:
        """Parse a TXT transcript into utterance segments and tokens."""

        _emit_progress(options, "parse", "Reading plain-text transcript", 40, 100)
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
        text, encoding_used = _read_text_with_fallback(path, options.encoding)
        lines = [line.rstrip("\n") for line in text.splitlines() if line.strip()]
        total = max(len(lines), 1)
        for order, line in enumerate(lines, start=1):
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
            if order == 1 or order == total or order % 100 == 0:
                _emit_progress(options, "parse", f"Parsed {order:,} of {total:,} text lines", 40 + int(order / total * 40), 100)
        return ImportedBundle(
            document=document,
            segments=segments,
            tokens=tokens,
            report={"segments": len(segments), "tokens": len(tokens), "encoding": encoding_used},
        )
