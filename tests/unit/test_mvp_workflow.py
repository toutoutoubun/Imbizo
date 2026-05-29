"""MVP workflow smoke tests."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from imbizo.domain.annotations import AnnotationDraft
from imbizo.domain.project import ProjectMetadata
from imbizo.exporters.base import ExportOptions
from imbizo.services.annotation_service import AnnotationService
from imbizo.services.export_service import ExportRequest, ExportService
from imbizo.services.import_service import ImportService
from imbizo.services.lid_service import LidService
from imbizo.services.metrics_service import MetricsService
from imbizo.services.project_service import ProjectService


def test_local_project_import_annotate_lid_metrics_export(tmp_path: Path) -> None:
    """Run the core MVP workflow without network services."""

    source = tmp_path / "interview.txt"
    source.write_text("I went to the market\nngiyabonga my friend\n", encoding="utf-8")
    context = ProjectService().create_project(tmp_path / "project", ProjectMetadata(project_uuid="", title="Test Project"))

    imported = ImportService().import_file(context, source)
    assert imported.bundle.document is not None

    annotation_service = AnnotationService()
    state = annotation_service.load_editor_state(context, imported.bundle.document.id)
    assert len(state.rows) == 8

    english = next(language for language in state.languages if language.code == "eng")
    annotation = annotation_service.save_token_annotation(
        context,
        state.rows[0].token.id,
        AnnotationDraft(language_id=english.id, memo="checked manually"),
    )
    assert annotation.language_id == english.id

    LidService().run_lid_for_document(context, imported.bundle.document.id)

    metrics_service = MetricsService()
    run = metrics_service.compute_metrics(context)
    results = metrics_service.get_results(context, run.id)
    assert {result.metric_name for result in results} >= {
        "m_index",
        "i_index",
        "burstiness",
        "dominant_language",
        "trigger_cooccurrence",
        "kwic",
    }

    exports = tmp_path / "exports"
    for format_name, suffix in [
        ("csv", "csv"),
        ("json", "json"),
        ("html", "html"),
        ("xlsx", "xlsx"),
        ("textgrid", "TextGrid"),
        ("pdf", "pdf"),
        ("quotation", "md"),
    ]:
        record = ExportService().export(
            context,
            ExportRequest(format_name=format_name, destination=exports / f"annotations.{suffix}", options=ExportOptions()),
        )
        assert Path(record.relative_path).exists()
        citation = Path(record.relative_path).with_name(Path(record.relative_path).name + ".CITATION.cff")
        citation_text = citation.read_text(encoding="utf-8")
        assert "AGPL-3.0-or-later" in citation_text
        assert "10.0000/imbizo-cs-workbench.placeholder" not in citation_text


def test_json_xlsx_and_ods_importers(tmp_path: Path) -> None:
    """Import structured JSON, XLSX, and ODS transcript files."""

    context = ProjectService().create_project(tmp_path / "project", ProjectMetadata(project_uuid="", title="Import Test"))

    json_source = tmp_path / "transcript.json"
    json_source.write_text(json.dumps({"segments": [{"text": "hello sawubona", "start_ms": 0, "end_ms": 900}]}), encoding="utf-8")
    json_result = ImportService().import_file(context, json_source)
    assert json_result.bundle.document is not None
    assert len(json_result.bundle.tokens) == 2

    from openpyxl import Workbook

    xlsx_source = tmp_path / "transcript.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["text", "start_ms", "end_ms"])
    sheet.append(["dumela friend", 1000, 2000])
    workbook.save(xlsx_source)
    xlsx_result = ImportService().import_file(context, xlsx_source)
    assert xlsx_result.bundle.document is not None
    assert len(xlsx_result.bundle.tokens) == 2

    path_header_source = tmp_path / "path_headers.xlsx"
    path_workbook = Workbook()
    path_sheet = path_workbook.active
    path_sheet.title = "balanced_engsot"
    path_sheet.append(["/Corpus", None, None, None])
    path_sheet.append(
        [
            "/SoapOpera/episode/utterance/#id",
            "/SoapOpera/episode/utterance/speaker_id",
            "/SoapOpera/episode/utterance/utterance_segment/lang_id",
            "/SoapOpera/episode/utterance/utterance_segment/transcription",
        ]
    )
    path_sheet.append([1, "AKHONA", "sot", "dumela friend"])
    path_sheet.append([2, "AKHONA", "eng", "hello friend"])
    path_workbook.save(path_header_source)
    path_header_result = ImportService().import_file(context, path_header_source)
    assert path_header_result.bundle.document is not None
    assert len(path_header_result.bundle.segments) == 2
    assert len(path_header_result.bundle.tokens) == 4
    assert path_header_result.bundle.report["imported_language_labels"] == 4
    imported_codes = {
        row["code"]
        for row in context.connection.execute(
            """
            SELECT languages.code FROM annotations
            JOIN languages ON languages.id = annotations.language_id
            WHERE annotations.source = 'imported'
            """
        ).fetchall()
    }
    assert {"eng", "sot"}.issubset(imported_codes)

    document_id = path_header_result.bundle.document.id
    from imbizo.persistence.repositories import TranscriptRepository

    transcript_repo = TranscriptRepository(context.connection)
    transcript_repo.clear_document_content(document_id)
    assert transcript_repo.count_tokens_for_document(document_id) == 0
    repaired = ImportService().repair_empty_document(context, document_id)
    assert repaired is not None
    assert repaired.report["tokens"] == 4
    assert transcript_repo.count_tokens_for_document(document_id) == 4

    ods_source = tmp_path / "transcript.ods"
    content_xml = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">
  <office:body><office:spreadsheet><table:table>
    <table:table-row>
      <table:table-cell><text:p>text</text:p></table:table-cell>
      <table:table-cell><text:p>start_ms</text:p></table:table-cell>
      <table:table-cell><text:p>end_ms</text:p></table:table-cell>
    </table:table-row>
    <table:table-row>
      <table:table-cell><text:p>go well friend</text:p></table:table-cell>
      <table:table-cell><text:p>0</text:p></table:table-cell>
      <table:table-cell><text:p>1000</text:p></table:table-cell>
    </table:table-row>
  </table:table></office:spreadsheet></office:body>
</office:document-content>
"""
    with zipfile.ZipFile(ods_source, "w") as archive:
        archive.writestr("content.xml", content_xml)
    ods_result = ImportService().import_file(context, ods_source)
    assert ods_result.bundle.document is not None
    assert len(ods_result.bundle.tokens) == 3
