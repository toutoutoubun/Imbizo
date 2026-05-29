"""Progress dialog helpers for local language identification."""

from __future__ import annotations

from typing import Any

from imbizo.domain.project import ProjectContext
from imbizo.lid.providers import LidOptions, LidProgress
from imbizo.services.lid_service import LidRunReport, LidService


def run_lid_with_progress(
    parent: Any,
    context: ProjectContext,
    document_id: str,
    lid_service: LidService,
    title: str = "Running Local LID",
) -> LidRunReport:
    """Run local LID while showing a modal progress dialog.

    The detector and all suggestions remain local. The dialog exists because
    larger transcripts can take long enough that macOS reports the application
    as unresponsive if the event loop is never allowed to repaint.
    """

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QProgressDialog

    dialog = QProgressDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setLabelText("Preparing local language identification")
    dialog.setRange(0, 100)
    dialog.setValue(0)
    dialog.setCancelButton(None)
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.setMinimumDuration(0)
    dialog.show()
    QApplication.processEvents()

    def update(progress: LidProgress) -> None:
        dialog.setLabelText(progress.message)
        dialog.setValue(max(0, min(progress.current, progress.total)))
        QApplication.processEvents()

    try:
        return lid_service.run_lid_for_document_report(context, document_id, LidOptions(progress_callback=update))
    finally:
        dialog.setValue(100)
        dialog.close()
        QApplication.processEvents()
