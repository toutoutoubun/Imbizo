"""Tests for the full local NLP analysis pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from click.testing import CliRunner

from imbizo.cli import cli
from imbizo.domain.annotations import AnnotationDraft
from imbizo.domain.project import ProjectMetadata
from imbizo.services.annotation_service import AnnotationService
from imbizo.services.import_service import ImportService
from imbizo.services.nlp_analysis_service import NlpAnalysisOptions, NlpAnalysisService
from imbizo.services.project_service import ProjectService


def _project_with_code_switching(tmp_path: Path) -> tuple[Any, str]:
    context = ProjectService().create_project(tmp_path / "project", ProjectMetadata(project_uuid="", title="Local NLP"))
    source = tmp_path / "interview.txt"
    source.write_text("Johannesburg ngiyabonga friend\nheita kasi dladla\n", encoding="utf-8")
    imported = ImportService().import_file(context, source)
    assert imported.bundle.document is not None

    state = AnnotationService().load_editor_state(context, imported.bundle.document.id)
    languages = {language.code: language.id for language in state.languages}
    labels = ["eng", "zul", "eng", "zul", "zul", "zul"]
    for row, code in zip(state.rows, labels, strict=True):
        AnnotationService().save_token_annotation(context, row.token.id, AnnotationDraft(language_id=languages[code]))
    return context, imported.bundle.document.id


def test_local_nlp_pipeline_records_report_metrics_and_provenance(tmp_path: Path) -> None:
    """One button should now run a concrete local NLP analysis workflow."""

    context, document_id = _project_with_code_switching(tmp_path)
    updates: list[tuple[str, int, int]] = []
    report = NlpAnalysisService().run(
        context,
        NlpAnalysisOptions(document_id=document_id, run_lid=False, run_mixed_code=True),
        progress_callback=lambda message, current, total: updates.append((message, current, total)),
    )

    assert report.metrics_run_id is not None
    assert Path(report.report_path).exists()
    assert updates[-1][0] == "Local NLP analysis complete"

    stage_counts = {stage.name: stage.counts for stage in report.stages}
    assert stage_counts["switch_profile"]["switch_count"] >= 2
    assert stage_counts["noun_class_hints"]["tokens_checked"] >= 1
    assert "trigger_candidates" in stage_counts
    assert "mixed_code_candidates" in stage_counts

    data = json.loads(Path(report.report_path).read_text(encoding="utf-8"))
    assert data["metrics_run_id"] == report.metrics_run_id
    provenance = context.connection.execute(
        "SELECT * FROM provenance_records WHERE event_type = 'local_nlp_analysis'"
    ).fetchone()
    assert provenance is not None


def test_cli_analyze_runs_without_network_or_gui(tmp_path: Path) -> None:
    """The same pipeline must be available for headless reproducible analysis."""

    context, _document_id = _project_with_code_switching(tmp_path)
    project_root = context.paths.root
    context.connection.close()

    result = CliRunner().invoke(cli, ["analyze", "--project", str(project_root), "--skip-lid", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["metrics_run_id"]
    assert any(stage["name"] == "metrics" for stage in payload["stages"])
