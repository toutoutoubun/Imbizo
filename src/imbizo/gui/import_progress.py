"""Progress dialog helpers for local file imports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from imbizo.domain.project import ProjectContext
from imbizo.importers.base import ImportOptions, ImportProgress
from imbizo.services.import_service import ImportResult, ImportService


def import_file_with_progress(
    parent: Any,
    context: ProjectContext,
    source_path: Path,
    import_service: ImportService,
    title: str = "Importing file",
) -> ImportResult:
    """Import a local file while showing a modal progress dialog.

    The import remains fully local and offline. Cancellation is intentionally
    not exposed yet because partial rollback needs a dedicated transaction
    boundary; until then, the progress bar makes long imports legible without
    pretending they are safely cancellable.
    """

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QProgressDialog

    dialog = QProgressDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setLabelText(f"Preparing {source_path.name}")
    dialog.setRange(0, 100)
    dialog.setValue(0)
    dialog.setCancelButton(None)
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.setMinimumDuration(0)
    dialog.show()
    QApplication.processEvents()

    def update(progress: ImportProgress) -> None:
        dialog.setLabelText(progress.message)
        dialog.setValue(max(0, min(progress.current, progress.total)))
        QApplication.processEvents()

    try:
        return import_service.import_file(context, source_path, ImportOptions(progress_callback=update))
    finally:
        dialog.setValue(100)
        dialog.close()
        QApplication.processEvents()
