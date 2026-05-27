"""Spreadsheet transcript importer for XLSX and ODS."""

from __future__ import annotations

import uuid
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from imbizo.app.errors import ImportFailure
from imbizo.domain.transcripts import SegmentLevel, SourceFormat, TranscriptDocument, TranscriptSegment, split_tokens_preserving_offsets
from imbizo.importers.base import ImportedBundle, ImportOptions


def _to_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


class SpreadsheetImporter:
    """Import XLSX and ODS spreadsheet transcripts."""

    name = "spreadsheet"

    def can_import(self, path: Path) -> bool:
        """Return whether this importer can parse a copied local file."""

        return path.suffix.lower() in {".xlsx", ".ods"}

    def import_file(self, path: Path, options: ImportOptions) -> ImportedBundle:
        """Parse spreadsheet rows into segments and tokens."""

        rows = self._read_xlsx(path) if path.suffix.lower() == ".xlsx" else self._read_ods(path)
        document = TranscriptDocument(
            id=str(uuid.uuid4()),
            name=path.stem,
            source_format=SourceFormat.XLSX if path.suffix.lower() == ".xlsx" else SourceFormat.ODS,
            media_asset_id=options.linked_media_asset_id,
            relative_path=str(path),
            original_filename=path.name,
        )
        segments: list[TranscriptSegment] = []
        tokens = []
        for order, row in enumerate(rows, start=1):
            text = str(row.get("text") or row.get("transcript") or row.get("utterance") or "").strip()
            if not text:
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
                external_ref=str(row.get("id") or ""),
            )
            segments.append(segment)
            tokens.extend(split_tokens_preserving_offsets(segment.id, text))
        return ImportedBundle(document=document, segments=segments, tokens=tokens, report={"segments": len(segments), "tokens": len(tokens)})

    def _read_xlsx(self, path: Path) -> list[dict[str, object]]:
        try:
            from openpyxl import load_workbook
        except ImportError as exc:
            raise ImportFailure("XLSX import requires the optional openpyxl package.") from exc
        workbook = load_workbook(path, read_only=True, data_only=True)
        sheet = workbook.active
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [str(value or "").strip().lower() for value in rows[0]]
        return [dict(zip(headers, row, strict=False)) for row in rows[1:]]

    def _read_ods(self, path: Path) -> list[dict[str, object]]:
        with zipfile.ZipFile(path) as archive:
            content = archive.read("content.xml")
        root = ET.fromstring(content)
        ns = {
            "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
            "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
        }
        table = root.find(".//table:table", ns)
        if table is None:
            return []
        matrix: list[list[str]] = []
        for row in table.findall("table:table-row", ns):
            values: list[str] = []
            for cell in row.findall("table:table-cell", ns):
                repeat = int(cell.attrib.get("{urn:oasis:names:tc:opendocument:xmlns:table:1.0}number-columns-repeated", "1"))
                text_parts = [node.text or "" for node in cell.findall(".//text:p", ns)]
                value = "\n".join(text_parts)
                values.extend([value] * repeat)
            if any(value for value in values):
                matrix.append(values)
        if not matrix:
            return []
        headers = [value.strip().lower() for value in matrix[0]]
        return [dict(zip(headers, row, strict=False)) for row in matrix[1:]]
