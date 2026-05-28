"""Metrics dashboard widget with local visualisation exports."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from imbizo import __version__
from imbizo.core.visualisation.heatmap import render_speaker_scene_heatmap
from imbizo.core.visualisation.sankey import render_language_transition_sankey


class MetricsDashboardWidget:
    """Metric request and result display."""

    def __init__(self, project: Any | None = None) -> None:
        self.project = project
        self.tabs = None

    def build(self) -> Any:
        """Build and return a PySide6 widget."""

        from PySide6.QtWidgets import QTabWidget, QTableWidget

        self.tabs = QTabWidget()
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Metric", "Scope", "Value", "Inputs"])
        self.tabs.addTab(table, "Metrics")
        self.tabs.addTab(self.build_speaker_scene_profile_tab(), "Speaker & Scene Profile")
        return self.tabs

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
