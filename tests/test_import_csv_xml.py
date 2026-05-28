"""Regression tests for CSV and generic XML imports."""

from __future__ import annotations

from pathlib import Path

from imbizo.importers.base import ImportOptions
from imbizo.importers.csv_importer import CsvTranscriptImporter
from imbizo.importers.xml_importer import XmlTranscriptImporter
from imbizo.services.import_service import ImportService


def test_csv_importer_accepts_excel_bom_and_semicolon_csv(tmp_path: Path) -> None:
    """Excel-exported CSV may include a UTF-8 BOM and semicolon delimiter."""

    source = tmp_path / "interview.csv"
    source.write_text("\ufeffspeaker;発話;start;end\nA;Sawubona friend;0;1200\n", encoding="utf-8")

    result = CsvTranscriptImporter().import_file(source, ImportOptions())

    assert len(result.segments) == 1
    assert result.segments[0].text_original == "Sawubona friend"
    assert result.segments[0].start_ms == 0
    assert result.report["delimiter"] == ";"


def test_csv_importer_accepts_cp932_japanese_headers(tmp_path: Path) -> None:
    """Japanese Excel CSV files often arrive as CP932 rather than UTF-8."""

    source = tmp_path / "interview.csv"
    source.write_bytes("番号,話者,発話内容\n1,A,ngiyabonga my friend\n".encode("cp932"))

    result = CsvTranscriptImporter().import_file(source, ImportOptions())

    assert len(result.segments) == 1
    assert result.segments[0].text_original == "ngiyabonga my friend"
    assert result.report["encoding"] == "cp932"


def test_xml_importer_accepts_simple_transcript_xml(tmp_path: Path) -> None:
    """Generic XML should not require Excel conversion for simple transcripts."""

    source = tmp_path / "interview.xml"
    source.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<transcript>
  <utterance id="u1" start="0" end="900">
    <text>Sawubona my friend</text>
  </utterance>
  <utterance id="u2" start_ms="1000" end_ms="1800" text="Ngiyabonga" />
</transcript>
""",
        encoding="utf-8",
    )

    result = XmlTranscriptImporter().import_file(source, ImportOptions())

    assert len(result.segments) == 2
    assert result.segments[0].text_original == "Sawubona my friend"
    assert result.segments[0].external_ref == "u1"
    assert result.segments[1].text_original == "Ngiyabonga"


def test_import_service_lists_xml_importer() -> None:
    """The service-level importer registry should include generic XML."""

    assert "xml" in ImportService().list_supported_formats()
