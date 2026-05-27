"""Transcript documents, segments, and tokens."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from enum import StrEnum


class SourceFormat(StrEnum):
    """Transcript source formats supported by the MVP."""

    TXT = "txt"
    CSV = "csv"
    TSV = "tsv"
    JSON = "json"
    EAF = "eaf"
    TEXTGRID = "textgrid"
    XLSX = "xlsx"
    ODS = "ods"
    MANUAL = "manual"


class SegmentLevel(StrEnum):
    """Supported transcript segmentation levels for the MVP."""

    UTTERANCE = "utterance"
    CLAUSE_PHRASE = "clause_phrase"


@dataclass(slots=True)
class TranscriptDocument:
    """A transcript source or manually created transcript document."""

    id: str
    name: str
    source_format: SourceFormat
    import_batch_id: str | None = None
    media_asset_id: str | None = None
    relative_path: str = ""
    original_filename: str = ""
    notes: str = ""


@dataclass(slots=True)
class TranscriptSegment:
    """A transcript segment at utterance or clause/phrase level."""

    id: str
    transcript_document_id: str
    segment_level: SegmentLevel
    sort_order: int
    text_original: str
    media_asset_id: str | None = None
    parent_segment_id: str | None = None
    speaker_id: str | None = None
    scene_id: str | None = None
    start_ms: int | None = None
    end_ms: int | None = None
    text_normalized: str | None = None
    external_ref: str = ""
    notes: str = ""


@dataclass(slots=True)
class Token:
    """A token belonging to a transcript segment."""

    id: str
    segment_id: str
    sort_order: int
    token_text: str
    normalized_text: str | None = None
    char_start: int | None = None
    char_end: int | None = None
    external_ref: str = ""


def split_tokens_preserving_offsets(segment_id: str, text: str) -> list[Token]:
    """Split text into tokens while preserving character offsets."""

    tokens: list[Token] = []
    for order, match in enumerate(re.finditer(r"\S+", text), start=1):
        tokens.append(
            Token(
                id=str(uuid.uuid4()),
                segment_id=segment_id,
                sort_order=order,
                token_text=match.group(0),
                char_start=match.start(),
                char_end=match.end(),
            )
        )
    return tokens


def segment_duration_ms(segment: TranscriptSegment) -> int | None:
    """Return segment duration when start and end times are available."""

    if segment.start_ms is None or segment.end_ms is None:
        return None
    return max(0, segment.end_ms - segment.start_ms)
