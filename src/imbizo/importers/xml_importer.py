"""Generic XML transcript importer.

This importer is intentionally conservative. ELAN `.eaf` files continue to use
the dedicated EAF importer, while generic `.xml` files are treated as local
transcript-like XML when they contain recognisable utterance, segment, row, item,
or annotation elements.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from imbizo.app.errors import ImportFailure
from imbizo.domain.transcripts import SegmentLevel, SourceFormat, TranscriptDocument, TranscriptSegment, split_tokens_preserving_offsets
from imbizo.importers.base import ImportedBundle, ImportOptions, ImportProgress


TEXT_KEYS = ("text", "transcript", "utterance", "content", "value")
START_KEYS = ("start_ms", "start", "begin", "onset", "start_time")
END_KEYS = ("end_ms", "end", "finish", "offset", "end_time")
ID_KEYS = ("id", "xml:id", "segment_id", "utterance_id", "ref")
SEGMENT_TAGS = {
    "annotation",
    "segment",
    "utterance",
    "u",
    "turn",
    "row",
    "item",
    "line",
    "entry",
}


def _emit_progress(options: ImportOptions, stage: str, message: str, current: int, total: int) -> None:
    """Notify a GUI or CLI progress observer when one is attached."""

    if options.progress_callback is not None:
        options.progress_callback(ImportProgress(stage=stage, message=message, current=current, total=total))


class XmlTranscriptImporter:
    """Import simple local XML transcript files as utterance segments."""

    name = "xml"

    def can_import(self, path: Path) -> bool:
        """Return whether this importer can parse a copied local file."""

        return path.suffix.lower() == ".xml"

    def import_file(self, path: Path, options: ImportOptions) -> ImportedBundle:
        """Parse generic XML transcript rows into segments and tokens."""

        _emit_progress(options, "parse", "Parsing XML transcript structure", 40, 100)
        document = TranscriptDocument(
            id=str(uuid.uuid4()),
            name=path.stem,
            source_format=SourceFormat.XML,
            media_asset_id=options.linked_media_asset_id,
            relative_path=str(path),
            original_filename=path.name,
        )
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            raise ImportFailure(f"Could not parse XML file {path.name}: {exc}") from exc
        candidates = _candidate_elements(root)
        if not candidates:
            candidates = [root]

        segments: list[TranscriptSegment] = []
        tokens = []
        total = max(len(candidates), 1)
        for order, element in enumerate(candidates, start=1):
            text = _element_text(element).strip()
            if not text:
                if order == 1 or order == total or order % 200 == 0:
                    _emit_progress(options, "parse", f"Scanned {order:,} of {total:,} XML elements", 45 + int(order / total * 35), 100)
                continue
            segment = TranscriptSegment(
                id=str(uuid.uuid4()),
                transcript_document_id=document.id,
                media_asset_id=options.linked_media_asset_id,
                segment_level=SegmentLevel.UTTERANCE,
                sort_order=order,
                text_original=text,
                start_ms=_to_int(_lookup(element, START_KEYS)),
                end_ms=_to_int(_lookup(element, END_KEYS)),
                external_ref=_lookup(element, ID_KEYS) or "",
            )
            segments.append(segment)
            tokens.extend(split_tokens_preserving_offsets(segment.id, text))
            if order == 1 or order == total or order % 200 == 0:
                _emit_progress(options, "parse", f"Parsed {order:,} of {total:,} XML elements", 45 + int(order / total * 35), 100)

        report: dict[str, object] = {"segments": len(segments), "tokens": len(tokens)}
        if not segments:
            report["warning"] = (
                "No transcript text was found in the XML. Expected segment-like "
                "elements such as utterance, segment, annotation, row, item, or line."
            )
        return ImportedBundle(document=document, segments=segments, tokens=tokens, report=report)


def _candidate_elements(root: ET.Element) -> list[ET.Element]:
    """Return elements whose local names look transcript-like."""

    return [element for element in root.iter() if _local_name(element.tag).lower() in SEGMENT_TAGS]


def _element_text(element: ET.Element) -> str:
    """Extract utterance text from attributes, child fields, or element text."""

    for key in TEXT_KEYS:
        value = _lookup(element, (key,))
        if value:
            return value
    direct_text = (element.text or "").strip()
    if direct_text:
        return direct_text
    parts: list[str] = []
    for child in element:
        if _local_name(child.tag).lower() in TEXT_KEYS and child.text:
            parts.append(child.text.strip())
    if parts:
        return " ".join(part for part in parts if part)
    return " ".join(text.strip() for text in element.itertext() if text.strip())


def _lookup(element: ET.Element, keys: tuple[str, ...]) -> str | None:
    """Find a value in attributes or direct children using local-name matching."""

    normalized = {_local_name(key).lower(): value for key, value in element.attrib.items()}
    for key in keys:
        value = normalized.get(key.lower())
        if value:
            return value
    for child in element:
        if _local_name(child.tag).lower() in keys and child.text:
            return child.text.strip()
    return None


def _local_name(tag: str) -> str:
    """Strip XML namespace syntax from a tag or attribute name."""

    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _to_int(value: str | None) -> int | None:
    """Convert integer-like timestamps to milliseconds."""

    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None
