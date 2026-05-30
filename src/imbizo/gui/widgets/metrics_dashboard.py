"""Metrics dashboard widget with local visualisation exports."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
import os
from pathlib import Path
from typing import Any

from imbizo import __version__
from imbizo.core.visualisation.heatmap import render_speaker_scene_heatmap
from imbizo.core.visualisation.sankey import render_language_transition_sankey
from imbizo.persistence.repositories import LanguageRepository
from imbizo.services.lid_accuracy_service import LidAccuracyRow, LidAccuracyService
from imbizo.services.metrics_service import MetricsService
from imbizo.services.nlp_analysis_service import NlpAnalysisOptions, NlpAnalysisService


class MetricsDashboardWidget:
    """Metric request and result display for local code-switching analysis."""

    def __init__(
        self,
        project: Any | None = None,
        metrics_service: MetricsService | None = None,
        nlp_analysis_service: NlpAnalysisService | None = None,
        lid_accuracy_service: LidAccuracyService | None = None,
    ) -> None:
        self.project = project
        self.metrics_service = metrics_service or MetricsService()
        self.nlp_analysis_service = nlp_analysis_service or NlpAnalysisService(metrics_service=self.metrics_service)
        self.lid_accuracy_service = lid_accuracy_service or LidAccuracyService()
        self.tabs = None
        self.metrics_table = None
        self.lid_accuracy_table = None
        self.lid_accuracy_summary_label = None
        self.summary_label = None
        self._active_progress_dialog = None

    def build(self) -> Any:
        """Build and return a PySide6 widget."""

        from PySide6.QtWidgets import QLabel, QHeaderView, QPushButton, QTableWidget, QTabWidget, QVBoxLayout, QWidget

        self.tabs = QTabWidget()
        metrics_page = QWidget()
        layout = QVBoxLayout(metrics_page)
        self.summary_label = QLabel(
            "Local analysis uses manual/imported language labels first, then advisory Local LID labels when available."
        )
        self.summary_label.setWordWrap(True)
        run_button = QPushButton("Run full local NLP analysis")
        run_button.clicked.connect(self.run_local_analysis)
        self.metrics_table = QTableWidget(0, 4)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Scope", "Value", "Inputs"])
        self.metrics_table.setWordWrap(True)
        header = self.metrics_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.summary_label)
        layout.addWidget(run_button)
        layout.addWidget(self.metrics_table)
        self.tabs.addTab(metrics_page, "Metrics")
        self.tabs.addTab(self.build_speaker_scene_profile_tab(), "Speaker & Scene Profile")
        self.tabs.addTab(self.build_lid_accuracy_tab(), "LID Accuracy")
        return self.tabs

    def run_local_analysis(self) -> list[Any]:
        """Run the local NLP pipeline and render code-switching metrics.

        This is the visible end-to-end analysis path: Local LID, advisory
        switch profiling, noun-class hinting, trigger-candidate detection, and
        transparent metrics all run on the researcher's machine. Manual labels
        remain authoritative and automatic labels remain overridable.
        """

        project = self._require_project()
        if not hasattr(project, "connection"):
            raise RuntimeError("Local code-switching analysis requires an opened Imbizo project.")
        progress = self._progress_callback("Running full local NLP analysis")
        try:
            report = self.nlp_analysis_service.run(
                project,
                NlpAnalysisOptions(run_mixed_code=False),
                progress_callback=progress,
            )
        finally:
            self._close_progress_dialog()
        if not report.metrics_run_id:
            return []
        results = self.metrics_service.get_results(project, report.metrics_run_id)
        self._render_metric_results(results)
        if self.summary_label is not None:
            stage_labels = ", ".join(f"{stage.name}:{stage.status}" for stage in report.stages)
            self.summary_label.setText(
                f"Completed local NLP analysis from {max((result.input_count for result in results), default=0):,} token rows. "
                f"Report: {Path(report.report_path).name}. Stages: {stage_labels}."
            )
        self.refresh_lid_accuracy()
        return results

    def _render_metric_results(self, results: list[Any]) -> None:
        """Render metric results in the dashboard table."""

        if self.metrics_table is None:
            return
        language_labels = self._language_labels()
        self.metrics_table.setRowCount(len(results))
        for row_index, result in enumerate(results):
            self.metrics_table.setItem(row_index, 0, self._item(_metric_label(result.metric_name)))
            self.metrics_table.setItem(row_index, 1, self._item(result.scope_type))
            self.metrics_table.setItem(
                row_index,
                2,
                self._item(
                    _format_metric_value(result.metric_name, result.value, language_labels),
                    tooltip=_format_raw_value(result.value),
                ),
            )
            self.metrics_table.setItem(row_index, 3, self._item(f"{result.input_count:,}"))
        self.metrics_table.resizeRowsToContents()
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

    def build_lid_accuracy_tab(self) -> Any:
        """Build a reviewed Local LID accuracy table."""

        from PySide6.QtWidgets import QLabel, QPushButton, QHeaderView, QTableWidget, QVBoxLayout, QWidget

        root = QWidget()
        layout = QVBoxLayout(root)
        self.lid_accuracy_summary_label = QLabel(
            "Reviewed accuracy compares active auto labels with manual/imported labels. No manual/imported labels means no accuracy claim."
        )
        self.lid_accuracy_summary_label.setWordWrap(True)
        refresh_button = QPushButton("Refresh LID accuracy")
        refresh_button.clicked.connect(self.refresh_lid_accuracy)
        self.lid_accuracy_table = QTableWidget(0, 8)
        self.lid_accuracy_table.setHorizontalHeaderLabels(
            ["Scope", "Language", "Reviewed", "Auto labelled", "Correct", "Accuracy", "Missing", "Wrong"]
        )
        header = self.lid_accuracy_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for section in range(2, 8):
            header.setSectionResizeMode(section, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.lid_accuracy_summary_label)
        layout.addWidget(refresh_button)
        layout.addWidget(self.lid_accuracy_table)
        return root

    def refresh_lid_accuracy(self) -> list[LidAccuracyRow]:
        """Refresh the reviewed Local LID accuracy table."""

        project = self._require_project()
        if not hasattr(project, "connection"):
            if self.lid_accuracy_summary_label is not None:
                self.lid_accuracy_summary_label.setText("Open an Imbizo project to compute reviewed LID accuracy.")
            return []
        rows = self.lid_accuracy_service.compute(project)
        self._render_lid_accuracy(rows)
        return rows

    def _render_lid_accuracy(self, rows: list[LidAccuracyRow]) -> None:
        """Render reviewed Local LID accuracy rows."""

        if self.lid_accuracy_table is None:
            return
        self.lid_accuracy_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self.lid_accuracy_table.setItem(row_index, 0, self._item(row.scope))
            self.lid_accuracy_table.setItem(row_index, 1, self._item(f"{row.language_code} - {row.language_name}", tooltip=row.basis))
            self.lid_accuracy_table.setItem(row_index, 2, self._item(f"{row.reviewed_count:,}"))
            self.lid_accuracy_table.setItem(row_index, 3, self._item(f"{row.auto_labelled_count:,}"))
            self.lid_accuracy_table.setItem(row_index, 4, self._item(f"{row.correct_count:,}"))
            self.lid_accuracy_table.setItem(row_index, 5, self._item(_format_accuracy(row.accuracy)))
            self.lid_accuracy_table.setItem(row_index, 6, self._item(f"{row.missing_count:,}"))
            self.lid_accuracy_table.setItem(row_index, 7, self._item(f"{row.incorrect_count:,}"))
        self.lid_accuracy_table.resizeRowsToContents()
        if self.lid_accuracy_summary_label is not None:
            if rows:
                reviewed = sum(row.reviewed_count for row in rows if row.scope == "token")
                correct = sum(row.correct_count for row in rows if row.scope == "token")
                self.lid_accuracy_summary_label.setText(
                    f"Token LID reviewed accuracy: {_format_accuracy(correct / reviewed if reviewed else None)} "
                    f"({correct:,}/{reviewed:,}). Manual/imported labels are treated as review evidence."
                )
            else:
                self.lid_accuracy_summary_label.setText(
                    "No reviewed manual/imported token or span labels are available yet, so Imbizo-CS cannot estimate LID accuracy."
                )

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

    def _language_labels(self) -> dict[str, str]:
        """Return language IDs mapped to compact display codes."""

        project = self._require_project()
        if not hasattr(project, "connection"):
            return {}
        try:
            languages = LanguageRepository(project.connection).list_languages()
        except Exception:
            return {}
        labels: dict[str, str] = {}
        for language in languages:
            labels[language.id] = language.code
            labels[language.code] = language.code
        return labels

    def _progress_callback(self, title: str) -> Any:
        """Return a GUI progress callback when Qt is active, otherwise None."""

        if os.environ.get("PYTEST_CURRENT_TEST"):
            return None
        try:
            from PySide6.QtCore import Qt
            from PySide6.QtWidgets import QApplication, QProgressDialog
        except Exception:
            return None
        app = QApplication.instance()
        if app is None or self.tabs is None:
            return None
        dialog = QProgressDialog(self.tabs)
        self._active_progress_dialog = dialog
        dialog.setWindowTitle(title)
        dialog.setLabelText("Preparing local NLP analysis")
        dialog.setRange(0, 100)
        dialog.setValue(0)
        dialog.setCancelButton(None)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.setMinimumDuration(0)
        dialog.show()
        QApplication.processEvents()

        def update(message: str, current: int, total: int) -> None:
            dialog.setLabelText(message)
            dialog.setMaximum(max(total, 1))
            dialog.setValue(max(0, min(current, total)))
            QApplication.processEvents()
            if current >= total:
                dialog.close()

        return update

    def _close_progress_dialog(self) -> None:
        """Close the local analysis progress dialog if one is open."""

        dialog = self._active_progress_dialog
        if dialog is not None:
            dialog.close()
            self._active_progress_dialog = None

    def _item(self, text: str, tooltip: str | None = None) -> Any:
        from PySide6.QtWidgets import QTableWidgetItem

        item = QTableWidgetItem(text)
        if tooltip:
            item.setToolTip(tooltip)
        return item


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


def _format_metric_value(metric_name: str, value: Any, language_labels: dict[str, str]) -> str:
    """Format one metric for researchers instead of exposing raw storage JSON."""

    if isinstance(value, float):
        return f"{value:.4f}"
    if metric_name == "language_proportion" and isinstance(value, dict):
        parts = [
            f"{_language_label(language_id, language_labels)}: {float(proportion) * 100:.2f}%"
            for language_id, proportion in sorted(value.items(), key=lambda item: str(item[0]))
        ]
        return "; ".join(parts) if parts else "No labelled tokens"
    if metric_name == "dominant_language" and isinstance(value, dict):
        counts = Counter(_language_label(language_id, language_labels) for language_id in value.values())
        parts = [f"{language}: {count:,} segments" for language, count in sorted(counts.items())]
        return "; ".join(parts) if parts else "No dominant-language evidence"
    if metric_name == "trigger_cooccurrence" and value == {}:
        return "No trigger co-occurrences in current labels"
    if metric_name == "kwic" and value == []:
        return "No KWIC pattern supplied"
    if metric_name == "switch_count" and isinstance(value, int):
        return f"{value:,}"
    if metric_name == "switch_density" and isinstance(value, (float, int)):
        return f"{float(value):.4f} per 100 tokens"
    if metric_name in {"m_index", "i_index", "burstiness"} and isinstance(value, (float, int)):
        return f"{float(value):.4f}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _format_raw_value(value: Any) -> str:
    """Return the exact stored metric value for tooltips and audit checks."""

    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
    return str(value)


def _format_accuracy(value: float | None) -> str:
    """Format a reviewed accuracy ratio."""

    if value is None:
        return "n/a"
    return f"{value * 100:.2f}%"


def _language_label(raw_id: object, language_labels: dict[str, str]) -> str:
    """Convert internal language IDs such as `lang-sot` into compact codes."""

    raw = str(raw_id)
    if raw in language_labels:
        return language_labels[raw]
    if raw.startswith("lang-") and len(raw) > 5:
        return raw[5:]
    return raw
