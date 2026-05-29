"""Spreadsheet-style annotation view."""

from __future__ import annotations

from typing import Any

from imbizo.domain.annotations import AnnotationDraft
from imbizo.persistence.repositories import TranscriptRepository
from imbizo.services.annotation_service import AnnotationService


TOKEN_ID_ROLE = 256


class SpreadsheetViewWidget:
    """Excel-like annotation grid over imported project transcripts.

    The view is intentionally local and SQLite-backed. It gives researchers a
    dense tabular surface for scanning many tokens, with direct edits for the
    two lowest-risk fields: language label and memo.
    """

    def __init__(self, context: Any, annotation_service: AnnotationService | None = None) -> None:
        self.context = context
        self.annotation_service = annotation_service or AnnotationService()
        self.widget = None
        self.table = None
        self.document_filter = None
        self.search_box = None
        self.status_label = None
        self.languages_by_label: dict[str, str] = {}
        self._is_loading = False

    def build(self) -> Any:
        """Build and return a PySide6 widget."""

        from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QVBoxLayout, QWidget

        page = QWidget()
        layout = QVBoxLayout(page)
        toolbar = QHBoxLayout()

        self.document_filter = QComboBox()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter tokens or memos")
        refresh_button = QPushButton("Refresh")
        self.status_label = QLabel("No rows loaded")

        toolbar.addWidget(QLabel("Document"))
        toolbar.addWidget(self.document_filter, 2)
        toolbar.addWidget(QLabel("Search"))
        toolbar.addWidget(self.search_box, 2)
        toolbar.addWidget(refresh_button)
        toolbar.addWidget(self.status_label)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(
            ["Document", "Segment", "Token #", "Token", "Language", "Source", "Confidence", "Switch", "Status", "Memo"]
        )
        self.table.cellChanged.connect(self._cell_changed)
        layout.addWidget(self.table)

        refresh_button.clicked.connect(self.refresh)
        self.document_filter.currentIndexChanged.connect(self.refresh)
        self.search_box.textChanged.connect(self.refresh)
        self.widget = page
        self.refresh_documents()
        self.refresh()
        return page

    def refresh_documents(self) -> None:
        """Reload the document selector from the open project."""

        if self.document_filter is None:
            return
        documents = TranscriptRepository(self.context.connection).list_documents()
        current = self.document_filter.currentData()
        self.document_filter.blockSignals(True)
        self.document_filter.clear()
        self.document_filter.addItem("All imported documents", "")
        for document in documents:
            self.document_filter.addItem(document.name, document.id)
        if current:
            for index in range(self.document_filter.count()):
                if self.document_filter.itemData(index) == current:
                    self.document_filter.setCurrentIndex(index)
                    break
        self.document_filter.blockSignals(False)

    def refresh(self) -> None:
        """Reload spreadsheet rows from SQLite."""

        if self.table is None:
            return
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QAbstractItemView

        document_id = str(self.document_filter.currentData() or "") if self.document_filter is not None else ""
        search = self.search_box.text().strip().lower() if self.search_box is not None else ""
        documents = TranscriptRepository(self.context.connection).list_documents()
        selected_documents = [document for document in documents if not document_id or document.id == document_id]
        rows: list[tuple[str, int, Any]] = []
        languages_seen = {}
        for document in selected_documents:
            state = self.annotation_service.load_editor_state(self.context, document.id)
            for language in state.languages:
                languages_seen[language.name] = language.id
                languages_seen[language.code] = language.id
            for row in state.rows:
                haystack = f"{row.token.token_text} {row.annotation.memo if row.annotation else ''}".lower()
                if search and search not in haystack:
                    continue
                rows.append((document.name, row.segment.sort_order, row))

        self.languages_by_label = languages_seen
        self._is_loading = True
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for row_index, (document_name, segment_order, row) in enumerate(rows):
            annotation = row.annotation
            language_name = self._language_name(annotation.language_id if annotation else None)
            confidence = ""
            if annotation is not None:
                confidence_value = annotation.researcher_confidence or annotation.auto_confidence
                confidence = str(confidence_value or "")
            values = [
                document_name,
                str(segment_order),
                str(row.token.sort_order),
                row.token.token_text,
                language_name,
                annotation.source.value if annotation else "",
                confidence,
                annotation.switch_type.value if annotation and annotation.switch_type else "",
                annotation.status.value if annotation else "",
                annotation.memo if annotation else "",
            ]
            for column, value in enumerate(values):
                editable = column in {4, 9}
                self.table.setItem(row_index, column, self._item(value, row.token.id, editable=editable))
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)
        self._is_loading = False
        if self.status_label is not None:
            self.status_label.setText(f"{len(rows):,} token rows")
        self.table.setAccessibleName("Spreadsheet annotation table")
        self.table.setToolTip("Edit Language or Memo cells directly. Other cells are read-only project evidence.")

    def _cell_changed(self, row: int, column: int) -> None:
        """Persist direct spreadsheet edits for language and memo cells."""

        if self._is_loading or self.table is None or column not in {4, 9}:
            return
        token_item = self.table.item(row, 3)
        token_id = token_item.data(TOKEN_ID_ROLE) if token_item else None
        if not token_id:
            return
        language_label = self.table.item(row, 4).text().strip() if self.table.item(row, 4) else ""
        memo = self.table.item(row, 9).text() if self.table.item(row, 9) else ""
        self.annotation_service.save_token_annotation(
            self.context,
            str(token_id),
            AnnotationDraft(language_id=self.languages_by_label.get(language_label, language_label or None), memo=memo),
        )
        self.refresh()

    def _language_name(self, language_id: str | None) -> str:
        if not language_id:
            return ""
        from imbizo.persistence.repositories import LanguageRepository

        for language in LanguageRepository(self.context.connection).list_languages():
            if language.id == language_id:
                return language.name
        return language_id

    def _item(self, text: str, token_id: str, *, editable: bool) -> Any:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QTableWidgetItem

        item = QTableWidgetItem(text)
        item.setData(TOKEN_ID_ROLE, token_id)
        flags = item.flags()
        if editable:
            item.setFlags(flags | Qt.ItemFlag.ItemIsEditable)
        else:
            item.setFlags(flags & ~Qt.ItemFlag.ItemIsEditable)
        return item
