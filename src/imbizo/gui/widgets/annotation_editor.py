"""Fully wired annotation editor widget."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from imbizo.domain.annotations import AnnotationDraft
from imbizo.gui.import_progress import import_file_with_progress
from imbizo.services.import_service import ImportService


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
        self.languages_by_name: dict[str, str] = {}

    def build(self) -> Any:
        """Build and return the PySide6 widget."""

        try:
            from PySide6.QtWidgets import (
                QComboBox,
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
        import_file = QPushButton("Import File")
        import_file.clicked.connect(self.import_file)
        run_lid = QPushButton("Run Local LID")
        run_lid.clicked.connect(self.run_lid)
        header.addWidget(QLabel("Document"))
        header.addWidget(self.document_selector)
        header.addWidget(import_file)
        header.addWidget(run_lid)
        layout.addLayout(header)
        layout.addWidget(QLabel("Waveform: link media to show local waveform peaks."))
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Token", "Language", "Source", "Confidence", "Memo"])
        self.table.cellChanged.connect(self._cell_changed)
        layout.addWidget(self.table)
        self.memo = QTextEdit()
        self.memo.setPlaceholderText("Selected-token memo")
        layout.addWidget(self.memo)
        self.widget = root
        self.refresh_documents()
        self.document_selector.currentIndexChanged.connect(self._document_changed)
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

        path, _ = QFileDialog.getOpenFileName(
            self.widget,
            "Import local file",
            "",
            (
                "Supported files (*.txt *.csv *.tsv *.xml *.eaf *.TextGrid *.textgrid "
                "*.json *.xlsx *.ods *.wav *.mp3 *.flac *.mp4 *.mkv);;All files (*)"
            ),
        )
        if not path:
            return
        try:
            result = import_file_with_progress(
                self.widget,
                self.context,
                Path(path),
                self.import_service,
                "Importing local file",
            )
        except Exception as exc:  # noqa: BLE001 - GUI boundary shows plain-language errors.
            QMessageBox.critical(self.widget, "Import failed", str(exc))
            return

        self.refresh_documents()
        if result.bundle.document is not None:
            self._select_document(result.bundle.document.id)
        QMessageBox.information(
            self.widget,
            "Import complete",
            f"Imported {result.copied_path.name}: {result.report}",
        )

    def load_document(self, document_id: str) -> None:
        """Load one document into the annotation grid."""

        if self.table is None:
            return
        self.document_id = document_id
        state = self.annotation_service.load_editor_state(self.context, document_id)
        self.languages_by_name = {language.name: language.id for language in state.languages}
        self.table.blockSignals(True)
        self.table.setRowCount(len(state.rows))
        for row_index, row in enumerate(state.rows):
            self.table.setItem(row_index, 0, self._item(row.token.token_text, row.token.id))
            self.table.setItem(row_index, 1, self._item(self._language_name(row.annotation.language_id if row.annotation else None), row.token.id))
            self.table.setItem(row_index, 2, self._item(row.annotation.source.value if row.annotation else "", row.token.id))
            self.table.setItem(row_index, 3, self._item(str(row.annotation.researcher_confidence or row.annotation.auto_confidence or "") if row.annotation else "", row.token.id))
            self.table.setItem(row_index, 4, self._item(row.annotation.memo if row.annotation else "", row.token.id))
        self.table.blockSignals(False)

    def run_lid(self) -> None:
        """Run local LID for the current document and refresh the grid."""

        if self.document_id:
            self.lid_service.run_lid_for_document(self.context, self.document_id)
            self.load_document(self.document_id)

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
        from imbizo.persistence.repositories import LanguageRepository

        for language in LanguageRepository(self.context.connection).list_languages():
            if language.id == language_id:
                return language.name
        return language_id

    def _item(self, text: str, token_id: str) -> Any:
        from PySide6.QtWidgets import QTableWidgetItem

        item = QTableWidgetItem(text)
        item.setData(256, token_id)
        return item
