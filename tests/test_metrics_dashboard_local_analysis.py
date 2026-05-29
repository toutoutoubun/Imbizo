"""Regression tests for visible local code-switching analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from imbizo.domain.annotations import AnnotationDraft
from imbizo.domain.project import ProjectMetadata
from imbizo.services.annotation_service import AnnotationService
from imbizo.services.import_service import ImportService
from imbizo.services.project_service import ProjectService


def _annotated_project(tmp_path: Path) -> Any:
    context = ProjectService().create_project(tmp_path / "project", ProjectMetadata(project_uuid="", title="CS Analysis"))
    source = tmp_path / "interview.txt"
    source.write_text("hello dumela hello\n", encoding="utf-8")
    imported = ImportService().import_file(context, source)
    assert imported.bundle.document is not None

    service = AnnotationService()
    state = service.load_editor_state(context, imported.bundle.document.id)
    languages = {language.code: language.id for language in state.languages}
    for row, code in zip(state.rows, ("eng", "sot", "eng"), strict=True):
        service.save_token_annotation(context, row.token.id, AnnotationDraft(language_id=languages[code]))
    return context


def test_metrics_dashboard_runs_local_code_switch_analysis(tmp_path: Path) -> None:
    """The dashboard should expose the local NLP analysis path, not just a blank table."""

    from imbizo.gui.widgets.metrics_dashboard import MetricsDashboardWidget

    context = _annotated_project(tmp_path)
    results = MetricsDashboardWidget(context).run_local_analysis()
    values = {result.metric_name: result.value for result in results}

    assert values["switch_count"] == 2
    assert values["switch_density"] > 0
    assert values["m_index"] > 0
    assert values["i_index"] > 0


def test_metrics_dashboard_table_populates_when_qt_available(tmp_path: Path) -> None:
    """Pressing the dashboard analysis action should populate visible metric rows."""

    qt_widgets: Any = pytest.importorskip("PySide6.QtWidgets")

    from imbizo.gui.widgets.metrics_dashboard import MetricsDashboardWidget

    app = qt_widgets.QApplication.instance() or qt_widgets.QApplication([])
    dashboard = MetricsDashboardWidget(_annotated_project(tmp_path))
    widget = dashboard.build()
    results = dashboard.run_local_analysis()

    assert widget is not None
    assert dashboard.metrics_table is not None
    assert dashboard.metrics_table.rowCount() == len(results)
    rendered_metrics = {dashboard.metrics_table.item(row, 0).text() for row in range(dashboard.metrics_table.rowCount())}
    assert "Switch count" in rendered_metrics
    rendered_values = [dashboard.metrics_table.item(row, 2).text() for row in range(dashboard.metrics_table.rowCount())]
    assert any("eng:" in value and "sot:" in value for value in rendered_values)
    assert all("lang-eng" not in value and "lang-sot" not in value for value in rendered_values)
    app.quit()
