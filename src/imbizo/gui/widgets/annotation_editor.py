"""Fully wired annotation editor widget."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from imbizo.domain.annotations import AnnotationDraft
from imbizo.gui.import_progress import import_file_with_progress, repair_empty_document_with_progress
from imbizo.gui.lid_progress import run_lid_with_progress
from imbizo.lid.providers import LidOptions
from imbizo.services.import_service import ImportService

MAX_VISIBLE_TOKEN_ROWS = 1000
LOGGER = logging.getLogger(__name__)


class AnnotationEditorWidget:
    """Main annotation workbench screen.

    The class creates PySide6 widgets lazily so importing the package still
    works in headless/offline build environments where PySide6 is not installed.
    """

    def __init__(self, context: Any, annotation_service: Any, lid_service: Any) -> None:
        self.context = context
        self.annotation_service = annotation_service
        self.lid_service = lid_service
        self.import_service = ImportService()
        self.document_id: str | None = None
        self.widget = None
        self.table = None
        self.status_label = None
        self.import_file_button = None
        self.run_lid_button = None
        self.coarse_group_gate_checkbox = None
        self.languages_by_name: dict[str, str] = {}
        self.language_names_by_id: dict[str, str] = {}
        self._repair_attempted_document_ids: set[str] = set()

    def build(self) -> Any:
        """Build and return the PySide6 widget."""

        try:
            from PySide6.QtWidgets import (
                QComboBox,
                QCheckBox,
                QHBoxLayout,
                QLabel,
                QPushButton,
                QTableWidget,
                QTableWidgetItem,
                QTextEdit,
                QVBoxLayout,
                QWidget,
            )
        except ImportError as exc:
            raise RuntimeError("PySide6 is required to show the graphical annotation editor.") from exc

        root = QWidget()
        layout = QVBoxLayout(root)
        header = QHBoxLayout()
        self.document_selector = QComboBox()
        self.import_file_button = QPushButton("Import File")
        self.import_file_button.setObjectName("annotation-import-file")
        self.import_file_button.setToolTip(
            "Import TXT, CSV, TSV, XML, EAF, TextGrid, JSON, XLSX, ODS, audio, or video into this project."
        )
        self.import_file_button.clicked.connect(lambda _checked=False: self.import_file())
        self.run_lid_button = QPushButton("Run Local LID")
        self.run_lid_button.setObjectName("annotation-run-local-lid")
        self.run_lid_button.setToolTip("Run fully local language identification for the selected document.")
        self.run_lid_button.clicked.connect(lambda _checked=False: self.run_lid())
        self.coarse_group_gate_checkbox = QCheckBox("Coarse group gate")
        self.coarse_group_gate_checkbox.setObjectName("annotation-coarse-group-gate")
        self.coarse_group_gate_checkbox.setToolTip(
            "Default off. When enabled, closely related language evidence can block risky auto labels while keeping suggestions."
        )
        header.addWidget(QLabel("Document"))
        header.addWidget(self.document_selector)
        header.addWidget(self.import_file_button)
        header.addWidget(self.run_lid_button)
        header.addWidget(self.coarse_group_gate_checkbox)
        layout.addLayout(header)
        layout.addWidget(QLabel("Waveform: link media to show local waveform peaks."))
        self.status_label = QLabel("No token rows loaded")
        layout.addWidget(self.status_label)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Token", "Language", "Source", "Confidence", "Memo"])
        self.table.cellChanged.connect(self._cell_changed)
        layout.addWidget(self.table)
        self.memo = QTextEdit()
        self.memo.setPlaceholderText("Selected-token memo")
        layout.addWidget(self.memo)
        self.widget = root
        self.refresh_documents()
        self.document_selector.currentIndexChanged.connect(lambda _index: self._document_changed())
        return root

    def refresh_documents(self) -> None:
        """Load documents into the selector."""

        if self.widget is None:
            return
        from imbizo.persistence.repositories import TranscriptRepository

        documents = TranscriptRepository(self.context.connection).list_documents()
        self.document_selector.blockSignals(True)
        self.document_selector.clear()
        for document in documents:
            self.document_selector.addItem(document.name, document.id)
        self.document_selector.blockSignals(False)
        if documents:
            self.document_id = documents[0].id
            self.load_document(documents[0].id)

    def import_file(self) -> None:
        """Import a local transcript or media file into the open project."""

        from PySide6.QtWidgets import QFileDialog, QMessageBox

        self._set_status("Opening import file dialog...")
        path, _ = QFileDialog.getOpenFileName(
            self.widget,
            "Import local file",
            "",
            (
                "Supported files (*.txt *.text *.md *.markdown *.log *.srt *.vtt *.csv *.tsv *.xml *.eaf *.TextGrid *.textgrid "
                "*.json *.xlsx *.ods *.wav *.mp3 *.flac *.mp4 *.mkv);;All files (*)"
            ),
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if not path:
            self._set_status("Import cancelled.")
            return
        try:
            self._set_status(f"Importing {Path(path).name}...")
            result = import_file_with_progress(
                self.widget,
                self.context,
                Path(path),
                self.import_service,
                "Importing local file",
            )
        except Exception as exc:  # noqa: BLE001 - GUI boundary shows plain-language errors.
            self._set_status(f"Import failed: {exc}")
            QMessageBox.critical(self.widget, "Import failed", str(exc))
            return

        self.refresh_documents()
        if result.bundle.document is not None:
            self._select_document(result.bundle.document.id)
        self._set_status(f"Imported {result.copied_path.name}: {result.report}")
        QMessageBox.information(
            self.widget,
            "Import complete",
            f"Imported {result.copied_path.name}: {result.report}",
        )

    def load_document(self, document_id: str) -> None:
        """Load one document into the annotation grid."""

        if self.table is None:
            return
        from imbizo.persistence.repositories import TranscriptRepository

        self.document_id = document_id
        transcript_repo = TranscriptRepository(self.context.connection)
        total_token_rows = transcript_repo.count_tokens_for_document(document_id)
        state = self.annotation_service.load_editor_state(
            self.context,
            document_id,
            token_limit=MAX_VISIBLE_TOKEN_ROWS,
        )
        if not state.rows and document_id not in self._repair_attempted_document_ids:
            self._repair_attempted_document_ids.add(document_id)
            if self._try_repair_empty_document(document_id):
                return
        self.languages_by_name = {language.name: language.id for language in state.languages}
        self.language_names_by_id = {language.id: language.name for language in state.languages}
        visible_rows = state.rows
        self.table.blockSignals(True)
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(visible_rows))
        for row_index, row in enumerate(visible_rows):
            self.table.setItem(row_index, 0, self._item(row.token.token_text, row.token.id))
            language_name = self._language_name(row.annotation.language_id if row.annotation else None)
            confidence = ""
            if row.annotation:
                confidence = str(row.annotation.researcher_confidence or row.annotation.auto_confidence or "")
            source = row.annotation.source.value if row.annotation else ""
            self.table.setItem(row_index, 1, self._item(language_name, row.token.id))
            self.table.setItem(row_index, 2, self._item(source, row.token.id))
            self.table.setItem(row_index, 3, self._item(confidence, row.token.id))
            self.table.setItem(row_index, 4, self._item(row.annotation.memo if row.annotation else "", row.token.id))
        self.table.setUpdatesEnabled(True)
        self.table.blockSignals(False)
        if self.status_label is not None:
            if total_token_rows > len(visible_rows):
                total_rows = f"{total_token_rows:,}"
                self.status_label.setText(
                    f"Showing first {len(visible_rows):,} of {total_rows} token rows. "
                    "Use the Spreadsheet tab search for focused review."
                )
            else:
                self.status_label.setText(f"{len(state.rows):,} token rows")

    def run_lid(self) -> None:
        """Run local LID for the current document and refresh the grid."""

        from PySide6.QtWidgets import QMessageBox

        self._set_status("Starting Local LID...")
        if not self.document_id:
            self._set_status("No document selected for Local LID.")
            QMessageBox.information(
                self.widget,
                "No document selected",
                "Import or select a transcript before running Local LID.",
            )
            return
        use_coarse_group_gate = bool(
            self.coarse_group_gate_checkbox is not None and self.coarse_group_gate_checkbox.isChecked()
        )
        try:
            report = run_lid_with_progress(
                self.widget,
                self.context,
                self.document_id,
                self.lid_service,
                options=LidOptions(use_coarse_group_gate=use_coarse_group_gate),
            )
        except Exception as exc:  # noqa: BLE001 - GUI boundary shows plain-language errors.
            self._set_status(f"Local LID failed: {exc}")
            QMessageBox.critical(self.widget, "Local LID failed", str(exc))
            return
        self.load_document(self.document_id)
        method_note = f"\nProvider: {report.provider_method}."
        if report.provider_message:
            method_note += f"\nNote: {report.provider_message}"
        gate_note = ""
        if report.coarse_group_gate_enabled:
            gate_note = (
                "\nCoarse group gate: "
                f"withheld {report.coarse_group_gated_count:,} risky auto labels "
                f"({report.coarse_group_ambiguous_count:,} closely-related, "
                f"{report.coarse_group_low_confidence_count:,} low-confidence)."
            )
        self._set_status(
            "Local LID complete: "
            f"{report.auto_annotations_count:,} auto labels, "
            f"{report.suggestions_count:,} suggestions"
            f"{'; coarse gate withheld ' + format(report.coarse_group_gated_count, ',') if report.coarse_group_gate_enabled else ''}."
        )
        QMessageBox.information(
            self.widget,
            "Local LID complete",
            (
                f"Saved {report.suggestions_count} suggestions and applied "
                f"{report.auto_annotations_count} useful auto labels.\n"
                f"Skipped {report.skipped_unknown_count} uncertain Unknown labels; "
                f"preserved {report.preserved_manual_count} manual labels."
                f"{gate_note}"
                f"{method_note}"
            ),
        )

    def _document_changed(self) -> None:
        document_id = self.document_selector.currentData()
        if document_id:
            self.load_document(str(document_id))

    def _select_document(self, document_id: str) -> None:
        if self.document_selector is None:
            return
        for index in range(self.document_selector.count()):
            if self.document_selector.itemData(index) == document_id:
                self.document_selector.setCurrentIndex(index)
                self.load_document(document_id)
                return

    def _try_repair_empty_document(self, document_id: str) -> bool:
        """Attempt to fill a zero-token document from its preserved import copy."""

        from PySide6.QtWidgets import QMessageBox

        try:
            result = repair_empty_document_with_progress(
                self.widget,
                self.context,
                document_id,
                self.import_service,
                "Repairing empty imported document",
            )
        except Exception as exc:  # noqa: BLE001 - GUI boundary shows plain-language errors.
            if self.status_label is not None:
                self.status_label.setText("0 token rows. Repair failed; import the source file again.")
            QMessageBox.warning(self.widget, "Repair failed", str(exc))
            return False
        if result is None:
            if self.status_label is not None:
                self.status_label.setText("0 token rows. Import the source file again to populate this project.")
            return False
        self.refresh_documents()
        self._select_document(document_id)
        QMessageBox.information(
            self.widget,
            "Empty import repaired",
            f"Recovered {result.report.get('tokens', 0):,} tokens from the preserved local import copy.",
        )
        return True

    def _cell_changed(self, row: int, column: int) -> None:
        if self.table is None or column not in {1, 4}:
            return
        token_item = self.table.item(row, 0)
        token_id = token_item.data(256) if token_item else None
        if not token_id:
            return
        language_name = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
        memo = self.table.item(row, 4).text() if self.table.item(row, 4) else ""
        self.annotation_service.save_token_annotation(
            self.context,
            str(token_id),
            AnnotationDraft(language_id=self.languages_by_name.get(language_name, language_name or None), memo=memo),
        )
        if self.document_id:
            self.load_document(self.document_id)

    def _language_name(self, language_id: str | None) -> str:
        if not language_id:
            return ""
        return self.language_names_by_id.get(language_id, language_id)

    def _item(self, text: str, token_id: str) -> Any:
        from PySide6.QtWidgets import QTableWidgetItem

        item = QTableWidgetItem(text)
        item.setData(256, token_id)
        return item

    def _set_status(self, message: str) -> None:
        """Update the visible status line and emit a console log for GUI actions."""

        LOGGER.info("Annotation editor: %s", message)
        if self.status_label is not None:
            self.status_label.setText(message)
        try:
            from PySide6.QtWidgets import QApplication

            QApplication.processEvents()
        except Exception:  # noqa: BLE001 - status updates must never break GUI actions.
            LOGGER.debug("Could not process Qt events during status update", exc_info=True)
