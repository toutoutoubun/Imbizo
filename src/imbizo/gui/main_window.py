"""Main PySide6 window."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from imbizo.app.strings import StringCatalog, load_string_catalog
from imbizo.domain.project import ProjectMetadata
from imbizo.gui.import_progress import import_file_with_progress
from imbizo.services.import_service import ImportService
from imbizo.services.annotation_service import AnnotationService
from imbizo.services.lid_service import LidService
from imbizo.services.project_service import ProjectService


class MainWindow:
    """Top-level Imbizo-CS Workbench window wrapper."""

    def __init__(self) -> None:
        self.context = None
        self.qt_window = None
        self.tabs = None
        self.project_service = ProjectService()
        self.import_service = ImportService()
        self.strings = self._load_strings()

    def build(self) -> Any:
        """Build and return the PySide6 main window."""

        try:
            from PySide6.QtWidgets import QMainWindow
        except ImportError as exc:
            raise RuntimeError("PySide6 is required to show the graphical interface.") from exc

        window = QMainWindow()
        window.setWindowTitle(self.strings.text("app.title"))
        window.resize(1100, 760)
        self.qt_window = window
        self._show_welcome()
        return window

    def open_project(self, project_root: Path) -> None:
        """Open and display a local project."""

        if self.qt_window is None:
            self.build()
        try:
            self.context = self.project_service.open_project(project_root)
        except Exception as exc:  # noqa: BLE001 - GUI boundary shows plain-language errors.
            self._show_error(self.strings.text("project.open_failed"), str(exc))
            return
        from imbizo.gui.widgets.annotation_editor import AnnotationEditorWidget
        from imbizo.gui.widgets.metrics_dashboard import MetricsDashboardWidget
        from imbizo.gui.widgets.project_settings import ProjectSettingsWidget
        from imbizo.gui.widgets.spreadsheet_view import SpreadsheetViewWidget
        from imbizo.gui.widgets.timeline_view import TimelineViewWidget
        from PySide6.QtWidgets import QTabWidget

        annotation_service = AnnotationService()
        editor = AnnotationEditorWidget(self.context, annotation_service, LidService())
        spreadsheet = SpreadsheetViewWidget(self.context, annotation_service)
        self.tabs = QTabWidget()
        self.tabs.clear()
        self.tabs.addTab(editor.build(), self.strings.text("tab.annotation"))
        spreadsheet_page = spreadsheet.build()
        self.tabs.addTab(spreadsheet_page, self.strings.text("tab.spreadsheet"))
        self.tabs.addTab(TimelineViewWidget().build(), self.strings.text("tab.timeline"))
        self.tabs.addTab(MetricsDashboardWidget(self.context).build(), self.strings.text("tab.metrics"))
        self.tabs.addTab(ProjectSettingsWidget().build(), self.strings.text("tab.project_settings"))
        def refresh_spreadsheet_tab(index: int) -> None:
            if self.tabs and self.tabs.widget(index) is spreadsheet_page:
                spreadsheet.refresh_documents()
                spreadsheet.refresh()

        self.tabs.currentChanged.connect(refresh_spreadsheet_tab)
        self.qt_window.setCentralWidget(self.tabs)

    def close_project(self) -> None:
        """Close the current project view."""

        if self.context:
            self.project_service.close_project(self.context)
            self.context = None
        self._show_welcome()

    def _show_welcome(self) -> None:
        """Show the no-project landing screen instead of an empty window."""

        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QFrame,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QVBoxLayout,
            QWidget,
        )

        page = QWidget()
        page.setObjectName("welcome-page")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(48, 48, 48, 48)
        outer.setSpacing(24)

        title = QLabel(self.strings.text("welcome.title"))
        title.setObjectName("welcome-title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: 600;")

        subtitle = QLabel(self.strings.text("welcome.subtitle"))
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #5A5754;")

        actions = QFrame()
        actions.setObjectName("welcome-actions")
        action_layout = QHBoxLayout(actions)
        action_layout.setSpacing(12)
        action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        new_button = QPushButton(self.strings.text("project.new"))
        open_button = QPushButton(self.strings.text("project.open"))
        data_button = QPushButton(self.strings.text("project.import_data"))
        import_button = QPushButton(self.strings.text("project.import_zip"))
        for button in (new_button, data_button, open_button, import_button):
            button.setMinimumHeight(36)
            button.setMinimumWidth(160)
            action_layout.addWidget(button)

        new_button.clicked.connect(self._choose_new_project)
        data_button.clicked.connect(self._choose_data_file_for_new_project)
        open_button.clicked.connect(self._choose_existing_project)
        import_button.clicked.connect(self._choose_project_zip)

        folder_note = QLabel(self.strings.text("welcome.project_folder_note"))
        folder_note.setWordWrap(True)
        folder_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        folder_note.setStyleSheet("font-size: 12px; color: #5A5754;")

        offline_note = QLabel(self.strings.text("welcome.offline_note"))
        offline_note.setWordWrap(True)
        offline_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        offline_note.setStyleSheet("font-size: 12px; color: #5A5754;")

        outer.addStretch(1)
        outer.addWidget(title)
        outer.addWidget(subtitle)
        outer.addWidget(actions)
        outer.addWidget(folder_note)
        outer.addWidget(offline_note)
        outer.addStretch(2)

        if self.qt_window is not None:
            self.qt_window.setCentralWidget(page)

    def _choose_existing_project(self) -> None:
        """Ask the researcher for a local project folder and open it."""

        from PySide6.QtWidgets import QFileDialog

        folder = QFileDialog.getExistingDirectory(
            self.qt_window,
            self.strings.text("project.open_dialog_title"),
        )
        if folder:
            self.open_project(Path(folder))

    def _choose_data_file_for_new_project(self) -> None:
        """Create a new project and immediately import a local data file."""

        from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

        source, _ = QFileDialog.getOpenFileName(
            self.qt_window,
            self.strings.text("project.import_data_dialog_title"),
            "",
            self.strings.text("project.import_data_filter"),
        )
        if not source:
            return
        parent_folder = QFileDialog.getExistingDirectory(
            self.qt_window,
            self.strings.text("project.import_data_destination_title"),
        )
        if not parent_folder:
            return
        folder_name, ok = QInputDialog.getText(
            self.qt_window,
            self.strings.text("project.import_data_name_title"),
            self.strings.text("project.import_data_name_label"),
        )
        if not ok:
            return
        folder_name = folder_name.strip() or self.strings.text("project.import_data_default_name")
        project_root = Path(parent_folder) / folder_name
        title, ok = QInputDialog.getText(
            self.qt_window,
            self.strings.text("project.import_data_title_dialog_title"),
            self.strings.text("project.import_data_title_dialog_label"),
        )
        if not ok:
            return
        title = title.strip() or Path(source).stem
        try:
            context = self.project_service.create_project(project_root, ProjectMetadata(project_uuid="", title=title))
            result = import_file_with_progress(
                self.qt_window,
                context,
                Path(source),
                self.import_service,
                self.strings.text("project.import_data_progress_title"),
            )
        except Exception as exc:  # noqa: BLE001 - GUI boundary shows plain-language errors.
            self._show_error(self.strings.text("project.import_data_failed"), str(exc))
            return

        self.open_project(context.paths.root)
        QMessageBox.information(
            self.qt_window,
            self.strings.text("project.import_data_complete_title"),
            self.strings.text(
                "project.import_data_complete_message",
                filename=result.copied_path.name,
                project=str(context.paths.root),
            ),
        )

    def _choose_new_project(self) -> None:
        """Ask for a folder and title, then create a local project."""

        from PySide6.QtWidgets import QFileDialog, QInputDialog

        folder = QFileDialog.getExistingDirectory(
            self.qt_window,
            self.strings.text("project.create_dialog_title"),
        )
        if not folder:
            return
        title, ok = QInputDialog.getText(
            self.qt_window,
            self.strings.text("project.title_dialog_title"),
            self.strings.text("project.title_dialog_label"),
        )
        if not ok:
            return
        title = title.strip() or self.strings.text("project.untitled")
        try:
            context = self.project_service.create_project(Path(folder), ProjectMetadata(project_uuid="", title=title))
        except Exception as exc:  # noqa: BLE001 - GUI boundary shows plain-language errors.
            self._show_error(self.strings.text("project.create_failed"), str(exc))
            return
        self.open_project(context.paths.root)

    def _choose_project_zip(self) -> None:
        """Import a local project ZIP into a researcher-chosen folder."""

        from PySide6.QtWidgets import QFileDialog, QInputDialog

        archive, _ = QFileDialog.getOpenFileName(
            self.qt_window,
            self.strings.text("project.import_dialog_title"),
            "",
            self.strings.text("project.zip_filter"),
        )
        if not archive:
            return
        parent_folder = QFileDialog.getExistingDirectory(
            self.qt_window,
            self.strings.text("project.import_destination_title"),
        )
        if not parent_folder:
            return
        folder_name, ok = QInputDialog.getText(
            self.qt_window,
            self.strings.text("project.import_name_title"),
            self.strings.text("project.import_name_label"),
        )
        if not ok:
            return
        folder_name = folder_name.strip() or self.strings.text("project.import_default_name")
        destination = Path(parent_folder) / folder_name
        try:
            context = self.project_service.import_project_zip(Path(archive), destination)
        except Exception as exc:  # noqa: BLE001 - GUI boundary shows plain-language errors.
            self._show_error(self.strings.text("project.import_failed"), str(exc))
            return
        self.open_project(context.paths.root)

    def _show_error(self, title: str, message: str) -> None:
        """Show a modal error dialog with a plain-language message."""

        from PySide6.QtWidgets import QMessageBox

        QMessageBox.critical(self.qt_window, title, message)

    def _load_strings(self) -> StringCatalog:
        """Load bundled English strings for the desktop shell."""

        resources_dir = Path(__file__).resolve().parents[1] / "resources"
        return load_string_catalog("en", resources_dir)
