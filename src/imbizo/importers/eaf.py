"""ELAN EAF importer."""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from imbizo.domain.transcripts import SegmentLevel, SourceFormat, TranscriptDocument, TranscriptSegment, split_tokens_preserving_offsets
from imbizo.importers.base import ImportedBundle, ImportOptions


class EafImporter:
    """Import ELAN EAF annotations as utterance segments."""

    name = "eaf"

    def can_import(self, path: Path) -> bool:
        """Return whether this importer can parse a copied local file."""

        return path.suffix.lower() == ".eaf"

    def import_file(self, path: Path, options: ImportOptions) -> ImportedBundle:
        """Parse alignable EAF annotations into segments and tokens."""

        document = TranscriptDocument(
            id=str(uuid.uuid4()),
            name=path.stem,
            source_format=SourceFormat.EAF,
            media_asset_id=options.linked_media_asset_id,
            relative_path=str(path),
            original_filename=path.name,
        )
        root = ET.parse(path).getroot()
        times: dict[str, int] = {}
        for slot in root.findall(".//TIME_SLOT"):
            slot_id = slot.attrib.get("TIME_SLOT_ID", "")
            value = slot.attrib.get("TIME_VALUE")
            if slot_id and value is not None:
                try:
                    times[slot_id] = int(value)
                except ValueError:
                    continue
        segments: list[TranscriptSegment] = []
        tokens = []
        order = 0
        for annotation in root.findall(".//ALIGNABLE_ANNOTATION"):
            value_node = annotation.find("ANNOTATION_VALUE")
            text = value_node.text if value_node is not None and value_node.text else ""
            if not text.strip():
                continue
            order += 1
            segment = TranscriptSegment(
                id=str(uuid.uuid4()),
                transcript_document_id=document.id,
                media_asset_id=options.linked_media_asset_id,
                segment_level=SegmentLevel.UTTERANCE,
                sort_order=order,
                text_original=text,
                start_ms=times.get(annotation.attrib.get("TIME_SLOT_REF1", "")),
                end_ms=times.get(annotation.attrib.get("TIME_SLOT_REF2", "")),
                external_ref=annotation.attrib.get("ANNOTATION_ID", ""),
            )
            segments.append(segment)
            tokens.extend(split_tokens_preserving_offsets(segment.id, text))
        return ImportedBundle(document=document, segments=segments, tokens=tokens, report={"segments": len(segments), "tokens": len(tokens)})
