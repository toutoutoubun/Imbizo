"""Progress dialog helpers for opening local projects."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from imbizo.domain.project import ProjectContext
from imbizo.services.project_service import ProjectOpenProgress, ProjectService


def open_project_with_progress(
    parent: Any,
    project_service: ProjectService,
    project_root: Path,
    title: str = "Opening project",
) -> ProjectContext:
    """Open a local project while showing a modal progress dialog.

    Opening remains fully local and offline. Cancellation is intentionally not
    shown because the database connection and migration checks need a stable
    transaction boundary; the progress dialog makes slow project opens legible
    without pretending they can be safely interrupted mid-open.
    """

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QProgressDialog

    dialog = QProgressDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setLabelText("Checking project folder")
    dialog.setRange(0, 100)
    dialog.setValue(0)
    dialog.setCancelButton(None)
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.setMinimumDuration(0)
    dialog.show()
    QApplication.processEvents()

    def update(progress: ProjectOpenProgress) -> None:
        dialog.setLabelText(progress.message)
        dialog.setValue(max(0, min(progress.current, progress.total)))
        QApplication.processEvents()

    try:
        return project_service.open_project(project_root, progress_callback=update)
    finally:
        dialog.setValue(100)
        dialog.close()
        QApplication.processEvents()
