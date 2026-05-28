from pathlib import Path

import pytest

from imbizo.core.annotation import Project, Token
from imbizo.gui.widgets.metrics_dashboard import MetricsDashboardWidget


def _project(tmp_path: Path) -> Project:
    return Project(
        "p",
        "Synthetic",
        [
            Token("t1", "a", "u1", 1, "zul", speaker_id="S1", metadata={"scene": "A", "start_time_ms": 1}),
            Token("t2", "b", "u1", 2, "eng", speaker_id="S1", metadata={"scene": "A", "start_time_ms": 2}),
        ],
        project_path=str(tmp_path),
    )


def test_dashboard_exports_valid_files_without_qt_build(tmp_path: Path) -> None:
    dashboard = MetricsDashboardWidget(_project(tmp_path))
    heatmap = dashboard.export_heatmap("png")
    sankey = dashboard.export_sankey("svg")
    assert heatmap.exists() and heatmap.read_bytes().startswith(b"\x89PNG")
    assert sankey.exists() and "<svg" in sankey.read_text(encoding="utf-8")
    assert "Figure." in dashboard.copy_figure_caption()


def test_dashboard_widget_builds_when_pyside_available(tmp_path: Path) -> None:
    pytest.importorskip("PySide6")
    widget = MetricsDashboardWidget(_project(tmp_path)).build()
    assert widget is not None
