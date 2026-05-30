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
    options: LidOptions | None = None,
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
        base_options = options or LidOptions()
        run_options = LidOptions(
            max_languages=base_options.max_languages,
            min_confidence=base_options.min_confidence,
            use_optional_afrolid=base_options.use_optional_afrolid,
            use_coarse_group_gate=base_options.use_coarse_group_gate,
            progress_callback=update,
        )
        return lid_service.run_lid_for_document_report(context, document_id, run_options)
    finally:
        dialog.setValue(100)
        dialog.close()
        QApplication.processEvents()
