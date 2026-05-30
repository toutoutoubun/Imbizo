"""Regression tests for CSV and generic XML imports."""

from __future__ import annotations

from pathlib import Path

import pytest

from imbizo.app.errors import ImportFailure
from imbizo.domain.project import ProjectMetadata
from imbizo.importers.base import ImportOptions, ImportProgress
from imbizo.importers.csv_importer import CsvTranscriptImporter
from imbizo.importers.txt import TxtImporter
from imbizo.services.annotation_service import AnnotationService
from imbizo.importers.xml_importer import XmlTranscriptImporter
from imbizo.services.import_service import ImportService
from imbizo.services.project_service import ProjectService


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


def test_txt_importer_accepts_cp932_and_reports_progress(tmp_path: Path) -> None:
    """Single TXT files should import safely even when exported with CP932."""

    source = tmp_path / "interview.txt"
    source.write_bytes("Sawubona friend\n発話内容\n".encode("cp932"))
    events: list[ImportProgress] = []

    result = TxtImporter().import_file(source, ImportOptions(progress_callback=events.append))

    assert [segment.text_original for segment in result.segments] == ["Sawubona friend", "発話内容"]
    assert result.report["encoding"] == "cp932"
    assert events
    assert events[-1].current >= 80


def test_txt_importer_accepts_plain_text_extensions_and_speaker_lines(tmp_path: Path) -> None:
    """Plain text import should not be spreadsheet-column dependent."""

    source = tmp_path / "fieldnotes.md"
    source.write_text(
        "Speaker A: Dumela friend\n"
        "[00:00:02.500 - 00:00:04.000] Speaker B: Ke teng today\n",
        encoding="utf-8",
    )

    importer = TxtImporter()
    result = importer.import_file(source, ImportOptions())

    assert importer.can_import(source)
    assert [segment.text_original for segment in result.segments] == ["Dumela friend", "Ke teng today"]
    assert [segment.speaker_id for segment in result.segments] == ["Speaker A", "Speaker B"]
    assert result.segments[1].start_ms == 2500
    assert result.segments[1].end_ms == 4000
    assert result.report["plain_text_mode"] is True
    assert result.report["language_labels"] == 0


def test_txt_importer_accepts_srt_without_excel_conversion(tmp_path: Path) -> None:
    """Subtitle-style plain text should become timed utterance segments."""

    source = tmp_path / "captions.srt"
    source.write_text(
        "1\n00:00:01,000 --> 00:00:02,250\nA: Sawubona friend\n\n"
        "2\n00:00:03,000 --> 00:00:04,000\nB: Ngikhona\n",
        encoding="utf-8",
    )

    result = TxtImporter().import_file(source, ImportOptions())

    assert [segment.text_original for segment in result.segments] == ["Sawubona friend", "Ngikhona"]
    assert result.segments[0].speaker_id == "A"
    assert result.segments[0].start_ms == 1000
    assert result.segments[0].end_ms == 2250
    assert result.report["timestamped_lines"] == 2


def test_import_service_imports_single_txt_and_xml_files(tmp_path: Path) -> None:
    """Service-level imports should not crash for one TXT or one XML file."""

    project_root = tmp_path / "project"
    context = ProjectService().create_project(project_root, ProjectMetadata(project_uuid="", title="Import Test"))
    txt = tmp_path / "one.txt"
    txt.write_text("Sawubona friend\n", encoding="utf-8")
    xml = tmp_path / "one.xml"
    xml.write_text("<transcript><utterance><text>Ngiyabonga friend</text></utterance></transcript>", encoding="utf-8")
    events: list[ImportProgress] = []

    txt_result = ImportService().import_file(context, txt, ImportOptions(progress_callback=events.append))
    xml_result = ImportService().import_file(context, xml, ImportOptions(progress_callback=events.append))

    assert txt_result.report["segments"] == 1
    assert xml_result.report["segments"] == 1
    assert [event.stage for event in events][:2] == ["preflight", "copy"]
    assert events[-1].stage == "complete"


def test_import_service_displays_tokens_for_txt_without_language_column(tmp_path: Path) -> None:
    """TXT imports have no language column, but token rows must still load."""

    project_root = tmp_path / "project"
    context = ProjectService().create_project(project_root, ProjectMetadata(project_uuid="", title="Plain Text Test"))
    source = tmp_path / "plain.text"
    source.write_text("ao double-licious no ko tsalanang\n", encoding="utf-8")

    result = ImportService().import_file(context, source)
    document_id = result.bundle.document.id if result.bundle.document else ""
    state = AnnotationService().load_editor_state(context, document_id)

    assert [row.token.token_text for row in state.rows] == ["ao", "double-licious", "no", "ko", "tsalanang"]
    assert all(row.annotation is None for row in state.rows)
    assert result.report["language_labels"] == 0


def test_import_service_reports_progress_while_saving_many_rows(tmp_path: Path) -> None:
    """Large transcript saves should keep emitting progress during SQLite writes."""

    project_root = tmp_path / "project"
    context = ProjectService().create_project(project_root, ProjectMetadata(project_uuid="", title="Large Import Test"))
    txt = tmp_path / "large.txt"
    txt.write_text("\n".join(f"line {index}" for index in range(650)), encoding="utf-8")
    events: list[ImportProgress] = []

    result = ImportService().import_file(context, txt, ImportOptions(progress_callback=events.append))

    save_events = [event for event in events if event.stage == "save"]
    assert result.report["segments"] == 650
    assert len(save_events) >= 3
    assert any("Saved" in event.message for event in save_events)
    assert events[-1].stage == "complete"


def test_xml_importer_reports_parse_error_as_import_failure(tmp_path: Path) -> None:
    """Malformed XML should show a user-facing import failure, not a traceback."""

    source = tmp_path / "broken.xml"
    source.write_text("<transcript><utterance>", encoding="utf-8")

    with pytest.raises(ImportFailure, match="Could not parse XML"):
        XmlTranscriptImporter().import_file(source, ImportOptions())
