"""CSV and TSV transcript importer."""

from __future__ import annotations

import csv
import uuid
from pathlib import Path
from typing import Iterable

from imbizo.domain.transcripts import SegmentLevel, SourceFormat, TranscriptDocument, TranscriptSegment, split_tokens_preserving_offsets
from imbizo.importers.base import ImportedBundle, ImportOptions, ImportProgress


TEXT_COLUMNS = {
    "text",
    "transcript",
    "utterance",
    "sentence",
    "segment",
    "content",
    "発話",
    "発話内容",
    "テキスト",
    "本文",
}
START_COLUMNS = {"start_ms", "start", "begin", "onset", "start_time", "開始", "開始時刻"}
END_COLUMNS = {"end_ms", "end", "finish", "offset", "end_time", "終了", "終了時刻"}
ID_COLUMNS = {"id", "segment_id", "utterance_id", "ref", "番号"}
COMMON_NON_TEXT_COLUMNS = START_COLUMNS | END_COLUMNS | ID_COLUMNS | {"speaker", "speaker_id", "話者", "language", "lang"}
FALLBACK_ENCODINGS = ("utf-8-sig", "utf-8", "cp932", "shift_jis", "latin-1")


def _emit_progress(options: ImportOptions, stage: str, message: str, current: int, total: int) -> None:
    """Notify a GUI or CLI progress observer when one is attached."""

    if options.progress_callback is not None:
        options.progress_callback(ImportProgress(stage=stage, message=message, current=current, total=total))


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

        _emit_progress(options, "parse", "Reading delimited transcript", 40, 100)
        text, encoding_used = _read_text_with_fallback(path, options.encoding)
        delimiter = _detect_delimiter(text, path)
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
        lines = text.splitlines()
        reader = csv.DictReader(lines, delimiter=delimiter)
        if not reader.fieldnames:
            return ImportedBundle(document=document, report={"warning": "No rows found.", "encoding": encoding_used})

        fieldnames = [_clean_header(name) for name in reader.fieldnames]
        text_column = _choose_text_column(fieldnames)
        start_column = _first_matching(fieldnames, START_COLUMNS)
        end_column = _first_matching(fieldnames, END_COLUMNS)
        id_column = _first_matching(fieldnames, ID_COLUMNS)

        total = max(len(lines) - 1, 1)
        for order, raw_row in enumerate(reader, start=1):
            row = {_clean_header(key): (value or "") for key, value in raw_row.items() if key is not None}
            segment_text = row.get(text_column or "", "")
            if not segment_text.strip():
                if order == 1 or order == total or order % 500 == 0:
                    _emit_progress(options, "parse", f"Scanned {order:,} of {total:,} rows", 40 + int(order / total * 40), 100)
                continue
            segment = TranscriptSegment(
                id=str(uuid.uuid4()),
                transcript_document_id=document.id,
                media_asset_id=options.linked_media_asset_id,
                segment_level=SegmentLevel.UTTERANCE,
                sort_order=order,
                text_original=segment_text,
                start_ms=_to_int(row.get(start_column or "")),
                end_ms=_to_int(row.get(end_column or "")),
                external_ref=row.get(id_column or "", ""),
            )
            segments.append(segment)
            tokens.extend(split_tokens_preserving_offsets(segment.id, segment_text))
            if order == 1 or order == total or order % 500 == 0:
                _emit_progress(options, "parse", f"Parsed {order:,} of {total:,} rows", 40 + int(order / total * 40), 100)

        report: dict[str, object] = {
            "segments": len(segments),
            "tokens": len(tokens),
            "encoding": encoding_used,
            "delimiter": "\\t" if delimiter == "\t" else delimiter,
            "text_column": text_column,
            "columns": fieldnames,
        }
        if not segments:
            report["warning"] = (
                "No transcript rows were imported. Add a text/transcript/utterance column, "
                "or put the utterance text in the first non-metadata column."
            )
        return ImportedBundle(document=document, segments=segments, tokens=tokens, report=report)


def _read_text_with_fallback(path: Path, preferred_encoding: str) -> tuple[str, str]:
    """Read CSV text with offline fallbacks for Excel-origin files."""

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


def _detect_delimiter(text: str, path: Path) -> str:
    """Detect CSV delimiter while preserving explicit TSV handling."""

    if path.suffix.lower() == ".tsv":
        return "\t"
    sample = "\n".join(text.splitlines()[:20])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
    except csv.Error:
        return ","
    return dialect.delimiter


def _clean_header(value: str | None) -> str:
    """Normalize spreadsheet headers, including UTF-8 BOM from Excel."""

    return (value or "").replace("\ufeff", "").strip().lower()


def _first_matching(fieldnames: Iterable[str], candidates: set[str]) -> str | None:
    for name in fieldnames:
        if name in candidates:
            return name
    return None


def _choose_text_column(fieldnames: list[str]) -> str | None:
    explicit = _first_matching(fieldnames, TEXT_COLUMNS)
    if explicit:
        return explicit
    for name in fieldnames:
        if name and name not in COMMON_NON_TEXT_COLUMNS:
            return name
    return fieldnames[0] if fieldnames else None
