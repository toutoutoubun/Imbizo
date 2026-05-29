"""Metrics dashboard widget with local visualisation exports."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from imbizo import __version__
from imbizo.core.visualisation.heatmap import render_speaker_scene_heatmap
from imbizo.core.visualisation.sankey import render_language_transition_sankey
from imbizo.services.metrics_service import MetricsRequest, MetricsService


class MetricsDashboardWidget:
    """Metric request and result display for local code-switching analysis."""

    def __init__(self, project: Any | None = None, metrics_service: MetricsService | None = None) -> None:
        self.project = project
        self.metrics_service = metrics_service or MetricsService()
        self.tabs = None
        self.metrics_table = None
        self.summary_label = None

    def build(self) -> Any:
        """Build and return a PySide6 widget."""

        from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget, QTabWidget, QVBoxLayout, QWidget

        self.tabs = QTabWidget()
        metrics_page = QWidget()
        layout = QVBoxLayout(metrics_page)
        self.summary_label = QLabel(
            "Local analysis uses manual/imported language labels first, then advisory Local LID labels when available."
        )
        self.summary_label.setWordWrap(True)
        run_button = QPushButton("Run local code-switching analysis")
        run_button.clicked.connect(self.run_local_analysis)
        self.metrics_table = QTableWidget(0, 4)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Scope", "Value", "Inputs"])
        layout.addWidget(self.summary_label)
        layout.addWidget(run_button)
        layout.addWidget(self.metrics_table)
        self.tabs.addTab(metrics_page, "Metrics")
        self.tabs.addTab(self.build_speaker_scene_profile_tab(), "Speaker & Scene Profile")
        return self.tabs

    def run_local_analysis(self) -> list[Any]:
        """Compute local code-switching metrics and render them in the table.

        This is the visible end-to-end NLP analysis path: imported/manual/auto
        token language labels are treated as advisory evidence, adjacent
        language changes become switch points, and transparent code-switching
        indices are persisted in the project database.
        """

        project = self._require_project()
        if not hasattr(project, "connection"):
            raise RuntimeError("Local code-switching analysis requires an opened Imbizo project.")
        run = self.metrics_service.compute_metrics(project, MetricsRequest())
        results = self.metrics_service.get_results(project, run.id)
        self._render_metric_results(results)
        return results

    def _render_metric_results(self, results: list[Any]) -> None:
        """Render metric results in the dashboard table."""

        if self.metrics_table is None:
            return
        self.metrics_table.setRowCount(len(results))
        for row_index, result in enumerate(results):
            self.metrics_table.setItem(row_index, 0, self._item(_metric_label(result.metric_name)))
            self.metrics_table.setItem(row_index, 1, self._item(result.scope_type))
            self.metrics_table.setItem(row_index, 2, self._item(_format_value(result.value)))
            self.metrics_table.setItem(row_index, 3, self._item(str(result.input_count)))
        self.metrics_table.resizeColumnsToContents()
        if self.summary_label is not None:
            annotated_inputs = max((result.input_count for result in results), default=0)
            self.summary_label.setText(
                f"Computed {len(results)} local code-switching metrics from {annotated_inputs:,} token rows. "
                "Automatic labels remain advisory and can be overridden."
            )

    def build_speaker_scene_profile_tab(self) -> Any:
        """Build the visualisation tab with export and caption actions."""

        from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.addWidget(QLabel("Speaker × scene heatmap and language-transition Sankey render locally with matplotlib."))
        heatmap_button = QPushButton("Export heatmap")
        sankey_button = QPushButton("Export Sankey")
        caption_button = QPushButton("Copy as figure caption")
        self.caption_box = QTextEdit()
        self.caption_box.setReadOnly(True)
        heatmap_button.clicked.connect(lambda: self.export_heatmap("png"))
        sankey_button.clicked.connect(lambda: self.export_sankey("svg"))
        caption_button.clicked.connect(self.copy_figure_caption)
        layout.addWidget(heatmap_button)
        layout.addWidget(sankey_button)
        layout.addWidget(caption_button)
        layout.addWidget(self.caption_box)
        return root

    def export_heatmap(self, format: str = "png") -> Path:
        """Render the speaker-scene heatmap into the project exports folder."""

        project = self._require_project()
        path = self._exports_dir() / f"speaker_scene_heatmap.{format}"
        result = render_speaker_scene_heatmap(project, path, format=format)  # type: ignore[arg-type]
        return result if isinstance(result, Path) else result[0]

    def export_sankey(self, format: str = "svg") -> Path:
        """Render the language-transition Sankey into the project exports folder."""

        project = self._require_project()
        result = render_language_transition_sankey(project, self._exports_dir() / f"language_transition_sankey.{format}", format=format)  # type: ignore[arg-type]
        return result if isinstance(result, Path) else result[0]

    def copy_figure_caption(self) -> str:
        """Generate and display a citation-ready figure caption."""

        project = self._require_project()
        title = getattr(project, "title", None) or getattr(getattr(project, "metadata", None), "title", "Imbizo-CS project")
        caption = (
            f"Figure. Speaker and scene code-switching profile for {title}, generated "
            f"{datetime.now(UTC).date().isoformat()} with Imbizo-CS {__version__}. "
            "Language palette and figure rendering follow PRINCIPLES.md commitments to offline reproducibility and accessibility."
        )
        if getattr(self, "caption_box", None) is not None:
            self.caption_box.setPlainText(caption)
        return caption

    def _exports_dir(self) -> Path:
        project = self._require_project()
        if getattr(project, "project_path", None):
            path = Path(str(project.project_path)) / "exports" / "figures"
        elif hasattr(project, "paths"):
            path = project.paths.exports / "figures"
        else:
            path = Path("exports") / "figures"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _require_project(self) -> Any:
        if self.project is None:
            raise RuntimeError("A project must be loaded before exporting dashboard figures.")
        return self.project

    def _item(self, text: str) -> Any:
        from PySide6.QtWidgets import QTableWidgetItem

        return QTableWidgetItem(text)


def _metric_label(metric_name: str) -> str:
    """Return a readable label for one metric key."""

    return {
        "language_proportion": "Language proportions",
        "switch_count": "Switch count",
        "switch_density": "Switch density per 100 tokens",
        "dominant_language": "Dominant language by segment",
        "m_index": "M-index",
        "i_index": "I-index",
        "burstiness": "Switch burstiness",
        "trigger_cooccurrence": "Trigger co-occurrence",
        "kwic": "KWIC rows",
    }.get(metric_name, metric_name)


def _format_value(value: Any) -> str:
    """Format metric values without hiding their structure."""

    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)
