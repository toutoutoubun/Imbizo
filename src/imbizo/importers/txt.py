"""Plain text transcript importer."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
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
PLAIN_TEXT_SUFFIXES = {".txt", ".text", ".md", ".markdown", ".log", ".srt", ".vtt"}
TIMESTAMP_RE = re.compile(
    r"^\s*(?:\[)?(?P<start>\d{1,2}:\d{2}(?::\d{2})?(?:[,.]\d{1,3})?)"
    r"(?:\s*(?:-->|-|–|—)\s*(?P<end>\d{1,2}:\d{2}(?::\d{2})?(?:[,.]\d{1,3})?))?"
    r"(?:\])?\s*(?P<text>.*)$"
)
SPEAKER_PREFIX_RE = re.compile(r"^\s*(?P<speaker>[\w .@#-]{1,48})\s*[:：\t]\s*(?P<text>\S.*)$", re.UNICODE)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?。！？])\s+")


@dataclass(frozen=True, slots=True)
class PlainTextLine:
    """One parsed plain-text segment before conversion to domain objects."""

    text: str
    speaker_label: str | None = None
    start_ms: int | None = None
    end_ms: int | None = None
    external_ref: str = ""


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
    """Import local plain-text transcripts while preserving readable text.

    The importer intentionally does not require spreadsheet columns. It accepts
    ordinary prose, line-based transcripts, Markdown notes, log-like exports,
    and common subtitle-style text cues. Language labels remain blank until the
    researcher runs Local LID or supplies manual annotations.
    """

    name = "txt"

    def can_import(self, path: Path) -> bool:
        """Return whether this importer can parse a copied local file."""

        return path.suffix.lower() in PLAIN_TEXT_SUFFIXES

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
        parsed_lines = _parse_plain_text(text, path.suffix.lower())
        lines_with_speakers = sum(1 for line in parsed_lines if line.speaker_label)
        lines_with_times = sum(1 for line in parsed_lines if line.start_ms is not None or line.end_ms is not None)
        total = max(len(parsed_lines), 1)
        for order, line in enumerate(parsed_lines, start=1):
            segment = TranscriptSegment(
                id=str(uuid.uuid4()),
                transcript_document_id=document.id,
                media_asset_id=options.linked_media_asset_id,
                segment_level=SegmentLevel.UTTERANCE,
                sort_order=order,
                text_original=line.text,
                speaker_id=line.speaker_label,
                start_ms=line.start_ms,
                end_ms=line.end_ms,
                external_ref=line.external_ref,
            )
            segments.append(segment)
            tokens.extend(split_tokens_preserving_offsets(segment.id, line.text))
            if order == 1 or order == total or order % 100 == 0:
                _emit_progress(options, "parse", f"Parsed {order:,} of {total:,} text lines", 40 + int(order / total * 40), 100)
        return ImportedBundle(
            document=document,
            segments=segments,
            tokens=tokens,
            report={
                "segments": len(segments),
                "tokens": len(tokens),
                "encoding": encoding_used,
                "plain_text_mode": True,
                "extension": path.suffix.lower() or "none",
                "speaker_prefixed_lines": lines_with_speakers,
                "timestamped_lines": lines_with_times,
                "language_labels": 0,
            },
        )


def _parse_plain_text(text: str, suffix: str) -> list[PlainTextLine]:
    """Parse plain text into utterance-like lines without table assumptions."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    if suffix in {".srt", ".vtt"} or "-->" in normalized:
        subtitle_lines = _parse_subtitle_text(normalized)
        if subtitle_lines:
            return subtitle_lines
    raw_lines = [line.strip() for line in normalized.split("\n")]
    non_empty = [line for line in raw_lines if line]
    if len(non_empty) == 1:
        sentence_parts = [part.strip() for part in SENTENCE_SPLIT_RE.split(non_empty[0]) if part.strip()]
        if len(sentence_parts) > 1:
            non_empty = sentence_parts
    parsed = [_parse_plain_line(line, index) for index, line in enumerate(non_empty, start=1)]
    return [line for line in parsed if line.text]


def _parse_plain_line(raw_line: str, order: int) -> PlainTextLine:
    """Parse one line for optional timestamps and speaker prefixes."""

    line = raw_line.strip()
    start_ms: int | None = None
    end_ms: int | None = None
    timestamp_match = TIMESTAMP_RE.match(line)
    if timestamp_match and timestamp_match.group("text"):
        start_ms = _timestamp_to_ms(timestamp_match.group("start"))
        end_raw = timestamp_match.group("end")
        end_ms = _timestamp_to_ms(end_raw) if end_raw else None
        line = timestamp_match.group("text").strip()

    speaker_label: str | None = None
    speaker_match = SPEAKER_PREFIX_RE.match(line)
    if speaker_match and _looks_like_speaker_label(speaker_match.group("speaker")):
        speaker_label = speaker_match.group("speaker").strip()
        line = speaker_match.group("text").strip()
    return PlainTextLine(
        text=line,
        speaker_label=speaker_label,
        start_ms=start_ms,
        end_ms=end_ms,
        external_ref=f"line:{order}",
    )


def _parse_subtitle_text(text: str) -> list[PlainTextLine]:
    """Parse simple SRT/WebVTT cues as plain-text transcript segments."""

    lines: list[PlainTextLine] = []
    blocks = re.split(r"\n\s*\n", text.strip())
    for block_index, block in enumerate(blocks, start=1):
        block_lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not block_lines:
            continue
        if block_lines[0].upper().startswith("WEBVTT"):
            continue
        cue_id = ""
        if block_lines and "-->" not in block_lines[0]:
            cue_id = block_lines.pop(0)
        if not block_lines or "-->" not in block_lines[0]:
            continue
        timing = block_lines.pop(0)
        start_raw, _, end_raw = timing.partition("-->")
        start_ms = _timestamp_to_ms(start_raw.strip())
        end_ms = _timestamp_to_ms(end_raw.strip().split()[0]) if end_raw.strip() else None
        utterance = " ".join(block_lines).strip()
        if not utterance:
            continue
        parsed = _parse_plain_line(utterance, block_index)
        lines.append(
            PlainTextLine(
                text=parsed.text,
                speaker_label=parsed.speaker_label,
                start_ms=start_ms,
                end_ms=end_ms,
                external_ref=cue_id or f"cue:{block_index}",
            )
        )
    return lines


def _timestamp_to_ms(value: str | None) -> int | None:
    """Convert HH:MM:SS.mmm or MM:SS.mmm timestamps to milliseconds."""

    if not value:
        return None
    cleaned = value.strip().replace(",", ".")
    parts = cleaned.split(":")
    try:
        seconds = float(parts[-1])
        minutes = int(parts[-2]) if len(parts) >= 2 else 0
        hours = int(parts[-3]) if len(parts) >= 3 else 0
    except ValueError:
        return None
    return int(round((hours * 3600 + minutes * 60 + seconds) * 1000))


def _looks_like_speaker_label(value: str) -> bool:
    """Avoid treating ordinary prose with colons as speaker-labelled turns."""

    stripped = value.strip()
    if not stripped or len(stripped) > 48:
        return False
    lower = stripped.lower()
    if lower.startswith(("http", "https", "file")):
        return False
    return any(character.isalpha() for character in stripped)
