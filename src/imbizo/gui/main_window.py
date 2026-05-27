"""Main PySide6 window."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from imbizo.services.annotation_service import AnnotationService
from imbizo.services.lid_service import LidService
from imbizo.services.project_service import ProjectService


class MainWindow:
    """Top-level Imbizo-CS Workbench window wrapper."""

    def __init__(self) -> None:
        self.context = None
        self.qt_window = None
        self.project_service = ProjectService()

    def build(self) -> Any:
        """Build and return the PySide6 main window."""

        try:
            from PySide6.QtWidgets import QMainWindow, QTabWidget
        except ImportError as exc:
            raise RuntimeError("PySide6 is required to show the graphical interface.") from exc

        window = QMainWindow()
        window.setWindowTitle("Imbizo-CS Workbench")
        tabs = QTabWidget()
        window.setCentralWidget(tabs)
        self.qt_window = window
        self.tabs = tabs
        return window

    def open_project(self, project_root: Path) -> None:
        """Open and display a local project."""

        if self.qt_window is None:
            self.build()
        self.context = self.project_service.open_project(project_root)
        from imbizo.gui.widgets.annotation_editor import AnnotationEditorWidget
        from imbizo.gui.widgets.metrics_dashboard import MetricsDashboardWidget
        from imbizo.gui.widgets.project_settings import ProjectSettingsWidget
        from imbizo.gui.widgets.spreadsheet_view import SpreadsheetViewWidget
        from imbizo.gui.widgets.timeline_view import TimelineViewWidget

        editor = AnnotationEditorWidget(self.context, AnnotationService(), LidService())
        self.tabs.clear()
        self.tabs.addTab(editor.build(), "Annotation")
        self.tabs.addTab(SpreadsheetViewWidget().build(), "Spreadsheet")
        self.tabs.addTab(TimelineViewWidget().build(), "Timeline")
        self.tabs.addTab(MetricsDashboardWidget().build(), "Metrics")
        self.tabs.addTab(ProjectSettingsWidget().build(), "Project Settings")

    def close_project(self) -> None:
        """Close the current project view."""

        if self.context:
            self.project_service.close_project(self.context)
            self.context = None
